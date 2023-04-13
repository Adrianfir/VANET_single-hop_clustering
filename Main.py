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

        self.zone_vehicles = {}
        self.zone_buses = {}
        self.time = config.start_time
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            understudied_area = area_zones.understudied_area()
            if 'bus' in veh.getAttribute('id'):
                self.bus_table.set_item(veh.getAttribute('id'),
                                        dict(long=veh.getAttribute('x'),
                                             lat=veh.getAttribute('y'),
                                             angle=veh.getAttribute('angle'),
                                             speed=veh.getAttribute('speed'),
                                             pos=veh.getAttribute('pos'),
                                             lane=veh.getAttribute('lane'),
                                             zone=zone_id,
                                             prev_zone=None,
                                             neighbor_zones=zones.neighbor_zones(zone_id),
                                             message_dest={},
                                             message_source={},
                                             MAC=util.mac_address(),
                                             IP=None,
                                             cluster_head=True,
                                             other_CHs=[],
                                             cluster_members=Graph(),
                                             bridges={},
                                             in_area=util.presence(understudied_area, veh),
                                             trans_range=config.trans_range
                                             )
                                        )
            else:
                self.veh_table.set_item(veh.getAttribute('id'),
                                        dict(long=veh.getAttribute('x'),
                                             lat=veh.getAttribute('y'),
                                             angle=veh.getAttribute('angle'),
                                             speed=veh.getAttribute('speed'),
                                             pos=veh.getAttribute('pos'),
                                             lane=veh.getAttribute('lane'),
                                             zone=zone_id,
                                             prev_zone=None,
                                             neighbor_zones=zones.neighbor_zones(zone_id),
                                             cluster_head=False,
                                             # if the vehicle is a CH, it will be changed to a Graph in the Clustering
                                             primary_CH=None,
                                             other_CHs=[],
                                             cluster_members={},
                                             IP=None,
                                             MAC=util.mac_address(),  # The mac address of each car is determined
                                             # using mac_address method
                                             in_area=util.presence(understudied_area, veh),
                                             trans_range=config.trans_range,
                                             counter=3  # a counter_time to search and join a cluster
                                             )
                                        )
            b = []  # Used for appending buses of a zone (As we need a list to do it)
            v = []  # Used for appending vehicles of a zone (As we need a list to do it)
            if 'bus' in veh.getAttribute('id'):
                self.zone_buses[zone_id] = \
                    b.append(veh.getAttribute('id'))
            else:
                self.zone_vehicles[zone_id] = \
                    v.append(veh.getAttribute('id'))

    def update(self, config, zones):
        """
        this method updates the bus_table and veh_table values for the current interval
        :return:
        """
        self.time += 1
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            if 'bus' in veh.getAttribute('id'):
                self.bus_table.values(veh.getAttribute('id'))['prev_zone'] = \
                    self.bus_table.values(veh.getAttribute('id'))['zone']  # update prev_zone

                self.bus_table.values(veh.getAttribute('id'))['long'] = veh.getAttribute('x')
                self.bus_table.values(veh.getAttribute('id'))['lat'] = veh.getAttribute('y')
                self.bus_table.values(veh.getAttribute('id'))['angle'] = veh.getAttribute('angle')
                self.bus_table.values(veh.getAttribute('id'))['speed'] = veh.getAttribute('speed')
                self.bus_table.values(veh.getAttribute('id'))['pos'] = veh.getAttribute('pos')
                self.bus_table.values(veh.getAttribute('id'))['lane'] = veh.getAttribute('lane')
                self.bus_table.values(veh.getAttribute('id'))['zone'] = zone_id
                self.bus_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)

    def print_table(self):
        self.bus_table.print_hash_table()
        self.veh_table.print_hash_table()

    def find_cluster(self, veh_id):
        """
        This method is designed for finding a cluster for veh_id
        :return: cluster heads and connection between them including through the bridges
        """

        if self.veh_table.values(veh_id)['cluster_head'] is None:
            bus_candidates = []
            for j in self.veh_table.values(veh_id)['neighbor_zones']:
                if 'bus' in j:
                    if hs.haversine((self.veh_table.values(veh_id)["long"], self.veh_table.values(veh_id)["lat"]),
                                    (self.bus_table.values(j)['long'], self.bus_table.values(j)['lat']),
                                    unit=hs.Unit.METERS) <= min(self.veh_table.values(veh_id)['trans_range'],
                                                                self.bus_table(veh_id)):
                        bus_candidates.append(veh_id)

                # else:

            if len(bus_candidates) > 0:
                if len(bus_candidates) == 1:
                    self.veh_table.values(veh_id)['primary_CH'] = j
                    self.veh_table.values(veh_id)['other_CHs'] = []
                    self.bus_table.values(j)['cluster_members'].add_vertex(veh_id)
                    self.bus_table.values(j)['cluster_members'].add_edge(j, veh_id)
                else:
                    bus_ch = util.det_bus_ch(self.bus_table,  # determine the most suitable from bus_candidates
                                             self.veh_table.values(veh_id),
                                             area_zones,
                                             bus_candidates)

                    self.veh_table.values(veh_id)['primary_CH'] = bus_ch
                    bus_candidates.remove(bus_ch)
                    self.veh_table(veh_id)['other_CHs'] = bus_candidates
                    self.bus_table.values(bus_ch)['cluster_members'].add_vertex(veh_id)
                    self.bus_table.values(bus_ch)['cluster_members'].add_edge(bus_ch, veh_id)


a = DataTable(configs, area_zones)
print('bus-ids: ', a.bus_table.ids())
print('vehicles-ids: ', a.veh_table.ids())
print('\n')
a.print_table()
