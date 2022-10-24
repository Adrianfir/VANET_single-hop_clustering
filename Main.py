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
car_hash = Hash.HashTable(number_of_cars)

for each_second in times[0:10]:
    for veh in each_second.childNodes[1::2]:
        car_hash.set_item(veh.getAttribute('id'),
                          dict(x=veh.getAttribute('x'),
                               y=veh.getAttribute('y'),
                               angle=veh.getAttribute('angle'),
                               speed=veh.getAttribute('speed'),
                               pos=veh.getAttribute('pos'),
                               lane=veh.getAttribute('lane'))
                          )


car_hash.print_hash_table()
