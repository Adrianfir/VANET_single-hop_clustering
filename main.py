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
import random

if __name__ == "__main__":
    random.seed(42)
    configs = Configs().config

    area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
    area_zones.zones()
    cluster = DataTable(configs, area_zones)
    connections = list()
    n_chs = list()
    n_savs = list()
    start_time = time.time()
    for i in range(configs.iter):
        cluster.update(configs, area_zones)
        print(cluster.time)
        cluster.update_cluster(cluster.veh_table.ids(), configs, area_zones)
        cluster.stand_alones_cluster(configs, area_zones)
        cluster.update_other_connections()
        cluster.form_net_graph()
        connection_evaluation = cluster.connected_components()
        connections.append(connection_evaluation)
        n_chs.append(len(cluster.all_chs))
        n_savs.append(len(cluster.stand_alone))
        if cluster.time < start_time + (configs.iter/10):
            cluster.gen_message(configs)
        cluster.route(configs)
    #     cluster.show_graph(configs)
    #     cluster.save_map_img(1, '/Users/pouyafirouzmakan/Desktop/slideshow/saved_imgs/Graph' + str(i))
    # #
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
    print(f'avg_chs: {sum(n_chs)/len(n_chs)}')
    print(f'avg_stand_alones: {sum(n_savs)/len(n_savs)}')
    print(f'execution time: {end_time - start_time}')
    print(f'all the edges: \n{cluster.net_graph.edges()}')
    print(f'number of generated packets: {cluster.pck_queue}')
    print(f'number of delivered packets: {len(cluster.delivered_packets)}')
    non_delivered_packets = 0
    for i in cluster.veh_table.ids().union(cluster.bus_table.ids()):
        table = cluster.veh_table if 'veh' in i else cluster.bus_table
        non_delivered_packets += len(table.values(i)['packets_to_pass'])

    print(f'number of non-delivered packets: {non_delivered_packets}')
    print(f'number of dropped packets: {len(cluster.drops)}')


    # ch_high_mems = 0
    # for i in cluster.all_chs:
    #     if len(cluster.veh_table.values(i)['cluster_members'])>10:
    #         ch_high_mems += 1
    # print(f'ch_high_mems: {ch_high_mems}')
    plt.show()