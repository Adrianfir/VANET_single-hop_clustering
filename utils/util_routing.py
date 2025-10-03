"""
This is the utils file including the small functions for basic routing implementation
using https://ieeexplore.ieee.org/abstract/document/8588189
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = [

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
from selenium.webdriver.firefox.service import Service
import os
import cv2
import re

def gen_message(veh_table, s_id, d_id, send_time):
    """
    This function defines the message generation and encoding to be transmitted. Also the whole message considered in
    this message generator can be considered as one packet, still in the paper we are going to say each word is
    considered as one packet just for evaluation purposes. In general, to have more than one packet,
    the message must exceed  Maximum Transmission Unit (MTU), e.g., 512B or even 1500B depending on the network
    raw_message = dict(text="This" + "is" + str(s_id),
                   source=s_id,
                   dest=d_id,
                   )
    :param veh_table: vehicle's hash table
    :param s_id: source id
    :param d_id: destination id
    :param send_time: time that the message is about to be sent
    :return: the updated vehicle's hash table
    """

    message = dict(one=["This", s_id, d_id],
                   two=["is", s_id, d_id],
                   three=[str(s_id), s_id, d_id],
                   s_time=send_time,
                   deliver_time=None,
                   hops=0)
    veh_table.message_to_send.add(message)
    return veh_table