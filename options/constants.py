"""
This .py file is for adding arguments to argparse
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import numpy
import numpy as np
import argparse
import pathlib
import xml.dom.minidom
import yaml
import math

class Inputs:
    def __init__(self):
        ####### Clustering Constants that we need to pass as arguments
        trace_path = str(pathlib.Path(__file__).parent.parent.parent.absolute().
                         joinpath('traffic_data', 'final_data_Richmondhill_largesize', 'sumoTrace_no_bus_and_rsu.xml'))
        sumo_edge_path = str(pathlib.Path(__file__).parent.parent.parent.absolute().
                         joinpath('traffic_data', 'final_data_Richmondhill_largesize', 'osm.net.xml'))
        sumo_node_path = str(pathlib.Path(__file__).parent.parent.parent.absolute().
                         joinpath('traffic_data', 'final_data_Richmondhill_largesize', 'osm_bbox.osm.xml'))

        messages_path = "/Users/pouyafirouzmakan/Desktop/traffic_data/Generated_messages/testing_RL/messages_largesize.yaml"
        sumo_trace = xml.dom.minidom.parse(trace_path)
        sumo_edge = xml.dom.minidom.parse(sumo_edge_path)
        sumo_node = xml.dom.minidom.parse(sumo_node_path)
        fcd = sumo_trace.documentElement
        times = fcd.getElementsByTagName('timestep')
        area = dict(min_lat=43.850130,
                    min_long=-79.472871,
                    max_lat=43.8895,
                    max_long=-79.422551)
        alpha = 1
        veh_trans_range = 300
        bus_trans_range = 800
        start_time = 1700
        iter = 200
        counter = 4
        priority_counter = 100   # this is not used for decision-making to join a cluster in single-hop algorithm
        map_zoom = 15.3
        center_loc = [43.869846, -79.443523]
        fps = 5
        weights = np.array([0.9, 0.0, 0.1])      # direction's angle, speed, distance



        ####### Routing Constants that we need to pass as arguments
        mess_gen_repeat = 5    # number of times at each interval that we do the message generation
        link_limit_bit = 500000      # the link capacity based on bps
        drop_count = 15     # after this amount of iteration, the packet would be dropped
        qol_thresh = 0.7    # threshold for quality of link
        mtu = 1500          # Maximum Transmission Unit which is the maximum size of each packet based on byte
        header_size = 70    # the header_size of each packet can be around 58-70 bytes
        beacon_size = 160   # it should be considered for the beacons related to the clustering
        # for each interval. (10 beacons/sec * 200 bytes each = 20000 bytes/sec (~160kbps))
        max_hop = 5         # maximum number of hops that a packet can travel per tick. this number is because if there
        link_limit = link_limit_bit / 8
        # is a path through gates between CHs, this path is maximum 4 hops in single-hop clustering
        with open(messages_path, 'r') as f:
            messages = yaml.safe_load(f)

        ######## Q-Learning Routing Constants that we need to pass as arguments

        zone_order = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        zone_to_idx = {z: i for i, z in enumerate(zone_order)}
        idx_to_zone = {i: z for i, z in enumerate(zone_order)}
        state_dim = 13
        action_dim = 8
        gamma = 0.99
        lr = 0.001
        buffer_capacity = 100000
        batch_size = 128
        epsilon_start = 1.0
        epsilon_end = 0.05
        epsilon_decay_steps = 50000
        target_update_freq = 1000

        # reward parameters – tweak these
        # ----- REWARD PARAMETERS (TUNABLE) -----

        # Base cost per perimeter hop
        hop_penalty = -0.5
        # Reward for getting closer to dest (per hop)
        # r_dist = distance_weight * (prev_dist_norm - new_dist_norm)
        distance_weight = 3.0
        # Extra penalty when packet returns to a previously visited zone
        loop_penalty = -8.0  # in zone-space, not node-space
        # Delay shaping: after this many ticks, undelivered packets are "too slow"
        delay_threshold_ticks = 6
        # Per-perimeter-decision penalty once age > delay_threshold_ticks
        delay_penalty_per_tick = -1.0
        # Big success bonus when packet eventually gets delivered (via greedy)
        success_bonus = 80.0
        # No big drop penalty, since drops are random car exits unrelated to perimeter choices
        drop_penalty = 0.0  # or at most -1.0 if you want a tiny push
        trained_agent_path = 'checkpoints/dqn_vanet_tr300_alpha0.5_tick1400_to_tick1600'





        parser = argparse.ArgumentParser()
        parser.add_argument('--area', type=dict, default=area,
                            help='this argument is the latitudes and longitudes of the understudied area')
        parser.add_argument('--n_cars', type=int, default=8000,
                            help='this is an assumption regarding the number of cars in order to create a HashTabel')
        parser.add_argument('--messages', type=str, default=messages,
                            help='generated messages')
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
        parser.add_argument('--mess_gen_repeat', type=int, default=mess_gen_repeat,
                            help='number of times at each interval that we do the message generation')
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
        parser.add_argument('--max_hop', type=float, default=max_hop,
                            help='maximum number of hops that a packet can travel per tick')

        ###### RL

        parser.add_argument('--zone_order', type=float, default=zone_order,
                            help='ordering neighbor zones for RL to take action')
        parser.add_argument('--zone_to_idx', type=float, default=zone_to_idx,
                            help='giving id to neighbor zones based on zone_order')
        parser.add_argument('--idx_to_zone', type=float, default=idx_to_zone,
                            help='retrieving the neighbor zone from its idx')

        parser.add_argument('--state_dim', type=float, default=state_dim,
                            help='number of states which can be calculated in the qlearning_state.pyReturn the '
                                 'dimensionality of the state vector produced by build_state.')
        parser.add_argument('--action_dim', type=float, default=action_dim,
                            help='number of actions that the agent can select.')
        parser.add_argument('--gamma', type=float, default=gamma,
                            help='discount factor.')
        parser.add_argument('--lr', type=float, default=lr,
                            help='learning rate.')
        parser.add_argument('--buffer_capacity', type=float, default=buffer_capacity,
                            help='length of buffer')
        parser.add_argument('--batch_size', type=float, default=batch_size,
                            help='batch_size for neural network')
        parser.add_argument('--epsilon_start', type=float, default=epsilon_start,
                            help='')
        parser.add_argument('--epsilon_end', type=float, default=epsilon_end,
                            help='')
        parser.add_argument('--epsilon_decay_steps', type=float, default=epsilon_decay_steps,
                            help='')
        parser.add_argument('--target_update_freq', type=float, default=target_update_freq,
                            help='')




        parser.add_argument('--hop_penalty', type=float, default=hop_penalty,
                            help='penalty for each hop')
        parser.add_argument('--success_bonus', type=float, default=success_bonus,
                            help='reward for if packets gets delivered')
        parser.add_argument('--fail_penalty', type=float, default=drop_penalty,
                            help='in case the packet gets dropped')
        parser.add_argument('--loop_penalty', type=float, default=loop_penalty,
                            help='in case the packet gets dropped')
        parser.add_argument('--delay_threshold_ticks', type=float, default=delay_threshold_ticks,
                            help='We have an estimate of the average delay of GPSR in our data. So we can say if the '
                                 'packet does not gets delivered after a little highr than that, consider a penalty '
                                 'for it')
        parser.add_argument('--delay_penalty_per_tick', type=float, default=delay_penalty_per_tick,
                            help='The penalty if the packet doeas not get delivered after delay_threshold_ticks')
        parser.add_argument('--distance_weight', type=float, default=distance_weight,
                            help='Reward for getting closer to dest (per hop) '
                                 'r_dist = distance_weight * (prev_dist_norm - new_dist_norm)')
        parser.add_argument('--trained_agent_path', type=str, default=trained_agent_path,
                            help='trained model directory')


        self.parser = parser

    def get_parser(self):
        """
        this methods can be used on order to return the parser and be used in config file
        :return: it returns the parser
        """
        return self.parser.parse_args()