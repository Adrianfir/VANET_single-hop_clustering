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

# def gen_message(veh_table, s_id, d_id, send_time):
#     """
#     This function defines the message generation and encoding to be transmitted. Also the whole message considered in
#     this message generator can be considered as one packet, still in the paper we are going to say each word is
#     considered as one packet just for evaluation purposes. In general, to have more than one packet,
#     the message must exceed  Maximum Transmission Unit (MTU), e.g., 512B or even 1500B depending on the network
#     raw_message = dict(text= "Hey!!" + "This is" str(s_id) + "!! still on the road! I’ll be there soon!",
#                    source=s_id,
#                    dest=d_id,
#                    )
#     :param veh_table: vehicle's hash table
#     :param s_id: source id
#     :param d_id: destination id
#     :param send_time: time that the message is about to be sent
#     :return: the updated vehicle's hash table
#     """
#     message = ("Hey!" + "I" + " am" + " at " + str(veh_table.values(s_id)['lat'], veh_table.values(s_id)['long']) +
#                "! I" +  "'ll" + " be" + " there" + " soon!!")
#
#     pck_dict = dict()
#     for i in range(len(message)):
#         pck_dict[i] = dict(pck=message[i], s_time=send_time, d_time=None, hops=0)
#     return message, pck_dict

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


def pass_packet(current_node, veh_table, bus_table, packet, configs):
    """
    The important thing is that the maximum speed is considered as 80 here
    :param current_node:
    :param veh_table:
    :param bus_table:
    :param configs
    :return:
    """
    ch_id = veh_table.values(current_node)['primary_ch']
    if 'bus' in ch_id:

        q_link = intra_q_link(current_node, ch_id, veh_table, bus_table, configs)
    else:
        q_link = intra_q_link(current_node, ch_id, veh_table, veh_table, configs)

    return True


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

