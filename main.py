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
import pandas as pd


if __name__ == "__main__":
    configs = Configs().config
    dif_tr = [100, ]
    rsu = False
    bus = False
    ########################### Define different weights
    # Define the size of each list and the step increment
    list_size = 3
    step = 1

    # Generate all possible values from 0 to 1 with the given step
    possible_values = [round(i * step, 1) for i in range(int(1 / step) + 1)]

    # Generate all possible combinations of values with sum equal to 1
    all_weight_lists = []

    for val1 in possible_values:
        for val2 in possible_values:
            remaining = round(1 - val1 - val2, 1)
            if remaining in possible_values and remaining >= 0:
                all_weight_lists.append([val1, val2, remaining])
    ############################

    area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
    area_zones.zones()
    num_times = 1
    start_time = time.time()

    for configs.veh_trans_range in dif_tr:
        # cols = ['rsu', 'TR', 'weights', 'n_veh', 'n_buses', 'n_sav', 'n_chs', 'stab_eval']
        out_put = pd.DataFrame()
        for configs.weights in all_weight_lists:

            cluster = DataTable(configs, area_zones, train_mode=False)
            connections = list()
            n_chs = list()
            n_savs = list()
            start_time = time.time()

            for i in range(configs.iter):
                cluster.update(configs, area_zones)
                # print(cluster.time)
                cluster.update_cluster(cluster.veh_table.ids(), configs, area_zones)
                cluster.stand_alones_cluster(configs, area_zones)
                cluster.update_other_connections()
                cluster.form_net_graph()
                connection_evaluation = cluster.connected_components()
                connections.append(connection_evaluation)
                n_chs.append(len(cluster.all_chs))
                n_savs.append(len(cluster.stand_alone))

            vcsm_metric = dict(vcsm=cluster.vcsm(configs))
            vcsmr_metrics = cluster.vcsm_r(configs)
            vcsm_cm_metrics = cluster.vcsm_cm(configs)

            metrics = dict(rsu=rsu, bus=bus, TR=configs.veh_trans_range, weights=configs.weights) | dict(TR=configs.veh_trans_range) |vcsm_metric | vcsmr_metrics | vcsm_cm_metrics

            # print(f'n_vehs: {len(cluster.veh_table.ids())}')
            # print(f'n_buses: {len(cluster.bus_table.ids())}')
            # print(f'avg_chs: {sum(n_chs)/len(n_chs)}')
            # print(f'avg_stand_alones: {sum(n_savs)/len(n_savs)}')
            # print(f'connection_evaluation: {sum(connections) / len(connections)}')

            print(num_times, configs.veh_trans_range, configs.weights,
                  len(cluster.veh_table.ids()), len(cluster.bus_table.ids()),
                  len(cluster.stand_alone), len(cluster.all_chs), vcsm_metric, vcsmr_metrics, vcsm_cm_metrics
              )
            num_times += 1

            metrics['n_vehs'] = len(cluster.veh_table.ids())
            metrics['n_buses'] = len(cluster.bus_table.ids())
            metrics['avg_chs'] = sum(n_chs) / len(n_chs)
            metrics['avg_savs'] = sum(n_savs) / len(n_savs)
            metrics['connection_evaluation'] = sum(connections) / len(connections)
            print(metrics)
            # new_row = pd.Series(['no', configs.veh_trans_range, configs.weights,
            #                      len(cluster.veh_table.ids()), len(cluster.bus_table.ids()),
            #                      sum(n_savs) / len(n_savs), sum(n_chs) / len(n_chs), eval_cluster], index=cols)

            out_put = pd.concat([out_put, pd.DataFrame([metrics])], ignore_index=True)

    out_put.to_csv('results/' + str(configs.veh_trans_range) + '_rsu:' + str(rsu) + '_bus:' + str(bus) + '.csv')
    end_time = time.time()
    print("execution time: ", end_time - start_time)