"""
<<main.py>>

This project is related to clustering and routing problem in VANET

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import networkx as nx
import matplotlib.pyplot as plt

from data_cluster import DataTable
from configs.config import Configs
from Zone import ZoneID

if __name__ == "__main__":
    configs = Configs().config

    area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
    area_zones.zones()

    a = DataTable(configs, area_zones)
    a.print_table()
    a.update(configs, area_zones)
    a.update_cluster(configs, area_zones)
    print('n_bus: ', len(a.bus_table.ids()))
    print('n_veh: ', len(a.veh_table.ids()))
    print('bus-ids: ', a.bus_table.ids())
    print('vehicles-ids: ', a.veh_table.ids())
    print('\n')
    a.print_table()
    # print(a.all_CHs)

    # Create a networkx graph
    # G = nx.Graph()
    #
    # # Add nodes and edges with coordinates to the networkx graph
    # for vertex, data in a.bus_table.values('bus127')['cluster_members'].adj_list.items():
    #     G.add_node(vertex, pos=data['pos'])
    #     for edge in data['edges']:
    #         G.add_edge(vertex, edge)
    #
    # # Extract positions from node attributes
    # pos = nx.get_node_attributes(G, 'pos')
    #
    # # Plot the graph on a map
    # plt.figure(figsize=(10, 8))
    # nx.draw(G, pos, with_labels=True, node_size=100, font_size=6, font_weight='bold', alpha=0.5, node_color='lightblue',
    #         edge_color='gray', width=1.0)
    #
    # # Show the plot
    # plt.show()
