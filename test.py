import xml.dom.minidom
path = '/Users/pouyafirouzmakan/Desktop/VANET_single-hop_clustering/final_data_Richmondhill/osm_bbox.osm.xml'
node_info = dict()
file = xml.dom.minidom.parse(path)
for node in file.documentElement.getElementsByTagName('node'):
    node_info[node.getAttribute('id')] = {'lat': node.getAttribute('lat'), 'long': node.getAttribute('lon')}


print(node_info)