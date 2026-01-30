"""
This is the utils file including the small functions for basic routing implementation
using https://ieeexplore.ieee.org/abstract/document/8588189
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['gen_message', 'intra_q_link', 'pass_packet']

# from distutils.command.config import config
#
import numpy as np
import random
import math
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
import networkx as nx
from networkx import nodes

# import haversine as hss
# from debugpy.common.timestamp import current
#
# from linked_list import LinkedList
import utils.util as util
# from scipy import spatial
# import time
# from PIL import Image
# from io import BytesIO
# from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.firefox.service import Service
# import os
# import cv2
# import re


def gen_message(veh_table,sent_messages, message_count,
                nodes_with_pack, pck_queue, time, configs):
    """
    :param veh_table:
    :param sent_messages:
    :param message_id:
    :param nodes_with_pack:
    :param pck_queue:
    :param time:
    :param configs:
    :return:
    """

    for i in configs.messages[time]:
        message = configs.messages[time][i]
        message_count += 1
        for pck in configs.messages[time][i]['mess']:
            pck_dict = dict(pck=pck, message_id=i, source=message['source'], dest=message['dest'],
                            current_node=message['source'],s_time=time,  d_time=None, del_check=False,
                            drop_count=configs.drop_count, hops=list(), actions=list(), zones=list(), gate_path=list(),
                            d_loc = dict(lat=veh_table.values(message['dest'])['lat'],
                                         long=veh_table.values(message['dest'])['long']),
                            d_zone = veh_table.values(message['dest'])['zone'],
                            d_update=5, last_dir=None, tabu_dir=None, tabu_zone=None
                            )
            pck_dict['size'] = random.randint(configs.header_size + 1, configs.mtu) if pck == configs.messages[time][i]['mess'][-1] \
                else configs.mtu  # the last packet of the message can have a size
            # between configs.header_size+1 and configs.mtu
            pck_dict['zones'].append(veh_table.values(message['source'])['zone'])

            veh_table.values(message['source'])['packets_to_pass'].append(pck_dict)
            nodes_with_pack.add(message['source'])
            pck_queue += 1

    return veh_table,sent_messages, message_count, nodes_with_pack, pck_queue

def pass_packet(current_node, next_node, veh_table, bus_table, nodes_with_packet,
                delivered_packets, link_cap, any_pck_transmitted ,packet, time):
    """
    The important thing is that the maximum speed is considered as 80 here
    :param any_pck_transmitted:
    :param link_cap:
    :param nodes_with_packet:
    :param next_node:
    :param time:
    :param packet:
    :param delivered_packets:
    :param current_node:
    :param veh_table:
    :param bus_table:
    :return:
    """

    # if next_node in packet['hops'][-3:]:
    #     return veh_table, bus_table, nodes_with_packet, delivered_packets, link_cap, any_pck_transmitted

    if ('veh' in current_node) and ('veh' in next_node):

        packet['hops'].append(next_node)
        packet['zones'].append(veh_table.values(next_node)['zone'])
        packet['current_node'] = next_node
        if next_node == packet['dest']:
            packet['del_check'] = True
            packet['d_time'] = time
            if packet['message_id'] not in veh_table.values(next_node)['packets_received'].keys():
                veh_table.values(next_node)['packets_received'][packet['message_id']] = list()
            veh_table.values(next_node)['packets_received'][packet['message_id']].append(packet)
            delivered_packets.append(packet)
        else:
            veh_table.values(next_node)['packets_to_pass'].append(packet)
            nodes_with_packet.add(next_node)

        veh_table.values(current_node)['packets_to_pass'].remove(packet)
        if not veh_table.values(current_node)['packets_to_pass']:
            nodes_with_packet.remove(current_node)

    if ('veh' in current_node) and ('bus' in next_node):
        packet['hops'].append(next_node)
        packet['zones'].append(bus_table.values(next_node)['zone'])
        packet['current_node'] = next_node
        if next_node == packet['dest']:
            packet['del_check'] = True
            packet['d_time'] = time
            if packet['message_id'] not in bus_table.values(next_node)['packets_received'].keys():
                bus_table.values(next_node)['packets_received'][packet['message_id']] = list()
            bus_table.values(next_node)['packets_received'][packet['message_id']].append(packet)
            delivered_packets.append(packet)
        else:
            bus_table.values(next_node)['packets_to_pass'].append(packet)
            nodes_with_packet.add(next_node)

        veh_table.values(current_node)['packets_to_pass'].remove(packet)
        if not veh_table.values(current_node)['packets_to_pass']:
            nodes_with_packet.remove(current_node)

    if ('bus' in current_node) and ('veh' in next_node):
        packet['hops'].append(next_node)
        packet['zones'].append(veh_table.values(next_node)['zone'])
        packet['current_node'] = next_node
        if next_node == packet['dest']:
            packet['del_check'] = True
            packet['d_time'] = time
            if packet['message_id'] not in veh_table.values(next_node)['packets_received'].keys():
                veh_table.values(next_node)['packets_received'][packet['message_id']] = list()
            veh_table.values(next_node)['packets_received'][packet['message_id']].append(packet)
            delivered_packets.append(packet)
        else:
            veh_table.values(next_node)['packets_to_pass'].append(packet)
            nodes_with_packet.add(next_node)

        bus_table.values(current_node)['packets_to_pass'].remove(packet)
        if not bus_table.values(current_node)['packets_to_pass']:
            nodes_with_packet.remove(current_node)

    if ('bus' in current_node) and ('bus' in next_node):
        packet['hops'].append(next_node)
        packet['zones'].append(bus_table.values(next_node)['zone'])
        packet['current_node'] = next_node
        if next_node == packet['dest']:
            packet['del_check'] = True
            packet['d_time'] = time
            if packet['message_id'] not in bus_table.values(next_node)['packets_received'].keys():
                bus_table.values(next_node)['packets_received'][packet['message_id']] = list()
            bus_table.values(next_node)['packets_received'][packet['message_id']].append(packet)
            delivered_packets.append(packet)
        else:
            bus_table.values(next_node)['packets_to_pass'].append(packet)
            nodes_with_packet.add(next_node)

        bus_table.values(current_node)['packets_to_pass'].remove(packet)
        if not bus_table.values(current_node)['packets_to_pass']:
            nodes_with_packet.remove(current_node)

    link_cap[tuple(sorted((current_node, next_node)))] -= packet['size']
    any_pck_transmitted = True

    return veh_table, bus_table, nodes_with_packet, delivered_packets, link_cap, any_pck_transmitted

def removed_nodes_packets(k, k_values, veh_table, bus_table, temp_left_vehs, temp_left_buses,
                          drops, nodes_with_pack, delivered_packets, config, link_cap, time, node_is_veh=True):
    pot_next_node = None
    if node_is_veh:
        if k_values['primary_ch'] is not None:
            pot_next_node = k_values['primary_ch']

        elif (k_values['cluster_head']) and (k_values['other_chs'] - {k}):  # >1 because in self.veh_table, the k itself is in other_chs too
            for v in k_values['other_chs'] - {k}:
                if (v not in temp_left_vehs) and (v not in temp_left_buses) and (v != k):
                    pot_next_node = v
                    break

        elif (k_values['cluster_head']) and (not (k_values['other_chs'] - {k})):
            if k_values['cluster_members']:
                for v in k_values['cluster_members']:
                    if v not in temp_left_vehs:
                        pot_next_node = v
                        break
            else:
                if k_values['other_vehs']:
                    for v in k_values['other_vehs']:
                        if v not in temp_left_vehs:
                            pot_next_node = v
                            break

        elif (not k_values['cluster_head']) and (not k_values['primary_ch']) and (not (k_values['other_chs'] - {k})):
            if k_values['other_vehs']:
                for v in k_values['other_vehs']:
                    if v not in temp_left_vehs:
                        pot_next_node = v
                        break

    if not node_is_veh:
        if k_values['other_chs']:
            for v in k_values['other_chs']:
                if (v not in temp_left_vehs) and (v not in temp_left_buses) and (v != k):
                    pot_next_node = v
                    break
        else:
            if k_values['cluster_members']:
                for v in k_values['cluster_members']:
                    if v not in temp_left_vehs:
                        pot_next_node = v
                        break

    if pot_next_node is None:
        if k_values['packets_to_pass']:
            for drop in k_values['packets_to_pass']:
                drops.append(drop)
            nodes_with_pack.remove(k)
    else:
        packets_to_pass = k_values['packets_to_pass'].copy()
        for pck in packets_to_pass:
            any_pck_transmitted = False
            try:
                _ = link_cap[tuple(sorted((k, pot_next_node)))]
            except KeyError:
                link_cap[tuple(sorted((k, pot_next_node)))] = config.link_limit
            (veh_table, bus_table,
             nodes_with_pack,
             delivered_packets,
             link_cap, any_pck_transmitted) = pass_packet(k, pot_next_node, veh_table, bus_table, nodes_with_pack,
                                                          delivered_packets, link_cap, any_pck_transmitted, pck,
                                                          time)

    return veh_table, bus_table, k_values, nodes_with_pack, delivered_packets, link_cap

def intra_q_link(current_node, ch_id, veh_table, table, configs):
    """

    :param current_node:
    :param ch_id:
    :param veh_table:
    :param table:
    :param configs:
    :return:
    """

    dist = util.det_dist(current_node, veh_table, ch_id, table)
    q_link = ((1 - dist / configs.veh_trans_range) * (1 - abs((veh_table.values(current_node)['speed'] -
                                                              table.values(ch_id)['speed']) / 80)) *
              (1 - (abs(veh_table.values(current_node)['angle'] -table.values(ch_id)['angle']) / 180)))
    return q_link

def inter_ch_eval(node, ch, dest, veh_table, bus_table, configs):
    """

    :param node:
    :param ch:
    :param dest:
    :param veh_table:
    :param bus_table:
    :param configs:
    :return:
    """
    node_table = veh_table if 'veh' in node else bus_table
    next_ch_table = veh_table if 'veh' in node else bus_table
    dest_table = veh_table if 'veh' in dest else bus_table

    d = (util.det_dist(node, node_table, ch, next_ch_table)/
         max(node_table.values(node)['trans_range'], next_ch_table.values(ch)['trans_range']))
    #
    d_dest = (util.det_dist(ch, next_ch_table, dest, next_ch_table)/
         max(node_table.values(node)['trans_range'], next_ch_table.values(ch)['trans_range']))

    v = (abs(node_table.values(node)['speed'] - next_ch_table.values(ch)['speed'])/
         max(node_table.values(node)['speed'], next_ch_table.values(ch)['speed']))


    return (0 * v) + (1 * d_dest)

def eval_routing(cluster):
    """

    :param cluster:
    :return:
    """
    hops_pck = 0
    delay_pck = 0

    for pck in cluster.delivered_packets:
        hops_pck += len(pck['hops'])
        delay_pck += pck['d_time'] - pck['s_time']

    return hops_pck/(len(cluster.delivered_packets) + 0.000001), delay_pck/(len(cluster.delivered_packets) + 0.000001)

def greedy_gpsr(node, veh_table, packet, ne_nodes):
    """

    :param node:
    :param veh_table:
    :param packet:
    :param ne_nodes:
    :return:
    """
    next_node = None
    dist_to_dest = util.det_dist(node, veh_table, packet['dest'], veh_table)
    for n in ne_nodes:
        new_dist_to_dest = util.det_dist(n, veh_table, packet['dest'], veh_table)
        if new_dist_to_dest < dist_to_dest:
            next_node = n
            dist_to_dest = new_dist_to_dest
    return next_node

def perimeter_gpsr(current_node_id, dest_node_id, neighbors, veh_table, prev_node_id=None):
    """
    Perimeter-phase GPSR forwarding (Gabriel Graph + right-hand rule).
    Always returns a valid neighbor if at least one exists.
    """

    def angle_between(v1, v2):
        ang = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
        if ang < 0:
            ang += 2 * math.pi
        return ang

    # --- Coordinates
    cur_lat = veh_table.values(current_node_id)['lat']
    cur_lon = veh_table.values(current_node_id)['long']
    dest_lat = veh_table.values(dest_node_id)['lat']
    dest_lon = veh_table.values(dest_node_id)['long']

    # --- If only one neighbor, return it directly
    if len(neighbors) == 1:
        return next(iter(neighbors))

    # --- Build Gabriel Graph (GG)
    GG_neighbors = []
    for nid in neighbors:
        n_lat = veh_table.values(nid)['lat']
        n_lon = veh_table.values(nid)['long']
        mid = ((cur_lat + n_lat) / 2, (cur_lon + n_lon) / 2)
        radius = util.det_dist(current_node_id, veh_table, nid, veh_table) / 2
        keep_edge = True

        # Check circle rule
        for oid in neighbors:
            if oid == nid:
                continue
            o_lat = veh_table.values(oid)['lat']
            o_lon = veh_table.values(oid)['long']
            d_mid_o = math.sqrt((mid[0] - o_lat)**2 + (mid[1] - o_lon)**2)
            if d_mid_o < radius:
                keep_edge = False
                break

        if keep_edge:
            GG_neighbors.append(nid)

    # If GG filtering removed all, keep all neighbors instead
    if not GG_neighbors:
        GG_neighbors = list(neighbors)

    # --- Compute destination vector
    dest_vec = (dest_lat - cur_lat, dest_lon - cur_lon)

    # --- Apply right-hand rule (always pick smallest positive angle)
    best_node, best_angle = None, float('inf')
    for nid in GG_neighbors:
        n_lat = veh_table.values(nid)['lat']
        n_lon = veh_table.values(nid)['long']
        nbr_vec = (n_lat - cur_lat, n_lon - cur_lon)
        ang = angle_between(dest_vec, nbr_vec)
        if ang < best_angle:
            best_angle = ang
            best_node = nid

    # Always return a neighbor if any exist
    return best_node

def gate_chs_mem(node, veh_table, bus_table):
    """

    :param node:
    :param veh_table:
    :param bus_table:
    :return:
    """
    gate_chs_members = set()
    gate_gate_chs = set()
    other_other_vehs = set()
    table = veh_table if 'veh' in node else bus_table
    for gc in table.values(node)['gate_chs']:
        if gc not in table.values(node)['other_chs']:
            gc_table = veh_table if 'veh' in gc else bus_table
            gate_chs_members = gate_chs_members.union(gc_table.values(gc)['cluster_members'])

    for mem in table.values(node)['cluster_members']:
        for ov in veh_table.values(mem)['other_vehs']:
            if veh_table.values(ov)['primary_ch'] is not None:
                other_other_vehs.add(mem)
            if ((veh_table.values(ov)['primary_ch'] is not None) and
                    (veh_table.values(ov)['primary_ch'] not in
                     table.values(node)['gate_chs'].union(table.values(node)['other_chs']))):
                gate_gate_chs.add(veh_table.values(ov)['primary_ch'])
                if 'veh' in veh_table.values(ov)['primary_ch']:
                    gate_chs_members.union(veh_table.values(veh_table.values(ov)['primary_ch'])['cluster_members'])
                else:
                    gate_chs_members.union(bus_table.values(veh_table.values(ov)['primary_ch'])['cluster_members'])

    return gate_gate_chs, gate_chs_members, other_other_vehs

def other_chs_mem(node, table, veh_table, bus_table):
    """

    :param node:
    :param table:
    :return:
    """
    other_chs_members = set()
    for oc in table.values(node)['other_chs']:
        oc_table = veh_table if 'veh' in oc else bus_table
        other_chs_members = other_chs_members.union(oc_table.values(oc)['cluster_members'])
    return other_chs_members

def find_gate_path(node, gate_chs_members, veh_table,
                   packet, net_graph):
    """

    :param node:
    :param gate_chs_members:
    :param veh_table:
    :param packet:
    :param net_graph:
    :return:
    """
    if veh_table.values(packet['dest'])['cluster_head'] is True:
        dest_ch = packet['dest']
    else:
        dest_ch = veh_table.values(packet['dest'])['primary_ch']
    if len(nx.shortest_path(net_graph, source=node, target=dest_ch)) > 4:
        print("the shortest path does not working efficiently")
    path = nx.shortest_path(net_graph, source=node, target=dest_ch)
    path.reverse()
    return path[:-1]


def left_dest(node, packet, left_dest_pack, nodes_with_pack, veh_table, bus_table):
    """

    :param node:
    :param packet:
    :param left_dest_pack:
    :param nodes_with_pack:
    :param veh_table:
    :param bus_table:
    :return:
    """
    left_dest_pack.append(packet)
    if 'veh' in node:
        veh_table.values(node)['packets_to_pass'].remove(packet)
        if len(veh_table.values(node)['packets_to_pass']) == 0:
            nodes_with_pack.remove(node)
    else:
        bus_table.values(node)['packets_to_pass'].remove(packet)
        if len(bus_table.values(node)['packets_to_pass']) == 0:
            nodes_with_pack.remove(node)

    return left_dest_pack, nodes_with_pack, veh_table, bus_table

def pdvr_criteria(veh0, table0, veh_ne, table_ne, veh_dest, table_dest):
    """

    :param veh0: current_node
    :param table0:
    :param veh_ne: neighbor node
    :param table_ne:
    :param veh_dest: destination node
    :param table_dest:
    :return:
    """
    vec_0ne = (table_ne.values(veh_ne)['lat'] - table0.values(veh0)['lat'],
               table_ne.values(veh_ne)['long'] - table0.values(veh0)['long'])

    data_ne = table_ne.values(veh_ne)['lat']
    if data_ne is None:
        raise ValueError(f"No data found for neighbor vehicle {veh_ne}")

    vec_0dest = (table_dest.values(veh_dest)['lat'] - table0.values(veh0)['lat'],
                 table_dest.values(veh_dest)['long'] - table0.values(veh0)['long'])


    angle_deg_0 = table_dest.values(veh_dest)['angle']  # from SUMO
    angle_rad_0 = math.radians(angle_deg_0)

    # Road direction vector R
    rx0 = math.cos(angle_rad_0)
    ry0 = math.sin(angle_rad_0)
    r_0 = (rx0, ry0)  # current node moving vector

    cos_sd = np.dot(r_0, vec_0dest)/ (np.linalg.norm(r_0) * np.linalg.norm(vec_0dest) + 0.00001)

    cos_sn = np.dot(r_0, vec_0ne)/ (np.linalg.norm(r_0) * np.linalg.norm(vec_0ne) + 0.00001)

    return cos_sd * cos_sn

def rl_perimeter_mode(agent, node_id, packet, helper, current_tick, veh_table,
                      bus_table, configs, n_zone_cols, train_reward_log, train):
    # for tick in range(num_ticks):
    #   for h in range(max_hops_per_tick):
    #       for node_id in nodes_having_packets:
    #           for packet in packets_at_node:
    """

    :param agent:
    :param node_id:
    :param packet:
    :param helper:
    :param current_tick:
    :param veh_table:
    :param bus_table:
    :param configs:
    :param n_zone_cols:
    :param train_reward_log
    :return:
    """
    current_node_id = node_id
    dest_id = packet["dest"]

    # # make sure packet has zones & s_tick initialized
    # if "zones" not in packet:
    #     node_info = helper._node_info(current_node_id)
    #     packet["zones"] = [node_info["zone_id"]]  # start history at current zone
    # if "s_tick" not in packet:
    #     packet["s_tick"] = current_tick

    # 1) build current state
    state = helper.build_state(current_node_id, packet, current_tick)

    # 2) select action (zone index 0..7)
    action = agent.select_action(state)

    # 3) distance BEFORE move (normalized)
    prev_dist = helper._distance_node_to_dest(current_node_id, dest_id)
    prev_dist_norm = min(prev_dist / helper.max_dist, 1.0)

    # 4) choose concrete next node for that zone
    next_node_id = rl_perimeter_choose_next_node(node_id, action, veh_table, bus_table, configs, n_zone_cols, packet)

    if next_node_id is None:
        # No neighbor in that zone:
        #   -> treat as bad action, stay at same node, small negative reward.
        reward = -2.0  # you can tune this (e.g., hop_penalty + extra)
        next_state = state
        done = False  # routing not necessarily terminal

        # 🔹 only train if we are in training mode
        if train:
            agent.store_transition(state, action, reward, next_state, done)
            agent.train_step()

        # you might also fall back to standard perimeter or greedy here if you want
    else:
        # 5) move packet in your sim (outside the RL code)
        # update packet['current_node'] & zone history
        # packet["current_node"] = next_node_id
        next_node_table = veh_table if 'veh' in next_node_id else bus_table
        next_info = next_node_table.values(next_node_id)
        next_zone_id = next_info["zone"]

        # 6) distance AFTER move
        new_dist = helper._distance_node_to_dest(next_node_id, dest_id)
        new_dist_norm = min(new_dist / helper.max_dist, 1.0)

        # 7) compute reward using your shaping (hop, distance, loop, delay)
        reward = helper.compute_reward(prev_dist_norm, new_dist_norm, packet, current_tick)

        # 8) build next state
        next_state = helper.build_state(next_node_id, packet, current_tick)

        # 9) terminal flag from RL perspective
        # Typically False here; you can set True if packet delivered/dropped right after.
        done = False
        # 🔹 only train if we are in training mode
        if train:
            agent.store_transition(state, action, reward, next_state, done)
            agent.train_step()

    train_reward_log.append(reward)
    return agent, train_reward_log, action, next_node_id

            # after this, your normal GPSR logic will decide if you go back to greedy mode

def rl_perimeter_choose_next_node(node_id, action, veh_table, bus_table, configs, n_zone_cols, packet):
    """

    :param node_id:
    :param action:
    :param veh_table:
    :param bus_table:
    :param configs:
    :param n_zone_cols:
    :param packet:
    :return:
    """
    node_table = veh_table if 'veh' in node_id else bus_table
    next_zone = configs.idx_to_zone[action]
    zone_name = zone_name_retrieval(node_id, n_zone_cols, configs, node_table, action)
    candidates = list()
    neighbor_nodes = node_table.values(node_id)['other_vehs'].union(node_table.values(node_id)['other_vehs'],
                                                              node_table.values(node_id)['cluster_members'])
    if node_table.values(node_id)['primary_ch'] is not None:
        neighbor_nodes.union({node_table.values(node_id)['primary_ch']})
    for veh in neighbor_nodes:
        table = veh_table if 'veh' in veh else bus_table
        if table.values(veh)['zone'] == zone_name:
            candidates.append(veh)
            continue

        sub_neighbor_nodes = table.values(veh)['other_vehs'].union(table.values(veh)['other_vehs'],
                                                                  table.values(veh)['cluster_members'])
        if table.values(veh)['primary_ch'] is not None:
            sub_neighbor_nodes.union({table.values(veh)['primary_ch']})

        for sub_veh in sub_neighbor_nodes:
            sub_table = veh_table if 'veh' in sub_veh else bus_table
            if sub_table.values(sub_veh)['zone'] == zone_name:
                candidates.append(veh)
                break


    next_node = None
    if len(candidates) == 0:
        return next_node
    else:
        dist_to_dest = 100000
        for veh in candidates:
            temp_table = veh_table if 'veh' in node_id else bus_table
            if util.det_dist(veh, temp_table, packet['dest'], veh_table) < dist_to_dest:
                next_node = veh

        return next_node

def zone_name_retrieval(node_id, n_zone_cols, configs, table, action):
    """
    want to retrieve the next node name from "N", "NE", "E", "SE", "S", "SW", "W", or "NW"
    :param node_id:
    :param n_zone_cols:
    :param configs
    :param action
    :return:
    """
    current_zone_number = int(table.values(node_id)['zone'][4:])
    zone_to_name = dict(
        N='zone' + str(current_zone_number + n_zone_cols),
        NE='zone' + str(current_zone_number + n_zone_cols + 1),
        E='zone' + str(current_zone_number + 1),
        SE='zone' + str(current_zone_number - n_zone_cols + 1),
        S='zone' + str(current_zone_number - n_zone_cols),
        SW='zone' + str(current_zone_number - n_zone_cols - 1),
        W='zone' + str(current_zone_number - 1),
        NW='zone' + str(current_zone_number + n_zone_cols - 1)
    )

    return zone_to_name[configs.idx_to_zone[action]]

def closest_reachable_zones(zc: int, zd: int, zone_table):
    """
    Returns a small 'directional cone' of candidate zones:
      current zone + 3 neighbor zones around the dominant direction to destination.

    Output: set of int zone IDs (validated)
    """
    n_cols = zone_table.n_cols
    n_rows = zone_table.n_rows  # ensure you have this; otherwise compute from total_zones/n_cols
    n_zones = n_cols * n_rows

    # def in_bounds(z):
    #     return 0 <= z < n_zones

    # --- centroid of a zone ---
    def centroid(z):
        v = zone_table.zone_hash.values(z)
        lat = 0.5 * (v['min_lat'] + v['max_lat'])
        lon = 0.5 * (v['min_long'] + v['max_long'])
        return lat, lon

    lat_c, lon_c = centroid(zc)
    lat_d, lon_d = centroid(zd)

    dlat = lat_d - lat_c
    dlon = lon_d - lon_c

    # --- neighbor indices ---
    zc_int = int(zc[4:])
    N  = str(zc_int + n_cols)
    S  = str(zc_int - n_cols)
    E  = str(zc_int + 1)
    W  = str(zc_int - 1)
    NE = str(zc_int + n_cols + 1)
    NW = str(zc_int + n_cols - 1)
    SE = str(zc_int - n_cols + 1)
    SW = str(zc_int - n_cols - 1)

    # Determine dominant direction (8-way)
    # (lat increases north; lon increases east)
    if (dlat >= 0) and (dlon >= 0):
        primary = 'NE' if abs(dlat) > 0 and abs(dlon) > 0 else ('N' if abs(dlat) >= abs(dlon) else 'E')
    elif (dlat >= 0) and (dlon < 0):
        primary = 'NW' if abs(dlat) > 0 and abs(dlon) > 0 else ('N' if abs(dlat) >= abs(dlon) else 'W')
    elif (dlat < 0) and (dlon >= 0):
        primary = 'SE' if abs(dlat) > 0 and abs(dlon) > 0 else ('S' if abs(dlat) >= abs(dlon) else 'E')
    else:
        primary = 'SW' if abs(dlat) > 0 and abs(dlon) > 0 else ('S' if abs(dlat) >= abs(dlon) else 'W')

    cone = {
        'N':  {zc, N, NE, NW},
        'S':  {zc, S, SE, SW},
        'E':  {zc, E, NE, SE},
        'W':  {zc, W, NW, SW},
        'NE': {zc, N, NE, E},
        'NW': {zc, N, NW, W},
        'SE': {zc, S, SE, E},
        'SW': {zc, S, SW, W},
    }[primary]

    # Filter out-of-bounds zones
    return {z for z in cone}

def zone_dist_fn(z1: int, z2: int, zone_table) -> int:
    """
    Chebyshev distance between two zones in a rectangular grid.
    """
    n_cols = zone_table.n_cols

    r1, c1 = divmod(z1, n_cols)
    r2, c2 = divmod(z2, n_cols)

    return max(abs(r1 - r2), abs(c1 - c2))

def greedy_smzcra( node_id, veh_table, bus_table, packet, ne_nodes, candidate_zones, zone_table,
    allow_regress_ratio=0.00, w_tr=0.15, tr_clip_ratio=3.0, w_bus=0.20, eps=1e-9
):
    """
    ZRHR++ Greedy at CH level, using ONLY ne_nodes.

    Stage 1 (zone-first):
      - Filter to candidate_zones cone
      - Require strict zoneDist improvement (Chebyshev grid distance)
      - Choose best by (zoneDist, geoDist), with bounded bus/TR preference.

    Stage 2 (zone-relaxed):
      - If Stage 1 fails, do CGGR-style geo greedy/perimeter-like choice on FULL pool
        to prevent orbit inflation when TR << zone size.
      - For veh-only neighborhoods, call your greedy_gpsr / perimeter_gpsr.
      - For mixed/bus cases, use distance-based fallback.

    Returns: next node id or None (caller may call orbit).
    """

    # ---------- helpers ----------
    def is_bus(nid):
        return str(nid).startswith("bus")

    def table_of(nid):
        return bus_table if is_bus(nid) else veh_table

    def vals_of(nid):
        return table_of(nid).values(nid)

    def to_zone_str(z):
        if z is None:
            return None
        if isinstance(z, str):
            return z
        return "zone" + str(int(z))

    def zone_id_int(zs):
        return int(str(zs).replace("zone", ""))

    def zone_dist(z1_str, z2_str):
        n_cols = zone_table.n_cols
        z1 = zone_id_int(z1_str)
        z2 = zone_id_int(z2_str)
        r1, c1 = divmod(z1, n_cols)
        r2, c2 = divmod(z2, n_cols)
        return max(abs(r1 - r2), abs(c1 - c2))

    def not_standalone(nid):
        # buses always valid
        if is_bus(nid):
            return True
        v = veh_table.values(nid)
        return bool(v.get("cluster_head")) or (v.get("primary_ch") is not None)

    # destination from packet (required)
    d_zone = to_zone_str(packet.get("d_zone"))
    d_loc = packet.get("d_loc")
    if d_zone is None or not d_loc:
        return None
    dx, dy = float(d_loc["long"]), float(d_loc["lat"])

    cur_zone = to_zone_str(vals_of(node_id).get("zone"))
    if cur_zone is None:
        return None
    cur_zdist = zone_dist(cur_zone, d_zone)

    # geometric baseline
    cv = vals_of(node_id)
    cx, cy = float(cv["long"]), float(cv["lat"])
    base_d = math.hypot(cx - dx, cy - dy)
    if base_d <= eps:
        return None

    # normalize candidate zones
    cz_set = set()
    if isinstance(candidate_zones, (set, list, tuple)):
        for z in candidate_zones:
            zs = to_zone_str(z)
            if zs is not None:
                cz_set.add(zs)
    else:
        zs = to_zone_str(candidate_zones)
        if zs is not None:
            cz_set.add(zs)

    # tabu zones from packet
    tabu = packet.get("tabu_zone", None)
    tabu_set = set()
    if isinstance(tabu, (set, list, tuple)):
        tabu_set = {to_zone_str(z) for z in tabu if to_zone_str(z) is not None}
    else:
        tz = to_zone_str(tabu)
        if tz is not None:
            tabu_set.add(tz)

    # candidate pool from ne_nodes only
    pool = []
    for nid in ne_nodes:
        if nid is None or nid == node_id:
            continue
        if not not_standalone(nid):
            continue
        pool.append(nid)
    if not pool:
        return None

    # -------------------------
    # Stage 1: zone-first strict macro progress in cone
    # -------------------------
    stage1 = []
    for nid in pool:
        v = vals_of(nid)
        z = to_zone_str(v.get("zone"))
        if z is None:
            continue
        if cz_set and (z not in cz_set):
            continue
        if z in tabu_set:
            continue

        zdist = zone_dist(z, d_zone)
        if zdist >= cur_zdist:
            continue  # strict zone progress

        nx, ny = float(v["long"]), float(v["lat"])
        geo_d = math.hypot(nx - dx, ny - dy)

        # geometric guardrail (optional)
        if geo_d > base_d * (1.0 + allow_regress_ratio):
            continue

        tr = float(v.get("trans_range", 0.0))
        bus_term = 1.0 if is_bus(nid) else 0.0
        stage1.append((zdist, geo_d, -bus_term, -min(tr, tr_clip_ratio), nid))

    if stage1:
        stage1.sort()
        return stage1[0][-1]

    # -------------------------
    # Stage 2: zone-relaxed (CGGR-like) geo progress over full pool
    # -------------------------
    dest_id = packet.get("dest")

    # 2A) If pure veh-only neighborhood, use your exact GPSR primitives
    if (dest_id is not None) and (not is_bus(node_id)) and (not is_bus(dest_id)) and all(not is_bus(n) for n in pool):
        nxt = greedy_gpsr(node_id, veh_table, packet, pool)
        if nxt is not None and not_standalone(nxt):
            return nxt

        # perimeter as a last resort inside Stage 2 (still before orbit)
        prev_node_id = packet["hops"][-1] if packet.get("hops") else None
        nxt = perimeter_gpsr(node_id, dest_id, set(pool), veh_table, prev_node_id=prev_node_id)
        if nxt is not None and not_standalone(nxt):
            return nxt

        return None

    # 2B) Mixed/bus-safe fallback: choose any node that reduces Euclidean distance most,
    #     with bounded bus/TR preference.
    best = None
    best_score = float("inf")

    # robust TR baseline (median)
    trs = sorted([float(vals_of(n).get("trans_range", 0.0)) for n in pool])
    tr_med = trs[len(trs)//2] if trs else 1.0
    if tr_med <= eps:
        tr_med = 1.0

    for nid in pool:
        v = vals_of(nid)
        nx, ny = float(v["long"]), float(v["lat"])
        geo_d = math.hypot(nx - dx, ny - dy)

        # require some geometric progress (otherwise orbit should handle)
        if geo_d >= base_d:
            continue

        tr = float(v.get("trans_range", 0.0))
        tr_ratio = min(max(tr / tr_med, 0.0), tr_clip_ratio)
        tr_term = math.log1p(tr_ratio) / math.log1p(tr_clip_ratio)

        bus_term = 1.0 if is_bus(nid) else 0.0

        # primary: normalized distance-to-dest; secondary: bus/TR (bounded)
        score = (geo_d / max(base_d, eps)) - w_bus * bus_term - w_tr * tr_term

        if score < best_score:
            best_score = score
            best = nid

    return best

def orbit_smzcra(node_id, veh_table, bus_table, packet, ne_nodes,
                 zone_table, orbit_zone_budget=12, orbit_inzone_budget=6, eps=1e-9):
    """
    ORBIT mode for SMZCA-ZRHR++ using ONLY ne_nodes and packet-carried destination zone.

    A) ORBIT_ZONE:
       - choose a neighbor-zone direction via zone-level right-hand rule around bearing to dest-zone
       - pick best node within that chosen neighbor zone
       - set tabu_zone = current_zone and tabu_dir = reverse(chosen_dir) to prevent ping-pong

    B) If no neighbor zone is reachable:
       - ORBIT_INZONE: GPSR greedy else GPSR perimeter inside current zone (bounded).
    """

    # -------------------------
    # Helpers: table access / normalization
    # -------------------------
    def is_bus(nid):
        return str(nid).startswith("bus")

    def table_of(nid):
        return bus_table if is_bus(nid) else veh_table

    def vals_of(nid):
        return table_of(nid).values(nid)

    def to_zone_str(z):
        if z is None:
            return None
        if isinstance(z, str):
            return z
        return "zone" + str(int(z))

    def zone_id_int(zs: str) -> int:
        return int(str(zs).replace("zone", ""))

    def zone_rc(zs: str):
        zid = zone_id_int(zs)
        r, c = divmod(zid, zone_table.n_cols)
        return r, c

    def zone_dist(z1: str, z2: str) -> int:
        r1, c1 = zone_rc(z1)
        r2, c2 = zone_rc(z2)
        return max(abs(r1 - r2), abs(c1 - c2))  # Chebyshev

    def not_standalone(nid) -> bool:
        if is_bus(nid):
            return True
        v = veh_table.values(nid)
        return bool(v.get("cluster_head", False)) or (v.get("primary_ch", None) is not None)

    def centroid_of_zone(zs: str):
        """
        Uses your ZoneID interface (same style as your closest_reachable_zones code):
          zone_table.values("zone343") -> dict(min_lat, max_lat, min_long, max_long)
        """
        try:
            zv = zone_table.values(zs)
        except Exception:
            # fallback if ZoneID stores zones differently (only if needed)
            zv = zone_table.zone_hash.values(zs)
        cx = 0.5 * (float(zv["min_long"]) + float(zv["max_long"]))
        cy = 0.5 * (float(zv["min_lat"]) + float(zv["max_lat"]))
        return cx, cy

    def zone_valid(zs: str) -> bool:
        try:
            _ = centroid_of_zone(zs)
            return True
        except Exception:
            return False

    # reverse direction for tabu_dir
    rev = {"N":"S","S":"N","E":"W","W":"E","NE":"SW","SW":"NE","NW":"SE","SE":"NW"}

    # -------------------------
    # Packet targets (MUST come from packet)
    # -------------------------
    d_zone = to_zone_str(packet.get("d_zone", None))
    if d_zone is None:
        return None

    dloc = packet.get("d_loc", None)
    if not dloc or "lat" not in dloc or "long" not in dloc:
        return None
    dx, dy = float(dloc["long"]), float(dloc["lat"])

    cur_zone = to_zone_str(vals_of(node_id).get("zone", None))
    if cur_zone is None:
        return None

    # -------------------------
    # Budgets (count via actions)
    # -------------------------
    actions = packet.get("actions", [])
    n_orbit_zone_used = sum(1 for a in actions if isinstance(a, str) and a.startswith("ORBIT_ZONE"))
    n_orbit_inzone_used = sum(1 for a in actions if isinstance(a, str) and a.startswith("ORBIT_INZONE"))

    # tabu_zone normalization
    tabu_zone = packet.get("tabu_zone", None)
    if tabu_zone is None:
        tabu_zone_set = set()
    elif isinstance(tabu_zone, (set, list, tuple)):
        tabu_zone_set = {to_zone_str(z) for z in tabu_zone if to_zone_str(z) is not None}
    else:
        tz = to_zone_str(tabu_zone)
        tabu_zone_set = {tz} if tz is not None else set()

    # tabu_dir normalization
    tabu_dir = packet.get("tabu_dir", None)
    if isinstance(tabu_dir, (set, list, tuple)):
        tabu_dir_set = set(tabu_dir)
    elif isinstance(tabu_dir, str):
        tabu_dir_set = {tabu_dir}
    else:
        tabu_dir_set = set()

    # -------------------------
    # Candidate pool from ne_nodes (not stand-alone only)
    # -------------------------
    pool = [nid for nid in ne_nodes if nid is not None and nid != node_id and not_standalone(nid)]
    if not pool:
        return None

    # Map pool nodes to zones
    zone_to_nodes = {}
    for nid in pool:
        z = to_zone_str(vals_of(nid).get("zone", None))
        if z is None:
            continue
        zone_to_nodes.setdefault(z, []).append(nid)

    # -------------------------
    # ORBIT_ZONE (if budget remains)
    # -------------------------
    if n_orbit_zone_used < orbit_zone_budget:
        n_cols = zone_table.n_cols
        zc_int = zone_id_int(cur_zone)

        dir_to_zone = {
            "N":  "zone" + str(zc_int + n_cols),
            "NE": "zone" + str(zc_int + n_cols + 1),
            "E":  "zone" + str(zc_int + 1),
            "SE": "zone" + str(zc_int - n_cols + 1),
            "S":  "zone" + str(zc_int - n_cols),
            "SW": "zone" + str(zc_int - n_cols - 1),
            "W":  "zone" + str(zc_int - 1),
            "NW": "zone" + str(zc_int + n_cols - 1),
        }

        # bearing from cur-zone centroid to dest-zone centroid
        cxz, cyz = centroid_of_zone(cur_zone)
        dxz, dyz = centroid_of_zone(d_zone)
        base_ang = math.atan2((dyz - cyz), (dxz - cxz))  # atan2(lat, long)

        # direction vectors (lat, long)
        dir_vec = {
            "E":  (0.0, 1.0),
            "NE": (1.0, 1.0),
            "N":  (1.0, 0.0),
            "NW": (1.0, -1.0),
            "W":  (0.0, -1.0),
            "SW": (-1.0, -1.0),
            "S":  (-1.0, 0.0),
            "SE": (-1.0, 1.0),
        }

        def wrap_0_2pi(a):
            while a < 0:
                a += 2 * math.pi
            while a >= 2 * math.pi:
                a -= 2 * math.pi
            return a

        # smallest positive rotation from base direction
        reachable_dirs = []
        for d, z in dir_to_zone.items():
            if not zone_valid(z):
                continue
            if z in tabu_zone_set:
                continue
            if d in tabu_dir_set:
                continue
            if z not in zone_to_nodes:
                continue

            vlat, vlon = dir_vec[d]
            ang = math.atan2(vlat, vlon)
            delta = wrap_0_2pi(ang - base_ang)
            reachable_dirs.append((delta, d, z))

        if reachable_dirs:
            reachable_dirs.sort(key=lambda t: t[0])
            _, chosen_dir, target_zone = reachable_dirs[0]

            # pick best node inside target_zone
            candidates = []
            for nid in zone_to_nodes.get(target_zone, []):
                v = vals_of(nid)
                z = to_zone_str(v.get("zone", None))
                if z is None:
                    continue

                zterm = zone_dist(z, d_zone)
                nx, ny = float(v["long"]), float(v["lat"])
                gterm = math.hypot(nx - dx, ny - dy)
                bus_term = 1 if is_bus(nid) else 0
                tr = float(v.get("trans_range", 0.0))

                # sort: zone progress, then geometric, then prefer bus, then TR
                candidates.append((zterm, gterm, -bus_term, -tr, nid))

            if candidates:
                candidates.sort()
                nxt = candidates[0][-1]

                packet["last_dir"] = chosen_dir
                packet["actions"].append(f"ORBIT_ZONE:{chosen_dir}->{target_zone}")

                # prevent immediate ping-pong:
                packet["tabu_zone"] = cur_zone
                packet["tabu_dir"] = rev.get(chosen_dir, None)

                return nxt

    # -------------------------
    # ORBIT_INZONE (bounded micro recovery)
    # -------------------------
    if n_orbit_inzone_used >= orbit_inzone_budget:
        return None

    inzone = [nid for nid in pool if to_zone_str(vals_of(nid).get("zone", None)) == cur_zone]
    if not inzone:
        return None

    dest_id = packet.get("dest", None)

    # Only call your GPSR functions when everything is veh_table-based
    if dest_id is not None and (not is_bus(node_id)) and (not is_bus(dest_id)) and all(not is_bus(n) for n in inzone):
        nxt = greedy_gpsr(node_id, veh_table, packet, inzone)
        if nxt is not None and not_standalone(nxt):
            packet["actions"].append("ORBIT_INZONE:GPSR_GREEDY")
            return nxt

        prev_node_id = packet["hops"][-1] if packet.get("hops") else None
        nxt = perimeter_gpsr(node_id, dest_id, set(inzone), veh_table, prev_node_id=prev_node_id)
        if nxt is not None and not_standalone(nxt):
            packet["actions"].append("ORBIT_INZONE:GPSR_PERIM")
            return nxt

    return None

def greedy_zcggr(
    node_id,
    veh_table,
    bus_table,
    packet,
    ne_nodes,
    candidate_zones,     # output of closest_reachable_zones(...)
    zone_table,          # zones object (must have n_cols and zone_hash.values("zone###") bounds)
    # weights / knobs
    alpha_zone=10.0,     # weight for zoneDist
    beta_cone=2.0,       # bonus for being in candidate cone zones
    gamma_geo=0.25,      # weight for normalized Euclidean distance term
    eta_tr=0.15,         # bonus for larger TR
    w_bus=0.20,          # bonus for buses
    allow_regress_ratio=0.05,  # allow small geometric regression if needed
    eps=1e-9,
):
    """
    Zone-assisted greedy for Z-CGGR.

    - Does NOT hard-require zoneDist decrease (zone is preference, not a constraint).
    - Prefers neighbors in directional cone (candidate_zones).
    - Uses packet-carried destination zone (packet['d_zone']) and destination loc (packet['d_loc']).
    - Returns next_node_id or None.
    """

    def is_bus(nid: str) -> bool:
        return str(nid).startswith("bus")

    def table_of(nid):
        return bus_table if is_bus(nid) else veh_table

    def vals_of(nid):
        return table_of(nid).values(nid)

    def to_zone_str(z):
        if z is None:
            return None
        if isinstance(z, str):
            return z
        return "zone" + str(int(z))

    def zone_id_int(zs: str) -> int:
        # expects "zone343"
        return int(str(zs).replace("zone", ""))

    def zone_dist(z1: str, z2: str) -> int:
        # Chebyshev distance on zone grid
        n_cols = zone_table.n_cols
        a = zone_id_int(z1)
        b = zone_id_int(z2)
        r1, c1 = divmod(a, n_cols)
        r2, c2 = divmod(b, n_cols)
        return max(abs(r1 - r2), abs(c1 - c2))

    def not_standalone(nid) -> bool:
        # valid forwarding target:
        #   buses always valid
        #   vehicles valid if cluster_head==True OR primary_ch is not None
        if is_bus(nid):
            return True
        v = veh_table.values(nid)
        return bool(v.get("cluster_head", False)) or (v.get("primary_ch", None) is not None)

    # --- destination info from packet ---
    d_zone = to_zone_str(packet.get("d_zone", None))
    dloc = packet.get("d_loc", None)
    if d_zone is None or not dloc or "lat" not in dloc or "long" not in dloc:
        return None

    dx = float(dloc["long"])
    dy = float(dloc["lat"])

    cur_vals = vals_of(node_id)
    cx = float(cur_vals["long"])
    cy = float(cur_vals["lat"])
    base_d = math.hypot(cx - dx, cy - dy)
    if base_d <= eps:
        return None

    cur_zone = to_zone_str(cur_vals.get("zone", None))
    if cur_zone is None:
        return None

    # normalize candidate_zones to set of "zone###"
    if candidate_zones is None:
        cone_zones = set()
    elif isinstance(candidate_zones, (set, list, tuple)):
        cone_zones = set(to_zone_str(z) for z in candidate_zones if to_zone_str(z) is not None)
    else:
        z = to_zone_str(candidate_zones)
        cone_zones = {z} if z is not None else set()

    # normalize tabu_zone
    tabu_zone = packet.get("tabu_zone", None)
    if tabu_zone is None:
        tabu_set = set()
    elif isinstance(tabu_zone, (set, list, tuple)):
        tabu_set = set(to_zone_str(z) for z in tabu_zone if to_zone_str(z) is not None)
    else:
        z = to_zone_str(tabu_zone)
        tabu_set = {z} if z is not None else set()

    # --- candidate pool (ne_nodes only) ---
    pool = []
    for nid in ne_nodes:
        if nid is None or nid == node_id:
            continue
        if not not_standalone(nid):
            continue
        v = vals_of(nid)
        nz = to_zone_str(v.get("zone", None))
        if nz is None:
            continue
        if nz in tabu_set:
            continue
        pool.append(nid)

    if not pool:
        return None

    # Guardrail: allow small regression only (avoid random wandering)
    max_allowed = base_d * (1.0 + allow_regress_ratio)

    # Build scored candidates
    # score = alpha*zoneDist - beta*I(cone) + gamma*(geo/base) - eta*TRbonus - w_bus*bus
    # lower score is better
    best_n = None
    best_score = float("inf")

    # robust TR baseline (median) for normalization
    trs = []
    for nid in pool:
        trs.append(float(vals_of(nid).get("trans_range", 0.0)))
    trs.sort()
    tr_med = trs[len(trs)//2] if trs else 1.0
    if tr_med <= eps:
        tr_med = 1.0

    for nid in pool:
        v = vals_of(nid)
        nz = to_zone_str(v.get("zone", None))

        nx = float(v["long"])
        ny = float(v["lat"])
        geo_d = math.hypot(nx - dx, ny - dy)
        if geo_d > max_allowed:
            # too much geometric regression
            continue

        z_term = zone_dist(nz, d_zone)
        cone_bonus = 1.0 if (cone_zones and nz in cone_zones) else 0.0

        g_term = geo_d / max(base_d, eps)

        tr = float(v.get("trans_range", 0.0))
        tr_ratio = max(0.0, tr / tr_med)
        tr_bonus = math.log1p(tr_ratio)  # diminishing returns

        bus_bonus = 1.0 if is_bus(nid) else 0.0

        score = (
            alpha_zone * z_term
            - beta_cone * cone_bonus
            + gamma_geo * g_term
            - eta_tr * tr_bonus
            - w_bus * bus_bonus
        )

        if score < best_score:
            best_score = score
            best_n = nid

    # If nothing passes guardrail, relax guardrail once: pick best by geo distance (safe fallback)
    if best_n is None:
        best_n = min(pool, key=lambda nid: math.hypot(float(vals_of(nid)["long"]) - dx,
                                                     float(vals_of(nid)["lat"]) - dy))

    return best_n


def perimeter_zcggr(
    node_id,
    veh_table,
    bus_table,
    packet,
    ne_nodes,
    zone_table,
    candidate_zones=None,
    eps=1e-9,
):
    """
    Perimeter-style recovery for Z-CGGR.

    Strategy:
      1) If veh-only context, use your perimeter_gpsr for micro recovery (within ne_nodes).
      2) Otherwise, do a right-hand rule selection on mixed neighbor set using destination direction,
         with a zone-aware tie-break (prefer cone zones, then smaller zoneDist, then closer geo).

    Returns next_node_id or None.
    """

    def is_bus(nid: str) -> bool:
        return str(nid).startswith("bus")

    def table_of(nid):
        return bus_table if is_bus(nid) else veh_table

    def vals_of(nid):
        return table_of(nid).values(nid)

    def to_zone_str(z):
        if z is None:
            return None
        if isinstance(z, str):
            return z
        return "zone" + str(int(z))

    def zone_id_int(zs: str) -> int:
        return int(str(zs).replace("zone", ""))

    def zone_dist(z1: str, z2: str) -> int:
        n_cols = zone_table.n_cols
        a = zone_id_int(z1)
        b = zone_id_int(z2)
        r1, c1 = divmod(a, n_cols)
        r2, c2 = divmod(b, n_cols)
        return max(abs(r1 - r2), abs(c1 - c2))

    def not_standalone(nid) -> bool:
        if is_bus(nid):
            return True
        v = veh_table.values(nid)
        return bool(v.get("cluster_head", False)) or (v.get("primary_ch", None) is not None)

    # packet-carried destination info
    d_zone = to_zone_str(packet.get("d_zone", None))
    dloc = packet.get("d_loc", None)
    if d_zone is None or not dloc or "lat" not in dloc or "long" not in dloc:
        return None

    dx = float(dloc["long"])
    dy = float(dloc["lat"])

    # normalize cone zones
    if candidate_zones is None:
        cone_zones = set()
    elif isinstance(candidate_zones, (set, list, tuple)):
        cone_zones = set(to_zone_str(z) for z in candidate_zones if to_zone_str(z) is not None)
    else:
        z = to_zone_str(candidate_zones)
        cone_zones = {z} if z is not None else set()

    # candidate pool
    pool = []
    for nid in ne_nodes:
        if nid is None or nid == node_id:
            continue
        if not not_standalone(nid):
            continue
        nz = to_zone_str(vals_of(nid).get("zone", None))
        if nz is None:
            continue
        pool.append(nid)
    if not pool:
        return None

    # ---- Option 1: veh-only perimeter via your GPSR implementation (micro recovery) ----
    dest_id = packet.get("dest", None)
    if dest_id is not None and (not is_bus(node_id)) and (not is_bus(dest_id)) and all(not is_bus(n) for n in pool):
        # NOTE: perimeter_gpsr expects a set/list of neighbors
        prev_node_id = packet["hops"][-1] if packet.get("hops") else None
        try:
            nxt = perimeter_gpsr(node_id, dest_id, set(pool), veh_table, prev_node_id=prev_node_id)
        except Exception:
            nxt = None
        if nxt is not None and not_standalone(nxt):
            return nxt

    # ---- Option 2: mixed right-hand rule (geometric) with zone-aware tie-break ----
    cur = vals_of(node_id)
    cx = float(cur["long"])
    cy = float(cur["lat"])

    # destination vector (from current to dest)
    dv = (dy - cy, dx - cx)  # (lat, long) style for atan2
    base_ang = math.atan2(dv[0], dv[1])

    def cw_angle(from_ang, to_ang):
        a = to_ang - from_ang
        if a < 0:
            a += 2 * math.pi
        return a

    best = None
    best_key = None

    for nid in pool:
        v = vals_of(nid)
        nx = float(v["long"])
        ny = float(v["lat"])

        nv = (ny - cy, nx - cx)
        ang = math.atan2(nv[0], nv[1])
        rhr = cw_angle(base_ang, ang)  # smaller is more right-hand

        nz = to_zone_str(v.get("zone", None))
        zterm = zone_dist(nz, d_zone)
        cone = 1 if (cone_zones and nz in cone_zones) else 0
        geo = math.hypot(nx - dx, ny - dy)

        # key order:
        # 1) smallest right-hand angle
        # 2) prefer cone zones (cone=1 -> sort earlier)
        # 3) smaller zoneDist
        # 4) smaller geo distance
        key = (rhr, -cone, zterm, geo)

        if best_key is None or key < best_key:
            best_key = key
            best = nid

    return best