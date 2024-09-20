"""
<<main.py>>

This project is related to clustering and routing problem in VANET

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import time
from data_cluster import DataTable
from configs.config import Configs
from zonex import ZoneID
import utils.util as util
import re
import networkx as nx
import matplotlib.pyplot as plt

if __name__ == "__main__":
    configs = Configs().config

    area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
    area_zones.zones()
    cluster = DataTable(configs, area_zones)
    connections = list()
    start_time = time.time()
    for i in range(configs.iter):
        cluster.update(configs, area_zones)
        print(cluster.time)
        cluster.update_cluster(cluster.veh_table.ids(), configs, area_zones)
        cluster.dsca_clustering(configs, area_zones)
        cluster.update_other_connections()
        cluster.form_net_graph()
        connection_evaluation = cluster.connected_components()
        connections.append(connection_evaluation)
        # cluster.show_graph(configs)
    #     cluster.save_map_img(1, '/Users/pouyafirouzmakan/Desktop/slideshow/saved_imgs/Graph' + str(i))
    #
    end_time = time.time()
    # util.make_slideshow('/Users/pouyafirouzmakan/Desktop/slideshow/saved_imgs/',
    #                     '/Users/pouyafirouzmakan/Desktop/slideshow/saved_imgs/slide.mp4', configs.fps)

    cluster.print_table()
    nx.draw(cluster.ch_net, with_labels=False)
    print(f'stability_evaluation: {cluster.eval_cluster(configs)}')
    print(f'connection_evaluation: {sum(connections)/len(connections)}->{connections}')
    print('\n')
    print(f'n_vehs: {len(cluster.veh_table.ids())}')
    print(f'n_buses: {len(cluster.bus_table.ids())}')
    print(f'chs: {len(cluster.all_chs)}->{cluster.all_chs}')
    print(f'stand_alones: {len(cluster.stand_alone)}->{cluster.stand_alone}')
    print(f'execution time: {end_time - start_time}')
    print(f'all the edges: \n{cluster.net_graph.edges()}')
    plt.show()