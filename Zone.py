"""
This function is defined in order to determine the zones based on the Latitude and Longitude
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import numpy as np
import haversine as hs

import Hash


class ZoneID:

    def __init__(self, area):
        """

        :param area: includes the min and max of lat and long of the area (coordinates of the area)
        """
        self.zone_hash = None
        self.area = area
        self.x_area = None
        self.y_area = None
        self.cols = None
        self.rows = None

    def zones(self):
        """

        # first the x and y based on km is calculated to determine the area (hear greater Toronto Area (GTA) and some
        # cities around it. Then the area will be devided into several zones (almost 1km^2 for each zone)
        :return: a hash table including the zones' ids as keys and (lat , long) as values
        """
        self.x_area = hs.haversine((self.area["min_long"], 0), (self.area["max_long"], 0), unit=hs.Unit.KILOMETERS)
        self.y_area = hs.haversine((self.area["min_lat"], 0), (self.area["max_lat"], 0), unit=hs.Unit.KILOMETERS)
        area_surface = self.x_area * self.y_area
        self.rows = np.linspace(self.area["min_lat"], self.area["max_lat"],
                                num=int(np.floor(self.y_area)))  # dividing longitude by almost 1km length
        self.cols = np.linspace(self.area["min_long"], self.area["max_long"],
                                num=int(np.ceil(self.x_area)))  # dividing latitude by almost 1km length
        self.zone_hash = Hash.HashTable(int(np.ceil(area_surface)) * 100)
        z = 0  # zone counter
        for r in range(len(self.rows) - 1):
            for c in range(len(self.cols) - 1):
                self.zone_hash.set_item('zone' + str(z),
                                        [(self.rows[r], self.cols[c]),
                                         (self.rows[r + 1], self.cols[c + 1])]
                                        )
                z += 1

    def det_zone(self, lat, long):
        """
        :param lat:  current latitude of the vehicle
        :param long: current longitude of the vehicle
        :return: the zone that the car is in it
        """
        centre_row = round(len(self.rows) / 2)
        centre_col = round(len(self.cols) / 2)

        centre_zone_id = ((centre_row - 1) * len(self.cols)) + centre_col - 1
        

# area = {"min_lat": 43.586568, "min_long": -79.540771, "max_lat": 44.012923, "max_long": -79.238069}
# a = ZoneID(area)
# a.zones()
# a.zone_hash.print_hash_table()
