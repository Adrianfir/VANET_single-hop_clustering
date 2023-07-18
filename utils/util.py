"""
This is the utils file including the small functions
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['initiate_new_bus', 'initiate_new_veh', 'mac_address',
           'middle_zone', 'presence', 'choose_ch', 'det_buses_other_CH',
           'det_near_ch', 'update_bus_table', 'update_veh_table',
           'update_sa_net_graph', 'det_near_sa', 'det_dist', 'det_pot_ch']

import numpy as np
import random
import haversine as hs
from scipy import spatial
from graph import Graph


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
                speed=float(veh.getAttribute('speed')) + 0.01,
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
                other_CHs=set(),  # other CHs in the trans range of veh.getAttribute('id)
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
                speed=float(veh.getAttribute('speed')) + 0.01,
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
                other_CHs=set(),  # other CHs in the trans range of veh.getAttribute('id)
                cluster_members=set(),  # This will be a Graph if the vehicle is a CH
                gates=dict(),
                gate_CHs=set(),
                IP=None,
                MAC=mac_address(),
                counter=config.counter  # a counter_time to search and join a cluster
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


def middle_zone(u_row: object, u_col: object,
                l_row: object, l_col: object,
                n_cols: object) -> object:
    """
    This function is used in the zonex.py file
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
    middle_zone_id = ((middle_row - 1) * n_cols) + middle_col - 1
    middle_row -= 1             # because the formal numbering has been considered form 0 not 1
    middle_col -= 1             # because the formal numbering has been considered form 0 not 1
    return 'zone' + str(middle_zone_id), middle_row, middle_col


