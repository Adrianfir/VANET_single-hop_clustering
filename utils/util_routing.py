"""
This is the utils file including the small functions for basic routing implementation
using https://ieeexplore.ieee.org/abstract/document/8588189
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['gen_message', 'intra_q_link', 'pass_packet']

# from distutils.command.config import config
#
# import numpy as np
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


def gen_message(s_id, d_id, veh_table,sent_messages, iter_messages, message_id,
                nodes_with_pack, pck_queue, time, configs):
    """

    :param s_id:
    :param d_id:
    :param veh_table:
    :param sent_messages:
    :param message_id:
    :param nodes_with_pack:
    :param pck_queue:
    :param time:
    :param configs:
    :return:
    """
    len_message = random.randint(3, 10)
    message = ['packet' + str(pck) for pck in range(len_message)]
    veh_table.values(s_id)['messages_sent']['message_id'] = dict(mess=message, source=s_id, dest=d_id,
                                                                 s_time=time, d_time=None, hops=0,
                                                                 length=len_message,
                                                                 d_loc = dict(lat=veh_table.values(d_id)['lat'],
                                                                              long=veh_table.values(d_id)['long'])
                                                                 )

    sent_messages[message_id] = dict(mess=message, source=s_id, dest=d_id, s_time=time,
                                       d_time=None, hops=0, length=len_message,
                                       d_loc = dict(lat=veh_table.values(d_id)['lat'],
                                                    long=veh_table.values(d_id)['long'])
                                       )
    iter_messages[message_id] = sent_messages[message_id]
    message_id += 1
    pck_dict = dict()
    for pck in message:
        pck_dict = dict(pck=pck, message_id=message_id, source=s_id, dest=d_id, current_node=s_id,s_time=time,
                        d_time=None, del_check=False, drop_count=configs.drop_count, hops=list(), gate_path=list(),
                        d_loc = dict(lat=veh_table.values(d_id)['lat'], long=veh_table.values(d_id)['long'])
                        )
        pck_dict['size'] = random.randint(configs.header_size + 1, configs.mtu) if pck == message[-1] \
            else configs.mtu  # the last packet of the message can have a size
        # between configs.header_size+1 and configs.mtu

        nodes_with_pack.add(s_id)
        pck_queue += 1
    return veh_table,sent_messages, iter_messages, message_id, nodes_with_pack, pck_queue

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
    # ch_id = veh_table.values(current_node)['primary_ch']
    # if 'bus' in ch_id:
    #
    #     q_link = intra_q_link(current_node, ch_id, veh_table, bus_table, configs)
    # else:
    #     q_link = intra_q_link(current_node, ch_id, veh_table, veh_table, configs)
    #
    # return True
    if ('veh' in current_node) and ('veh' in next_node):

        packet['hops'].append(next_node)
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

    dist = util.det_dist(current_node, veh_table, ch_id, table)
    q_link = ((1 - dist / configs.veh_trans_range) * (1 - abs((veh_table.values(current_node)['speed'] -
                                                              table.values(ch_id)['speed']) / 80)) *
              (1 - (abs(veh_table.values(current_node)['angle'] -table.values(ch_id)['angle']) / 180)))
    return q_link

def inter_ch_eval(node, ch, dest, veh_table, bus_table, configs):
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
    hops_pck = 0
    delay_pck = 0

    for pck in cluster.delivered_packets:
        hops_pck += len(pck['hops'])
        delay_pck += pck['d_time'] - pck['s_time']

    return hops_pck/(len(cluster.delivered_packets) + 0.000001), delay_pck/(len(cluster.delivered_packets) + 0.000001)

def greedy_gpsr(node, veh_table, packet, ne_nodes):
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
    other_chs_members = set()
    for oc in table.values(node)['other_chs']:
        other_chs_members = other_chs_members.union(table.values(oc)['cluster_members'])
    return other_chs_members

def find_gate_path(node, gate_chs_members, veh_table,
                   packet, net_graph):
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