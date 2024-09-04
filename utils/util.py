"""
This is the utils file including the small functions
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = [
           'choose_ch', 'det_befit', 'det_border_speed_count', 'det_buses_other_ch', 'det_con_factor', 'det_dist',
           'det_linkage_fac', 'det_near_ch', 'det_near_sa', 'det_pot_ch', 'det_pot_ch_dsca', 'image_num',
           'initiate_new_bus', 'initiate_new_veh', 'mac_address', 'make_slideshow', 'middle_zone', 'presence',
           'save_img', 'sumo_net_info', 'update_bus_table', 'update_degree_n', 'update_sa_net_graph', 'update_sai',
           'update_veh_table'
           ]

import numpy as np
import random
import haversine as hs
from linked_list import LinkedList
from scipy import spatial
import time
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import os
import cv2
import re


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
                lane={'id': veh.getAttribute('lane'), 'timer': 0},
                zone=zone_id,
                prev_zone=zone_id,
                neighbor_zones=zones.neighbor_zones(zone_id),
                in_area=presence(understudied_area, veh),
                arrive_time=None,
                depart_time=None,
                trans_range=config.bus_trans_range,
                message_dest={},
                message_source={},
                cluster_head=True,
                other_chs=set(),  # other chs in the trans range of veh.getAttribute('id)
                cluster_members=set(),
                gate_chs=set(),
                gates=dict(),
                ip=None,
                mac=mac_address(),
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
    lane_id = veh.getAttribute('lane')
    if ":" not in lane_id:
        pattern = re.compile(f"^(.*?){re.escape('_')}")
        match = pattern.search(lane_id)
        if match:
            lane_id = match.group(1)

    return dict(long=float(veh.getAttribute('x')),
                lat=float(veh.getAttribute('y')),
                angle=float(veh.getAttribute('angle')),
                speed=float(veh.getAttribute('speed')) + 0.01,
                sai=1,  # this feature is added for BeFit factor to make comparison
                degree_n=0,  # this is the neighborhood degree for Befit factor to make comparison
                pos=float(veh.getAttribute('pos')),
                lane={'id': lane_id, 'timer': 0},
                zone=zone_id,
                prev_zone=zone_id,
                neighbor_zones=zones.neighbor_zones(zone_id),
                in_area=presence(understudied_area, veh),
                arrive_time=None,
                depart_time=None,
                trans_range=config.veh_trans_range,
                message_dest={},
                message_source={},
                cluster_head=False,  # if the vehicle is a ch, it will be True
                primary_ch=None,
                other_chs=set(),  # other chs in the trans range of veh.getAttribute('id)
                cluster_members=set(),  # This will be a Graph if the vehicle is a ch
                gates=dict(),
                gate_chs=set(),
                other_vehs=set(),
                ip=None,
                mac=mac_address(),
                counter=config.counter,  # a counter_time to search and join a cluster
                start_ch_zone=None,  # This is the zone that vehicle starts becoming a ch
                cluster_record=LinkedList(None, {'start_time': None, 'ef': None, 'timer': None})  # the linked_list
                # would record the clusters that this vehicle would join. key is the cluster_head which is None when the
                # vehicle gets initialized, value['ef'] is the "ef" and value['timer] is the amount of time that this
                # vehicle would remain in that cluster
                )


def mac_address():
    """
    This function is used in the Main.py file
    :return: this function will return a generated random mac Address for vehicles
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
    middle_row -= 1  # because the formal numbering has been considered form 0 not 1
    middle_col -= 1  # because the formal numbering has been considered form 0 not 1
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
    This function will determine the buses and chs nearby veh_id
    :param veh_table:
    :param bus_table:
    :param zone_buses:
    :param zone_vehicles:
    :param veh_id:
    :return: it returns bus_candidate which includes buses and vehicles being ch which are in neighbor zones
    """
    bus_candidates = set()
    ch_candidates = set()
    other_vehs = set()
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
        euclidian_dist = det_dist(veh_id, veh_table, j, veh_table)

        if euclidian_dist <= min(veh_table.values(veh_id)['trans_range'],
                                 veh_table.values(j)['trans_range']):
            if veh_table.values(j)['cluster_head'] is True:
                ch_candidates.add(j)
            else:
                other_vehs.add(j)

    return bus_candidates, ch_candidates, other_vehs


def det_buses_other_ch(bus_id, veh_table, bus_table,
                       zone_buses, zone_chs):
    """

    :param bus_id:
    :param veh_table:
    :param bus_table:
    :param zone_buses:
    :param zone_chs:
    :return: the CHs in transmission range of bus_id
    """
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


def choose_ch(table, veh_table_i, area_zones, candidates, config):
    """
    This function will be used to choose a ch among all other candidates or a ch from other chs nearby as the vehicle's
    primary_ch. The Factors are [proposed similarity factor, speed similarity, distance].
    """

    # Latitude and longitude of the centre of the previous zone that the vehicle was in
    prev_veh_lat = (area_zones.zone_hash.values(veh_table_i['prev_zone'])['max_lat'] +
                    area_zones.zone_hash.values(veh_table_i['prev_zone'])['min_lat']) / 2
    prev_veh_long = (area_zones.zone_hash.values(veh_table_i['prev_zone'])['max_long'] +
                     area_zones.zone_hash.values(veh_table_i['prev_zone'])['min_long']) / 2

    euclidean_distance = hs.haversine((prev_veh_lat, prev_veh_long),
                                      (veh_table_i['lat'], veh_table_i['long']),
                                      unit=hs.Unit.METERS)

    veh_alpha = np.arctan2((veh_table_i['long'] - prev_veh_long), (veh_table_i['lat'] - prev_veh_lat))

    veh_vector_x = np.multiply(euclidean_distance, np.cos(veh_alpha))
    veh_vector_y = np.multiply(euclidean_distance, np.sin(veh_alpha))

    min_ef = float('inf')
    nominee = None

    for j in candidates:
        # Latitude and longitude of the centre of the previous zone that the candidate was in
        prev_ch_lat = (area_zones.zone_hash.values(table.values(j)['prev_zone'])['max_lat'] +
                       area_zones.zone_hash.values(table.values(j)['prev_zone'])['min_lat']) / 2
        prev_ch_long = (area_zones.zone_hash.values(table.values(j)['prev_zone'])['max_long'] +
                        area_zones.zone_hash.values(table.values(j)['prev_zone'])['min_long']) / 2

        euclidean_distance_ch = hs.haversine((prev_ch_lat, prev_ch_long),
                                             (table.values(j)['lat'], table.values(j)['long']),
                                             unit=hs.Unit.METERS)

        ch_alpha = np.arctan2((table.values(j)['long'] - prev_ch_long), (table.values(j)['lat'] - prev_ch_lat))

        ch_vector_x = np.multiply(euclidean_distance_ch, np.cos(ch_alpha))
        ch_vector_y = np.multiply(euclidean_distance_ch, np.sin(ch_alpha))

        # Calculate cosine similarity
        cos_sim = 1 - spatial.distance.cosine([veh_vector_x, veh_vector_y], [ch_vector_x, ch_vector_y])
        theta_sim = np.arccos(np.clip(cos_sim, -1.0, 1.0)) / (2 * np.pi)  # Ensure cos_sim is within valid range

        theta_dist = euclidean_distance / min(table.values(j)['trans_range'], veh_table_i['trans_range'])

        with np.errstate(divide='ignore', invalid='ignore'):
            speed_sim = np.divide(np.abs(table.values(j)['speed'] - veh_table_i['speed']) + 0.001,
                                  max(np.abs(table.values(j)['speed']), veh_table_i['speed']) + 0.001)

        # Calculate the Eligibility Factor (EF) for candidates
        weights = np.divide(config.weights, sum(config.weights))  # Normalize the weights
        ef = np.matmul(np.transpose(weights), np.array([theta_sim, speed_sim, theta_dist]))

        if ef < min_ef:
            min_ef = ef
            nominee = j

    return nominee, min_ef


def update_bus_table(veh, bus_table, zone_id, understudied_area, zones, config, zone_buses, zone_ch, current_time):
    """
    this function updates the bus_tabel and zone_buses from main.py
    :param current_time: self.time in the data_cluster.py
    :param zone_ch: the self.zone_ch dictionary
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
        zone_ch[bus_table.values(veh.getAttribute('id'))['zone']]. \
            remove(veh.getAttribute('id'))
        if bus_table.values(veh.getAttribute('id'))['lane']['id'] == veh.getAttribute('lane'):
            bus_table.values(veh.getAttribute('id'))['lane']['timer'] += 1
        else:
            bus_table.values(veh.getAttribute('id'))['lane']['id'] = veh.getAttribute('lane')
            bus_table.values(veh.getAttribute('id'))['lane']['timer'] = 0
        bus_table.values(veh.getAttribute('id'))['long'] = float(veh.getAttribute('x'))
        bus_table.values(veh.getAttribute('id'))['lat'] = float(veh.getAttribute('y'))
        bus_table.values(veh.getAttribute('id'))['angle'] = float(veh.getAttribute('angle'))
        bus_table.values(veh.getAttribute('id'))['speed'] = float(veh.getAttribute('speed')) + 0.01
        bus_table.values(veh.getAttribute('id'))['pos'] = float(veh.getAttribute('pos'))
        bus_table.values(veh.getAttribute('id'))['zone'] = zone_id
        bus_table.values(veh.getAttribute('id'))['in_area'] = presence(understudied_area, veh)
        bus_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)
        bus_table.values(veh.getAttribute('id'))['gate_chs'] = set()
        bus_table.values(veh.getAttribute('id'))['gates'] = dict()
        bus_table.values(veh.getAttribute('id'))['other_chs'] = set()
        zone_buses[zone_id].add(veh.getAttribute('id'))
        zone_ch[zone_id].add(veh.getAttribute('id'))

    else:
        bus_table.set_item(veh.getAttribute('id'), initiate_new_bus(veh, zones, zone_id,
                                                                    config, understudied_area))
        bus_table.values(veh.getAttribute('id'))['arrive_time'] = current_time
        zone_buses[zone_id].add(veh.getAttribute('id'))
        zone_ch[zone_id].add(veh.getAttribute('id'))
    return bus_table, zone_buses, zone_ch


