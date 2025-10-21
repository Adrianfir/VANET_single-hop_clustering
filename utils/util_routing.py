"""
This is the utils file including the small functions for basic routing implementation
using https://ieeexplore.ieee.org/abstract/document/8588189
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['gen_message', 'intra_q_link', 'pass_packet', 'packet_pass_left_ch']

# from distutils.command.config import config
#
# import numpy as np
import random
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


def gen_message(s_id, d_id, veh_table,sent_messages, message_id,
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
                                                                      length=len_message)

    sent_messages['message_id'] = dict(mess=message, source=s_id, dest=d_id, s_time=time,
                                            d_time=None, hops=0, length=len_message)

    message_id += 1
    pck_dict = dict()
    for pck in message:
        pck_dict = dict(pck=pck, message_id=message_id, source=s_id, dest=d_id, current_node=s_id,
                           s_time=time, d_time=None, del_check=False, drop_count=configs.drop_count, hops=list(),
                           )
        pck_dict['size'] = random.randint(configs.header_size + 1, configs.mtu) if pck == message[-1] \
            else configs.mtu  # the last packet of the message can have a size
        # between configs.header_size+1 and configs.mtu

        veh_table.values(s_id)['packets_to_pass'].append(pck_dict)
        nodes_with_pack.add(s_id)
        pck_queue += 1
    return veh_table,sent_messages, message_id, nodes_with_pack, pck_queue

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


def packet_pass_left_ch(current_node, veh_table, bus_table, nodes_with_packet,
                delivered_packets, link_cap ,packet, time, configs):
    """
    This function is designed for passing packets of the chs leaving the area to the best candidates
    :param current_node:
    :param veh_table:
    :param bus_table:
    :param nodes_with_packet:
    :param delivered_packets:
    :param link_cap:
    :param packet:
    :param time:
    :param configs:
    :return:
    """
    table = veh_table if 'veh' in current_node else bus_table
    all_pot_next_nodes = table.values(current_node)['cluster_members']\
            .union(table.values(current_node)['other_chs'].union(table.values(current_node)['other_vehs']))
    next_node = all_pot_next_nodes.pop()
    eval_next_node = inter_ch_eval(current_node, next_node, packet['dest'], veh_table, bus_table, configs)
    for node in all_pot_next_nodes:
        # we use inter_ch_eval for even other_vehs
        if inter_ch_eval(current_node, node, packet['dest'], veh_table, bus_table, configs) > eval_next_node:
            eval_next_node = inter_ch_eval(current_node, node, packet['dest'], veh_table, bus_table, configs)
            next_node = node


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

    return veh_table, bus_table, nodes_with_packet, delivered_packets, link_cap

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

    d_dest = (util.det_dist(ch, next_ch_table, dest, next_ch_table)/
         max(node_table.values(node)['trans_range'], next_ch_table.values(ch)['trans_range']))

    v = (abs(node_table.values(node)['speed'] - next_ch_table.values(ch)['speed'])/
         max(node_table.values(node)['speed'], next_ch_table.values(ch)['speed']))


    return (0.5 * v) + (0.5 * d_dest)

def eval_routing(cluster):
    hops_pck = 0
    delay_pck = 0

    for pck in cluster.delivered_packets:
        hops_pck += len(pck['hops'])
        delay_pck += pck['d_time'] - pck['s_time']

    return hops_pck/len(cluster.delivered_packets), delay_pck/len(cluster.delivered_packets)