"""
<<main.py>>

This project is related to clustering and routing problem in VANET

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import os
import random
import numpy as np
import time
from data_cluster import DataTable
from configs.config import Configs
from zonex import ZoneID
import utils.util_routing as util_routing
import matplotlib.pyplot as plt
from qlearning_state import QRoutingHelper
import xml.dom.minidom


if __name__ == "__main__":
    # Select clustering and routing algorithms
    clustering = input('please enter 1 for SMZCA or 2 for DCSA: ')
    routing = input('please enter 1 for NTLCRP, 2 for GPSR, 3 for CGGR, 4 for PDVR, '
                    ' 5 for training RL-based GPSR, and 6 for ZCGGR: ')
    training_mode = input('you are up to training the agent: true or false? ')
    routing_train_mode = True if training_mode=="true" else False
    clustering_name = 'SMZCA' if clustering == '1' else 'DCSA'
    routing_name = 'NTLCRP'
    routing_name = 'GPSR' if routing == '2' else routing_name
    routing_name = 'CGGR' if routing == '3' else routing_name
    routing_name = 'PDVR' if routing == '4' else routing_name
    routing_name = 'RL-based GPSR' if routing == '5' else routing_name
    routing_name = 'ZCGGR' if routing == '6' else routing_name
    configs = Configs().config

    area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
    area_zones.zones()
    cluster = DataTable(configs, area_zones, train_mode=routing_train_mode)
    connections = list()
    n_chs = list()
    n_savs = list()
    start_time = time.time()

    for i in range(configs.iter):
        cluster.update(configs, area_zones)
        print(cluster.time)
        cluster.update_cluster(cluster.veh_table.ids(), configs, area_zones)
        if clustering == '1':
            cluster.stand_alones_cluster(configs, area_zones)
        if clustering == '2':
            cluster.dsca_clustering(configs, area_zones)
        cluster.update_other_connections()
        cluster.form_net_graph()
        connection_evaluation = cluster.connected_components()
        connections.append(connection_evaluation)
        n_chs.append(len(cluster.all_chs))
        n_savs.append(len(cluster.stand_alone))

        if (cluster.time < configs.start_time + (5/6)*configs.iter) and (cluster.time >= configs.start_time + 5):
            cluster.read_message(configs)

        if routing == '1':
            cluster.route_ntlcrp(configs)
        if routing == '2':
            cluster.route_gpsr(configs)
        if routing == '3':
            cluster.route_cggr(configs, clustering_name)
        if routing == '4':
            cluster.route_pdvr(configs)
        if routing == '5':
            cluster.route_gpsr_rl(configs)
        if routing == '6':
            cluster.route_zcggr(configs, clustering_name, area_zones)

    #     cluster.show_graph(configs)
    #     cluster.save_map_img(1, '/Users/pouyafirouzmakan/Desktop/slideshow/saved_imgs/Graph' + str(i))
    # #
    end_time = time.time()
    # util.make_slideshow('/Users/pouyafirouzmakan/Desktop/slideshow/saved_imgs/',
    #                     '/Users/pouyafirouzmakan/Desktop/slideshow/saved_imgs/slide.mp4', configs.fps)
    # cluster.print_table()
    # nx.draw(cluster.ch_net, with_labels=False)
    # print(f'delivered_packets are: {cluster.delivered_packets}')
    
    avg_hops, avg_delay = util_routing.eval_routing(cluster)
    print(f'stability_evaluation: {cluster.eval_cluster(configs)}')
    print(f'connection_evaluation: {sum(connections)/len(connections)}->{connections}')
    print('\n')
    print(f'n_vehs: {len(cluster.veh_table.ids())}')
    print(f'n_buses: {len(cluster.bus_table.ids())}')
    print(f'avg_chs: {sum(n_chs)/len(n_chs)}')
    print(f'avg_stand_alones: {sum(n_savs)/len(n_savs)}')
    print(f'execution time: {end_time - start_time}')
    # print(f'all the edges: \n{cluster.net_graph.edges()}')
    # print(f'dropped_packers are: {cluster.drops}')
    # print(f'delivered_packets are: {cluster.delivered_packets}')
    print(f'number of generated messages: {cluster.message_count}')
    print(f'number of generated packets: {cluster.pck_queue}')
    print(f'number of delivered packets: {len(cluster.delivered_packets)}')
    non_delivered_packets = list()
    for i in cluster.veh_table.ids().union(cluster.bus_table.ids()):
        table = cluster.veh_table if 'veh' in i else cluster.bus_table
        non_delivered_packets = non_delivered_packets + table.values(i)['packets_to_pass']

    print(f'number of non-delivered packets: {len(non_delivered_packets)}')
    print(f'number of left-dest packets: {len(cluster.left_dest_pack)}')
    print(f'number of dropped packets: {len(cluster.drops)}')
    print(f'delivery ratio: {len(cluster.delivered_packets)/cluster.pck_queue}')
    print(f'average_hops: {avg_hops}')
    print(f'average delay: {avg_delay}')
    print('################################################################################')
    print(f'clustering algorithm: {clustering_name} --- routing algorithm: {routing_name}')
    print(f'number of premiter mode: {cluster.n_perimeter}')
    if routing_train_mode is True:
        cluster.agent.save("checkpoints/dqn_vanet_tr300_alpha0.5_tick1400_to_tick1600")
    # print(cluster.actions_review)
    # plt.plot([sum(cluster.train_reward_log[0:i]) for i in range(len(cluster.train_reward_log))])
    # plt.show()