def update_veh_table(veh, veh_table, zone_id, understudied_area, zones, config,
                     zone_vehicles, zone_ch, stand_alone, zone_stand_alone, current_time):
    """
    this function updates the veh_tabel and zone_vehicles from main.py
    :param current_time: self.time in data_cluster.py
    :param zone_stand_alone: its the self.zone_stand_alone
    :param stand_alone: its the self.stand_alone
    :param zone_ch: the self.zone_ch dictionary
    :param veh: it's the veh from .xml file
    :param veh_table: its veh_table
    :param zone_id: the zon_id f the vehicle
    :param understudied_area: the un_padded area
    :param zones: the area_zones.zones() or zones table from the DataTable class in the main.py
    :param config:
    :param zone_vehicles: zone_vehicles from the DataTable class in the main.py
    :return: updated veh_table, zone_vehicles, zone_ch, stand_alone, zone_stand_alone
    """
    if veh.getAttribute('id') in veh_table.ids():
        if veh_table.values(veh.getAttribute('id'))['zone'] != zone_id:
            veh_table.values(veh.getAttribute('id'))['prev_zone'] = \
                veh_table.values(veh.getAttribute('id'))['zone']  # update prev_zone
        zone_vehicles[veh_table.values(veh.getAttribute('id'))['zone']]. \
            remove(veh.getAttribute('id'))  # remove the vehicle from its previous zone_vehicles
        if veh_table.values(veh.getAttribute('id'))['cluster_head'] is True:
            zone_ch[veh_table.values(veh.getAttribute('id'))['zone']]. \
                remove(veh.getAttribute('id'))
        if veh_table.values(veh.getAttribute('id'))['lane']['id'] == veh.getAttribute('lane'):
            veh_table.values(veh.getAttribute('id'))['lane']['timer'] += 1
        else:
            lane_id = veh.getAttribute('lane')
            if ":" not in lane_id:
                pattern = re.compile(f"^(.*?){re.escape('_')}")
                match = pattern.search(lane_id)
                if match:
                    lane_id = match.group(1)
            veh_table.values(veh.getAttribute('id'))['lane']['id'] = lane_id
            veh_table.values(veh.getAttribute('id'))['lane']['timer'] = 0
        veh_table.values(veh.getAttribute('id'))['sai'] = update_sai(veh_table, veh.getAttribute('id'))
        veh_table.values(veh.getAttribute('id'))['long'] = float(veh.getAttribute('x'))
        veh_table.values(veh.getAttribute('id'))['lat'] = float(veh.getAttribute('y'))
        veh_table.values(veh.getAttribute('id'))['angle'] = float(veh.getAttribute('angle'))
        veh_table.values(veh.getAttribute('id'))['speed'] = float(veh.getAttribute('speed')) + 0.01
        veh_table.values(veh.getAttribute('id'))['pos'] = float(veh.getAttribute('pos'))
        veh_table.values(veh.getAttribute('id'))['zone'] = zone_id
        veh_table.values(veh.getAttribute('id'))['in_area'] = presence(understudied_area, veh)
        veh_table.values(veh.getAttribute('id'))['neighbor_zones'] = zones.neighbor_zones(zone_id)
        veh_table.values(veh.getAttribute('id'))['gate_chs'] = set()
        veh_table.values(veh.getAttribute('id'))['gates'] = dict()
        veh_table.values(veh.getAttribute('id'))['other_chs'] = set()
        zone_vehicles[zone_id].add(veh.getAttribute('id'))
        if veh_table.values(veh.getAttribute('id'))['cluster_head'] is True:
            zone_ch[zone_id].add(veh.getAttribute('id'))
        elif (veh_table.values(veh.getAttribute('id'))['cluster_head'] is False) and \
                (veh_table.values(veh.getAttribute('id'))['primary_ch'] is None):
            stand_alone.add(veh.getAttribute('id'))
            if veh.getAttribute('id') in zone_stand_alone[veh_table.values(veh.getAttribute('id'))['prev_zone']]:
                zone_stand_alone[veh_table.values(veh.getAttribute('id'))['prev_zone']].remove(veh.getAttribute('id'))

            zone_stand_alone[zone_id].add(veh.getAttribute('id'))

    else:
        veh_table.set_item(veh.getAttribute('id'), initiate_new_veh(veh, zones, zone_id,
                                                                    config, understudied_area))
        veh_table.values(veh.getAttribute('id'))['arrive_time'] = current_time
        zone_vehicles[zone_id].add(veh.getAttribute('id'))
        stand_alone.add(veh.getAttribute('id'))
        zone_stand_alone[veh_table.values(veh.getAttribute('id'))['zone']].add(veh.getAttribute('id'))
    return veh_table, zone_vehicles, zone_ch, stand_alone, zone_stand_alone