def presence(area_cord, veh_cord):
    """
    This function will determine if the vehicle or bus is in the understudied area (padded area)
    :param area_cord: the coordination of the understudied area (padded area)
    :param veh_cord: the coordination of the vehicle or bus
    :return: it returns True or False
    """
    if (
            (float(veh_cord.getAttribute('x')) < area_cord['max_long']) and
            (float(veh_cord.getAttribute('x')) > area_cord['min_long']) and
            (float(veh_cord.getAttribute('y')) < area_cord['max_lat']) and
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
    neigh_veh = []
    for neigh_z in veh_table.values(veh_id)['neighbor_zones']:
        neigh_bus += zone_buses[neigh_z]  # adding all the buses in the neighbor zones to a list
        neigh_veh += zone_vehicles[neigh_z]

    for j in neigh_bus:
        euclidian_dist = det_dist(veh_id, veh_table, j, bus_table)

        if euclidian_dist <= min(veh_table.values(veh_id)['trans_range'],
                                 bus_table.values(j)['trans_range']):
            bus_candidates.add(j)

    for j in neigh_veh:
        if veh_table.values(j)['cluster_head'] is True:
            euclidian_dist = det_dist(veh_id, veh_table, j, veh_table)

            if euclidian_dist <= min(veh_table.values(veh_id)['trans_range'],
                                     veh_table.values(j)['trans_range']):
                ch_candidates.add(j)

    return bus_candidates, ch_candidates


def det_buses_other_CH(bus_id, veh_table, bus_table,
                       zone_buses, zone_chs):
    all_near_chs = set()
    all_chs = set()
    for zone in bus_table.values(bus_id)['neighbor_zones']:
        all_chs.update(all_chs.union(zone_chs[zone]))
        # all_chs.update(all_chs.union(zone_buses[zone]))
    for ch in all_chs:
        if ch == bus_id:
            continue
        elif 'bus' in ch:
            ch_table = bus_table
        elif 'veh' in ch:
            ch_table = veh_table
        else:
            continue
        euclidian_dist = det_dist(bus_id, bus_table, ch, ch_table)

        if euclidian_dist <= min(bus_table.values(bus_id)['trans_range'], ch_table.values(ch)['trans_range']):
            all_near_chs.add(ch)
    return all_near_chs


def choose_ch(table, veh_table_i,
              area_zones, candidates):
    """
    this function will be used to choose a ch among all other candidates or a ch from other chs nearby as the vehicle's
    primary_CH.
    :param table: bus_table or veh_table based on the case that this function will be used
    :param veh_table_i:
    :param area_zones:
    :param candidates:
    :return: it This function will return the best candidate near to i (vehicle_i) to be
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
    min_ef = 1000000
    for j in candidates:

        # latitude of the centre of previous zone that ch were in
        prev_ch_lat = (area_zones.zone_hash.values(table.values(j)['prev_zone'])['max_lat'] +
                       area_zones.zone_hash.values(table.values(j)['prev_zone'])['min_lat']) / 2
        # latitude of the centre of previous zone that ch were in
        prev_ch_long = (area_zones.zone_hash.values(table.values(j)['prev_zone'])['max_long'] +
                        area_zones.zone_hash.values(table.values(j)['prev_zone'])['min_long']) / 2

        euclidian_distance = hs.haversine((prev_ch_lat, prev_ch_long),
                                          (table.values(j)['lat'], table.values(j)['long']),
                                          unit=hs.Unit.METERS)

        ch_alpha = np.arctan((prev_veh_long - veh_table_i['long']) /
                             (prev_veh_lat - veh_table_i['lat']))

        ch_vector_x = np.multiply(euclidian_distance, np.cos(ch_alpha))
        ch_vector_y = np.multiply(euclidian_distance, np.sin(ch_alpha))

        cos_sim = 1 - spatial.distance.cosine([veh_vector_x, veh_vector_y], [ch_vector_x, ch_vector_y])
        theta_sim = np.arccos(cos_sim) / 2 * np.pi
        theta_dist = euclidian_distance / min(table.values(j)['trans_range'], veh_table_i['trans_range'])
        # since it might return RuntimeWarning regarding the division, the warning will be ignored
        with np.errstate(divide='ignore', invalid='ignore'):
            speed_sim = np.divide(np.abs(table.values(j)['speed'] - veh_table_i['speed']),
                                  np.abs(table.values(j)['speed']))

        # calculate the Eligibility Factor (EF) for chs
        ef = theta_sim + speed_sim + theta_dist

        if ef < min_ef:
            nominee = j
    return nominee


# def det_veh_ch(veh_table, veh_table_i,
#                area_zones, bus_candidates):


def update_bus_table(veh, bus_table, zone_id, understudied_area, zones, config, zone_buses, zone_CH):
    """
    this function updates the bus_tabel and zone_buses from main.py
    :param zone_CH: the self.zone_CH dictionary
    :param veh: it's the veh from .xml file
    :param bus_table: its bus_table
    :param zone_id: the zon_id f the vehicle
    :param understudied_area: the un_padded area
    :param zones: the area_zones.zones() or zones table from the DataTable class in the main.py
    :param config:
    :param zone_buses: zone_buses from the DataTable class in the main.py
    :return: updated bus_table and zone_buses
    """
    if veh.getAttribute('id') in bus_table.ids():
        if bus_table.values(veh.getAttribute('id'))['zone'] != zone_id:
            bus_table.values(veh.getAttribute('id'))['prev_zone'] = \
                bus_table.values(veh.getAttribute('id'))['zone']  # update prev_zone
        zone_buses[bus_table.values(veh.getAttribute('id'))['zone']]. \
            remove(veh.getAttribute('id'))  # This will remove the vehicle from its previous zone_buses
        zone_CH[bus_table.values(veh.getAttribute('id'))['zone']]. \
            remove(veh.getAttribute('id'))
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
        zone_CH[zone_id].add(veh.getAttribute('id'))

    else:
        bus_table.set_item(veh.getAttribute('id'), initiate_new_bus(veh, zones, zone_id,
                                                                    config, understudied_area))
        zone_buses[zone_id].add(veh.getAttribute('id'))
        zone_CH[zone_id].add(veh.getAttribute('id'))
    return bus_table, zone_buses, zone_CH


def update_veh_table(veh, veh_table, zone_id, understudied_area, zones, config,
                     zone_vehicles, zone_CH, stand_alone, zone_stand_alone):
    """
    this function updates the veh_tabel and zone_vehicles from main.py
    :param zone_stand_alone: its the self.zone_stand_alone
    :param stand_alone: its the self.stand_alone
    :param zone_CH: the self.zone_CH dictionary
    :param veh: it's the veh from .xml file
    :param veh_table: its veh_table
    :param zone_id: the zon_id f the vehicle
    :param understudied_area: the un_padded area
    :param zones: the area_zones.zones() or zones table from the DataTable class in the main.py
    :param config:
    :param zone_vehicles: zone_vehicles from the DataTable class in the main.py
    :return: updated veh_table, zone_vehicles, zone_CH, stand_alone, zone_stand_alone
    """
    if veh.getAttribute('id') in veh_table.ids():
        if veh_table.values(veh.getAttribute('id'))['zone'] != zone_id:
            veh_table.values(veh.getAttribute('id'))['prev_zone'] = \
                veh_table.values(veh.getAttribute('id'))['zone']  # update prev_zone
        zone_vehicles[veh_table.values(veh.getAttribute('id'))['zone']]. \
            remove(veh.getAttribute('id'))  # remove the vehicle from its previous zone_vehicles
        if veh_table.values(veh.getAttribute('id'))['cluster_head'] is True:
            zone_CH[veh_table.values(veh.getAttribute('id'))['zone']]. \
                remove(veh.getAttribute('id'))
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
        if veh_table.values(veh.getAttribute('id'))['cluster_head'] is True:
            zone_CH[zone_id].add(veh.getAttribute('id'))
        elif (veh_table.values(veh.getAttribute('id'))['cluster_head'] is False) and \
                (veh_table.values(veh.getAttribute('id'))['primary_CH'] is None):
            stand_alone.add(veh.getAttribute('id'))
            if veh.getAttribute('id') in zone_stand_alone[veh_table.values(veh.getAttribute('id'))['prev_zone']]:
                zone_stand_alone[veh_table.values(veh.getAttribute('id'))['prev_zone']].remove(veh.getAttribute('id'))

            zone_stand_alone[zone_id].add(veh.getAttribute('id'))

    else:
        veh_table.set_item(veh.getAttribute('id'), initiate_new_veh(veh, zones, zone_id,
                                                                    config, understudied_area))
        zone_vehicles[zone_id].add(veh.getAttribute('id'))
        stand_alone.add(veh.getAttribute('id'))
        zone_stand_alone[veh_table.values(veh.getAttribute('id'))['zone']].add(veh.getAttribute('id'))
    return veh_table, zone_vehicles, zone_CH, stand_alone, zone_stand_alone


def det_near_sa(veh_id, veh_table,
                stand_alone, zone_stand_alone):
    """
    This function would determine the nearby stand_alone vehicles to veh_id
    :param veh_id: the stand-alone vehicle that we want to find the other stand-alones to it
    :param veh_table: self.vehicle_table in the data_cluster.py
    :param stand_alone: self.stand_alone in the data_cluster.py
    :param zone_stand_alone: self.zone_stand_alone in the data_cluster.py
    :return: nearby stand-alone vehicles to veh_id
    """
    result = set()
    neigh_stand_alones = []
    for neigh_z in veh_table.values(veh_id)['neighbor_zones']:
        neigh_stand_alones += zone_stand_alone[neigh_z]  # adding all the CHs in the neighbor zones to a list

    for j in neigh_stand_alones:
        if j != veh_id:
            euclidian_dist = det_dist(veh_id, veh_table, j, veh_table)

            if euclidian_dist <= min(veh_table.values(veh_id)['trans_range'],
                                     veh_table.values(j)['trans_range']):
                result.add(j)

    return result


def update_sa_net_graph(veh_table, k, near_sa, net_graph):
    """
    this function is used to determine chs among the stand-alones to k which is ch too
    :param veh_table:
    :param k:
    :param near_sa:
    :param net_graph:
    :return: chs among the stand-alones to k which is ch too
    """
    result = set()
    for j in near_sa[k]:
        if veh_table.values(k)['cluster_head'] + veh_table.values(j)['cluster_head'] > 0:
            dist = det_dist(k, veh_table, j, veh_table)

            if dist < min(veh_table.values(k)['cluster_head'],
                          veh_table.values(j)['cluster_head']):
                if veh_table.values(k)['cluster_head'] + veh_table.values(j)['cluster_head'] == 2:
                    veh_table.values(k)['other_CHs'].add(j)
                    veh_table.values(j)['other_CHs'].add(k)
                    net_graph.add_edge(k, j)

                elif (veh_table.values(k)['cluster_head'] is True) and \
                        (veh_table.values(j)['cluster_head'] is False):

                    if veh_table.values(j)['primary_CH'] != k:
                        veh_table.values(j)['other_CHs'].add(k)
                        veh_table.values(veh_table.values(j)['primary_CH'])['gates'][j].add(k)
                        veh_table.values(veh_table.values(j)['primary_CH'])['gate_CHs'].add(k)

                elif (veh_table.values(j)['cluster_head'] is True) and \
                        (veh_table.values(k)['cluster_head'] is False):

                    if veh_table.values(k)['primary_CH'] != j:
                        veh_table.values(k)['other_CHs'].add(j)
                        veh_table.values(veh_table.values(k)['primary_CH'])['gates'][k].add(j)
                        veh_table.values(veh_table.values(k)['primary_CH'])['gate_CHs'].add(j)

    return veh_table, net_graph


def det_dist(id1, table1, id2, table2):
    dist = hs.haversine((table1.values(id1)["lat"],
                         table1.values(id1)["long"]),
                        (table2.values(id2)['lat'],
                         table2.values(id2)['long']),
                        unit=hs.Unit.METERS)

    return dist


def det_pot_ch(veh_id, near_sa, n_near_sa):
    pot_ch = veh_id
    for mem in near_sa[veh_id]:
        if mem in near_sa.keys():
            if n_near_sa[mem] > n_near_sa[pot_ch]:
                pot_ch = mem
            else:
                continue
        else:
            continue
    return pot_ch
