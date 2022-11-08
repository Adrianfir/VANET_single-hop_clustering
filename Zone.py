"""
This function is defined in order to determine the zones based on the Latitude and Longitude
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import haversine as hs

import Hash


def zones(min_lat, min_long, max_lat, max_long, hash_size):
    x = hs.haversine((min_lat, 0), (max_lat, 0))
    y = hs.haversine((min_long, 0), (max_long, 0))
    