def det_near_sa(veh_id, veh_table,
                stand_alone, zone_stand_alone):
    """
    This function would determine the nearby stand_alone vehicles to veh_id
    :param veh_id: the stand-alone vehicle that we want to find the other stand-alones to it
    :param veh_table: vehicle_table in the data_cluster.py
    :param stand_alone: self.stand_alone in the data_cluster.py
    :param zone_stand_alone: self.zone_stand_alone in the data_cluster.py
    :return: nearby stand-alone vehicles to veh_id
    """
    result = set()
    neigh_stand_alones = []
    for neigh_z in veh_table.values(veh_id)['neighbor_zones']:
        neigh_stand_alones += zone_stand_alone[neigh_z]  # adding all the SAVs in the neighbor zones to a list

    for j in neigh_stand_alones:
        if j != veh_id:
            euclidian_dist = det_dist(veh_id, veh_table, j, veh_table)

            if euclidian_dist <= min(veh_table.values(veh_id)['trans_range'],
                                     veh_table.values(j)['trans_range']):
                result.add(j)

    return result


def det_befit(veh_table, veh_id,
              sumo_edges, sumo_nodes, config):
    """

    :param veh_table: self.veh_table
    :param sumo_edges: info related to roads in sumo
    :param sumo_nodes: info related to nodes in sumo
    :param veh_id: vehicle id
    :param config: config
    :return: the BF_v for making comparison
    """
    # T_leave
    road = veh_table.values(veh_id)['lane']['id']
    if (":" in road) or ('cluster' in road):
        return 0.0001           # because according to data, such edges are too short to be considered
    t = veh_table.values(veh_id)['lane']['timer']  # amount of time to cover distance "d"
    l = sumo_edges[road]['length']  # Length of the road segment
    from_node = sumo_edges[road]['from']
    if 'cluster' in from_node:  # some nodes are like "cluster_709104099_9493129504" -> 709104099 is good
        match = re.search(r'\d+', from_node)

        if match:
            from_node = match.group()
    d = hs.haversine((veh_table.values(veh_id)['lat'], veh_table.values(veh_id)['long']),
                     (sumo_nodes[from_node]['lat'], sumo_nodes[from_node]['long']),
                     unit=hs.Unit.METERS)  # Distance covered by a vehicle on that segment
    t_leave = (((l - d) / d) * t) / (
            l / veh_table.values(veh_id)['speed'])  # l/veh_table.values('veh_id)')['speed'] is for normalization

    # Sai_v
    sai_v = veh_table.values(veh_id)['sai'] / (
                1 + (config.iter * 0.01))              # (1 + (config.iter*0.01)) is for normalization

    # Degree_n
    if len(veh_table.values(veh_id)['other_vehs']) > 0:
        degree_n = update_degree_n(veh_table, veh_id)/len(veh_table.values(veh_id)['other_vehs'])
    else:
        degree_n = 0

    return t_leave + sai_v + degree_n


