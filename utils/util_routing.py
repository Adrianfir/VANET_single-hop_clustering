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
                            d_update=configs.des_address_update, last_dir=None, tabu_dir=None,
                            tabu_zone=list(),
            # CGCGR recovery state
            cgcgr_recovery_active = False,
            cgcgr_recovery_anchor = None
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
        # packet['tabu_zone'] = packet['zones'][-2:-1]
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
        # packet['tabu_zone'] = packet['zones'][-2:-1]
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
        # packet['tabu_zone'] = packet['zones'][-2:-1]
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
        # packet['tabu_zone'] = packet['zones'][-2:-1]
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
    nodes_with_pack.discard(k)
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
                    gate_chs_members = gate_chs_members.union(veh_table.values(veh_table.values(ov)['primary_ch'])['cluster_members'])
                else:
                    gate_chs_members = gate_chs_members.union(bus_table.values(veh_table.values(ov)['primary_ch'])['cluster_members'])

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
        'N':  {zc, N, NE, NW, W, E},
        'S':  {zc, S, SE, SW, W, E},
        'E':  {zc, E, NE, SE, N, S},
        'W':  {zc, W, NW, SW, N, W},
        'NE': {zc, N, NE, E, S, NW, SE},
        'NW': {zc, N, NW, W, S, NE, SW},
        'SE': {zc, S, SE, N, E, NE, SW},
        'SW': {zc, S, SW, N, W, SE, NW},
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
    alpha_zone=10.0,  # weight for zoneDist
    beta_cone=2.0,  # bonus for being in candidate cone zones
    gamma_geo=10.0,  # weight for normalized Euclidean distance term
    eta_tr=0.15,  # bonus for larger TR
    w_bus=0.20,  # bonus for buses
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
        return bool(v["cluster_head"] is True) or bool(v["primary_ch"] is not None)

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

# ============================================================
# CGCGR
# Cone-Guided Cluster-Aware Geographic Routing
# ============================================================

_CGCGR_CONE_ORDER_CW = (
    "NW",
    "NE",
    "EN",
    "ES",
    "SE",
    "SW",
    "WS",
    "WN",
)


# A cone is identified by the two reference-boundary rays
# enclosing it.
_CGCGR_CONE_FROM_BOUNDARY_PAIR = {

    frozenset(("NW", "N")): "NW",

    frozenset(("N", "NE")): "NE",

    frozenset(("NE", "E")): "EN",

    frozenset(("E", "SE")): "ES",

    frozenset(("SE", "S")): "SE",

    frozenset(("S", "SW")): "SW",

    frozenset(("SW", "W")): "WS",

    frozenset(("W", "NW")): "WN",
}


_CGCGR_CONE_BOUNDARIES = {

    "NW": ("NW", "N"),

    "NE": ("N", "NE"),

    "EN": ("NE", "E"),

    "ES": ("E", "SE"),

    "SE": ("SE", "S"),

    "SW": ("S", "SW"),

    "WS": ("SW", "W"),

    "WN": ("W", "NW"),
}


# ============================================================
# BASIC ACCESS HELPERS
# ============================================================

def _cgcgr_is_bus(node_id):

    return str(node_id).startswith("bus")


def _cgcgr_table(
        node_id,
        veh_table,
        bus_table
):

    if _cgcgr_is_bus(node_id):
        return bus_table

    return veh_table


def _cgcgr_values(
        node_id,
        veh_table,
        bus_table
):

    return _cgcgr_table(
        node_id,
        veh_table,
        bus_table
    ).values(node_id)


# ============================================================
# ANGLE HELPERS
# ============================================================

def _cgcgr_wrap_pi(angle):
    """
    Return angle in [-pi, pi).
    """

    return (
        angle + math.pi
    ) % (
        2.0 * math.pi
    ) - math.pi


def _cgcgr_norm_2pi(angle):
    """
    Return angle in [0, 2*pi).
    """

    return angle % (
        2.0 * math.pi
    )


# ============================================================
# FIXED LOCAL CARTESIAN FRAME + REFERENCE ENVELOPE
# ============================================================

