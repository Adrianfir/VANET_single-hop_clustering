"""
<<main.py>>

This project is related to clustering and routing problem in VANET

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import time
import numpy as np
import pandas as pd
from data_cluster import DataTable
from configs.config import Configs
from zonex import ZoneID
import utils.util as util
import re

if __name__ == "__main__":
    configs = Configs().config
    dif_tr = [400, ]
    ########################### Define different weights
    # Define the size of each list and the step increment
    list_size = 3
    step = 0.1

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
        cols = ['rsu', 'TR', 'weights', 'n_veh', 'n_buses', 'n_sav', 'n_chs', 'stab_eval', 'con_eval']
        out_put = pd.DataFrame(columns=cols)
        for configs.weights in all_weight_lists:
            configs.weights = np.array(configs.weights)
            cluster = DataTable(configs, area_zones)
            connections = list()
            n_chs = list()
            n_sav = list()
            for i in range(configs.iter):
                cluster.update(configs, area_zones)
                print(cluster.time)
                cluster.update_cluster(cluster.veh_table.ids(), configs, area_zones)
                cluster.stand_alones_cluster(configs, area_zones)
                connections.append(cluster.eval_connections())
                n_chs.append(len(cluster.all_chs))
                n_sav.append(len(cluster.stand_alone))

            eval_cluster = cluster.eval_cluster(configs)

            print(num_times, configs.veh_trans_range, configs.weights,
                  len(cluster.veh_table.ids()), len(cluster.bus_table.ids()),
                  len(cluster.stand_alone), len(cluster.all_chs), eval_cluster,
                  sum(connections)/len(connections)
                  )
            num_times += 1

            new_row = pd.Series(['no', configs.trans_range, configs.weights,
                                 len(cluster.veh_table.ids()), len(cluster.bus_table.ids()),
                                 sum(n_sav)/len(n_sav), sum(n_chs)/len(n_chs), eval_cluster,
                                 sum(connections)/len(connections)], index=cols)

            out_put = pd.concat([out_put, new_row.to_frame().T], ignore_index=True)

        out_put.to_csv('results/' + str(configs.trans_range) + '.csv')
        end_time = time.time()
        print("execution time: ", end_time - start_time)
