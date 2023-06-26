"""
This is the utils file including the small functions
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['initiate_new_bus', 'initiate_new_veh', 'mac_address',
           'middle_zone', 'presence', 'choose_ch', 'det_buses_other_CH',
           'det_near_ch', 'update_bus_table', 'update_veh_table']

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
    return dict(long=float(veh.getAttribute('x')),
                lat=float(veh.getAttribute('y')),
                angle=float(veh.getAttribute('angle')),
                speed=float(veh.getAttribute('speed')),
                pos=float(veh.getAttribute('pos')),
                lane=veh.getAttribute('lane'),
                zone=zone_id,
                prev_zone=zone_id,
                neighbor_zones=zones.neighbor_zones(zone_id),
                in_area=presence(understudied_area, veh),
                trans_range=config.trans_range,
                message_dest={},
                message_source={},
                cluster_head=True,
                other_CHs=set(),
                cluster_members=set(),
                gate_CHs=set(),
                gates=dict(),
                IP=None,
                MAC=mac_address(),
                counter=config.counter
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
    return dict(long=float(veh.getAttribute('x')),
                lat=float(veh.getAttribute('y')),
                angle=float(veh.getAttribute('angle')),
                speed=float(veh.getAttribute('speed')),
                pos=float(veh.getAttribute('pos')),
                lane=veh.getAttribute('lane'),
                zone=zone_id,
                prev_zone=zone_id,
                neighbor_zones=zones.neighbor_zones(zone_id),
                in_area=presence(understudied_area, veh),
                trans_range=config.trans_range,
                message_dest={},
                message_source={},
                cluster_head=False,  # if the vehicle is a CH, it will be True
                primary_CH=None,
                other_CHs=set(),
                cluster_members=set(),  # This will be a Graph if the vehicle is a CH
                gates=dict(),
                gate_CHs=set(),
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


def presence(area_cord, veh_cord):
    """
    This function will determine if the vehicle or bus is in the understudied area (padded area)
    :param area_cord: the coordination of the understudied area (padded area)
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


def det_near_ch(veh_id, veh_table, bus_table,
                zone_buses, zone_vehicles):
    """
    This function will determine the buses and CHs nearby veh_id
    :param veh_table:
    :param bus_table:
    :param zone_buses:
    :param zone_vehicles:
    :param veh_id:
    :return: it returns bus_candidate which includes buses and vehicles being CH which are in neighbor zones
    """
    bus_candidates = set()
    ch_candidates = set()
    neigh_bus = []
    neigh_ch = []
    for neigh_z in veh_table.values(veh_id)['neighbor_zones']:
        neigh_bus += zone_buses[neigh_z]  # adding all the buses in the neighbor zones to a list
        neigh_ch += zone_vehicles[neigh_z]

    for j in neigh_bus:
        euclidian_dist = hs.haversine((veh_table.values(veh_id)["lat"],
                                       veh_table.values(veh_id)["long"]),
                                      (bus_table.values(j)['lat'],
                                       bus_table.values(j)['long']), unit=hs.Unit.METERS)

        if euclidian_dist <= min(veh_table.values(veh_id)['trans_range'],
                                 bus_table.values(j)['trans_range']):
            bus_candidates.add(j)

    for j in neigh_ch:
        if veh_table.values(j)['cluster_head'] is True:
            euclidian_dist = hs.haversine((veh_table.values(veh_id)["lat"],
                                           veh_table.values(veh_id)["long"]),
                                          (veh_table.values(j)['lat'],
                                           veh_table.values(j)['long']), unit=hs.Unit.METERS)

            if (euclidian_dist <= min(veh_table.values(veh_id)['trans_range'], veh_table.values(j)['trans_range'])) & \
                    (veh_table.values(j)['cluster_head'] is True):
                ch_candidates.add(j)

    return bus_candidates, ch_candidates