def _cgcgr_projection_context(configs):
    """
    Construct and cache the fixed local Cartesian reference frame.

    x = East
    y = North

    The actual simulation coordinates are stored as latitude /
    longitude. CGCGR converts them to one local metric Cartesian
    frame before performing angular and penetration geometry.

    The reference envelope is also constructed here once and
    cached for the entire simulation.
    """

    cached = getattr(
        configs,
        "_cgcgr_projection_cache",
        None
    )

    if cached is not None:
        return cached


    study = configs.area

    explicit_ref = getattr(
        configs,
        "cgcgr_reference_area",
        None
    )

    margin_m = float(
        getattr(
            configs,
            "cgcgr_reference_margin_m",
            1600.0
        )
    )


    # --------------------------------------------------------
    # Projection origin: fixed centre of studied region.
    # --------------------------------------------------------

    lat0_deg = 0.5 * (
        float(study["min_lat"])
        +
        float(study["max_lat"])
    )

    lon0_deg = 0.5 * (
        float(study["min_long"])
        +
        float(study["max_long"])
    )

    lat0 = math.radians(
        lat0_deg
    )

    lon0 = math.radians(
        lon0_deg
    )

    earth_radius = 6371000.0

    cos_lat0 = math.cos(
        lat0
    )


    def project(lat, lon):
        """
        Local equirectangular projection.

        Sufficient for the geographic scale of the
        Richmond Hill simulation.
        """

        lat_r = math.radians(
            float(lat)
        )

        lon_r = math.radians(
            float(lon)
        )

        x = (
            earth_radius
            *
            cos_lat0
            *
            (lon_r - lon0)
        )

        y = (
            earth_radius
            *
            (lat_r - lat0)
        )

        return x, y


    # --------------------------------------------------------
    # Studied-area bounds in metric Cartesian coordinates.
    # --------------------------------------------------------

    sx0, sy0 = project(
        study["min_lat"],
        study["min_long"]
    )

    sx1, sy1 = project(
        study["max_lat"],
        study["max_long"]
    )

    study_xmin = min(
        sx0,
        sx1
    )

    study_xmax = max(
        sx0,
        sx1
    )

    study_ymin = min(
        sy0,
        sy1
    )

    study_ymax = max(
        sy0,
        sy1
    )


    # --------------------------------------------------------
    # Outer CGCGR reference envelope.
    # --------------------------------------------------------

    if explicit_ref is None:

        xmin = (
            study_xmin
            -
            margin_m
        )

        xmax = (
            study_xmax
            +
            margin_m
        )

        ymin = (
            study_ymin
            -
            margin_m
        )

        ymax = (
            study_ymax
            +
            margin_m
        )

    else:

        rx0, ry0 = project(
            explicit_ref["min_lat"],
            explicit_ref["min_long"]
        )

        rx1, ry1 = project(
            explicit_ref["max_lat"],
            explicit_ref["max_long"]
        )

        ref_xmin = min(
            rx0,
            rx1
        )

        ref_xmax = max(
            rx0,
            rx1
        )

        ref_ymin = min(
            ry0,
            ry1
        )

        ref_ymax = max(
            ry0,
            ry1
        )


        # Minimum-margin safeguard.
        xmin = min(
            ref_xmin,
            study_xmin - margin_m
        )

        xmax = max(
            ref_xmax,
            study_xmax + margin_m
        )

        ymin = min(
            ref_ymin,
            study_ymin - margin_m
        )

        ymax = max(
            ref_ymax,
            study_ymax + margin_m
        )


    xm = 0.5 * (
        xmin + xmax
    )

    ym = 0.5 * (
        ymin + ymax
    )


    # Four corners + four side midpoints.
    refs = {

        "NW": (
            xmin,
            ymax
        ),

        "N": (
            xm,
            ymax
        ),

        "NE": (
            xmax,
            ymax
        ),

        "E": (
            xmax,
            ym
        ),

        "SE": (
            xmax,
            ymin
        ),

        "S": (
            xm,
            ymin
        ),

        "SW": (
            xmin,
            ymin
        ),

        "W": (
            xmin,
            ym
        ),
    }


    context = {

        "project": project,

        "bounds": (
            xmin,
            xmax,
            ymin,
            ymax
        ),

        "refs": refs
    }


    setattr(
        configs,
        "_cgcgr_projection_cache",
        context
    )

    return context


