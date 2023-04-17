"""
This is the Utils file to have all the small functions
"""
import numpy as np
import random
import haversine as hs
from scipy import spatial


def mac_address():
    """
    This function is used in the Main.py file
    :return: this function will return a generated random MAC Address for ehicles
    """
    mac = [152, 237, 92,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def middle_zone(u_row, u_col,
                l_row, l_col,
                n_cols):
    """
    This function is used in the Zone.py file
    :param u_row: The upper row id +1
    :param l_row: The lower row id +1
    :param u_col: The upper col id +1
    :param l_col: The lower col id +1
    :param n_cols: The maximum number of columns in the whole area
    :return: The zone in the middle of the inputs
    """
    # the almost centre zone id will be obtained here
    middle_row = int(np.floor((u_row + l_row) / 2))
    middle_col = int(np.floor((u_col + l_col) / 2))
    middle_zone_id = ((middle_row - 1) * n_cols) + middle_col
    return 'zone' + str(middle_zone_id), middle_row, middle_col


def det_bus_ch(bus_table, veh_table_i,
               area_zones, bus_candidates):
    """

    :param bus_table:
    :param veh_table_i:
    :param area_zones:
    :param bus_candidates:
    :return: it This function will return the best candidate among all the buses near to i (vehicle_i) to be
     its cluster head
    """
    # latitude of the centre of previous zone that vehicle were in
    prev_veh_lat = (area_zones.zone_hash.values(veh_table_i['prev_zone'])['max_lat'] +
                    area_zones.zone_hash.values(veh_table_i['prev_zone'])['min_lat']) / 2
    # longitude of the centre of previous zone that vehicle were in
    prev_veh_long = (area_zones.zone_hash.values(veh_table_i['prev_zone'])['max_long'] +
                     area_zones.zone_hash.values(veh_table_i['prev_zone'])['min_long']) / 2

    euclidian_distance = hs.haversine((prev_veh_long, prev_veh_lat),
                                      (veh_table_i['long'], veh_table_i['lat']),
                                      unit=hs.Unit.METERS)

    veh_alpha = np.arctan((prev_veh_long - veh_table_i['long']) /
                          (prev_veh_lat - veh_table_i['lat']))

    veh_vector_x = np.multiply(euclidian_distance, np.cos(veh_alpha))
    veh_vector_y = np.multiply(euclidian_distance, np.sin(veh_alpha))

    nominee = ''
    min_ef = 10
    for j in bus_candidates:
        # latitude of the centre of previous zone that bus were in
        prev_bus_lat = (area_zones.zone_hash.values(bus_table.values(j)['prev_zone'])['max_lat'] +
                        area_zones.zone_hash.values(bus_table.values(j)['prev_zone'])['min_lat']) / 2
        # latitude of the centre of previous zone that bus were in
        prev_bus_long = (area_zones.zone_hash.values(bus_table.values(j)['prev_zone'])['max_long'] +
                         area_zones.zone_hash.values(bus_table.values(j)['prev_zone'])['min_long']) / 2

        euclidian_distance = hs.haversine((prev_bus_long, prev_bus_lat),
                                          (bus_table.values(j)['long'], bus_table.values(j)['lat']),
                                          unit=hs.Unit.METERS)

        bus_alpha = np.arctan((prev_veh_long - veh_table_i['long']) /
                              (prev_veh_lat - veh_table_i['lat']))

        bus_vector_x = np.multiply(euclidian_distance, np.cos(bus_alpha))
        bus_vector_y = np.multiply(euclidian_distance, np.sin(bus_alpha))

        cos_sim = 1 - spatial.distance.cosine([veh_vector_x, veh_vector_y], [bus_vector_x, bus_vector_y])
        theta_sim = np.arccos(cos_sim) / 2 * np.pi
        speed_sim = np.divide(np.abs(bus_table.values(j)['speed'] - veh_table_i['speed']),
                              np.abs(bus_table.values(j)['speed']))

        # calculate the Eligibility Factor (EF) for buses
        ef = theta_sim + speed_sim

        if ef < min_ef:
            nominee = j

    return nominee


def presence(area_cord, veh_cord):
    """
    This function will determine if the vehicle or bus is in the understudied area (unpadded area)
    :param area_cord: the coordination of the understudied area (unpadded area)
    :param veh_cord: the coordination of the vehicle or bus
    :return: it returns True or False
    """
    if (
            (float(veh_cord.getAttribute('x')) < area_cord['max_long']) &
            (float(veh_cord.getAttribute('x')) > area_cord['min_long']) &
            (float(veh_cord.getAttribute('y')) < area_cord['max_lat']) &
            (float(veh_cord.getAttribute('y')) > area_cord['min_lat'])
       ):
        return True
    else:
        return False
