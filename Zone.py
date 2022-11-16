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
                n_cols):
    """

    :param u_row: The upper row id +1
    :param l_row: The lower row id +1
    :param u_col: The upper col id +1
    :param l_col: The lower col id +1
    :param n_cols: The maximum number of columns in the whole area
    :return:
    """
    # the almost centre zone id will be obtained here
    middle_row = int(np.floor((u_row + l_row) / 2))
    middle_col = int(np.floor((u_col + l_col) / 2))
    middle_zone_id = ((middle_row-1) * n_cols) + middle_col
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
        self.lat_rows = np.linspace(self.area["min_lat"], self.area["max_lat"],
                                    num=int(np.floor(self.y_area)), endpoint=True)  # dividing longitude by almost 1km
        # length
        self.long_cols = np.linspace(self.area["min_long"], self.area["max_long"],
                                     num=int(np.floor(self.x_area)),
                                     endpoint=True)  # dividing latitude by almost 1km length

        # Here we are going to have a Hash Table for zones
        self.zone_hash = Hash.HashTable(400)
        self.centre_col = int()
        self.centre_row = int()
        self.centre_zone = str()

    def zones(self):
        """

        :return: uploading self.zone_hash by the zones and their min & max lat & long
        """
        z = 0  # zone counter
        for r in range(len(self.lat_rows) - 1):
            for c in range(len(self.long_cols) - 1):
                self.zone_hash.set_item('zone' + str(z), dict(min_lat=self.lat_rows[r],
                                                              min_long=self.long_cols[c],
                                                              max_lat=self.lat_rows[r + 1],
                                                              max_long=self.long_cols[c + 1]
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
        temp, temp_row, temp_col = middle_zone(len(self.lat_rows)-1, len(self.long_cols)-1, 0, 0, len(self.long_cols)-1)
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
                    upper_row = len(self.lat_rows) - 1
                    upper_col = len(self.long_cols) - 1
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    lower_row = temp_row
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

            elif (lat < self.zone_hash.values(temp)["min_lat"]) & (long < self.zone_hash.values(temp)["min_long"]):
                if i == 0:
                    # the very North-East zone is considered as first prev
                    lower_row = 0
                    lower_col = 0
                    upper_row = temp_row
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    upper_row = temp_row
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

            elif (lat >= self.zone_hash.values(temp)["max_lat"]) & (long < self.zone_hash.values(temp)["min_long"]):
                if i == 0:
                    # the very North_East zone is considered as first prev
                    lower_row = temp_row
                    lower_col = 0
                    upper_row = len(self.lat_rows) - 1
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    lower_row = temp_row
                    upper_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

            elif (lat < self.zone_hash.values(temp)["min_lat"]) & (long >= self.zone_hash.values(temp)["max_long"]):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    lower_row = 0
                    lower_col = temp_col
                    upper_row = temp_row
                    upper_col = len(self.long_cols) - 1
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    upper_row = temp_row
                    lower_col = temp_col
                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

                i += 1

            elif ((lat < self.zone_hash.values(temp)["max_lat"]) &
                  (lat >= self.zone_hash.values(temp)["min_lat"])) & \
                    (long >= self.zone_hash.values(temp)["max_long"]):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_col = len(self.long_cols) - 1
                    lower_col = temp_col
                    upper_row = temp_row
                    lower_row = temp_row
                    if (upper_col - lower_col) == 1:
                        lower_col = upper_col

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    upper_row = temp_row
                    lower_row = temp_row
                    lower_col = temp_col
                    if (upper_col - lower_col) == 1:
                        lower_col = upper_col

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

                i += 1

            elif ((lat < self.zone_hash.values(temp)["max_lat"]) &
                  (lat >= self.zone_hash.values(temp)["min_lat"])) & \
                    (long < self.zone_hash.values(temp)["min_long"]):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_col = temp_col
                    lower_col = 0
                    upper_row = temp_row
                    lower_row = temp_row
                    if (upper_col - lower_col) == 1:
                        upper_col = lower_col

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    upper_row = temp_row
                    lower_row = temp_row
                    upper_col = temp_col
                    if (upper_col - lower_col) == 1:
                        upper_col = lower_col

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

                i += 1

            elif (lat < self.zone_hash.values(temp)["max_lat"]) & \
                    ((long < self.zone_hash.values(temp)["max_long"]) & \
                     (long > self.zone_hash.values(temp)["min_long"])):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_col = temp_col
                    lower_col = temp_col
                    upper_row = temp_row
                    lower_row = 0
                    if (upper_row - lower_row) == 1:
                        upper_row = lower_row

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    upper_row = temp_row
                    upper_col = temp_col
                    lower_col = temp_col
                    if (upper_row - lower_row) == 1:
                        upper_row = lower_row

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

                i += 1

            elif (lat < self.zone_hash.values(temp)["max_lat"]) & \
                    ((long < self.zone_hash.values(temp)["max_long"]) & \
                     (long > self.zone_hash.values(temp)["min_long"])):
                if i == 0:
                    # the very South_West zone is considered as first prev
                    upper_row = len(self.lat_rows) - 1
                    lower_row = temp_row
                    upper_col = temp_col
                    lower_col = temp_col
                    if (upper_row - lower_row) == 1:
                        lower_row = upper_row

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)
                    i += 1
                else:
                    lower_row = temp_row
                    upper_col = temp_col
                    lower_col = temp_col
                    if (upper_row - lower_row) == 1:
                        lower_row = upper_row

                    temp, temp_row, temp_col = middle_zone(upper_row, upper_col,
                                                           lower_row, lower_col,
                                                           len(self.long_cols) - 1)

                i += 1


area = {"min_lat": 43.586568, "min_long": -79.540771, "max_lat": 44.012923, "max_long": -79.238069}
a = ZoneID(area)
a.zones()
print(a.det_zone(43.6, -79.540771))