def _cgcgr_xy_record(
        record,
        configs
):

    project = (
        _cgcgr_projection_context(
            configs
        )["project"]
    )

    return project(
        record["lat"],
        record["long"]
    )


def _cgcgr_xy_location(
        location,
        configs
):

    project = (
        _cgcgr_projection_context(
            configs
        )["project"]
    )

    return project(
        location["lat"],
        location["long"]
    )


# ============================================================
# DYNAMIC CONE GEOMETRY
# ============================================================

def _cgcgr_build_node_geometry(
        current_xy,
        configs
):
    """
    Build the eight reference-ray bearings ONCE for one
    current routing decision.

    This is deliberately separated from candidate evaluation
    so we do not sort the eight reference rays for every
    candidate and every metric.
    """

    cx, cy = current_xy

    refs = (
        _cgcgr_projection_context(
            configs
        )["refs"]
    )

    rays = []

    boundary_angles = {}


    for name, (
            rx,
            ry
    ) in refs.items():

        angle = _cgcgr_norm_2pi(

            math.atan2(
                ry - cy,
                rx - cx
            )
        )

        rays.append(
            (
                angle,
                name
            )
        )

        boundary_angles[
            name
        ] = angle


    rays.sort(
        key=lambda x: x[0]
    )


    return {

        "current_xy":
            current_xy,

        "rays":
            rays,

        "boundary_angles":
            boundary_angles
    }


def _cgcgr_cone_label_fast(
        point_xy,
        geometry
):
    """
    Determine the dynamic cone containing point_xy using
    already-computed current-node boundary rays.
    """

    cx, cy = (
        geometry["current_xy"]
    )

    px, py = point_xy

    if (
        px == cx
        and py == cy
    ):
        return None


    theta = _cgcgr_norm_2pi(

        math.atan2(
            py - cy,
            px - cx
        )
    )


    rays = geometry["rays"]

    n = len(rays)


    for i in range(n):

        angle_0, name_0 = (
            rays[i]
        )

        angle_1, name_1 = (
            rays[
                (i + 1) % n
            ]
        )


        if i == n - 1:

            inside = (
                theta >= angle_0
                or
                theta < angle_1
            )

        else:

            inside = (
                angle_0
                <= theta
                < angle_1
            )


        if inside:

            return (
                _CGCGR_CONE_FROM_BOUNDARY_PAIR[
                    frozenset(
                        (
                            name_0,
                            name_1
                        )
                    )
                ]
            )


    return None


def _cgcgr_cone_distance(
        cone_a,
        cone_b
):
    """
    Circular cone distance:

    NW -> NE -> EN -> ES ->
    SE -> SW -> WS -> WN -> NW
    """

    if (
        cone_a is None
        or
        cone_b is None
    ):
        return 4


    ia = (
        _CGCGR_CONE_ORDER_CW
        .index(
            cone_a
        )
    )

    ib = (
        _CGCGR_CONE_ORDER_CW
        .index(
            cone_b
        )
    )


    diff = abs(
        ia - ib
    )


    return min(
        diff,
        8 - diff
    )


# ============================================================
# DYNAMIC NORMALIZED ANGULAR DEVIATION
# ============================================================

