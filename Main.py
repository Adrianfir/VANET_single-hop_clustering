"""
<<Main>>

This Module is coded for extracting data from XML file related to ..., ..., ....
The output Data Structure is :....
"""

import xml.dom.minidom

import Hash

__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

sumoTrace_address = input("Please Input sumoTrace file's address: ")
sumo_trace = xml.dom.minidom.parse(sumoTrace_address)      # this file is the sumoTrace.xml file extracted from SUMO
fcd = sumo_trace.documentElement
times = fcd.getElementsByTagName('timestep')

number_of_cars = 1000


class DataTable:
    # This class is determined for defining the hash_table, updating data, routing messages,
    # and defining IP addresses
    def __init__(self, sumo_trace, n_cars):
        self.table = Hash.HashTable(n_cars)
        for veh in sumo_trace.documentElement.getElementsByTagName('timestep')[0].childNodes[1::2]:
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
