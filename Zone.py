"""
This function is defined in order to determine the zones based on the Latitude and Longitude
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import numpy as np
import haversine as hs

import Hash


def middle_zone(u_row, u_col,
                l_row, l_col,
                max_col):
    """

    :param u_row: The upper row id +1
    :param l_row: The lower row id +1
    :param u_col: The upper col id +1
    :param l_col: The lower col id +1
    :param max_col: The maximum number of columns in the whole area
    :return:
    """
    # the almost centre zone id will be obtained here
    middle_row = int(np.ceil((u_row - l_row) / 2))
    middle_col = int(np.ceil((u_col - l_col) / 2))

    if (middle_row == 0) & (middle_col == 0):           # if both are in same zone
        middle_row = u_row
        middle_col = u_col
        middle_zone_id = ((u_row - 1) * max_col) + u_col - 1
    elif (middle_row == 0) & (middle_col != 0):           # if both are in same row
        middle_row = u_row
        middle_zone_id = ((u_row - 1) * max_col) + middle_col - 1
    elif (middle_row != 0) & (middle_col == 0):           # if both are in same column
        middle_col = u_col
        middle_zone_id = ((middle_row - 1) * max_col) + u_col - 1
    else:                           # if both are not in same column or row
        middle_zone_id = ((middle_row - 1) * max_col) + middle_col - 1

    return 'zone' + str(middle_zone_id), middle_row, middle_col


class ZoneID:

    def __init__(self, area_coordinate):
        """
        # first the x and y based on km is calculated to determine the area (hear greater Toronto Area (GTA) and some
        # cities around it. Then the area will be divided into several zones (almost 1km^2 for each zone)
        :param area: includes the min and max of lat and long of the area (coordinates of the area)
        """
        self.area = area_coordinate
        self.x_area = hs.haversine((self.area["min_long"], 0), (self.area["max_long"], 0), unit=hs.Unit.KILOMETERS)
        self.y_area = hs.haversine((self.area["min_lat"], 0), (self.area["max_lat"], 0), unit=hs.Unit.KILOMETERS)
        self.area_surface = self.x_area * self.y_area
        self.rows = np.linspace(self.area["min_lat"], self.area["max_lat"],
                                num=int(np.floor(self.y_area)), endpoint=True)  # dividing longitude by almost 1km
        # length
        self.cols = np.linspace(self.area["min_long"], self.area["max_long"],
                                num=int(np.floor(self.x_area)), endpoint=True)  # dividing latitude by almost 1km length

        # Here we are going to have a Hash Table for zones
        self.zone_hash = Hash.HashTable(400)
        self.centre_col = int()
        self.centre_row = int()
        self.centre_zone = str()

    def zones(self):
        """

        :return: uploading self.zone_hash by the zones and their min & max lat & long
        """
        z = 0000  # zone counter
        for r in range(len(self.rows) - 1):
            for c in range(len(self.cols) - 1):
                self.zone_hash.set_item('zone' + str(z), dict(min_lat=self.rows[r],
                                                              min_long=self.cols[c],
                                                              max_lat=self.rows[r + 1],
                                                              max_long=self.cols[c + 1]
                                                             )
                                        )
                z += 1

    def det_zone(self, lat, long):
        """
        :param lat:  current latitude of the vehicle
        :param long: current longitude of the vehicle
        :return: the zone that the car is in it
        """
        # middle_zone_id, its row+1, its col+1
        temp, temp_row, temp_col = middle_zone(len(self.rows), len(self.cols), 1, 1, len(self.cols))
        i = 0
        while temp:

            if ((lat >= self.zone_hash.values(temp)["min_lat"]) & (long >= self.zone_hash.values(temp)["min_long"])) & \
                    ((lat <= self.zone_hash.values(temp)["max_lat"]) & (
                            long <= self.zone_hash.values(temp)["max_long"])):
                return temp

            elif (lat >= self.zone_hash.values(temp)["max_lat"]) & (long >= self.zone_hash.values(temp)["max_long"]):
                if i == 0:
                    # the very North-East zone is considered as first prev
                    lower_row = temp_row
                    lower_col = temp_col
                    upper_row = len(self.rows)
                    upper_col = len(self.cols)
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    lower_row = temp_row
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

            elif (lat < self.zone_hash.values(temp)["min_lat"]) & (long < self.zone_hash.values(temp)["min_long"]):
                if i == 0:
                    # the very North-East zone is considered as first prev
                    lower_row = 1
                    lower_col = 1
                    upper_row = temp_row
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    upper_row = temp_row
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

            elif (lat >= self.zone_hash.values(temp)["max_lat"]) & (long < self.zone_hash.values(temp)["min_long"]):
                if i == 0:
                    # the very North_East zone is considered as first prev
                    lower_row = temp_row
                    lower_col = 1
                    upper_row = len(self.rows)
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    lower_row = temp_row
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

            elif (lat < self.zone_hash.values(temp)["min_lat"]) & (long >= self.zone_hash.values(temp)["max_long"]):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    lower_row = 1
                    lower_col = temp_col
                    upper_row = temp_row
                    upper_col = len(self.cols)
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    upper_row = temp_row
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

                i += 1

            elif ((lat < self.zone_hash.values(temp)["max_lat"]) & (lat >= self.zone_hash.values(temp)["min_lat"])) & \
                    (long >= self.zone_hash.values(temp)["max_long"]):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_col = len(self.cols)
                    lower_col = temp_col
                    upper_row = temp_row
                    lower_row = temp_row
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    upper_row = temp_row
                    lower_row = temp_row
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

                i += 1

            elif ((lat < self.zone_hash.values(temp)["max_lat"]) & (lat >= self.zone_hash.values(temp)["min_lat"])) & \
                    (long < self.zone_hash.values(temp)["min_long"]):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_col = temp_col
                    lower_col = 1
                    upper_row = temp_row
                    lower_row = temp_row
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    upper_row = temp_row
                    lower_row = temp_row
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

                i += 1

            elif (lat < self.zone_hash.values(temp)["max_lat"]) & \
                    ((long < self.zone_hash.values(temp)["max_long"]) &
                     (long > self.zone_hash.values(temp)["min_long"])):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_col = temp_col
                    lower_col = temp_col
                    upper_row = temp_row
                    lower_row = 1
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    upper_row = temp_row
                    upper_col = temp_col
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

                i += 1

            elif (lat < self.zone_hash.values(temp)["max_lat"]) & \
                    ((long < self.zone_hash.values(temp)["max_long"]) &
                     (long > self.zone_hash.values(temp)["min_long"])):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_row = len(self.row)
                    lower_row = temp_row
                    upper_col = temp_col
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))
                    i += 1
                else:
                    lower_row = temp_row
                    upper_col = temp_col
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.cols))

                i += 1


area = {"min_lat": 43.586568, "min_long": -79.540771, "max_lat": 44.012923, "max_long": -79.238069}
a = ZoneID(area)
a.zones()
a.det_zone(43.6, -79.540771)