def det_con_factor(veh_table, veh_id):
    """

    :param veh_table: self.veh_table
    :param veh_id: vehicle id
    :return: returns te connectivity factor for making comparison
    """
    cf_v = det_border_speed_count(veh_table, veh_id) + det_linkage_fac(veh_table, veh_id)
    return cf_v


def update_sa_net_graph(veh_table, k, near_sa, net_graph):
    """
    this function is used to determine chs among the stand-alones to k which is ch too
    :param veh_table:
    :param k:
    :param near_sa:
    :param net_graph:
    :return: chs among the stand-alones to k which is ch too
    """
    for j in near_sa[k]:
        if veh_table.values(k)['cluster_head'] + veh_table.values(j)['cluster_head'] > 0:
            dist = det_dist(k, veh_table, j, veh_table)

            if dist < min(veh_table.values(k)['cluster_head'],
                          veh_table.values(j)['cluster_head']):
                if veh_table.values(k)['cluster_head'] + veh_table.values(j)['cluster_head'] == 2:
                    veh_table.values(k)['other_chs'].add(j)
                    veh_table.values(j)['other_chs'].add(k)
                    net_graph.add_edges_from([(k, j),
                                              (j, k)])

                elif (veh_table.values(k)['cluster_head'] is True) and \
                        (veh_table.values(j)['cluster_head'] is False):

                    if veh_table.values(j)['primary_ch'] != k:
                        veh_table.values(j)['other_chs'].add(k)
                        veh_table.values(veh_table.values(j)['primary_ch'])['gates'][j].add(k)
                        veh_table.values(veh_table.values(j)['primary_ch'])['gate_chs'].add(k)

                elif (veh_table.values(j)['cluster_head'] is True) and \
                        (veh_table.values(k)['cluster_head'] is False):

                    if veh_table.values(k)['primary_ch'] != j:
                        veh_table.values(k)['other_chs'].add(j)
                        veh_table.values(veh_table.values(k)['primary_ch'])['gates'][k].add(j)
                        veh_table.values(veh_table.values(k)['primary_ch'])['gate_chs'].add(j)

    return veh_table, net_graph