def _cgcgr_kappa_fast(
        dest_xy,
        witness_xy,
        witness_cone,
        geometry,
        configs
):
    """
    Dynamically normalized angular deviation.

    kappa = angular deviation from destination
            ----------------------------------
            angular distance to relevant outer
            reference boundary

    Smaller is better.
    """

    if witness_cone is None:
        return float("inf")


    cx, cy = (
        geometry["current_xy"]
    )

    dx, dy = dest_xy

    ux, uy = witness_xy


    eps = float(
        getattr(
            configs,
            "cgcgr_geom_eps",
            1e-9
        )
    )


    theta_d = math.atan2(
        dy - cy,
        dx - cx
    )

    theta_u = math.atan2(
        uy - cy,
        ux - cx
    )


    delta_u = _cgcgr_wrap_pi(
        theta_u - theta_d
    )


    if abs(delta_u) <= eps:
        return 0.0


    boundary_1, boundary_2 = (
        _CGCGR_CONE_BOUNDARIES[
            witness_cone
        ]
    )


    theta_b1 = (
        geometry[
            "boundary_angles"
        ][boundary_1]
    )

    theta_b2 = (
        geometry[
            "boundary_angles"
        ][boundary_2]
    )


    d1 = _cgcgr_wrap_pi(
        theta_b1 - theta_d
    )

    d2 = _cgcgr_wrap_pi(
        theta_b2 - theta_d
    )


    boundary_diffs = [
        d1,
        d2
    ]


    # --------------------------------------------------------
    # Candidate is counter-clockwise from destination.
    # Use the outer boundary on that same side.
    # --------------------------------------------------------

    if delta_u > 0:

        same_side = [

            d for d
            in boundary_diffs

            if d > eps
        ]


        if same_side:

            boundary_delta = max(
                same_side
            )

        else:

            boundary_delta = max(
                boundary_diffs,
                key=abs
            )


    # --------------------------------------------------------
    # Candidate is clockwise from destination.
    # --------------------------------------------------------

    else:

        same_side = [

            d for d
            in boundary_diffs

            if d < -eps
        ]


        if same_side:

            boundary_delta = min(
                same_side
            )

        else:

            boundary_delta = max(
                boundary_diffs,
                key=abs
            )


    denominator = abs(
        boundary_delta
    )


    if denominator <= eps:
        return float("inf")


    return (
        abs(delta_u)
        /
        (
            denominator
            +
            eps
        )
    )


# ============================================================
# BOUNDARY PENETRATION
# ============================================================

def _cgcgr_penetration_fast(
        current_xy,
        witness_xy,
        configs
):
    """
    Normalized radial penetration through the current
    boundary-referenced direction.

        0 -> shallow candidate
        1 -> reference boundary
    """

    cx, cy = current_xy

    ux, uy = witness_xy


    vx = ux - cx

    vy = uy - cy


    eps = float(
        getattr(
            configs,
            "cgcgr_geom_eps",
            1e-9
        )
    )


    if math.hypot(
        vx,
        vy
    ) <= eps:

        return 0.0


    (
        xmin,
        xmax,
        ymin,
        ymax

    ) = _cgcgr_projection_context(
        configs
    )["bounds"]


    boundary_parameters = []


    if vx > eps:

        boundary_parameters.append(
            (
                xmax - cx
            ) / vx
        )

    elif vx < -eps:

        boundary_parameters.append(
            (
                xmin - cx
            ) / vx
        )


    if vy > eps:

        boundary_parameters.append(
            (
                ymax - cy
            ) / vy
        )

    elif vy < -eps:

        boundary_parameters.append(
            (
                ymin - cy
            ) / vy
        )


    boundary_parameters = [

        t for t
        in boundary_parameters

        if t > eps
    ]


    if not boundary_parameters:

        return 0.0


    t_boundary = min(
        boundary_parameters
    )


    # q = c + t(v)
    #
    # ||u-c|| / ||q-c|| = 1/t
    penetration = (
        1.0 /
        t_boundary
    )


    return max(
        0.0,
        min(
            1.0,
            penetration
        )
    )


# ============================================================
# CLUSTER-WITNESS PAIRS
# ============================================================

