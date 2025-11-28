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
import networkx as nx
# import haversine as hs
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

    pck_dict = dict()
    for i in configs.messages[time]:
        message = configs.messages[time][i]
        message_count += 1
        for pck in configs.messages[time][i]['mess']:
            pck_dict = dict(pck=pck, message_id=i, source=message['source'], dest=message['dest'],
                            current_node=message['source'],s_time=time,  d_time=None, del_check=False,
                            drop_count=configs.drop_count, hops=list(), actions=list(), zones=list(), gate_path=list(),
                            d_loc = dict(lat=veh_table.values(message['dest'])['lat'],
                                         long=veh_table.values(message['dest'])['long'])
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
        if len(veh_table.values(current_node)['packets_to_pass']) == 0:
            nodes_with_packet.remove(current_node)

    if ('veh' in current_node) and ('bus' in next_node):
        packet['hops'].append(next_node)
        packet['zones'].appned(bus_table.values(next_node)['zone'])
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
        if len(veh_table.values(current_node)['packets_to_pass']) == 0:
            nodes_with_packet.remove(current_node)

    if ('bus' in current_node) and ('veh' in next_node):
        packet['hops'].append(next_node)
        packet['zones'].appned(veh_table.values(next_node)['zone'])
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
        if len(bus_table.values(current_node)['packets_to_pass']) == 0:
            nodes_with_packet.remove(current_node)

    if ('bus' in current_node) and ('bus' in next_node):
        packet['hops'].append(next_node)
        packet['zones'].appned(bus_table.values(next_node)['zone'])
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
        if len(bus_table.values(current_node)['packets_to_pass']) == 0:
            nodes_with_packet.remove(current_node)

    link_cap[tuple(sorted((current_node, next_node)))] -= packet['size']
    any_pck_transmitted = True

    return veh_table, bus_table, nodes_with_packet, delivered_packets, link_cap, any_pck_transmitted


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
    table = veh_table if 'veh' in node else bus_table
    for gc in table.values(node)['gate_chs']:
        if gc not in table.values(node)['other_chs']:
            gate_chs_members = gate_chs_members.union(veh_table.values(gc)['cluster_members'])

    for mem in table.values(node)['cluster_members']:
        for ov in veh_table.values(mem)['other_vehs']:
            if ((veh_table.values(ov)['primary_ch'] is not None) and
                    (veh_table.values(ov)['primary_ch'] not in
                     table.values(node)['gate_chs'].union(table.values(node)['other_chs']))):
                gate_gate_chs.add(veh_table.values(ov)['primary_ch'])
                if 'veh' in veh_table.values(ov)['primary_ch']:
                    gate_chs_members.union(veh_table.values(veh_table.values(ov)['primary_ch'])['cluster_members'])
                else:
                    gate_chs_members.union(bus_table.values(veh_table.values(ov)['primary_ch'])['cluster_members'])

    return gate_gate_chs, gate_chs_members

def other_chs_mem(node, table):
    """

    :param node:
    :param table:
    :return:
    """
    other_chs_members = set()
    for oc in table.values(node)['other_chs']:
        other_chs_members = other_chs_members.union(table.values(oc)['cluster_members'])
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