def det_dist(id1, table1, id2, table2):
    """

    :param id1: vehicle 1
    :param table1: self.veh_table or self.bus_table
    :param id2: vehicle 2
    :param table2: self.veh_table or self.bus_table
    :return: distance between two vehicles or buses
    """
    dist = hs.haversine((table1.values(id1)["lat"],
                         table1.values(id1)["long"]),
                        (table2.values(id2)['lat'],
                         table2.values(id2)['long']),
                        unit=hs.Unit.METERS)

    return dist


def det_pot_ch(veh_id, near_sa, n_near_sa):
    """

    :param veh_id:
    :param near_sa: dictionary shows the SAVs and their nearby SAVs
    :param n_near_sa: number of stand_alone vehicles to veh_id
    :return: potential SAVs nearby veh_id that can be CH
    """
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


def det_pot_ch_dsca(veh_id, near_sa, n_near_sa, sf_factor):
    """

    :param veh_id:
    :param near_sa: dictionary shows the SAVs and their nearby SAVs
    :param n_near_sa: number of stand_alone vehicles to veh_id
    :return: potential SAVs nearby veh_id that can be CH
    """
    pot_ch = veh_id
    for mem in near_sa[veh_id]:
        if mem in near_sa.keys():
            if sf_factor[mem] > sf_factor[pot_ch]:
                pot_ch = mem
            else:
                continue
        else:
            continue
    return pot_ch


