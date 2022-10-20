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

car_tabel = hash
for each_second in times[0:11]:
    print('-------------------')
    print(f"Second: {each_second.getAttribute('time')}")
    for att in each_second.childNodes[1::2]:
        print(f"---- id: {att.getAttribute('id')}")
