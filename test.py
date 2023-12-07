import xml.dom.minidom
path = '/Users/pouyafirouzmakan/Desktop/VANET_single-hop_clustering/final_data_Richmondhill/osm.net.xml'
file = xml.dom.minidom.parse(path)
target_dict = dict()
for edge in file.documentElement.getElementsByTagName('edge'):
    target_dict[edge.getAttribute('id')] = {'from': edge.getAttribute('from')}
    target_dict[edge.getAttribute('id')]['length'] = edge.getElementsByTagName('lane')[0].getAttribute('length')


print(target_dict)