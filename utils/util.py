"""
This is the Utils file to have all the small functions
"""

__all__ = ['initiate_new_bus', 'initiate_new_veh', 'mac_address', 'middle_zone',
           'det_bus_ch', 'presence', 'update_bus_table', 'update_veh_table']

import numpy as np
import random
import haversine as hs
from scipy import spatial
from Graph import Graph


def initiate_new_bus(veh, zones, zone_id, config, understudied_area):
    """
    this function is for initialing the new bus coming to the area
    :param veh:veh extracted from .xml file
    :param zones:the hash_table related to zones
    :param zone_id:zone_id of the vehicle determined based on its location
    :param config:it is the config file
    :param understudied_area:the un_padded area
    :return:a dictionary for initiating the new bus coming to the area
    """
    return dict(long=veh.getAttribute('x'),
                lat=veh.getAttribute('y'),
                angle=veh.getAttribute('angle'),
                speed=veh.getAttribute('speed'),
                pos=veh.getAttribute('pos'),
                lane=veh.getAttribute('lane'),
                zone=zone_id,
                prev_zone=None,
                neighbor_zones=zones.neighbor_zones(zone_id),
                in_area=presence(understudied_area, veh),
                trans_range=config.trans_range,
                message_dest={},
                message_source={},
                cluster_head=True,
                other_CHs=[],
                cluster_members=Graph(),
                bridges={},
                IP=None,
                MAC=mac_address(),
                counter=3
                )


def initiate_new_veh(veh, zones, zone_id, config, understudied_area):
    """
    this function is for initialing the new vehicle coming to the area
    :param veh:veh extracted from .xml file
    :param zones:the hash_table related to zones
    :param zone_id:zone_id of the vehicle determined based on its location
    :param config:it is the config file
    :param understudied_area:the un_padded area
    :return:a dictionary for initiating the new vehicle coming to the area
    """
    return dict(long=veh.getAttribute('x'),
                lat=veh.getAttribute('y'),
                angle=veh.getAttribute('angle'),
                speed=veh.getAttribute('speed'),
                pos=veh.getAttribute('pos'),
                lane=veh.getAttribute('lane'),
                zone=zone_id,
                prev_zone=None,
                neighbor_zones=zones.neighbor_zones(zone_id),
                in_area=presence(understudied_area, veh),
                trans_range=config.trans_range,
                message_dest={},
                message_source={},
                cluster_head=False,  # if the vehicle is a CH, it will be True
                primary_CH=None,
                other_CHs=[],
                cluster_members=None,  # This will be a Graph if the vehicle is a CH
                IP=None,
                MAC=mac_address(),
                counter=3  # a counter_time to search and join a cluster
                )


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


def update_bus_table(veh, bus_table, zone_id, understudied_area, zones, config, zone_buses):
    """

    :param veh:
    :param bus_table:
    :param zone_id:
    :param understudied_area:
    :param zones:
    :param config:
    :param zone_buses:
    :return:
    """
    try:
        bus_table.values(veh.getAttribute('id'))['prev_zone'] = \
            bus_table.values(veh.getAttribute('id'))['zone']  # update prev_zone

        bus_table.values(veh.getAttribute('id'))['long'] = veh.getAttribute('x')
        bus_table.values(veh.getAttribute('id'))['lat'] = veh.getAttribute('y')
        bus_table.values(veh.getAttribute('id'))['angle'] = veh.getAttribute('angle')
        bus_table.values(veh.getAttribute('id'))['speed'] = veh.getAttribute('speed')
        bus_table.values(veh.getAttribute('id'))['pos'] = veh.getAttribute('pos')
        bus_table.values(veh.getAttribute('id'))['lane'] = veh.getAttribute('lane')
        bus_table.values(veh.getAttribute('id'))['zone'] = zone_id
        bus_table.values(veh.getAttribute('id'))['in_area'] = presence(understudied_area, veh)
        bus_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)

        zone_buses[zone_id].add(veh.getAttribute('id'))
        try:
            zone_buses[bus_table.values(veh.getAttribute('id'))['prev_zone']]. \
                remove(veh.getAttribute('id'))  # This will remove the vehicle from its previous zone_buses
        except KeyError:
            bus_table.set_item(veh.getAttribute('id'), initiate_new_bus(veh, zones, zone_id,
                                                                        config, understudied_area)
                               )
    except TypeError:
        bus_table.set_item(veh.getAttribute('id'), initiate_new_bus(veh, zones, zone_id,
                                                                    config, understudied_area))
    return bus_table, zone_buses


def update_veh_table(veh, veh_table, zone_id, understudied_area, zones, config, zone_vehicles):
    """

    :param veh:
    :param veh_table:
    :param zone_id:
    :param understudied_area:
    :param zones:
    :param config:
    :param zone_vehicles:
    :return:
    """
    try:
        veh_table.values(veh.getAttribute('id'))['long'] = veh.getAttribute('x')
        veh_table.values(veh.getAttribute('id'))['lat'] = veh.getAttribute('y')
        veh_table.values(veh.getAttribute('id'))['angle'] = veh.getAttribute('angle')
        veh_table.values(veh.getAttribute('id'))['speed'] = veh.getAttribute('speed')
        veh_table.values(veh.getAttribute('id'))['pos'] = veh.getAttribute('pos')
        veh_table.values(veh.getAttribute('id'))['lane'] = veh.getAttribute('lane')
        veh_table.values(veh.getAttribute('id'))['zone'] = zone_id
        veh_table.values(veh.getAttribute('id'))['in_area'] = presence(understudied_area, veh)
        veh_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)

        zone_vehicles[zone_id].add(veh.getAttribute('id'))
        try:
            zone_vehicles[veh_table.values(veh.getAttribute('id'))['prev_zone']]. \
                remove(veh.getAttribute('id'))  # remove the vehicle from its previous zone_vehicles
        except KeyError:
            # initiate the vehicle
            veh_table.set_item(veh.getAttribute('id'), initiate_new_veh(veh, zones, zone_id,
                                                                        config, understudied_area))
    except TypeError:
        veh_table.set_item(veh.getAttribute('id'), initiate_new_veh(veh, zones, zone_id,
                                                                    config, understudied_area))
    return veh_table, zone_vehicles
