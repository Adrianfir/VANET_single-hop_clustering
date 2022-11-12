"""
This function is defined in order to determine the zones based on the Latitude and Longitude
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import numpy as np
import haversine as hs

import Hash


def middle_zone(u_row, l_row,
                u_col, l_col):
    """

    :param u_row: The upper row id +1
    :param l_row: The lower row id +1
    :param u_col: The upper col id +1
    :param l_col: The lower col id +1
    :return:
    """
    # the almost centre zone id will be obtained here
    middle_row = np.round((u_row - l_row) / 2)
    middle_col = np.round((u_col - l_col) / 2)
    middle_zone_id = ((middle_row - 1) * len(u_col - l_col)) + middle_col - 1
    return "zone" + str(middle_zone_id), middle_row, middle_col


class ZoneID:

    def __init__(self, area):
        """

        :param area: includes the min and max of lat and long of the area (coordinates of the area)
        """
        self.centre_col = None
        self.centre_row = None
        self.centre_zone = None
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

        # Here we are going to have a Hash Table for zones
        self.zone_hash = Hash.HashTable(int(np.ceil(area_surface)) * 100)
        z = 0  # zone counter
        for r in range(len(self.rows) - 1):
            for c in range(len(self.cols) - 1):
                self.zone_hash.set_item("zone" + str(z),
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
        # middle_zone_id, its row+1, its col+1
        temp, temp_row, temp_col = middle_zone(len(self.rows), 1, len(self.cols), 1)
        i = 0
        while temp:

            if ((lat >= self.zone_hash(temp)["min_lat"]) & (long >= self.zone_hash(temp)["min_long"])) & \
                    ((lat < self.zone_hash(temp)["max_lat"]) & (long < self.zone_hash(temp)["max_long"])):
                return temp

            if (lat < self.zone_hash(temp)["min_lat"]) & (long < self.zone_hash(temp)["min_long"]):
                if i is 0:
                    temp_prev = self.zone_hash.ids()[0]  # the very first zone is considered as first prev
                    tem_row_prev = 1
                    temp_col_prev = 1
                # middle_zone_id, its row+1, its col+1
                temp_next, tem_row_next, temp_col_next = middle_zone(temp_row, tem_row_prev, temp_col, temp_col_prev)
                temp_prev, temp_prev_row, temp_prev_col = temp, temp_row, temp_col
                temp, temp_row, temp_col = temp_next, tem_row_next, temp_col_next

            elif (lat > self.zone_hash(temp)["max_lat"]) & (long > self.zone_hash(temp)["max_long"]):
                if i is 0:
                    temp_prev = self.zone_hash.ids()[-1]  # the very last zone is considered as first prev
                    tem_row_prev = len(self.rows)
                    temp_col_prev = len(self.cols)
                # middle_zone_id, its row+1, its col+1
                temp_next, tem_row_next, temp_col_next = middle_zone(temp_row, tem_row_prev, temp_col, temp_col_prev)
                temp_prev, temp_prev_row, temp_prev_col = temp, temp_row, temp_col
                temp, temp_row, temp_col = temp_next, tem_row_next, temp_col_next

# area = {"min_lat": 43.586568, "min_long": -79.540771, "max_lat": 44.012923, "max_long": -79.238069}
# a = ZoneID(area)
# a.zones()
# a.zone_hash.print_hash_table()
