"""
<<main.py>>

This project is related to clustering and routing problem in VANET

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import time
import numpy as np
import pandas as pd
import pathlib
from data_cluster import DataTable
from configs.config import Configs
from zonex import ZoneID
import utils.util as util

if __name__ == "__main__":
    configs = Configs().config

    cols = ['rsu', 'TR', 'weights', 'eval']
    out_put = pd.DataFrame(columns=cols)
    dif_tr = [200, ]
    dif_data = [str(pathlib.Path(__file__).parent.parent.absolute().
                    joinpath('small_data_Richmondhill', 'sumoTrace_rsu_geo.xml')),
                str(pathlib.Path(__file__).parent.parent.absolute().
                    joinpath('small_data_Richmondhill', 'sumoTrace_geo.xml'))
                ]
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
    start_time = time.time()
    for configs.trace_path in dif_data:
        for configs.trans_range in dif_tr:
            for configs.weights in all_weight_lists:
                configs.weights = np.array(configs.weights)
                a = DataTable(configs, area_zones)
                for i in range(configs.iter):
                    a.update(configs, area_zones)
                    print(a.time)
                    a.update_cluster(a.veh_table.ids(), configs, area_zones)
                    a.stand_alones_cluster(configs, area_zones)
                    # a.show_graph(configs)
                    # a.save_map_img(1, '/Users/pouyafirouzmakan/Desktop/VANET/saved_imgs/Graph' + str(i))
                eval_cluster = a.eval_cluster(configs)
                if 'rsu' in configs.trace_path:
                    out_put = out_put.append(['yes', configs.trans_range, configs.weights, eval_cluster])
                else:
                    out_put = out_put.append(['no', configs.trans_range, configs.weights, eval_cluster])
    end_time = time.time()
    out_put.to_csv('/Users/pouyafirouzmakan/Desktop/VANET/output_result.csv')
    # util.make_slideshow(-------)
    # a.show_graph(configs)
    # a.print_table()

    # print('evaluation: ', eval_cluster)
    # print('n_bus: ', len(a.bus_table.ids()))
    # print('n_veh: ', len(a.veh_table.ids()))
    # print('\n')
    # print('stand_alones: ', a.stand_alone)
    # print("execution time: ", end_time - start_time)
