"""
<<Main>>

This Module is coded for extracting data from XML file related to ..., ..., ....
The output Data Structure is :....

"""

# /Users/pouyafirouzmakan/Desktop/VANET/small_data_Richmondhill/sumoTrace_geo.xml

import random
import xml.dom.minidom
import haversine as hs

from configs.config import Configs
import utils.util as util
import Hash
from Zone import ZoneID

__author__ = "Pouya Firouzmakan"
__all__ = []

config = Configs().config

area_zones = ZoneID(config)  # This is a hash table including all zones and their max and min lat and longs
area_zones.zones()


class DataTable:
    # This class is determined for defining the hash_table, updating data, routing messages,
    # and defining IP addresses by using trace (which is sumo_trace)

    def __init__(self, configs, zones):
        """

        :param trace: sumo_trace file from SUMO
        :param n_cars: number of cars
        :param zones: all the zones of the area
        """

        self.bus_table = Hash.HashTable(config.n_cars * 100)
        self.veh_table = Hash.HashTable(config.n_cars * 100)

        self.zone_vehicles = {}
        self.zone_buses = {}
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[0].childNodes[1::2]:
            if 'bus' in veh.getAttribute('id'):
                zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                         float(veh.getAttribute('x'))
                                         )
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
                                             cluster={},
                                             trans_range=500
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
                                             head_cluster=None,
                                             IP=None,
                                             MAC=util.mac_address(),  # The mac address of each car is determined
                                             # using mac_address method
                                             in_area=True,
                                             trans_range=500
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

    def print_table(self):
        self.bus_table.print_hash_table()
        self.veh_table.print_hash_table()

    def gen_clusters(self):
        for i in self.bus_table.ids():
            for j in self.bus_table.values(i)['neighbor_zones']:
                if j in self.zone_vehicles:
                    if self.zone_vehicles[j] is not None:
                        for k in self.zone_vehicles[j]:
                            if self.veh_table.values(k)['head_cluster'] is None:
                                if hs.haversine((self.veh_table.values(k)["long"], self.veh_table.values(k)["lat"]),
                                                (self.bus_table.values(i)['long'], self.bus_table.values(i)['lat']),
                                                unit=hs.Unit.KILOMETERS
                                                ) <= min(self.veh_table.values(k)['trans_range'],
                                                         self.bus_table(i)) / 1000:
                                    # /1000 is for converting meter to kilometer
                                    self.veh_table.values(k)['head_cluster'] = i  # add "i" as the head cluster for k
                                    self.bus_table.values(i)['cluster'][k] = {'MAC': self.veh_table.values(k)['MAC']}

    # def det_IP(self):

a = DataTable(config, area_zones)
a.gen_clusters()
a.print_table()
