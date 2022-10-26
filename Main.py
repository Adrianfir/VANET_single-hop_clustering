"""
<<Main>>

This Module is coded for extracting data from XML file related to ..., ..., ....
The output Data Structure is :....
"""

import xml.dom.minidom

import Hash

__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

sumoTrace_address = input("Please Input sumoTrace.xml file's address: ")
osmPoly_address = input("Please Input osm.poly.xml file's address: ")

# this file is the sumoTrace.xml file extracted from SUMO
sumo_trace = xml.dom.minidom.parse(sumoTrace_address)
fcd = sumo_trace.documentElement                           # Floating Car Data (FCD) from sumoTrace.xml
times = fcd.getElementsByTagName('timestep')               # includes data for all seconds

# for extracting min_long, min_lat, max_long. max_lat
osm_poly = xml.dom.minidom.parse(osmPoly_address)
location = osm_poly.documentElement.getElementsByTagName('location')[0].\
    getAttribute('origBoundary')                           # receives a string
location = location.split(",")                             # split the string to a list of strings
location = [float(x) for x in location]                    # float the strings in the list
min_long = location[1]
min_lat = location[0]
max_long = location[3]
max_lat = location[2]

number_of_cars = 1000


class DataTable:
    # This class is determined for defining the hash_table, updating data, routing messages,
    # and defining IP addresses by using trace (which is sumo_trace) and location information
    # obtained from osm.poly.xml file
    def __init__(self, trace, n_cars):
        self.table = Hash.HashTable(n_cars)
        for veh in trace.documentElement.getElementsByTagName('timestep')[0].childNodes[1::2]:
            if 'bus' in veh.getAttribute('id'):
                self.table.set_item(veh.getAttribute('id'),
                                    dict(x=veh.getAttribute('x'),
                                         y=veh.getAttribute('y'),
                                         angle=veh.getAttribute('angle'),
                                         speed=veh.getAttribute('speed'),
                                         pos=veh.getAttribute('pos'),
                                         lane=veh.getAttribute('lane'),
                                         message_dest={},
                                         message_source={},
                                         IP=None,
                                         cluster_IPs={},
                                         cluster_MACs={}
                                         )
                                    )
            else:
                self.table.set_item(veh.getAttribute('id'),
                                    dict(x=veh.getAttribute('x'),
                                         y=veh.getAttribute('y'),
                                         angle=veh.getAttribute('angle'),
                                         speed=veh.getAttribute('speed'),
                                         pos=veh.getAttribute('pos'),
                                         lane=veh.getAttribute('lane'),
                                         caluster_head={},
                                         IP=None)
                                    )

    def print_table(self):
        self.table.print_hash_table()

        def print_table(self):
            self


my = DataTable(sumo_trace, number_of_cars)
my.print_table()