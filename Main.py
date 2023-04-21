"""
<<Main>>

This Module is coded for extracting data from XML file related to ..., ..., ....
The output Data Structure is :....

"""
import haversine as hs

from configs.config import Configs
import utils.util as util
import Hash
from Zone import ZoneID

__author__ = "Pouya 'Adrian' Firouzmakan"

configs = Configs().config

area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
area_zones.zones()


class DataTable:
    # This class is determined for defining the hash_table, updating data, routing messages,
    # and defining IP addresses by using trace (which is sumo_trace)

    def __init__(self, config, zones):
        """

        :param config: look at options.py and config.py
        :param zones: all the zones of the area
        """

        self.bus_table = Hash.HashTable(config.n_cars * 100)
        self.veh_table = Hash.HashTable(config.n_cars * 100)

        self.zone_vehicles = dict(zip(zones.zone_hash.ids(),
                                      [set() for j in range(len(zones.zone_hash.ids()))]
                                      )
                                  )
        self.zone_buses = dict(zip(zones.zone_hash.ids(),
                                   [set() for j in range(len(zones.zone_hash.ids()))]
                                   )
                               )
        self.zone_CH = {}
        self.time = config.start_time
        self.understudied_area = area_zones.understudied_area()
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            # the bus_table will be initiated here for the very first time
            if 'bus' in veh.getAttribute('id'):
                self.bus_table.set_item(veh.getAttribute('id'), util.initiate_new_bus(veh, zones, zone_id, config,
                                                                                      self.understudied_area))
                # Here the buses will be added to zone_buses
                self.zone_buses[zone_id].add(veh.getAttribute('id'))

                # the veh_table will be initiated here for the very first time self.understudied_area))
            else:
                self.veh_table.set_item(veh.getAttribute('id'), util.initiate_new_veh(veh, zones, zone_id, config,
                                                                                      self.understudied_area))
                # Here the vehicles will be added to zone_vehicles
                self.zone_vehicles[zone_id].add(veh.getAttribute('id'))

    def update(self, config, zones):
        """
        this method updates the bus_table and veh_table values for the current interval.
        Attention: The properties related to clusters and IP addresses are going to be updated here
        :return:
        """
        self.time += 1
        bus_ids = set()
        veh_ids = set()
        zone_buses = set()  # to remove the buses that leave the area
        vehicles = set()    # to remove the vehicles that leave the area
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            self.zone_vehicles = dict(zip(zones.zone_hash.ids(),
                                          [set() for j in range(len(zones.zone_hash.ids()))]
                                          )
                                      )
            self.zone_buses = dict(zip(zones.zone_hash.ids(),
                                       [set() for j in range(len(zones.zone_hash.ids()))]
                                       )
                                   )
            # update the bus_table for the time step
            if 'bus' in veh.getAttribute('id'):
                bus_ids.add(veh.getAttribute('id'))
                self.bus_table, self.zone_buses = util.update_bus_table(veh, self.bus_table, zone_id,
                                                                        self.understudied_area, zones,
                                                                        config, self.zone_buses)
            else:
                veh_ids.add(veh.getAttribute('id'))
                self.veh_table, self.zone_vehicles = util.update_veh_table(veh, self.veh_table, zone_id,
                                                                           self.understudied_area, zones,
                                                                           config, self.zone_vehicles)
        #  turning in_area index of the buses left the area to False
        for k in (self.bus_table.ids() - bus_ids):
            self.bus_table.values(k)['in_area'] = False
        #  turning in_area index of the vehicles left the area to False
        for k in (self.veh_table.ids() - veh_ids):
            self.veh_table.values(k)['in_area'] = False

    def find_update_cluster(self, veh_id):
        """
        This method is designed for finding a cluster for veh_id
        :return: cluster heads and connection between them including through the bridges
        """
        # checking if the vehicle is in the understudied-area & if it's not in any cluster & if it's not a CH
        if (self.veh_table.values(veh_id)['in_area'] is True) & (self.veh_table.values(veh_id)['primary_CH'] is None) \
                & (self.veh_table.values(veh_id)['cluster_head'] is False):

            bus_candidates = []
            neigh_bus = []
            for neigh_z in self.veh_table.values(veh_id)['neighbor_zones']:
                neigh_bus += self.zone_buses[neigh_z]        # adding all the vehicles in the neighbor zones to a list

            for j in neigh_bus:
                euclidian_dist = hs.haversine((self.veh_table.values(veh_id)["long"],
                                               self.veh_table.values(veh_id)["lat"]),
                                              (self.bus_table.values(j)['long'],
                                               self.bus_table.values(j)['lat']), unit=hs.Unit.METERS)

                if euclidian_dist <= min(self.veh_table.values(veh_id)['trans_range'], self.bus_table(veh_id)):
                    bus_candidates.append(j)

            if len(bus_candidates) > 0:
                if len(bus_candidates) == 1:
                    self.veh_table.values(veh_id)['primary_CH'] = j
                    self.veh_table.values(veh_id)['other_CHs'] = []
                    self.bus_table.values(j)['cluster_members'].add_vertex(veh_id)
                    self.bus_table.values(j)['cluster_members'].add_edge(j, veh_id)
                else:
                    bus_ch = util.det_bus_ch(self.bus_table, self.veh_table.values(veh_id),
                                             area_zones,
                                             bus_candidates)  # determine the most suitable from bus_candidates

                    self.veh_table.values(veh_id)['primary_CH'] = bus_ch
                    bus_candidates.remove(bus_ch)
                    self.veh_table(veh_id)['other_CHs'] = bus_candidates
                    self.bus_table.values(bus_ch)['cluster_members'].add_vertex([bus_ch, veh_id])
                    self.bus_table.values(bus_ch)['cluster_members'].add_edge(bus_ch, veh_id)

    def print_table(self):
        self.bus_table.print_hash_table()
        self.veh_table.print_hash_table()


a = DataTable(configs, area_zones)
a.update(configs, area_zones)
a.find_update_cluster('veh250')
print('bus-ids: ', a.bus_table.ids())
print('vehicles-ids: ', a.veh_table.ids())
print('\n')
a.print_table()