def save_img(m, zoom_out_value, name):
    """
    :param name: name of the image
    :param zoom_out_value: zoom amount
    :param m: the map
    :return: an image will be saved to the directory path
    """
    # Save the map as an HTML file
    map_file = "map.html"
    m.save(map_file)

    # Set up the options for the webdriver
    options = Options()
    options.headless = True  # Run the browser in headless mode (without opening a visible window)

    # Initialize the Firefox webdriver
    driver = webdriver.Firefox(options=options)

    # Open the map HTML file
    driver.get('file:/Users/pouyafirouzmakan/Desktop/VANET/graph_map.html')

    # change the zoom
    script = f"document.getElementsByClassName('leaflet-control')[0].style.transform = 'scale({1 / zoom_out_value})';"
    driver.execute_script(script)
    # Wait for the map to load (you can adjust the waiting time if needed)
    time.sleep(1)

    # Take a screenshot of the entire webpage (including the map)
    screenshot = driver.get_screenshot_as_png()

    # Save the screenshot as an image file with good resolution
    img = Image.open(BytesIO(screenshot))
    img.save(name + '.png', 'PNG', quality=800)

    # Close the Firefox window and quit the webdriver instance
    driver.quit()

    # Delete the temporary HTML file
    os.remove(map_file)


def image_num(filename):
    """

    :param filename: name of the image
    :return: returns the number of image in the input folder to crearte the slideshow
    """
    # Extract the numeric part of the filename (assuming "Graph<number>.jpg" format)
    return int(''.join(filter(str.isdigit, filename)))


def make_slideshow(image_folder, output_path, fps):
    """
    :param image_folder: the images directory
    :param output_path: the output directory
    :param fps: play-back speed
    :return: it will create a mp4 video of the map_saved_imgs
    """
    image_files = [f for f in os.listdir(image_folder) if f.endswith('.jpg') or f.endswith('.png')]

    if not image_files:
        print("No images found in the specified folder.")
        return

    # Sort the image files based on the numeric part of the filename
    image_files.sort(key=image_num)

    # Determine the width and height of the images from the first image in the folder
    image_path = os.path.join(image_folder, image_files[0])
    first_image = cv2.imread(image_path)
    height, width, _ = first_image.shape

    # Create a VideoWriter object to save the video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'XVID' on Windows
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file)
        frame = cv2.imread(image_path)

        # Add the frame to the video
        out.write(frame)

    # Release the VideoWriter and close the video file
    out.release()

    print("Video creation complete.")


