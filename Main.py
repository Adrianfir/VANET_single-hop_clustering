"""
<<Main>>

This Module is coded for extracting data from XML file related to ..., ..., ....
The output Data Structure is :....
"""

import xml.dom.minidom

import Hash

__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

my_tree = xml.dom.minidom.parse("sumoTrace_test.xml")
fcd = my_tree.documentElement
times = fcd.getElementsByTagName('timestep')

number_of_cars = 1000


class DataTable:

    def __init__(self, xml_tree, n_cars):
        self.table = Hash.HashTable(n_cars)
        for veh in xml_tree.documentElement.getElementsByTagName('timestep')[0].childNodes[1::2]:
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
            self


my = DataTable(my_tree, number_of_cars)
my.table.print_hash_table()
