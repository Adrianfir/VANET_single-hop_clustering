"""
This function is defined in order to determine the zones based on the Latitude and Longitude
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import numpy as np
import haversine as hs

import Hash


def zones(min_lat, min_long, max_lat, max_long):
    """
    # first the x and y based on km is calculated to determine the area (hear greater Toronto Area (GTA) and some
    # cities around it. Then the area will be devided into several zones (almost 1km^2 for each zone)
    :param min_lat: obvious
    :param min_long: obvious
    :param max_lat: obvious
    :param max_long: obvious
    :return: a hash table including the zones' ids as keys and (lat , long) as values
    """
    x_area = hs.haversine((min_long, 0), (max_long, 0), unit=hs.Unit.KILOMETERS)
    y_area = hs.haversine((min_lat, 0), (max_lat, 0), unit=hs.Unit.KILOMETERS)
    area = x_area * y_area
    rows = np.linspace(min_lat, max_lat, num=int(np.floor(y_area)))  # dividing longitude by the 1km length
    cols = np.linspace(min_long, max_long, num=int(np.ceil(x_area)))  # dividing latitude by almost 1km length
    zone_hash = Hash.HashTable(int(np.ceil(area))*100)
    z = 0  # zone counter
    for r in range(len(rows) - 1):
        for c in range(len(cols) - 1):
            zone_hash.set_item('zone' + str(z),
                               [(rows[r], cols[c]),
                                (rows[r + 1], cols[c + 1])]
                               )
            z += 1
    return zone_hash

def det_zone(lat,long,zone_hash):
    """
    this function is designed to determine the zone of vehicles based on their location
    :param lat: latitude of vehicle
    :param long: longitude of vehicle
    :param zone_hash: hash tabe including all the zones
    :return: zone id that the vehicle is in it
    """

# min_lat_area = 43.586568
# min_long_area = -79.540771
# max_lat_area = 44.012923
# max_long_area = -79.238069
# a = det_zones(min_lat_area, min_long_area, max_lat_area, max_long_area)
# a.print_hash_table()
