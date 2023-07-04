"""
<<main.py>>

This project is related to clustering and routing problem in VANET

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import time
from data_cluster import DataTable
from configs.config import Configs
from Zone import ZoneID

if __name__ == "__main__":
    configs = Configs().config

    area_zones = ZoneID(configs)  # This is a hash table including all zones and their max and min lat and longs
    area_zones.zones()
    start_time = time.time()
    a = DataTable(configs, area_zones)
    a.update(configs, area_zones)
    a.update_cluster(a.veh_table.ids(), configs, area_zones)
    a.stand_alones_cluster(configs, area_zones)
    end_time = time.time()
    print('n_bus: ', len(a.bus_table.ids()))
    print('n_veh: ', len(a.veh_table.ids()))
    print('bus-ids: ', a.bus_table.ids())
    print('vehicles-ids: ', a.veh_table.ids())
    print('\n')
    a.print_table()
    a.show_graph()
    print('stand_alones: ', a.stand_alone)
    print("execution time: ", end_time - start_time)

    # Create a networkx graph

