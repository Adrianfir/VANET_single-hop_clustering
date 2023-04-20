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
from Graph import Graph

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

        # global zone_id
        self.bus_table = Hash.HashTable(config.n_cars * 100)
        self.veh_table = Hash.HashTable(config.n_cars * 100)

        self.zone_vehicles = dict(zip(zones.zone_hash.ids(),
                                      [[] for i in range(len(zones.zone_hash.ids()))]
                                      )
                                  )
        self.zone_buses = dict(zip(zones.zone_hash.ids(),
                                   [[] for i in range(len(zones.zone_hash.ids()))]
                                   )
                               )
        self.zone_CH = {}
        self.time = config.start_time
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            # the bus_table will be initiated here for the very first time
            self.understudied_area = area_zones.understudied_area()
            if 'bus' in veh.getAttribute('id'):
                self.bus_table.set_item(veh.getAttribute('id'), util.initiate_new_bus(veh, zones, zone_id, config,
                                                                                      self.understudied_area))

                # the veh_table will be initiated here for the very first time self.understudied_area))
            else:
                self.veh_table.set_item(veh.getAttribute('id'), util.initiate_new_veh(veh, zones, zone_id, config,
                                                                                      self.understudied_area))

            # Here the vehicles and buses will be added to and zone_vehicles zone_buses
            if 'bus' in veh.getAttribute('id'):
                self.zone_buses[zone_id].append(veh.getAttribute('id'))
            else:
                self.zone_vehicles[zone_id].append(veh.getAttribute('id'))

    def update(self, config, zones):
        """
        this method updates the bus_table and veh_table values for the current interval.
        Attention: The properties related to clusters and IP addresses are going to be updated here
        :return:
        """
        self.time += 1
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            if 'bus' in veh.getAttribute('id'):
                try:
                    self.bus_table.values(veh.getAttribute('id'))['prev_zone'] = \
                        self.bus_table.values(veh.getAttribute('id'))['zone']  # update prev_zone

                    self.bus_table.values(veh.getAttribute('id'))['long'] = veh.getAttribute('x')
                    self.bus_table.values(veh.getAttribute('id'))['lat'] = veh.getAttribute('y')
                    self.bus_table.values(veh.getAttribute('id'))['angle'] = veh.getAttribute('angle')
                    self.bus_table.values(veh.getAttribute('id'))['speed'] = veh.getAttribute('speed')
                    self.bus_table.values(veh.getAttribute('id'))['pos'] = veh.getAttribute('pos')
                    self.bus_table.values(veh.getAttribute('id'))['lane'] = veh.getAttribute('lane')
                    self.bus_table.values(veh.getAttribute('id'))['zone'] = zone_id
                    self.bus_table.values(veh.getAttribute('id'))['in_area'] = \
                        util.presence(self.understudied_area, veh)
                    self.bus_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)

                    self.zone_buses[zone_id].append(veh.getAttribute('id'))
                    try:
                        self.zone_buses[self.bus_table.values(veh.getAttribute('id'))['prev_zone']]. \
                            remove(veh.getAttribute('id'))  # This will remove the vehicle from its previous zone_buses
                    except KeyError:
                        self.bus_table.set_item(veh.getAttribute('id'),
                                                util.initiate_new_bus(veh, zones, zone_id, config,
                                                                      self.understudied_area
                                                                      )
                                                )
                except TypeError:
                    self.bus_table.set_item(veh.getAttribute('id'), util.initiate_new_bus(veh, zones, zone_id, config,
                                                                                          self.understudied_area))

            else:
                try:
                    self.veh_table.values(veh.getAttribute('id'))['long'] = veh.getAttribute('x')
                    self.veh_table.values(veh.getAttribute('id'))['lat'] = veh.getAttribute('y')
                    self.veh_table.values(veh.getAttribute('id'))['angle'] = veh.getAttribute('angle')
                    self.veh_table.values(veh.getAttribute('id'))['speed'] = veh.getAttribute('speed')
                    self.veh_table.values(veh.getAttribute('id'))['pos'] = veh.getAttribute('pos')
                    self.veh_table.values(veh.getAttribute('id'))['lane'] = veh.getAttribute('lane')
                    self.veh_table.values(veh.getAttribute('id'))['zone'] = zone_id
                    self.veh_table.values(veh.getAttribute('id'))['in_area'] = util.presence(self.understudied_area,
                                                                                             veh)
                    self.veh_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)

                    self.zone_vehicles[zone_id].append(veh.getAttribute('id'))
                    try:
                        self.zone_vehicles[self.veh_table.values(veh.getAttribute('id'))['prev_zone']]. \
                            remove(veh.getAttribute('id'))  # remove the vehicle from its previous zone_vehicles
                    except KeyError:
                        # initiate the vehicle
                        self.veh_table.set_item(veh.getAttribute('id'),
                                                util.initiate_new_veh(veh, zones, zone_id, config,
                                                                      self.understudied_area
                                                                      )
                                                )
                except TypeError:
                    self.veh_table.set_item(veh.getAttribute('id'), util.initiate_new_veh(veh, zones, zone_id, config,
                                                                                          self.understudied_area))

    def find_update_cluster(self, veh_id):
        """
        This method is designed for finding a cluster for veh_id
        :return: cluster heads and connection between them including through the bridges
        """
        # checking if the vehicle is in the understudied-area & if it's not in any cluster & if it's not a CH
        if (self.veh_table.values(veh_id)['in_area'] is True) & (self.veh_table.values(veh_id)['primary_CH'] is None) \
                & (self.veh_table.values(veh_id)['cluster_head'] is False):
            bus_candidates = []
            for neigh_z in self.veh_table.values(veh_id)['neighbor_zones']:
                if len(self.zone_buses[neigh_z]) != 0:
                    for j in self.zone_buses[neigh_z]:
                        if hs.haversine((self.veh_table.values(veh_id)["long"],
                                         self.veh_table.values(veh_id)["lat"]),
                                        (self.bus_table.values(j)['long'], self.bus_table.values(j)['lat']),
                                        unit=hs.Unit.METERS) <= min(self.veh_table.values(veh_id)['trans_range'],
                                                                    self.bus_table(veh_id)):
                            bus_candidates.append(j)

                # else:

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


if __name__ == '__main__':
    a = DataTable(configs, area_zones)
    for i in range(10):
        a.update(configs, area_zones)
    print('bus-ids: ', a.bus_table.ids())
    print('vehicles-ids: ', a.veh_table.ids())
    print('\n')
    a.print_table()
