"""
This function is defined in order to determine the zones based on the Latitude and Longitude
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import numpy as np
import haversine as hs

import Hash


def zones(area):
    """
    # first the x and y based on km is calculated to determine the area (hear greater Toronto Area (GTA) and some
    # cities around it. Then the area will be devided into several zones (almost 1km^2 for each zone)
    :param area: includes the min and max of lat and long of the area
    :return: a hash table including the zones' ids as keys and (lat , long) as values
    """
    x_area = hs.haversine((area["min_long"], 0), (area["max_long"], 0), unit=hs.Unit.KILOMETERS)
    y_area = hs.haversine((area["min_lat"], 0), (area["max_lat"], 0), unit=hs.Unit.KILOMETERS)
    area_surface = x_area * y_area
    rows = np.linspace(area["min_lat"], area["max_lat"],
                       num=int(np.floor(y_area)))  # dividing longitude by almost 1km length
    cols = np.linspace(area["min_long"], area["max_long"],
                       num=int(np.ceil(x_area)))  # dividing latitude by almost 1km length
    zone_hash = Hash.HashTable(int(np.ceil(area_surface)) * 100)
    z = 0  # zone counter
    for r in range(len(rows) - 1):
        for c in range(len(cols) - 1):
            zone_hash.set_item('zone' + str(z),
                               [(rows[r], cols[c]),
                                (rows[r + 1], cols[c + 1])]
                               )
            z += 1
    return zone_hash


def det_zone(lat, long, area_zones):
    rows = np.linspace(area["min_lat"], area["max_lat"],
                       num=int(np.floor(y_area)))  # dividing longitude by almost 1km length
    cols = np.linspace(area["min_long"], area["max_long"],
                       num=int(np.ceil(x_area)))  # dividing latitude by almost 1km length


    """
    this function is designed to determine the zone of vehicles based on their location
    :param lat: latitude of vehicle
    :param long: longitude of vehicle
    :param area_zones: hash tabe including all the zones
    :return: zone id that the vehicle is in it
    """

# area["min_lat"]_area = 43.586568
# area["min_long"]_area = -79.540771
# area["max_lat"]_area = 44.012923
# area["max_long"]_area = -79.238069
# a = det_zones(area["min_lat"]_area, area["min_long"]_area, area["max_lat"]_area, area["max_long"]_area)
# a.print_hash_table()
