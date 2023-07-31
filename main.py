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

if __name__ == "__main__":
    configs = Configs().config

    area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
    area_zones.zones()
    a = DataTable(configs, area_zones)
    start_time = time.time()
    for i in range(300):
        a.update(configs, area_zones)
        print(a.time)
        a.update_cluster(a.veh_table.ids(), configs, area_zones)
        a.stand_alones_cluster(configs, area_zones)
        a.show_graph(configs)
        a.save_map_img(1, '/Users/pouyafirouzmakan/Desktop/VANET/saved_imgs/Graph' + str(i))
    end_time = time.time()
    util.make_slideshow("/Users/pouyafirouzmakan/Desktop/VANET/saved_imgs",
                        "/Users/pouyafirouzmakan/Desktop/VANET/saved_imgs/slide_show.mp4", configs.fps)
    a.print_table()
    print('n_bus: ', len(a.bus_table.ids()))
    print('n_veh: ', len(a.veh_table.ids()))
    print('\n')
    print('stand_alones: ', a.stand_alone)
    print("execution time: ", end_time - start_time)