def cgcgr_cluster_pairs(
        current_node,
        candidate_ids,
        veh_table,
        bus_table
):
    """
    Convert candidate witness nodes into

        (logical_cluster, geometric_witness)

    pairs.

    A CH represents itself.

    A CM is mapped to its primary CH.

    Members of the CURRENT cluster are not valid independent
    inter-cluster targets.
    """

    all_ids = (

        set(
            veh_table.ids()
        )

        .union(

            set(
                bus_table.ids()
            )
        )
    )


    pairs = set()


    for witness in set(
        candidate_ids
    ):

        if (
            witness is None
            or
            witness == current_node
            or
            witness not in all_ids
        ):
            continue


        rec = _cgcgr_values(
            witness,
            veh_table,
            bus_table
        )


        if bool(
            rec.get(
                "cluster_head",
                False
            )
        ):

            cluster_id = witness

        else:

            cluster_id = rec.get(
                "primary_ch"
            )


        if cluster_id is None:
            continue


        if cluster_id == current_node:
            continue


        if cluster_id not in all_ids:
            continue


        pairs.add(
            (
                cluster_id,
                witness
            )
        )


    return pairs


# ============================================================
# COMPLETE CGCGR SELECTION
# ============================================================

def cgcgr_select_pair(
        current_node,
        packet,
        candidate_pairs,
        veh_table,
        bus_table,
        configs,
        gate_cost_fn=None
):
    """
    Select one logical cluster / witness pair.

    Returns

        target_cluster,
        witness,
        mode,
        entered_recovery

    mode is either

        "forward"
        "recovery"

    This function does NOT compute shortest paths for every
    candidate.

    gate_cost_fn is optional and is called ONLY if the complete
    geometric hierarchy ends with multiple tied candidates.
    """

    pairs = list(
        candidate_pairs
    )


    if not pairs:

        return (
            None,
            None,
            None,
            False
        )


    current_rec = _cgcgr_values(
        current_node,
        veh_table,
        bus_table
    )


    current_xy = _cgcgr_xy_record(
        current_rec,
        configs
    )


    d_loc = packet.get(
        "d_loc"
    )


    if (
        not d_loc
        or
        "lat" not in d_loc
        or
        "long" not in d_loc
    ):

        return (
            None,
            None,
            None,
            False
        )


    dest_xy = _cgcgr_xy_location(
        d_loc,
        configs
    )


    eps = float(
        getattr(
            configs,
            "cgcgr_geom_eps",
            1e-9
        )
    )


    current_distance = math.hypot(

        current_xy[0]
        -
        dest_xy[0],

        current_xy[1]
        -
        dest_xy[1]
    )


    if current_distance <= eps:

        return (
            None,
            None,
            None,
            False
        )


    tau = float(
        getattr(
            configs,
            "cgcgr_progress_tau",
            0.0
        )
    )


    eps_kappa = float(
        getattr(
            configs,
            "cgcgr_eps_kappa",
            0.10
        )
    )


    eps_pi = float(
        getattr(
            configs,
            "cgcgr_eps_pi",
            0.15
        )
    )


    eps_rho = float(
        getattr(
            configs,
            "cgcgr_eps_rho",
            1e-6
        )
    )


    recovery_tau = float(
        getattr(
            configs,
            "cgcgr_recovery_tau_m",
            25.0
        )
    )


    # --------------------------------------------------------
    # Build current-node cone geometry ONCE.
    # --------------------------------------------------------

    geometry = _cgcgr_build_node_geometry(
        current_xy,
        configs
    )


    destination_cone = (
        _cgcgr_cone_label_fast(
            dest_xy,
            geometry
        )
    )


    # --------------------------------------------------------
    # Evaluate all candidate pairs.
    # --------------------------------------------------------

    metrics = []


    for (
            cluster_id,
            witness
    ) in pairs:


        witness_rec = _cgcgr_values(
            witness,
            veh_table,
            bus_table
        )


        witness_xy = _cgcgr_xy_record(
            witness_rec,
            configs
        )


        witness_distance = math.hypot(

            witness_xy[0]
            -
            dest_xy[0],

            witness_xy[1]
            -
            dest_xy[1]
        )


        rho = (
            witness_distance
            /
            (
                current_distance
                +
                eps
            )
        )


        witness_cone = (
            _cgcgr_cone_label_fast(
                witness_xy,
                geometry
            )
        )


        cone_distance = (
            _cgcgr_cone_distance(
                witness_cone,
                destination_cone
            )
        )


        kappa = _cgcgr_kappa_fast(
            dest_xy,
            witness_xy,
            witness_cone,
            geometry,
            configs
        )


        penetration = (
            _cgcgr_penetration_fast(
                current_xy,
                witness_xy,
                configs
            )
        )


        metrics.append(

            {
                "pair":
                    (
                        cluster_id,
                        witness
                    ),

                "rho":
                    rho,

                "witness_distance":
                    witness_distance,

                "cone_distance":
                    cone_distance,

                "kappa":
                    kappa,

                "penetration":
                    penetration
            }
        )


    # ========================================================
    # STRICT NORMAL-FORWARDING GUARDRAIL
    # ========================================================

    progressive = [

        m for m
        in metrics

        if (
            m["rho"]
            <
            1.0 - tau
        )
    ]


    recovery_active = bool(

        packet.get(
            "cgcgr_recovery_active",
            False
        )
    )


    anchor = packet.get(
        "cgcgr_recovery_anchor"
    )


    # ========================================================
    # RECOVERY EXIT TEST
    # ========================================================

    if (
        recovery_active
        and
        anchor is not None
        and
        progressive
    ):


        anchor_xy = _cgcgr_xy_location(
            anchor,
            configs
        )


        anchor_distance = math.hypot(

            anchor_xy[0]
            -
            dest_xy[0],

            anchor_xy[1]
            -
            dest_xy[1]
        )


        if (
            current_distance
            <
            anchor_distance
            -
            recovery_tau
        ):

            packet[
                "cgcgr_recovery_active"
            ] = False

            packet[
                "cgcgr_recovery_anchor"
            ] = None

            recovery_active = False

            anchor = None


    # ========================================================
    # FINAL TIE BREAK HELPER
    # ========================================================

    def choose_final(
            final_set
    ):
        """
        Usually final_set contains one candidate.

        Only when multiple candidates survive the complete
        geometry do we evaluate gate-path cost.
        """

        if len(final_set) == 1:

            return final_set[0]


        # ----------------------------------------------------
        # Exact gate-path tie break, but ONLY for final ties.
        # ----------------------------------------------------

        if gate_cost_fn is not None:

            candidates_with_cost = []


            for m in final_set:

                target = (
                    m["pair"][0]
                )


                try:

                    cost = float(
                        gate_cost_fn(
                            target
                        )
                    )

                except Exception:

                    cost = float(
                        "inf"
                    )


                candidates_with_cost.append(
                    (
                        cost,
                        str(
                            m["pair"][0]
                        ),
                        str(
                            m["pair"][1]
                        ),
                        m
                    )
                )


            candidates_with_cost.sort(
                key=lambda x: (
                    x[0],
                    x[1],
                    x[2]
                )
            )


            return (
                candidates_with_cost[
                    0
                ][3]
            )


        # Deterministic fallback.
        return min(

            final_set,

            key=lambda m: (

                str(
                    m["pair"][0]
                ),

                str(
                    m["pair"][1]
                )
            )
        )


    # ========================================================
    # NORMAL FORWARDING
    # ========================================================

    if (
        not recovery_active
        and
        progressive
    ):

        # ----------------------------------------------------
        # Stage 1:
        # closest available cone layer
        # ----------------------------------------------------

        delta_min = min(

            m["cone_distance"]
            for m
            in progressive
        )


        cone_set = [

            m for m
            in progressive

            if (
                m["cone_distance"]
                ==
                delta_min
            )
        ]


        # ----------------------------------------------------
        # Stage 2:
        # dynamic normalized direction
        # ----------------------------------------------------

        kappa_min = min(

            m["kappa"]
            for m
            in cone_set
        )


        angular_set = [

            m for m
            in cone_set

            if (
                m["kappa"]
                <=
                kappa_min
                +
                eps_kappa
            )
        ]


        # ----------------------------------------------------
        # Stage 3:
        # penetration admissibility
        # ----------------------------------------------------

        pi_max = max(

            m["penetration"]
            for m
            in angular_set
        )


        penetration_set = [

            m for m
            in angular_set

            if (
                m["penetration"]
                >=
                pi_max
                -
                eps_pi
            )
        ]


        # ----------------------------------------------------
        # Stage 4:
        # exact geographic destination progress
        # ----------------------------------------------------

        rho_min = min(

            m["rho"]
            for m
            in penetration_set
        )


        geographic_set = [

            m for m
            in penetration_set

            if (
                m["rho"]
                <=
                rho_min
                +
                eps_rho
            )
        ]


        best = choose_final(
            geographic_set
        )


        return (
            best["pair"][0],
            best["pair"][1],
            "forward",
            False
        )


    # ========================================================
    # ENTER RECOVERY
    # ========================================================

    entered_recovery = False


    if not recovery_active:

        packet[
            "cgcgr_recovery_active"
        ] = True


        # Store recovery-anchor POSITION.
        packet[
            "cgcgr_recovery_anchor"
        ] = {

            "lat":
                float(
                    current_rec["lat"]
                ),

            "long":
                float(
                    current_rec["long"]
                )
        }


        recovery_active = True

        anchor = packet[
            "cgcgr_recovery_anchor"
        ]

        entered_recovery = True


    # ========================================================
    # RECOVERY MODE
    # ========================================================

    recovery_pool = metrics


    if not recovery_pool:

        return (
            None,
            None,
            "recovery",
            entered_recovery
        )


    # --------------------------------------------------------
    # Five-cone preferred PAIR pool.
    #
    # Destination cone + two cone layers on each side.
    # --------------------------------------------------------

    five_cone_pool = [

        m for m
        in recovery_pool

        if (
            m["cone_distance"]
            <= 2
        )
    ]


    if five_cone_pool:

        active_pool = (
            five_cone_pool
        )

    else:

        # Eight-cone fallback.
        active_pool = (
            recovery_pool
        )


    # --------------------------------------------------------
    # Recovery Stage 1:
    # minimum discrete cone separation
    # --------------------------------------------------------

    delta_min = min(

        m["cone_distance"]
        for m
        in active_pool
    )


    cone_set = [

        m for m
        in active_pool

        if (
            m["cone_distance"]
            ==
            delta_min
        )
    ]


    # --------------------------------------------------------
    # Recovery Stage 2:
    # normalized angular admissibility
    # --------------------------------------------------------

    kappa_min = min(

        m["kappa"]
        for m
        in cone_set
    )


    angular_set = [

        m for m
        in cone_set

        if (
            m["kappa"]
            <=
            kappa_min
            +
            eps_kappa
        )
    ]


    # --------------------------------------------------------
    # Recovery Stage 3:
    # penetration admissibility
    # --------------------------------------------------------

    pi_max = max(

        m["penetration"]
        for m
        in angular_set
    )


    penetration_set = [

        m for m
        in angular_set

        if (
            m["penetration"]
            >=
            pi_max
            -
            eps_pi
        )
    ]


    # --------------------------------------------------------
    # Recovery Stage 4:
    # moving-destination anchor-relative progress
    # --------------------------------------------------------

    anchor_xy = _cgcgr_xy_location(
        anchor,
        configs
    )


    anchor_distance = math.hypot(

        anchor_xy[0]
        -
        dest_xy[0],

        anchor_xy[1]
        -
        dest_xy[1]
    )


    for m in penetration_set:

        m[
            "rho_recovery"
        ] = (

            m["witness_distance"]
            /
            (
                anchor_distance
                +
                eps
            )
        )


    rho_recovery_min = min(

        m["rho_recovery"]
        for m
        in penetration_set
    )


    geographic_set = [

        m for m
        in penetration_set

        if (
            m["rho_recovery"]
            <=
            rho_recovery_min
            +
            eps_rho
        )
    ]


    best = choose_final(
        geographic_set
    )


    return (
        best["pair"][0],
        best["pair"][1],
        "recovery",
        entered_recovery
    )