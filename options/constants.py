"""
This .py file is for adding arguments to argparse
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import numpy
import numpy as np
import argparse
import pathlib
import xml.dom.minidom


class Inputs:
    def __init__(self):
        ####### Clustering Constants that we need to pass as arguments
        trace_path = str(pathlib.Path(__file__).parent.parent.parent.absolute().
                         joinpath('traffic_data', 'final_data_Richmondhill_smallsize', 'sumoTrace.xml'))
        sumo_edge_path = str(pathlib.Path(__file__).parent.parent.parent.absolute().
                         joinpath('traffic_data', 'final_data_Richmondhill_smallsize', 'osm.net.xml'))
        sumo_node_path = str(pathlib.Path(__file__).parent.parent.parent.absolute().
                         joinpath('traffic_data', 'final_data_Richmondhill_smallsize', 'osm_bbox.osm.xml'))
        sumo_trace = xml.dom.minidom.parse(trace_path)
        sumo_edge = xml.dom.minidom.parse(sumo_edge_path)
        sumo_node = xml.dom.minidom.parse(sumo_node_path)
        fcd = sumo_trace.documentElement
        times = fcd.getElementsByTagName('timestep')
        area = dict(min_lat=43.586568,
                    min_long=-79.540771,
                    max_lat=44.012923,
                    max_long=-79.238069)
        alpha = 1
        veh_trans_range = 300
        bus_trans_range = 800
        start_time = 1600
        iter = 60
        counter = 4
        priority_counter = 100   # this is not used for decision-making to join a cluster in single-hop algorithm
        map_zoom = 15.3
        center_loc = [43.869846, -79.443523]
        fps = 5
        weights = np.array([0.5, 0.5, 0.0])      # direction's angle, speed, distance



        ####### Routing Constants that we need to pass as arguments
        link_limit = 500000      # the link capacity based on bps
        drop_count = 15     # after this amount of iteration, the packet would be dropped
        qol_thresh = 0.7    # threshold for quality of link
        mtu = 1500          # Maximum Transmission Unit which is the maximum size of each packet based on byte
        header_size = 70    # the header_size of each packet can be around 58-70 bytes
        beacon_size = 160   # it should be considered for the beacons related to the clustering
        # for each interval. (10 beacons/sec * 200 bytes each = 20000 bytes/sec (~160kbps))




        parser = argparse.ArgumentParser()
        parser.add_argument('--area', type=dict, default=area,
                            help='this argument is the latitudes and longitudes of the understudied area')
        parser.add_argument('--n_cars', type=int, default=8000,
                            help='this is an assumption regarding the number of cars in order to create a HashTabel')
        parser.add_argument('--sumo_trace', type=xml.dom.minidom.Document, default=sumo_trace,
                            help='This is the sumo_trace file that includes all the data we need from the traffic')
        parser.add_argument('--sumo_edge', type=xml.dom.minidom.Document, default=sumo_edge,
                            help='This is the sumo_trace file that includes the edges (lanes) information')
        parser.add_argument('--sumo_node', type=xml.dom.minidom.Document, default=sumo_node,
                            help='This is the sumo_trace file that includes the nodes information of sumo net')
        parser.add_argument('--fcd', type=xml.dom.minidom.Element, default=fcd,
                            help='Floating Car Data (FCD) from sumoTrace.xml file')
        parser.add_argument('--times', type=xml.dom.minidom.NodeList, default=times,
                            help='includes data for all seconds')
        parser.add_argument('--alpha', type=float, default=alpha,
                            help='this is the regularization coefficient to change the sie of the zones based on TR')
        parser.add_argument('--veh_trans_range', type=int, default=veh_trans_range,
                            help='this is the transmission range of vehicles considered in this project and it can '
                                 'be up to 2000')
        parser.add_argument('--bus_trans_range', type=int, default=bus_trans_range,
                            help='this is the transmission range of buses considered in this project and it can '
                                 'be up to 2000')
        parser.add_argument('--start_time', type=int, default=start_time,
                            help='This is the time that the initial values would be extract from sumo_trace.xml file')
        parser.add_argument('--counter', type=int, default=counter,
                            help='This is the a counter for vehicle to make themselves as CH if they can not'
                                 ' find any Ch or nearby stand-alone vehicles to create a cluster')
        parser.add_argument('--priority_counter', type=int, default=priority_counter,
                            help='This is the a counter for vehicle to join same cluster through sub_chs after leaving '
                                 'that cluster')
        parser.add_argument('--map_zoom', type=float, default=map_zoom,
                            help='This is the amount to have a specific zoom on the map')
        parser.add_argument('--center_loc', type=float, default=center_loc,
                            help='The specific center location of the map for saving images and make slide-show')
        parser.add_argument('--fps', type=float, default=fps, help='frame per second')
        parser.add_argument('--iter', type=int, default=iter, help='number of intervals to run')
        parser.add_argument('--weights', type=numpy.ndarray, default=weights,
                            help='weights used for clustering')
        parser.add_argument('--link_limit', type=int, default=link_limit,
                            help='link capacity based on Mbps')
        parser.add_argument('--drop_count', type=int, default=drop_count,
                            help='this is a counter. The packet would be dropped after this counter ends in case it '
                                 'is not transmitted to the destination node')
        parser.add_argument('--qol_thresh', type=float, default=qol_thresh,
                            help='Threshold for quality of the link')
        parser.add_argument('--mtu', type=float, default=mtu,
                            help='Maximum Transmission Unit which is the maximum size of each packet based on byte')
        parser.add_argument('--header_size', type=float, default=header_size,
                            help='header size of each packet. it can be between 58 to 70 bytes.')
        parser.add_argument('--beacon_size', type=float, default=beacon_size,
                            help='size of beacons related to clustering per second (kbps)')
        self.parser = parser

    def get_parser(self):
        """
        this methods can be used on order to return the parser and be used in config file
        :return: it returns the parser
        """
        return self.parser.parse_args()