def det_buses_other_CH(bus_id, veh_table, bus_table,
                       zone_buses, zone_CH):

    all_near_chs = set()
    all_chs = set()
    for zone in bus_table.values(bus_id)['neighbor_zones']:
        all_chs = all_chs.union(zone_CH[zone])
        all_chs = all_chs.union(zone_buses[zone])

    for ch in all_chs:
        if ch == bus_id:
            continue
        elif 'bus' in ch:
            ch_table = bus_table
        else:
            ch_table = veh_table
        euclidian_dist = hs.haversine((bus_table.values(bus_id)["lat"],
                                       bus_table.values(bus_id)["long"]),
                                      (ch_table.values(ch)['lat'],
                                       ch_table.values(ch)['long']), unit=hs.Unit.METERS)

        if euclidian_dist < min(bus_table.values(bus_id)['trans_range'], ch_table.values(ch)['trans_range']):
            all_near_chs.add(ch)
    return all_near_chs


def choose_ch(table, veh_table_i,
              area_zones, bus_candidates):
    """
    this function will be used to choose a bus among all other buses or a ch from other chs nearby as the vehicle's
    primary_CH
    :param table:
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

    euclidian_distance = hs.haversine((prev_veh_lat, prev_veh_long),
                                      (veh_table_i['lat'], veh_table_i['long']),
                                      unit=hs.Unit.METERS)

    veh_alpha = np.arctan((prev_veh_long - veh_table_i['long']) /
                          (prev_veh_lat - veh_table_i['lat']))

    veh_vector_x = np.multiply(euclidian_distance, np.cos(veh_alpha))
    veh_vector_y = np.multiply(euclidian_distance, np.sin(veh_alpha))

    # nominee = ''
    min_ef = 10
    for j in bus_candidates:
        # latitude of the centre of previous zone that bus were in
        prev_bus_lat = (area_zones.zone_hash.values(table.values(j)['prev_zone'])['max_lat'] +
                        area_zones.zone_hash.values(table.values(j)['prev_zone'])['min_lat']) / 2
        # latitude of the centre of previous zone that bus were in
        prev_bus_long = (area_zones.zone_hash.values(table.values(j)['prev_zone'])['max_long'] +
                         area_zones.zone_hash.values(table.values(j)['prev_zone'])['min_long']) / 2

        euclidian_distance = hs.haversine((prev_bus_lat, prev_bus_long),
                                          (table.values(j)['lat'], table.values(j)['long']),
                                          unit=hs.Unit.METERS)

        bus_alpha = np.arctan((prev_veh_long - veh_table_i['long']) /
                              (prev_veh_lat - veh_table_i['lat']))

        bus_vector_x = np.multiply(euclidian_distance, np.cos(bus_alpha))
        bus_vector_y = np.multiply(euclidian_distance, np.sin(bus_alpha))

        cos_sim = 1 - spatial.distance.cosine([veh_vector_x, veh_vector_y], [bus_vector_x, bus_vector_y])
        theta_sim = np.arccos(cos_sim) / 2 * np.pi
        theta_dist = euclidian_distance/min(table.values(j)['trans_range'], veh_table_i['trans_range'])
        # since it might return RuntimeWarning regarding the division, the warning will be ignored
        with np.errstate(divide='ignore', invalid='ignore'):
            speed_sim = np.divide(np.abs(table.values(j)['speed'] - veh_table_i['speed']),
                                  np.abs(table.values(j)['speed']))

        # calculate the Eligibility Factor (EF) for buses
        ef = theta_sim + speed_sim + theta_dist

        if ef < min_ef:
            nominee = j

    return nominee


# def det_veh_ch(veh_table, veh_table_i,
#                area_zones, bus_candidates):


def update_bus_table(veh, bus_table, zone_id, understudied_area, zones, config, zone_buses):
    """
    this function updates the bus_tabel and zone_buses from main.py
    :param veh: it's the veh from .xml file
    :param bus_table: its bus_table
    :param zone_id: the zon_id f the vehicle
    :param understudied_area: the un_padded area
    :param zones: the area_zones.zones() or zones table from the DataTable class in the main.py
    :param config:
    :param zone_buses: zone_buses from the DataTable class in the main.py
    :return: updated bus_table and zone_buses
    """
    try:
        bus_table.values(veh.getAttribute('id'))['prev_zone'] = \
            bus_table.values(veh.getAttribute('id'))['zone']  # update prev_zone

        try:
            if bus_table.values(veh.getAttribute('id'))['prev_zone'] != \
                    bus_table.values(veh.getAttribute('id'))['zone']:
                zone_buses[bus_table.values(veh.getAttribute('id'))['prev_zone']]. \
                    remove(veh.getAttribute('id'))  # This will remove the vehicle from its previous zone_buses
        except KeyError:
            bus_table.set_item(veh.getAttribute('id'), initiate_new_bus(veh, zones, zone_id,
                                                                        config, understudied_area)
                               )

        bus_table.values(veh.getAttribute('id'))['long'] = float(veh.getAttribute('x'))
        bus_table.values(veh.getAttribute('id'))['lat'] = float(veh.getAttribute('y'))
        bus_table.values(veh.getAttribute('id'))['angle'] = float(veh.getAttribute('angle'))
        bus_table.values(veh.getAttribute('id'))['speed'] = float(veh.getAttribute('speed'))
        bus_table.values(veh.getAttribute('id'))['pos'] = float(veh.getAttribute('pos'))
        bus_table.values(veh.getAttribute('id'))['lane'] = veh.getAttribute('lane')
        bus_table.values(veh.getAttribute('id'))['zone'] = zone_id
        bus_table.values(veh.getAttribute('id'))['in_area'] = presence(understudied_area, veh)
        bus_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)
        bus_table.values(veh.getAttribute('id'))['gate_CHs'] = set()
        bus_table.values(veh.getAttribute('id'))['gates'] = dict()
        bus_table.values(veh.getAttribute('id'))['other_CHs'] = set()

        zone_buses[zone_id].add(veh.getAttribute('id'))

    except TypeError:
        bus_table.set_item(veh.getAttribute('id'), initiate_new_bus(veh, zones, zone_id,
                                                                    config, understudied_area))
    return bus_table, zone_buses


def update_veh_table(veh, veh_table, zone_id, understudied_area, zones, config, zone_vehicles):
    """
    this function updates the veh_tabel and zone_vehicles from main.py
    :param veh: it's the veh from .xml file
    :param veh_table: its veh_table
    :param zone_id: the zon_id f the vehicle
    :param understudied_area: the un_padded area
    :param zones: the area_zones.zones() or zones table from the DataTable class in the main.py
    :param config:
    :param zone_vehicles: zone_vehicles from the DataTable class in the main.py
    :return: updated veh_table and zone_vehicles
    """
    try:
        veh_table.values(veh.getAttribute('id'))['prev_zone'] = \
            veh_table.values(veh.getAttribute('id'))['zone']  # update prev_zone

        try:
            if veh_table.values(veh.getAttribute('id'))['prev_zone'] != \
                    veh_table.values(veh.getAttribute('id'))['zone']:
                zone_vehicles[veh_table.values(veh.getAttribute('id'))['prev_zone']]. \
                    remove(veh.getAttribute('id'))  # remove the vehicle from its previous zone_vehicles
        except KeyError:
            # initiate the vehicle
            veh_table.set_item(veh.getAttribute('id'), initiate_new_veh(veh, zones, zone_id,
                                                                        config, understudied_area)
                               )
        veh_table.values(veh.getAttribute('id'))['long'] = float(veh.getAttribute('x'))
        veh_table.values(veh.getAttribute('id'))['lat'] = float(veh.getAttribute('y'))
        veh_table.values(veh.getAttribute('id'))['angle'] = float(veh.getAttribute('angle'))
        veh_table.values(veh.getAttribute('id'))['speed'] = float(veh.getAttribute('speed'))
        veh_table.values(veh.getAttribute('id'))['pos'] = float(veh.getAttribute('pos'))
        veh_table.values(veh.getAttribute('id'))['lane'] = veh.getAttribute('lane')
        veh_table.values(veh.getAttribute('id'))['zone'] = zone_id
        veh_table.values(veh.getAttribute('id'))['in_area'] = presence(understudied_area, veh)
        veh_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)
        veh_table.values(veh.getAttribute('id'))['gate_CHs'] = set()
        veh_table.values(veh.getAttribute('id'))['gates'] = dict()
        veh_table.values(veh.getAttribute('id'))['other_CHs'] = set()

        zone_vehicles[zone_id].add(veh.getAttribute('id'))

    except TypeError:
        veh_table.set_item(veh.getAttribute('id'), initiate_new_veh(veh, zones, zone_id,
                                                                    config, understudied_area))
    return veh_table, zone_vehicles