def sumo_net_info(sumo_edge, sumo_node):
    """
    In this function, the information related to the sumo and its net are going to be put inside two dictionaries to
    clarify and use them for creating the papers we are going to make comparison with them
    :param sumo_edge: xml.dom.minidom.parse(sumo_edge_path) which is related to roads segments info
    :param sumo_node: xml.dom.minidom.parse(sumo_node_path) which is related to nodes info
    :return: edge_info and node_info
    """
    edge_info = dict()
    node_info = dict()
    for edge in sumo_edge.documentElement.getElementsByTagName('edge'):
        # just "from" is enough to define the T_leave
        if ':' in edge.getAttribute('id'):
            edge_info[edge.getAttribute('id')] = {'from': None}
        else:
            edge_info[edge.getAttribute('id')] = {'from': edge.getAttribute('from')}
            edge_info[edge.getAttribute('id')]['length'] = float(edge.getElementsByTagName('lane')[0].
                                                                 getAttribute('length'))

    for node in sumo_node.documentElement.getElementsByTagName('node'):
        # Note that in the osm_bbox.osm.xml file, the attributes are "lat" and "lon" and is not "long"
        node_info[node.getAttribute('id')] = {'lat': float(node.getAttribute('lat')),
                                              'long': float(node.getAttribute('lon'))
                                              }
    return edge_info, node_info


def update_sai(veh_table, veh_id):
    """

    :param veh_table: self.veh_table
    :param veh_id: vehicle id
    :return: This function returns updated sai_v for each vehicle
    """
    neighbors_speed = []
    dif_speed = []
    if len(veh_table.values(veh_id)['other_vehs']) == 0:
        return veh_table.values(veh_id)['sai']
    for i in veh_table.values(veh_id)['other_vehs']:
        neighbors_speed.append(veh_table.values(i)['speed'])
        dif_speed.append(abs(veh_table.values(veh_id)['speed'] - veh_table.values(i)['speed']))
    delta_s = np.std(dif_speed)
    if abs(veh_table.values(veh_id)['speed'] - np.average(neighbors_speed)) <= delta_s:
        return veh_table.values(veh_id)['sai'] + 0.01
    elif abs(veh_table.values(veh_id)['speed'] - np.average(neighbors_speed)) > delta_s:
        return veh_table.values(veh_id)['sai'] - 0.01


def update_degree_n(veh_table, veh_id):
    """

    :param veh_table: self.veh_table
    :param veh_id: vehicle id
    :return: This function returns updated sai_v for each vehicle
    """
    neighbors_speed = []
    dif_speed = []
    degree_n = 0
    if len(veh_table.values(veh_id)['other_vehs']) == 0:
        return 0
    for i in veh_table.values(veh_id)['other_vehs']:
        neighbors_speed.append(veh_table.values(i)['speed'])
        dif_speed.append(abs(veh_table.values(veh_id)['speed'] - veh_table.values(i)['speed']))
    delta_s = np.std(dif_speed)
    for k in neighbors_speed:
        if abs(k - np.average(neighbors_speed)) <= delta_s:
            degree_n += 1
    return degree_n


def det_border_speed_count(veh_table, veh_id):
    """

    :param veh_table: self.veh_table
    :param veh_id: vehicle id
    :return: This function returns BS_count for each vehicle to make comparison
    """
    if len(veh_table.values(veh_id)['other_vehs']) == 0:
        return 0
    bs_count = 0
    for i in veh_table.values(veh_id)['other_vehs']:
        if abs(veh_table.values(veh_id)['speed'] - veh_table.values(i)['speed']) <= 5:
            bs_count += 1
    return bs_count


def det_linkage_fac(veh_table, veh_id):
    d_i = 0
    d = len(veh_table.values(veh_id)['other_vehs'])
    for i in veh_table.values(veh_id)['other_vehs']:
        d_i += len(veh_table.values(i)['other_vehs'])
    return (0.5 * d) + (0.5 * d_i)





