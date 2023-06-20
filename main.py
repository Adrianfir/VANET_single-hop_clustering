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

    # G = nx.Graph(a.bus_table.values('bus124')['cluster_members'].adj_list)
    # nx.draw(G, with_labels=True, node_color='lightblue', node_size=500, font_weight='bold')
    # plt.show()