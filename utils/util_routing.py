"""
This is the utils file including the small functions for basic routing implementation
using https://ieeexplore.ieee.org/abstract/document/8588189
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['check_receiver', 'extra_ch_evaluation', 'intra_q_link', 'pack_delivered', 'pass_packet']

from distutils.command.config import config

import numpy as np
import random
import haversine as hs
from debugpy.common.timestamp import current

from linked_list import LinkedList
import utils.util as util
from scipy import spatial
import time
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import os
import cv2
import re


def check_receiver(on_way_packets, pack, veh_table, bus_table, current_node):
    """
    this function checks f the packet is delivered ti the destination.
    :param on_way_packets:
    :param pack: packet_id of the packet
    :param veh_table:
    :param bus_table:
    :param current_node:
    :return: 1 if the destination is the ch node having the packet. 0 if the destination node is inside the
    cluster members of the ch node that has received the packet. -1 if the destination node is  neither the ch nor
    inside that cluster
    """
    if current_node == on_way_packets[pack]['dest']:
        return 1

    elif ((('bus' in current_node) and
          (on_way_packets[pack]['dest'] in bus_table.values(current_node)['cluster_members']))
          or ((('veh' in current_node) and (veh_table.values(current_node)['cluster_head'] is True))
              and (on_way_packets[pack]['dest'] in veh_table.values(current_node)['cluster_members']))):
        return 0

    else:

        return -1


def pack_delivered(current_node, veh_table, bus_table,
                   pack, on_way_packets, delivered_packets):
    if 'bus' in current_node:
        on_way_packets[pack]['del_check'] = 1
        bus_table.values(current_node)['packet_received'][pack] = on_way_packets[pack]
        temp_pack = bus_table.values(current_node)['packet_received'][pack].pop()


    else:

    return True


def pass_packet(current_node, next_node, veh_table, bus_table, nodes_with_packet, packet, configs):
    """
    The important thing is that the maximum speed is considered as 80 here
    :param current_node:
    :param veh_table:
    :param bus_table:
    :param configs
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
        veh_table.values(next_node)['packet_to_pass'].append(packet)
        veh_table.values(next_node)['packet_to_pass'].remove(packet)
        nodes_with_packet.add(next_node)
        node_with_packet.remove(current_node) if len(veh_table.values(current_node)['packet_to_pass'])==0

    if ('veh' in current_node) and ('bus' in next_node):

    if ('bus' in current_node) and ('veh' in next_node):

    if ('bus' in current_node) and ('bus' in next_node):

    return veh_table, bus_table

def intra_q_link(current_node, ch_id, veh_table, table, configs):

    dist = util.det_dist(current_node, veh_table, ch_id, table)
    q_link = (1 - dist / configs.veh_trans_range) * (1 - abs(
        (veh_table.values(current_node)['speed'] - veh_table.values(ch_id)['speed']) / 80
    )
                                                     ) * (1 - (abs(veh_table.values(current_node)['angle'] -
                                                                   table.values(ch_id)['angle']) / 180))
    return q_link


def extra_ch_evaluation(current_node, veh_table, bus_table, configs):

    return True

