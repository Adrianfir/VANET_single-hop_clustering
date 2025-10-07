"""
This is the utils file including the small functions for basic routing implementation
using https://ieeexplore.ieee.org/abstract/document/8588189
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['gen_message', 'intra_pass_packet', 'extra_pass_packet']

from distutils.command.config import config

import numpy as np
import random
import haversine as hs
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

def intra_pass_packet(current_node, veh_table, bus_table, configs):
    """
    The important thing is that the maximum speed is considered as 80 here
    :param current_node:
    :param veh_table:
    :param bus_table:
    :param configs:
    :return:
    """
    ch_id = veh_table.values(current_node)['primary_ch']
    table = bus_table if 'bus' in ch_id else veh_table

    q_link = intra_q_link(current_node, ch_id, veh_table, table, configs)

    if q_link >= configs.qol_thresh:




def extra_pass_packet(current_node, veh_table, bus_table, configs):

    return True

def intra_q_link(current_node, ch_id, veh_table, table, configs):

    dist = util.det_dist(current_node, veh_table, ch_id, table)
    q_link = (1 - dist / configs.veh_trans_range) * (1 - abs(
        (veh_table.values(current_node)['speed'] - veh_table.values(ch_id)['speed']) / 80
    )
                                                     ) * (1 - (abs(veh_table.values(current_node)['angle'] -
                                                                   table.values(ch_id)['angle']) / 180))
    return q_link