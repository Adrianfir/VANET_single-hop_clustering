"""
<<main.py>>

This project is related to clustering and routing problem in VANET

"""
__author__ = "Pouya 'Adrian' Firouzmakan"


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
    for i in a.veh_table.ids():
        a.update_cluster(i, configs, area_zones)
    print('bus-ids: ', a.bus_table.ids())
    print('vehicles-ids: ', a.veh_table.ids())
    print('\n')
    a.print_table()
