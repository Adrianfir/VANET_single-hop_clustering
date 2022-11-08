"""
This function is defined in order to determine the zones based on the Latitude and Longitude
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import numpy as np
import haversine as hs

import Hash


def det_zones(min_lat, min_long, max_lat, max_long):
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
    rows = np.linspace(min_lat, max_lat, num=np.floor(x_area))  # dividing longitude by the 1km length
    cols = np.linspace(min_long, max_long, num=np.floor(y_area))  # # dividing latitude by the 1km length
    zone_hash = Hash.HashTable(np.ceil(area))
    z = 0  # zone counter
    for i in range(rows):
        for j in range(cols):
            zone_hash.set_item('zone' + str(z),
                               (i, j)  # (i: latitude, j: longitude)
                               )
    return zone_hash
