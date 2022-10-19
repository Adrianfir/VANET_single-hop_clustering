import xml.dom.minidom

my_tree = xml.dom.minidom.parse("sumoTrace_test.xml")

fcd = my_tree.documentElement

times = fcd.getElementsByTagName('timestep')

print
