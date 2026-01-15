"""

This Module is coded for extracting data from XML file related to SUMO and putting them to a Hash table.
There are methods in the main DataTable class to initiate and update the vehicles and buses coming to the
understudied area and creating and updating the clusters using recursion.

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import random

import numpy as np
import networkx as nx
import folium
from folium.plugins import MarkerCluster
import webbrowser
import sys

from matplotlib.table import table

# from graph import Graph
import utils.util as util
import utils.util_graph as util_graph
import utils.util_routing as util_routing
import hash
from qlearning_state import QRoutingHelper
from dqn_agent import DQNAgentTF



class DataTable:
    # This class is determined for defining the hash_table, updating data, routing messages,
    # and defining ip addresses by using trace (which is sumo_trace)

    def __init__(self, config, zones, train_mode):
        """

        :param config: look at options.py and config.py
        :param zones: all the zones of the area
        """

        self.map = None
        self.bus_table = hash.HashTable(config.n_cars * 100)
        self.veh_table = hash.HashTable(config.n_cars * 100)

        self.zone_vehicles = dict(zip(zones.zone_hash.ids(),
                                      [set() for j in range(len(zones.zone_hash.ids()))]
                                      )
                                  )
        self.zone_buses = dict(zip(zones.zone_hash.ids(),
                                   [set() for j in range(len(zones.zone_hash.ids()))]
                                   )
                               )
        self.zone_ch = dict(zip(zones.zone_hash.ids(),
                                [set() for j in range(len(zones.zone_hash.ids()))]
                                )
                            )
        self.zone_stand_alone = dict(zip(zones.zone_hash.ids(),
                                         [set() for j in range(len(zones.zone_hash.ids()))]
                                         )
                                     )
        self.n_zone_cols = zones.n_cols
        self.n_zone_rows = zones.n_rows
        self.stand_alone = set()
        self.all_chs = set()
        self.left_veh = dict()
        self.left_bus = dict()
        self.time = config.start_time
        self.understudied_area = zones.understudied_area()
        self.init_count = 0  # this counter is just for defining the self.net_graph for the very first time
        self.edge_color = ''
        self.sumo_edges, self.sumo_nodes = util.sumo_net_info(config.sumo_edge, config.sumo_node)
        self.ch_net = None
        self.actions_review = dict()
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            self.init_count += 1
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            # the bus_table will be initiated here for the very first time
            if 'bus' in veh.getAttribute('id'):
                self.bus_table.set_item(veh.getAttribute('id'), util.initiate_new_bus(veh, zones, zone_id, config,
                                                                                      self.understudied_area))
                self.bus_table.values(veh.getAttribute('id'))['arrive_time'] = self.time
                # Here the buses will be added to zone_buses
                self.zone_buses[zone_id].add(veh.getAttribute('id'))
                self.zone_ch[zone_id].add(veh.getAttribute('id'))
                self.all_chs.add(veh.getAttribute('id'))

                # the veh_table will be initiated here for the very first time self.understudied_area
            else:
                self.veh_table.set_item(veh.getAttribute('id'), util.initiate_new_veh(veh, zones, zone_id, config,
                                                                                      self.understudied_area))
                self.veh_table.values(veh.getAttribute('id'))['arrive_time'] = self.time
                # Here the vehicles will be added to zone_vehicles
                self.zone_vehicles[zone_id].add(veh.getAttribute('id'))
                self.stand_alone.add(veh.getAttribute('id'))
                self.zone_stand_alone[self.veh_table.values(veh.getAttribute('id'))['zone']].add(veh.getAttribute('id'))

            # create the self.net_graph or add the new vertex
            if self.init_count == 1:
                self.net_graph = nx.Graph()
                self.net_graph.add_node(veh.getAttribute('id'), pos=(float(veh.getAttribute('y')),
                                                                     float(veh.getAttribute('x'))
                                                                     )
                                        )
            else:
                self.net_graph.add_node(veh.getAttribute('id'), pos=(float(veh.getAttribute('y')),
                                                                     float(veh.getAttribute('x'))
                                                                     )
                                        )
        # initiation for routing part
        self.drops = list()
        self.sent_messages = dict()
        self.message_count = 0
        self.pck_queue = 0
        self.delivered_packets = list()
        # self.delivered_messages = list()
        self.link_cap = dict()
        self.nodes_with_pack = set()
        self.left_dest_pack = list()
        self.n_perimeter = 0


        # RL part
        self.train_mode = train_mode
        self.helper = QRoutingHelper(
            veh_table=self.veh_table,
            bus_table=self.bus_table,
            zones_dict={key: self.zone_vehicles[key] | self.zone_buses[key] for key in self.zone_vehicles},
            configs=config,
            n_cols=zones.n_cols,
            max_dist=3000.0,
            max_zone_count_cap=50,
            loop_window_zones=4,
            delay_threshold_ticks=6,
            )

        self.agent = DQNAgentTF(config)
        if self.train_mode is False:
            self.agent.load(config.trained_agent_path)
        self.train_reward_log = list()

    def update(self, config, zones):
        """
        this method updates the bus_table and veh_table values for the current interval.
        Attention: The properties related to clusters and ip addresses are going to be updated here
        :return:
        """
        self.time += 1
        bus_ids = set()
        veh_ids = set()
        self.net_graph.remove_edges_from(self.net_graph.edges())
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )

            # update the bus_table for the time step
            if 'bus' in veh.getAttribute('id'):
                bus_ids.add(veh.getAttribute('id'))
                self.bus_table, self.zone_buses, self.zone_ch = util.update_bus_table(veh, self.bus_table, zone_id,
                                                                                      self.understudied_area, zones,
                                                                                      config, self.zone_buses,
                                                                                      self.zone_ch, self.time)
                self.all_chs.add(veh.getAttribute('id'))

            else:
                veh_ids.add(veh.getAttribute('id'))
                self.veh_table, self.zone_vehicles, self.zone_ch, self.stand_alone, \
                self.zone_stand_alone = util.update_veh_table(veh, self.veh_table, zone_id, self.understudied_area,
                                                              zones, config, self.zone_vehicles, self.zone_ch,
                                                              self.stand_alone, self.zone_stand_alone, self.time)
                if self.veh_table.values(veh.getAttribute('id'))['cluster_head'] is True:
                    self.all_chs.add(veh.getAttribute('id'))
            # add the vertex to the graph
            try:
                self.net_graph.nodes[veh.getAttribute('id')]['pos'] = (float(veh.getAttribute('y')),
                                                                       float(veh.getAttribute('x'))
                                                                       )

            except KeyError:

                self.net_graph.add_node(veh.getAttribute('id'), pos=(float(veh.getAttribute('y')),
                                                                     float(veh.getAttribute('x'))
                                                                     )
                                        )
        # removing the buses, that have left the understudied area, from self.bus_table and self.zone_buses
        temp_left_buses = self.bus_table.ids() - bus_ids
        temp_left_vehs = self.veh_table.ids() - veh_ids
        for k in temp_left_buses:
            k_values = self.bus_table.values(k)
            ##pass packets:
            (self.veh_table, self.bus_table, k_values,
             self.nodes_with_pack, self.delivered_packets,
             self.link_cap) = util_routing.removed_nodes_packets(k, k_values, self.veh_table, self.bus_table,
                                                                 temp_left_vehs, temp_left_buses,
                                                                 self.drops, self.nodes_with_pack, self.delivered_packets,
                                                                 config, self.link_cap, self.time, node_is_veh=False)
            cm_temp = k_values(k)['cluster_members'].copy()
            for m in cm_temp:
                if m not in temp_left_vehs:  # this must be veh_ids not self.veh_table.ids()
                    mem_stays = True
                else:
                    mem_stays = False
                (self.veh_table, self.bus_table,
                 self.stand_alone, self.zone_stand_alone) = util.remove_member(m, k, self.veh_table,
                                                                               self.bus_table, config,
                                                                               self.stand_alone,
                                                                               self.zone_stand_alone,
                                                                               ch_stays=False,
                                                                              mem_stays=mem_stays)
                    # since k is not inside the area anymore, the priority_ch must be None
                    # self.veh_table.values(m)['priority_ch'] = None
                    # self.veh_table.values(m)['priority_counter'] = config.priority_counter

            self.zone_buses[k_values['zone']].remove(k)
            self.zone_ch[self.bus_table.values(k)['zone']].remove(k)
            self.all_chs.remove(k)
            self.bus_table.values(k)['depart_time'] = self.time - 1
            self.left_bus[k] = self.bus_table.values(k)

            # for drop in self.bus_table.values(k)['packets_to_pass']:
            #     self.drops.append(drop)
            self.bus_table.remove(k)
            self.net_graph.remove_node(k)

        # removing the vehicles, that have left the understudied area, from self.veh_table and self.zone_vehicles
        for k in temp_left_vehs:
            k_values = self.veh_table.values(k)
            #### pass the packets
            (self.veh_table, self.bus_table, k_values,
             self.nodes_with_pack, self.delivered_packets,
             self.link_cap) = util_routing.removed_nodes_packets(k, k_values, self.veh_table, self.bus_table,
                                                                 temp_left_vehs, temp_left_buses,
                                                                 self.drops, self.nodes_with_pack, self.delivered_packets,
                                                                 config, self.link_cap, self.time)
            if k_values['cluster_head'] is True:
                temp_cluster_members = k_values['cluster_members'].copy()
                for m in temp_cluster_members:
                    if m in veh_ids:  # this must be veh_ids not self.veh_table.ids()
                        mem_stays = True
                    else:
                        mem_stays = False
                    (self.veh_table, self.bus_table,
                     self.stand_alone, self.zone_stand_alone) = util.remove_member(m, k, self.veh_table,
                                                                                   self.bus_table, config,
                                                                                   self.stand_alone,
                                                                                   self.zone_stand_alone,
                                                                                   ch_stays=False,
                                                                                   mem_stays=mem_stays)

                self.zone_ch[k_values['zone']].remove(k)
                self.all_chs.remove(k)

            elif k_values['primary_ch'] is not None:
                k_ch = k_values['primary_ch']
                (self.veh_table, self.bus_table,
                 self.stand_alone, self.zone_stand_alone) = util.remove_member(k, k_ch, self.veh_table,
                                                                               self.bus_table, config,
                                                                               self.stand_alone,
                                                                               self.zone_stand_alone,
                                                                               mem_stays=False)

            elif k in self.stand_alone:
                self.stand_alone.remove(k)
                self.zone_stand_alone[k_values['zone']].remove(k)

            self.zone_vehicles[self.veh_table.values(k)['zone']].remove(k)
            self.veh_table.values(k)['depart_time'] = self.time - 1
            self.left_veh[k] = self.veh_table.values(k)

            self.veh_table.remove(k)
            self.net_graph.remove_node(k)

    def update_cluster(self, veh_ids, config, zones):

        """
        This method is designed for finding a cluster for veh_id
        :return: cluster heads and connection between them including through the gate_chs
        """
        for veh_id in veh_ids:
            self.veh_table.values(veh_id)['other_chs'] = set()
            self.veh_table.values(veh_id)['gates'] = dict()
            self.veh_table.values(veh_id)['gate_chs'] = set()
            self.veh_table.values(veh_id)['other_vehs'] = set()

            # determining the buses and cluster_head in neighbor zones
            bus_candidates, ch_candidates, other_vehs = util.det_near_ch(veh_id, self.veh_table, self.bus_table,
                                                                         self.zone_buses, self.zone_vehicles)
            if (len(bus_candidates) == 0) and (len(ch_candidates) == 0) and \
                    (self.veh_table.values(veh_id)['in_area'] is True) and \
                    (self.veh_table.values(veh_id)['primary_ch'] is None) and \
                    (self.veh_table.values(veh_id)['cluster_head'] is False):
                if self.veh_table.values(veh_id)['counter'] >= 1:
                    self.veh_table.values(veh_id)['counter'] -= 1
                    self.stand_alone.add(veh_id)
                    self.veh_table.values(veh_id)['other_vehs'] = other_vehs
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].add(veh_id)
                    continue
                else:
                    (self.veh_table, self.all_chs, self.stand_alone,
                     self.zone_stand_alone, self.zone_ch) = util.set_ch(veh_id, self.veh_table, self.all_chs,
                                                                        self.stand_alone, self.zone_stand_alone,
                                                                        self.zone_ch, config)
                    continue

            elif (self.veh_table.values(veh_id)['in_area'] is True) and \
                    (self.veh_table.values(veh_id)['primary_ch'] is None) and \
                    (self.veh_table.values(veh_id)['cluster_head'] is True):

                temp_mem = self.veh_table.values(veh_id)['cluster_members'].copy()
                for m in temp_mem:
                    dist = util.det_dist(veh_id, self.veh_table, m, self.veh_table)

                    if dist > min(self.veh_table.values(veh_id)['trans_range'],
                                  self.veh_table.values(m)['trans_range']):
                        (self.veh_table, self.bus_table,
                         self.stand_alone, self.zone_stand_alone) = (
                            util.remove_member(m, veh_id, self.veh_table, self.bus_table, config,
                                               self.stand_alone, self.zone_stand_alone))

                # if the veh_id is a ch and does not have any member, after changing its zone, it won't remain as a ch
                # unless get selected by another vehicles or can't find a cluster head after the counter
                if (len(self.veh_table.values(veh_id)['cluster_members']) == 0) and \
                        ((self.veh_table.values(veh_id)['start_ch_zone'] != self.veh_table.values(veh_id)['zone']) and
                         (self.veh_table.values(veh_id)['prev_zone'] != self.veh_table.values(veh_id)['zone'])):
                    (self.veh_table, self.zone_ch, self.all_chs,
                     self.stand_alone, self.zone_stand_alone) = util.set_ch_to_veh(veh_id, self.veh_table, self.zone_ch,
                                                                                   self.all_chs, self.stand_alone,
                                                                                   self.zone_stand_alone)
                    self.update_cluster([veh_id, ], config, zones)
                else:
                    self.zone_ch[self.veh_table.values(veh_id)['zone']].add(veh_id)
                    self.all_chs.add(veh_id)
                continue
            # checking if the vehicle is understudied-area and still in transmission range of its current primary_ch
            # or is not in its transmission_range anymore
            elif (self.veh_table.values(veh_id)['in_area'] is True) and \
                    (self.veh_table.values(veh_id)['cluster_head'] is False) and \
                    (self.veh_table.values(veh_id)['primary_ch'] is not None):
                ch_id = self.veh_table.values(veh_id)['primary_ch']
                dist_to_primarych = float()
                if 'bus' in self.veh_table.values(veh_id)['primary_ch']:
                    temp_table = self.bus_table
                else:
                    temp_table = self.veh_table
                dist_to_primarych = util.det_dist(veh_id, self.veh_table,
                                                  self.veh_table.values(veh_id)['primary_ch'], temp_table)

                if dist_to_primarych <= min(self.veh_table.values(veh_id)['trans_range'],
                                            temp_table.values(self.veh_table.values(veh_id)['primary_ch'])
                                            ['trans_range']):

                    if self.veh_table.values(veh_id)['cluster_record'].tail.value['start_time'] + \
                            self.veh_table.values(veh_id)['cluster_record'].tail.value['timer'] - 1 != self.time:
                        self.veh_table.values(veh_id)['cluster_record'].tail.value['timer'] += 1

                    continue
                # here the 'primary_ch' will be changed to None and recursion is applied
                else:
                    ch_id = self.veh_table.values(veh_id)['primary_ch']
                    (self.veh_table, self.bus_table,
                     self.stand_alone, self.zone_stand_alone) = (util.remove_member(veh_id, ch_id,
                                                                                    self.veh_table, self.bus_table,
                                                                                    config, self.stand_alone,
                                                                                    self.zone_stand_alone))
                    self.update_cluster([veh_id, ], config, zones)

            temp_stand_alone = self.stand_alone.copy()
            for veh_id in temp_stand_alone:
                self.veh_table.values(veh_id)['other_chs'] = set()
                self.veh_table.values(veh_id)['gates'] = dict()
                self.veh_table.values(veh_id)['gate_chs'] = set()
                self.veh_table.values(veh_id)['other_vehs'] = set()

                # determining the buses and cluster_head in neighbor zones
                (bus_candidates, ch_candidates, other_vehs) = util.det_near_ch(veh_id, self.veh_table, self.bus_table,
                                                                   self.zone_buses, self.zone_vehicles)

                self.single_hop(veh_id, config, zones,
                                bus_candidates, ch_candidates, other_vehs)

    def single_hop(self, veh_id, config, zones,
                   bus_candidates, ch_candidates, other_vehs):

                if len(bus_candidates) > 0:
                    bus_ch, ef = util.choose_ch(self.bus_table, self.veh_table.values(veh_id), zones,
                                                bus_candidates, config)  # determine the best from bus_candidates

                    (self.bus_table, self.veh_table,
                     self.stand_alone,
                     self.zone_stand_alone) = util.add_member(bus_ch, self.bus_table, veh_id, self.veh_table,
                                                              config, ef, self.time, bus_candidates,
                                                              ch_candidates, self.stand_alone,
                                                              self.zone_stand_alone, other_vehs)


                elif (len(bus_candidates) == 0) and (len(ch_candidates) > 0):

                    veh_ch, ef = util.choose_ch(self.veh_table, self.veh_table.values(veh_id),
                                                zones, ch_candidates, config)  # determine the best from vehicles

                    (self.bus_table, self.veh_table,
                     self.stand_alone,
                     self.zone_stand_alone) = util.add_member(veh_ch, self.bus_table, veh_id, self.veh_table,
                                                              config, ef, self.time, bus_candidates,
                                                              ch_candidates, self.stand_alone,
                                                              self.zone_stand_alone, other_vehs)

    def stand_alones_cluster(self, configs, zones):
        near_sa = dict()
        n_near_sa = dict()
        pot_ch = dict()
        for veh_id in self.stand_alone:
            # self.stand_alone_test(veh_id)
            near_sa[veh_id] = util.det_near_sa(veh_id, self.veh_table,
                                               self.stand_alone, self.zone_stand_alone
                                               )
            n_near_sa[veh_id] = len(near_sa[veh_id])

        for veh_id in near_sa.keys():
            if n_near_sa[veh_id] > 0:
                pot_ch[veh_id] = util.det_pot_ch(veh_id, near_sa, n_near_sa)
            else:
                continue

        unique_pot_ch = set(pot_ch.values())
        selected_chs = set()
        mem_control = set()  # after a vehicle become a member, add it to this and at the beginning of the
        # for-loop, check if veh_id is in it to not do anything new and ruin it
        temp = self.stand_alone.copy()
        temp = list(temp)
        temp.sort()
        temp.reverse()
        for veh_id in temp:
            if (self.veh_table.values(veh_id)['cluster_head'] is True) or \
                    (self.veh_table.values(veh_id)['primary_ch'] is not None) or \
                    (veh_id in mem_control) or (veh_id in selected_chs):
                continue
            if (n_near_sa[veh_id] == 1) and (list(near_sa[veh_id])[0] in near_sa.keys()):
                if n_near_sa[list(near_sa[veh_id])[0]] == 1:
                    veh_id_2 = list(near_sa[veh_id])[0]

                    (self.veh_table, self.all_chs, self.stand_alone,
                     self.zone_stand_alone, self.zone_ch) = util.set_ch(veh_id, self.veh_table, self.all_chs,
                                                                        self.stand_alone, self.zone_stand_alone,
                                                                        self.zone_ch, configs, its_sa_clustering=True)

                    (self.veh_table, self.all_chs, self.stand_alone,
                     self.zone_stand_alone, self.zone_ch) = util.set_ch(veh_id_2, self.veh_table, self.all_chs,
                                                                        self.stand_alone, self.zone_stand_alone,
                                                                        self.zone_ch, configs, its_sa_clustering=True)

                    selected_chs.add(veh_id)
                    selected_chs.add(veh_id_2)
                    continue

            if len(unique_pot_ch.intersection(near_sa[veh_id]) - mem_control) > 0:
                ch, ef = util.choose_ch(self.veh_table, self.veh_table.values(veh_id), zones,
                                        unique_pot_ch.intersection(near_sa[veh_id]) - mem_control, configs)
                selected_chs.add(ch)
                (self.veh_table, self.all_chs, self.stand_alone,
                 self.zone_stand_alone, self.zone_ch) = util.set_ch(ch, self.veh_table, self.all_chs,
                                                                    self.stand_alone, self.zone_stand_alone,
                                                                    self.zone_ch, configs, its_sa_clustering=True)

                (self.bus_table, self.veh_table,
                 self.stand_alone,
                 self.zone_stand_alone) = util.add_member(ch, self.bus_table, veh_id, self.veh_table,
                                                          configs, ef, self.time, set(), set(), self.stand_alone,
                                                          self.zone_stand_alone, set())

                mem_control.add(veh_id)

        self.update_cluster(self.veh_table.ids(), configs, zones)

    def update_other_connections(self):
        # finding buses' other_chs
        # Here the other_vehs must be updated again. Otherwise, the graph would face with some conflicts
        self.veh_table, self.bus_table = util.other_connections_update(self.veh_table, self.bus_table,
                                                                       self.zone_ch, self.zone_buses,
                                                                       self.zone_vehicles)

    def form_net_graph(self):
        for veh_id in self.veh_table.ids():
            if self.veh_table.values(veh_id)['cluster_head'] is False:
                self.net_graph = util_graph.veh_add_edges(veh_id, self.veh_table, self.net_graph)
            else:
                self.net_graph = util_graph.ch_add_edges(veh_id, self.veh_table, self.net_graph)

        for bus_id in self.bus_table.ids():
            self.net_graph = util_graph.bus_add_edges(bus_id, self.bus_table, self.net_graph)

    def eval_cluster(self, configs):
        total_clusters = 0
        n_sav_ch = 0  # number of vehicles that are allways ch or stand-alone (never experiences being a cm)
        for i in self.veh_table.ids():
            if self.veh_table.values(i)['depart_time'] is None:
                self.veh_table.values(i)['depart_time'] = configs.start_time + configs.iter
            in_area_time = self.veh_table.values(i)["depart_time"] - self.veh_table.values(i)["arrive_time"]
            total_length = self.veh_table.values(i)['cluster_record'].length
            if (total_length == 1) and (self.veh_table.values(i)['cluster_record'].head.value['timer'] is None):
                n_sav_ch += 1
                continue
            if in_area_time == 0:
                in_area_time += 1

            one_veh = 0
            temp = self.veh_table.values(i)['cluster_record'].head
            summing = 0
            while temp:
                if temp.value['timer'] is not None:
                    summing += temp.value['timer']  # temp.length acs as penalty
                temp = temp.next
            one_veh += np.divide(summing, total_length * in_area_time)
            total_clusters += one_veh

        for i in self.left_veh.keys():
            total_length = self.left_veh[i]['cluster_record'].length
            if (total_length == 1) and (self.left_veh[i]['cluster_record'].head.key is None):
                n_sav_ch += 1
                continue
            one_veh = 0
            temp = self.left_veh[i]['cluster_record'].head
            summing = 0
            in_area_time = self.left_veh[i]['depart_time'] - self.left_veh[i]['arrive_time']
            while temp:
                if temp.value['timer'] is not None:
                    summing += np.divide(temp.value['timer'],
                                         (total_length * in_area_time))  # temp.length acs as penalty
                temp = temp.next
            one_veh += np.divide(summing, total_length * in_area_time)
            total_clusters += one_veh
        return np.divide(total_clusters, len(self.veh_table.ids()) + len(self.left_veh) - n_sav_ch)

    def connected_components(self):
        n = 0  # this would return the minimum number of path needed to connect all the clusters
        investigated = set()
        self.ch_net = nx.Graph()
        self.ch_net.add_nodes_from(list(self.all_chs))

        for i in self.all_chs:
            investigated.add(i)
            for j in (self.all_chs - investigated):
                try:
                    nx.shortest_path(self.net_graph, source=i, target=j)
                    self.ch_net.add_edge(i,j)
                except nx.exception.NetworkXNoPath:
                    n += 1

        conn_comp = list(nx.connected_components(self.ch_net))

        return len(conn_comp)

    def show_graph(self, configs):
        """
        this function will illustrate the self.net_graph
        :return: Graph
        """

        # Extract positions from node attributes
        pos = nx.get_node_attributes(self.net_graph, 'pos')

        # Create a folium map centered around the first node
        self.map = folium.Map(location=configs.center_loc, zoom_start=configs.map_zoom, tiles='cartodbpositron',
                              attr='Google', name='Google Maps', prefer_canvas=True)

        # Create a MarkerCluster group for the networkx graph nodes
        marker_cluster = MarkerCluster(name='VANET')

        # Add nodes to the MarkerCluster group
        for node, node_pos in pos.items():
            if 'bus' in node:
                if 'rsu' in node:
                    marker = folium.CircleMarker(location=node_pos, radius=10, color='darkpurple', fill=True,
                                                 fill_color='red')
                else:
                    marker = folium.CircleMarker(location=node_pos, radius=10, color='red', fill=True,
                                                 fill_color='red')
            else:
                if self.veh_table.values(node)['cluster_head'] is True:
                    marker = folium.CircleMarker(location=node_pos, radius=10, color='red', fill=True,
                                                 fill_color='red')
                else:
                    marker = folium.CircleMarker(location=node_pos, radius=5, color='lightblue', fill=True,
                                                 fill_color='lightblue')
            marker.add_to(marker_cluster)

        # Add the MarkerCluster group to the map
        marker_cluster.add_to(self.map)

        # Create a feature group for the networkx graph edges
        edge_group = folium.FeatureGroup(name='Graph Edges')

        # Add edges to the feature group
        for edge in self.net_graph.edges():
            start_pos = pos[edge[0]]
            end_pos = pos[edge[1]]
            locations = [start_pos, end_pos]
            # determine the edge colors
            if ('bus' in edge[0]) and ('bus' in edge[1]):
                self.edge_color = 'pink'
            elif ('veh' in edge[0]) and ('bus' in edge[1]):
                if self.veh_table.values(edge[0])['cluster_head'] is True:
                    self.edge_color = 'pink'
                else:
                    if self.veh_table.values(edge[0])['primary_ch'] == edge[1]:
                        self.edge_color = 'green'
                    else:
                        self.edge_color = 'gray'
            elif ('bus' in edge[0]) and ('veh' in edge[1]):
                if self.veh_table.values(edge[1])['cluster_head'] is True:
                    self.edge_color = 'pink'
                else:
                    if self.veh_table.values(edge[1])['primary_ch'] == edge[0]:
                        self.edge_color = 'green'
                    else:
                        self.edge_color = 'gray'
            elif ('veh' in edge[0]) and ('veh' in edge[1]):
                if self.veh_table.values(edge[0])['cluster_head'] is True:
                    if self.veh_table.values(edge[1])['cluster_head'] is True:
                        self.edge_color = 'pink'
                    elif (self.veh_table.values(edge[1])['cluster_head'] is False) and \
                            (self.veh_table.values(edge[1])['primary_ch'] == edge[0]):
                        self.edge_color = 'green'
                    else:
                        self.edge_color = 'gray'
                else:
                    if self.veh_table.values(edge[1])['cluster_head'] is True:
                        if self.veh_table.values(edge[0])['primary_ch'] == edge[1]:
                            self.edge_color = 'green'
                        else:
                            self.edge_color = 'gray'
                    else:
                        self.edge_color = 'lightblue'

            folium.PolyLine(locations=locations, color=self.edge_color).add_to(edge_group)

        # Create a feature group for the networkx graph nodes
        node_group = folium.FeatureGroup(name='Graph Nodes')

        # Add nodes to the feature group
        for node, node_pos in pos.items():
            folium.Marker(location=node_pos,
                          icon=folium.DivIcon(html=f'<div style="font-size: 10pt; color: blue;">{node}</div>')).add_to(
                node_group)

        # Add the feature group to the map
        node_group.add_to(self.map)
        # Add the edge group to the map
        edge_group.add_to(self.map)

        # Add the map layer control
        folium.LayerControl().add_to(self.map)

        # Save the map as an HTML file
        self.map.save("graph_map.html")

        # Open the HTML file in a web browser
        webbrowser.open("graph_map.html")

        # save the map as image

    def save_map_img(self, zoom, name):
        util.save_img(self.map, zoom, name)

    def print_table(self):
        self.bus_table.print_hash_table()
        self.veh_table.print_hash_table()

    def check_general_framework(self, veh_id):
        """
        this test is to check if the veh_table is a cluster_head and inside another class at a same time
        :param veh_id:
        :return:
        """
        try:
            assert (
                    ((self.veh_table.values(veh_id)['cluster_head'] is True) and
                     (self.veh_table.values(veh_id)['primary_ch'] is None)) or
                    ((self.veh_table.values(veh_id)['cluster_head'] is False) and
                     (self.veh_table.values(veh_id)['primary_ch'] is not None)) or
                    ((self.veh_table.values(veh_id)['cluster_head'] is False) and
                     (self.veh_table.values(veh_id)['primary_ch'] is None) and
                     (veh_id in self.stand_alone))
            )
        except AssertionError:
            print(f'the error happens for {veh_id} at {self.time} \n'
                  f'this test is to check if the veh_table is a cluster_head and inside another class at a same time \n'
                  f'{self.veh_table.values(veh_id)}')

            sys.exit(1)

    def stand_alone_test(self, veh_id):
        """
        this test is to check if a stand_alone vehicle is not in a cluster or is a cluster_head
        :param veh_id:
        :return:
        """
        try:
            assert ((self.veh_table.values(veh_id)['cluster_head'] is False) and
                    ((veh_id in self.stand_alone) and
                     (self.veh_table.values(veh_id)['primary_ch'] is None)))
        except AssertionError:
            print(f'the error happens for {veh_id} at {self.time} \n '
                  f'this test is to check if a stand_alone vehicle is not in a cluster or is a cluster_head \n'
                  f'{self.veh_table.values(veh_id)}')
            sys.exit(1)

    def dsca_clustering(self, configs, zones):
        near_sa = dict()
        n_near_sa = dict()
        pot_ch = dict()
        befit_factor = dict()              # BeFit factor for making comparison
        con_factor = dict()            # Connectivity Factor for making comparison
        sf_factor = dict()             # Stability Factor for making comparison
        for veh_id in self.stand_alone:
            near_sa[veh_id] = util.det_near_sa(veh_id, self.veh_table,
                                               self.stand_alone, self.zone_stand_alone
                                               )
            n_near_sa[veh_id] = len(near_sa[veh_id])

        for veh_id in self.stand_alone:
            befit_factor[veh_id] = util.det_befit(self.veh_table, veh_id,
                                                  self.sumo_edges, self.sumo_nodes, configs)
            con_factor[veh_id] = util.det_con_factor(self.veh_table, veh_id)
            sf_factor[veh_id] = (0.5 * befit_factor[veh_id]) + (0.5 * con_factor[veh_id])
        for veh_id in near_sa.keys():
            if n_near_sa[veh_id] > 0:
                pot_ch[veh_id] = util.det_pot_ch_dsca(veh_id, near_sa, n_near_sa, sf_factor)
            else:
                continue

        unique_pot_ch = set(pot_ch.values())
        selected_chs = set()
        mem_control = set()   # after a vehicle become a member, add it to this and at the beginning of the
        # for-loop, check if veh_id is in it to not do anything new and ruin it
        temp = self.stand_alone.copy()
        for veh_id in temp:
            if (self.veh_table.values(veh_id)['cluster_head'] is True) or \
                    (self.veh_table.values(veh_id)['primary_ch'] is not None) or \
                    (veh_id in mem_control) or (veh_id in selected_chs):
                continue
            if (n_near_sa[veh_id] == 1) and (list(near_sa[veh_id])[0] in near_sa.keys()):
                if (n_near_sa[list(near_sa[veh_id])[0]]) == 1:
                    veh_id_2 = list(near_sa[veh_id])[0]
                    (self.veh_table, self.all_chs, self.stand_alone,
                     self.zone_stand_alone, self.zone_ch) = util.set_ch(veh_id, self.veh_table, self.all_chs,
                                                                        self.stand_alone, self.zone_stand_alone,
                                                                        self.zone_ch, configs, its_sa_clustering=True)

                    (self.veh_table, self.all_chs, self.stand_alone,
                     self.zone_stand_alone, self.zone_ch) = util.set_ch(veh_id_2, self.veh_table, self.all_chs,
                                                                        self.stand_alone, self.zone_stand_alone,
                                                                        self.zone_ch, configs, its_sa_clustering=True)
                    selected_chs.add(veh_id)
                    selected_chs.add(veh_id_2)
                    continue

            if len(unique_pot_ch.intersection(near_sa[veh_id]) - mem_control) > 0:
                if ((len(unique_pot_ch.intersection(near_sa[veh_id])) == 1) and
                        (self.veh_table.values(list(near_sa[veh_id])[0])['primary_ch'] is None)):
                    ch = list(near_sa[veh_id])[0]
                    ef = 0
                else:
                    ch = list(unique_pot_ch.intersection(near_sa[veh_id]))[0]
                    ef = 0
                    for ch_i in unique_pot_ch.intersection(near_sa[veh_id]):
                        if sf_factor[ch_i] > sf_factor[ch]:
                            ch = ch_i
                selected_chs.add(ch)

                (self.veh_table, self.all_chs, self.stand_alone,
                 self.zone_stand_alone, self.zone_ch) = util.set_ch(ch, self.veh_table, self.all_chs,
                                                                    self.stand_alone, self.zone_stand_alone,
                                                                    self.zone_ch, configs, its_sa_clustering=True)

                (self.bus_table, self.veh_table,
                 self.stand_alone,
                 self.zone_stand_alone) = util.add_member(ch, self.bus_table, veh_id, self.veh_table,
                                                          configs, ef, self.time, set(), set(), self.stand_alone,
                                                          self.zone_stand_alone, set())
                mem_control.add(veh_id)
                try:
                    self.stand_alone.remove(ch)
                    self.zone_stand_alone[self.veh_table.values(ch)['zone']].remove(ch)
                except KeyError:
                    pass
                continue

        # Determining the updating self.veh_tale and self.net_graph
        for k in near_sa.keys():
            self.veh_table, self.net_graph = util.update_sa_net_graph(self.veh_table, k, near_sa, self.net_graph)

        self.update_cluster(self.veh_table.ids(), configs, zones)

    def read_message(self, configs):
        """
        here we assumed that each message contains 3-10 packets. the last packet would have a size more than 50-70 bytes
        (which is the size dedicated to header size) and configs.mtu which is the maximum size of a packet.
        :param configs:
        :return:
        """


        (self.veh_table, self.sent_messages,
         self.message_id, self.nodes_with_pack,
         self.pck_queue) = util_routing.gen_message(self.veh_table, self.sent_messages,
                                                    self.message_count, self.nodes_with_pack, self.pck_queue,
                                                    self.time, configs)

    def route_ntlcrp(self, configs):
        # 0) Initialize link capacities (do this once per graph change ideally)
        edges = list(self.net_graph.edges())
        self.link_cap = {}
        for (u, v) in edges:
            a, b = (u, v) if u < v else (v, u)
            self.link_cap[(a, b)] = configs.link_limit

        # 1) Filter nodes_with_pack to valid ids
        all_ids = set(self.veh_table.ids()) | set(self.bus_table.ids())
        self.nodes_with_pack = self.nodes_with_pack.intersection(all_ids)

        for h in range(configs.max_hop):
            any_pck_transmitted = False

            veh_ids = set(self.veh_table.ids())  # cache per hop
            nodes_with_pack = list(self.nodes_with_pack.difference(self.stand_alone))
            nodes_with_pack.sort()  # keep only if determinism is required

            for node in nodes_with_pack:
                table = self.bus_table if "bus" in node else self.veh_table
                rec = table.values(node)
                packets = rec.get("packets_to_pass", [])

                if not packets:
                    if hasattr(self.nodes_with_pack, "discard"):
                        self.nodes_with_pack.discard(node)
                    else:
                        if node in self.nodes_with_pack:
                            self.nodes_with_pack.remove(node)
                    continue

                is_ch = (rec.get("cluster_head") is True)
                primary_ch = rec.get("primary_ch")

                # --------------------------
                # Case 1: CM with primary CH
                # --------------------------
                if (not is_ch) and (primary_ch is not None):
                    for pkt in packets[:]:
                        if pkt["dest"] not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, pkt, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        ch_id = primary_ch
                        a, b = (node, ch_id) if node < ch_id else (ch_id, node)
                        key = (a, b)
                        try:
                            cap = self.link_cap[key]
                        except KeyError:
                            self.link_cap[key] = configs.link_limit
                            cap = self.link_cap[key]
                        if cap < pkt["size"]:
                            continue

                        ch_table = self.veh_table if "veh" in ch_id else self.bus_table
                        q_link = util_routing.intra_q_link(node, ch_id, self.veh_table, ch_table, configs)

                        temp_gates = set(self.veh_table.values(node).get("other_vehs", set()))
                        temp_gates = temp_gates.intersection(ch_table.values(ch_id).get("cluster_members", set()))

                        # If QoL ok OR no gates => send directly to CH
                        if (q_link > configs.qol_thresh) or (not temp_gates):
                            (self.veh_table, self.bus_table, self.nodes_with_pack, self.delivered_packets,
                             self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, ch_id,
                                self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted,
                                pkt, self.time
                            )
                            continue

                        # Otherwise choose best gate by intra_q_link
                        best = ch_id
                        best_q = q_link
                        for g in temp_gates:
                            # Only consider if link exists
                            a, b = (node, g) if node < g else (g, node)
                            key = (a, b)
                            try:
                                cap_g = self.link_cap[key]
                            except KeyError:
                                self.link_cap[key] = configs.link_limit
                                cap_g = self.link_cap[key]
                            if cap_g < pkt["size"]:
                                continue

                            qg = util_routing.intra_q_link(g, ch_id, self.veh_table, ch_table, configs)
                            if qg > best_q:
                                best = g
                                best_q = qg

                        (self.veh_table, self.bus_table, self.nodes_with_pack, self.delivered_packets,
                         self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                            node, best,
                            self.veh_table, self.bus_table,
                            self.nodes_with_pack, self.delivered_packets,
                            self.link_cap, any_pck_transmitted,
                            pkt, self.time
                        )

                    continue

                # --------------------------
                # Case 2: CM with no primary CH
                # --------------------------
                if (not is_ch) and (primary_ch is None):
                    for pkt in packets:
                        pkt["drop_count"] = pkt.get("drop_count", 0) - 1
                    continue

                # --------------------------
                # Case 3: CH forwarding
                # --------------------------
                if is_ch:
                    other_chs = rec.get("other_chs", set())
                    others = set(other_chs) - {node}

                    # Build members of other CHs once
                    other_chs_members = set()
                    for oc in other_chs:
                        other_chs_members.update(table.values(oc).get("cluster_members", set()))

                    for pkt in packets[:]:
                        dest = pkt["dest"]

                        if dest not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, pkt, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        # deliver to own member
                        if dest in rec.get("cluster_members", set()):
                            a, b = (node, dest) if node < dest else (dest, node)
                            cap = self.link_cap.setdefault((a, b), configs.link_limit)
                            if cap >= pkt["size"]:
                                (self.veh_table, self.bus_table,
                                 self.nodes_with_pack,
                                 self.delivered_packets,
                                 self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                    node, dest,
                                    self.veh_table, self.bus_table,
                                    self.nodes_with_pack, self.delivered_packets,
                                    self.link_cap, any_pck_transmitted,
                                    pkt, self.time
                                )
                            continue

                        # destination is another CH or its member
                        if (dest in other_chs) or (dest in other_chs_members):
                            dest_rec = self.veh_table.values(dest)
                            dest_ch = dest if dest_rec.get("cluster_head") is True else dest_rec.get("primary_ch")
                            if dest_ch is not None:
                                a, b = (node, dest_ch) if node < dest_ch else (dest_ch, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= pkt["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, dest_ch,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        pkt, self.time
                                    )
                            continue

                        # No other CH candidates => decrement drop_count
                        if not others:
                            pkt["drop_count"] = pkt.get("drop_count", 0) - 1
                            continue

                        # Choose next CH by inter_ch_eval among feasible links
                        best_ch = None
                        best_metric = None
                        for ch in others:
                            a, b = (node, ch) if node < ch else (ch, node)
                            cap = self.link_cap.setdefault((a, b), configs.link_limit)
                            if cap < pkt["size"]:
                                continue

                            metric = util_routing.inter_ch_eval(
                                node, ch, dest, self.veh_table, self.bus_table, configs
                            )
                            if (best_metric is None) or (metric < best_metric):
                                best_metric = metric
                                best_ch = ch

                        if best_ch is None:
                            pkt["drop_count"] = pkt.get("drop_count", 0) - 1
                            continue

                        (self.veh_table, self.bus_table,
                         self.nodes_with_pack,
                         self.delivered_packets,
                         self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                            node, best_ch,
                            self.veh_table, self.bus_table,
                            self.nodes_with_pack, self.delivered_packets,
                            self.link_cap, any_pck_transmitted,
                            pkt, self.time
                        )

            if any_pck_transmitted is False:
                break

    def route_pdvr(self, configs):
        """
        This routing approach is a basic approach that is proposed based on
        a paper titled "Position-based Directional Vehicular Routing" a
        :param configs:
        :return:
        """
        for edge in range(len(list(self.net_graph.edges()))):
            self.link_cap[tuple(sorted(list(self.net_graph.edges())[edge]))] = configs.link_limit

        self.nodes_with_pack = self.nodes_with_pack.intersection(self.veh_table.ids().union(self.bus_table.ids()))
        for h in range(configs.max_hop):
            any_pck_transmitted = False  # this is a control parameter to break from the hop-loop if no packet transmitted
            nodes_with_pack = self.nodes_with_pack.difference(self.stand_alone).copy()
            for node in nodes_with_pack:
                table = self.bus_table if 'bus' in node else self.veh_table

                if len(table.values(node)['packets_to_pass']) == 0:
                    self.nodes_with_pack.remove(node)
                    continue

                neighbor_nodes = table.values(node)['other_vehs'].union(table.values(node)['other_chs'])
                if table.values(node)['cluster_head'] is True:
                    neighbor_nodes = neighbor_nodes.union(table.values(node)['cluster_members']).difference({node})
                if table.values(node)['primary_ch'] is not None:
                    neighbor_nodes = neighbor_nodes.union({table.values(node)['primary_ch']})

                if len(neighbor_nodes) == 0:
                    continue
                for packet in table.values(node)['packets_to_pass']:
                    if packet['dest'] not in self.veh_table.ids():
                        (self.left_dest_pack, self.nodes_with_pack,
                         self.veh_table, self.bus_table) = util_routing.left_dest(node, packet, self.left_dest_pack,
                                                                                  self.nodes_with_pack,
                                                                                  self.veh_table, self.bus_table)
                        continue
                    next_node = None
                    critic = -1000
                    for n in neighbor_nodes:
                        if self.link_cap[tuple(sorted((node, n)))] >= packet['size']:

                            next_node_table = self.veh_table if 'veh' in n else self.bus_table
                            temp_critic = util_routing.pdvr_criteria(node, table, n, next_node_table,
                                                          packet['dest'], self.veh_table)
                            if temp_critic >= 0:
                                if temp_critic > critic:
                                    critic = temp_critic
                                    next_node = n

                    if next_node is None:
                        continue

                    (self.veh_table, self.bus_table,
                     self.nodes_with_pack,
                     self.delivered_packets,
                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(node, next_node,
                                                                                    self.veh_table,
                                                                                    self.bus_table,
                                                                                    self.nodes_with_pack,
                                                                                    self.delivered_packets,
                                                                                    self.link_cap,
                                                                                    any_pck_transmitted,
                                                                                    packet, self.time)


    def route_gpsr(self, configs):
        """

        :param configs:
        :return:
        """
        self.link_cap = {}
        veh_ids = set(self.veh_table.ids())

        for h in range(configs.max_hop):
            any_pck_transmitted = False
            for node in list(self.nodes_with_pack):  # safe snapshot
                v = self.veh_table.values(node)

                ne_nodes = set(v['other_vehs']) | set(v['other_chs'])
                if v['primary_ch'] is not None:
                    ne_nodes.add(v['primary_ch'])

                if v['cluster_head'] is not True:
                    ne_nodes.discard(node)
                    ne_nodes.update(v['cluster_members'])

                if not ne_nodes:
                    continue

                packets = v['packets_to_pass']
                for pck in packets[:]:  # iterate over copy; safe removal
                    dest = pck['dest']
                    size = pck['size']

                    if dest not in veh_ids:
                        self.left_dest_pack.append(pck)
                        packets.remove(pck)
                        if not packets:
                            self.nodes_with_pack.discard(node)  # if set; else remove w/ guard
                        continue

                    # choose next hop
                    if dest in ne_nodes:
                        next_node = dest
                    else:
                        next_node = util_routing.greedy_gpsr(node, self.veh_table, pck, ne_nodes)
                        if next_node is None:
                            next_node = util_routing.perimeter_gpsr(node, dest, ne_nodes, self.veh_table)
                            self.n_perimeter += 1
                        if next_node is None:
                            continue  # no route

                    key = (node, next_node) if node < next_node else (next_node, node)
                    try:
                        cap = self.link_cap[key]
                    except KeyError:
                        self.link_cap[key] = configs.link_limit
                        cap = self.link_cap[key]
                    if cap < size:
                        continue

                    (self.veh_table, self.bus_table,
                     self.nodes_with_pack,
                     self.delivered_packets,
                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                        node, next_node, self.veh_table, self.bus_table, self.nodes_with_pack, self.delivered_packets,
                        self.link_cap, any_pck_transmitted, pck, self.time)

            if not any_pck_transmitted:
                break

    def route_cggr(self, configs, clustering_name):
        """

        :param configs:
        :return:
        """
        self.link_cap = {}

        for h in range(configs.max_hop):
            any_pck_transmitted = False

            # Cache vehicle ids once per hop (fast membership)
            veh_ids = set(self.veh_table.ids())

            # Snapshot nodes safely (avoid concurrent modification during routing)
            nodes_with_pack = list(self.nodes_with_pack)

            # Cache shortest paths within this hop to avoid repeated nx.shortest_path calls
            path_cache = {}

            for node in nodes_with_pack:
                table = self.bus_table if "bus" in node else self.veh_table
                rec = table.values(node)
                packets = rec.get("packets_to_pass", [])

                # If empty, remove from nodes_with_pack master set
                if not packets:
                    # if hasattr(self.nodes_with_pack, "discard"):
                    #     self.nodes_with_pack.discard(node)
                    # else:
                    #     if node in self.nodes_with_pack:
                    #         self.nodes_with_pack.remove(node)
                    continue

                is_ch = bool(rec.get("cluster_head"))
                primary_ch = rec.get("primary_ch")

                # -------------------------
                # Case A: Non-CH with primary CH
                # -------------------------
                if (is_ch is False) and (primary_ch is not None):
                    for packet in packets[:]:  # snapshot: safe against mutations in util_routing
                        # Left-destination handling
                        if packet["dest"] not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        # 1) Try an existing gate_path first
                        if packet.get("gate_path"):
                            next_node = packet["gate_path"].pop()
                            if next_node in veh_ids:
                                a, b = (node, next_node) if node < next_node else (next_node, node)
                                key = (a, b)
                                try:
                                    cap = self.link_cap[key]
                                except KeyError:
                                    self.link_cap[key] = configs.link_limit
                                    cap = self.link_cap[key]
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_node,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                                    continue
                                else:
                                    # restore hop for retry later
                                    packet["gate_path"].append(next_node)
                            else:
                                packet["gate_path"] = []

                        # 2) Fallback: transmit to primary CH
                        a, b = (node, primary_ch) if node < primary_ch else (primary_ch, node)
                        key = (a, b)
                        try:
                            cap = self.link_cap[key]
                        except KeyError:
                            self.link_cap[key] = configs.link_limit
                            cap = self.link_cap[key]
                        if cap >= packet["size"]:
                            (self.veh_table, self.bus_table, self.nodes_with_pack, self.delivered_packets,
                             self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, primary_ch,
                                self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted,
                                packet, self.time
                            )

                    continue

                # -------------------------
                # Case B: Non-CH with no primary CH (primary left)
                # -------------------------
                if (is_ch is False) and (primary_ch is None):
                    other_vehs = rec.get("other_vehs", set())
                    for packet in packets[:]:
                        if packet["dest"] not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        if not other_vehs:
                            continue

                        next_node = util_routing.greedy_gpsr(node, self.veh_table, packet, other_vehs)
                        if next_node is None:
                            next_node = util_routing.perimeter_gpsr(node, packet["dest"], other_vehs, self.veh_table)
                            if next_node is None:
                                continue

                        a, b = (node, next_node) if node < next_node else (next_node, node)
                        key = (a, b)
                        try:
                            cap = self.link_cap[key]
                        except KeyError:
                            self.link_cap[key] = configs.link_limit
                            cap = self.link_cap[key]
                        if cap >= packet["size"]:
                            (self.veh_table, self.bus_table,
                             self.nodes_with_pack,
                             self.delivered_packets,
                             self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, next_node,
                                self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted,
                                packet, self.time
                            )

                    continue

                # -------------------------
                # Case C: Cluster Head
                # -------------------------
                if is_ch is True:
                    other_chs_members = util_routing.other_chs_mem(node, table)
                    gate_gate_chs, gate_chs_members, other_other_vehs = util_routing.gate_chs_mem(node, self.veh_table, self.bus_table)

                    cluster_members = rec.get("cluster_members", set())
                    other_chs = rec.get("other_chs", set())
                    gate_chs = rec.get("gate_chs", set())
                    other_vehs = rec.get("other_vehs", set())

                    # Build candidate set once per node (avoid repeated unions per packet)
                    ch_candidates = set(other_chs)
                    if clustering_name == 'SMZCA':
                        ch_candidates.update(gate_chs)
                        ch_candidates.update(gate_gate_chs)
                        ch_candidates.update(gate_chs_members)
                        ch_candidates.update(other_other_vehs)
                    ch_candidates.update(other_chs_members)
                    ch_candidates.update(cluster_members)
                    ch_candidates.update(other_vehs)

                    for packet in packets[:]:
                        dest = packet["dest"]

                        if dest not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        # 1) Try existing gate_path
                        if packet.get("gate_path"):
                            next_node = packet["gate_path"].pop()
                            if next_node in veh_ids:
                                a, b = (node, next_node) if node < next_node else (next_node, node)
                                key = (a, b)
                                try:
                                    cap = self.link_cap[key]
                                except KeyError:
                                    self.link_cap[key] = configs.link_limit
                                    cap = self.link_cap[key]
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_node,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                                    continue
                                else:
                                    packet["gate_path"].append(next_node)
                            else:
                                packet["gate_path"] = []

                        # 2) Direct delivery to cluster member
                        if dest in cluster_members:
                            a, b = (node, dest) if node < dest else (dest, node)
                            key = (a, b)
                            try:
                                cap = self.link_cap[key]
                            except KeyError:
                                self.link_cap[key] = configs.link_limit
                                cap = self.link_cap[key]
                            if cap >= packet["size"]:
                                (self.veh_table, self.bus_table,
                                 self.nodes_with_pack,
                                 self.delivered_packets,
                                 self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                    node, dest,
                                    self.veh_table, self.bus_table,
                                    self.nodes_with_pack, self.delivered_packets,
                                    self.link_cap, any_pck_transmitted,
                                    packet, self.time
                                )
                            continue

                        # 3) Destination is another CH or belongs to another CH
                        if (dest in other_chs) or (dest in other_chs_members):
                            dest_rec = self.veh_table.values(dest)
                            dest_ch = dest if dest_rec.get("cluster_head") is True else dest_rec.get("primary_ch")
                            if dest_ch is not None:
                                a, b = (node, dest_ch) if node < dest_ch else (dest_ch, node)
                                key = (a, b)
                                cap = self.link_cap.setdefault(key, configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, dest_ch,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                            continue

                        # 4) Destination is in gate regions: compute a gate path
                        if (dest in gate_chs) or (dest in gate_chs_members) or (dest in gate_gate_chs):
                            packet["gate_path"] = util_routing.find_gate_path(
                                node, gate_chs_members, self.veh_table, packet, self.net_graph
                            )
                            if packet.get("gate_path"):
                                next_node = packet["gate_path"].pop()
                                a, b = (node, next_node) if node < next_node else (next_node, node)
                                key = (a, b)
                                try:
                                    cap = self.link_cap[key]
                                except KeyError:
                                    self.link_cap[key] = configs.link_limit
                                    cap = self.link_cap[key]
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_node,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                                else:
                                    packet["gate_path"].append(next_node)
                            continue

                        # 5) Otherwise: GPSR toward candidates, then shortest path (cached) to build gate_path
                        if ch_candidates:
                            next_node = util_routing.greedy_gpsr(node, self.veh_table, packet, ch_candidates)
                            if next_node is None:
                                next_node = util_routing.perimeter_gpsr(node, dest, ch_candidates, self.veh_table)
                                self.n_perimeter += 1
                                if next_node is None:
                                    continue

                            # Redirect to the candidate's primary CH if it exists
                            nxt_rec = self.veh_table.values(next_node)
                            if nxt_rec.get("primary_ch") is not None:
                                next_node = nxt_rec["primary_ch"]

                            # Cached shortest path node -> next_node
                            cache_key = (node, next_node)
                            if cache_key in path_cache:
                                path = path_cache[cache_key]
                            else:
                                try:
                                    path = nx.shortest_path(self.net_graph, source=node, target=next_node)
                                except (nx.NetworkXNoPath, nx.NodeNotFound):
                                    path = None
                                path_cache[cache_key] = path

                            if not path or len(path) < 2:
                                continue

                            # Convert to "pop from end" behavior:
                            # path = [node, ..., next_node]
                            hops = path[1:]  # [first_hop, ..., next_node]
                            first_hop = hops[0]
                            remaining = hops[1:]  # remaining after first hop
                            remaining.reverse()  # so pop() yields next hop
                            packet["gate_path"] = remaining

                            a, b = (node, first_hop) if node < first_hop else (first_hop, node)
                            key = (a, b)
                            try:
                                cap = self.link_cap[key]
                            except KeyError:
                                self.link_cap[key] = configs.link_limit
                                cap = self.link_cap[key]
                            if cap >= packet["size"]:
                                (self.veh_table, self.bus_table,
                                 self.nodes_with_pack,
                                 self.delivered_packets,
                                 self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                    node, first_hop,
                                    self.veh_table, self.bus_table,
                                    self.nodes_with_pack, self.delivered_packets,
                                    self.link_cap, any_pck_transmitted,
                                    packet, self.time
                                )
                            else:
                                # restore first hop into gate_path so behavior matches your retry logic
                                packet["gate_path"].append(first_hop)

                            continue

            if any_pck_transmitted is False:
                break

    def route_zcggr(self, configs, clustering_name, zones):
        """
        Z-CGGR: CGGR + zone-assisted greedy/perimeter at CHs.
        Requires:
          - packet has: d_loc, d_zone, des_update, gate_path, tabu_zone, hops, actions (as in your schema)
          - zones is your ZoneID/zone_table object
          - util_routing.pass_packet, left_dest, other_chs_mem, gate_chs_mem, find_gate_path exist
          - greedy_zcggr and perimeter_zcggr available (in util_routing or imported)
        """

        self.link_cap = {}

        def refresh_dest_zone_if_due(packet, veh_ids):
            # decrement des_update; if reaches 0, refresh d_loc and d_zone from current dest location
            # (this is the ONLY refresh point to match your "updated every 5 iterations" claim)
            if "des_update" not in packet:
                packet["des_update"] = configs.des_address_update

            packet["des_update"] = configs.des_address_update if packet["des_update"] == 0 else packet["des_update"] - 1

            if packet["des_update"] == configs.des_address_update:
                dest = packet.get("dest", None)
                # refresh only if destination still exists
                if dest is not None and dest in veh_ids:
                    dv = self.veh_table.values(dest)
                    packet["d_loc"] = {"lat": dv["lat"], "long": dv["long"]}
                    packet["d_zone"] = dv["zone"]

        for h in range(configs.max_hop):
            any_pck_transmitted = False

            veh_ids = set(self.veh_table.ids())
            nodes_with_pack = list(self.nodes_with_pack)
            path_cache = {}

            for node in nodes_with_pack:
                table = self.bus_table if "bus" in node else self.veh_table
                rec = table.values(node)
                packets = rec.get("packets_to_pass", [])

                if not packets:
                    continue

                is_ch = bool(rec.get("cluster_head"))
                primary_ch = rec.get("primary_ch")

                # -------------------------
                # Case A: Non-CH with primary CH
                # -------------------------
                if (is_ch is False) and (primary_ch is not None):
                    for packet in packets[:]:
                        refresh_dest_zone_if_due(packet, veh_ids)

                        if packet["dest"] not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        # 1) gate_path first
                        if packet.get("gate_path"):
                            next_node = packet["gate_path"].pop()
                            if next_node in veh_ids:
                                a, b = (node, next_node) if node < next_node else (next_node, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_node,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                                    continue
                                else:
                                    packet["gate_path"].append(next_node)
                            else:
                                packet["gate_path"] = []

                        # 2) fallback to primary CH
                        a, b = (node, primary_ch) if node < primary_ch else (primary_ch, node)
                        cap = self.link_cap.setdefault((a, b), configs.link_limit)
                        if cap >= packet["size"]:
                            (self.veh_table, self.bus_table, self.nodes_with_pack, self.delivered_packets,
                             self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, primary_ch,
                                self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted,
                                packet, self.time
                            )
                    continue

                # -------------------------
                # Case B: Non-CH with no primary CH
                # -------------------------
                if (is_ch is False) and (primary_ch is None):
                    other_vehs = rec.get("other_vehs", set())
                    for packet in packets[:]:
                        refresh_dest_zone_if_due(packet, veh_ids)

                        if packet["dest"] not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue
                        if not other_vehs:
                            continue

                        # keep your existing veh-only gpsr fallback
                        next_node = util_routing.greedy_gpsr(node, self.veh_table, packet, other_vehs)
                        if next_node is None:
                            next_node = util_routing.perimeter_gpsr(node, packet["dest"], other_vehs, self.veh_table)
                            if next_node is None:
                                continue

                        a, b = (node, next_node) if node < next_node else (next_node, node)
                        cap = self.link_cap.setdefault((a, b), configs.link_limit)
                        if cap >= packet["size"]:
                            (self.veh_table, self.bus_table,
                             self.nodes_with_pack,
                             self.delivered_packets,
                             self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, next_node,
                                self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted,
                                packet, self.time
                            )
                    continue

                # -------------------------
                # Case C: Cluster Head
                # -------------------------
                if is_ch is True:
                    other_chs_members = util_routing.other_chs_mem(node, table)
                    gate_gate_chs, gate_chs_members, other_other_vehs = util_routing.gate_chs_mem(
                        node, self.veh_table, self.bus_table
                    )

                    cluster_members = rec.get("cluster_members", set())
                    other_chs = rec.get("other_chs", set())
                    gate_chs = rec.get("gate_chs", set())
                    other_vehs = rec.get("other_vehs", set())

                    ch_candidates = set(other_chs)
                    if clustering_name == 'SMZCA':
                        ch_candidates.update(gate_chs)
                        ch_candidates.update(gate_gate_chs)
                        ch_candidates.update(gate_chs_members)
                        ch_candidates.update(other_other_vehs)
                    ch_candidates.update(other_chs_members)
                    ch_candidates.update(cluster_members)
                    ch_candidates.update(other_vehs)

                    for packet in packets[:]:
                        refresh_dest_zone_if_due(packet, veh_ids)
                        dest = packet["dest"]

                        if dest not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        # 1) gate_path first
                        if packet.get("gate_path"):
                            next_node = packet["gate_path"].pop()
                            if next_node in veh_ids:
                                a, b = (node, next_node) if node < next_node else (next_node, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_node,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                                    continue
                                else:
                                    packet["gate_path"].append(next_node)
                            else:
                                packet["gate_path"] = []

                        # 2) direct delivery to member
                        if dest in cluster_members:
                            a, b = (node, dest) if node < dest else (dest, node)
                            cap = self.link_cap.setdefault((a, b), configs.link_limit)
                            if cap >= packet["size"]:
                                (self.veh_table, self.bus_table,
                                 self.nodes_with_pack,
                                 self.delivered_packets,
                                 self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                    node, dest,
                                    self.veh_table, self.bus_table,
                                    self.nodes_with_pack, self.delivered_packets,
                                    self.link_cap, any_pck_transmitted,
                                    packet, self.time
                                )
                            continue

                        # 3) destination is another CH / belongs to another CH
                        if (dest in other_chs) or (dest in other_chs_members):
                            dest_rec = self.veh_table.values(dest)
                            dest_ch = dest if dest_rec.get("cluster_head") is True else dest_rec.get("primary_ch")
                            if dest_ch is not None:
                                a, b = (node, dest_ch) if node < dest_ch else (dest_ch, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, dest_ch,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                            continue

                        # 4) destination is in gate regions: compute a gate path
                        if (dest in gate_chs) or (dest in gate_chs_members) or (dest in gate_gate_chs):
                            packet["gate_path"] = util_routing.find_gate_path(
                                node, gate_chs_members, self.veh_table, packet, self.net_graph
                            )
                            if packet.get("gate_path"):
                                next_node = packet["gate_path"].pop()
                                a, b = (node, next_node) if node < next_node else (next_node, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table,
                                     self.nodes_with_pack,
                                     self.delivered_packets,
                                     self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_node,
                                        self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted,
                                        packet, self.time
                                    )
                                else:
                                    packet["gate_path"].append(next_node)
                            continue

                        # 5) zone-assisted CGGR decision: greedy_zcggr -> perimeter_zcggr, then gate_path
                        if ch_candidates:
                            # candidate zones from CURRENT CH zone toward packet-carried dest zone
                            candidate_zones = util_routing.closest_reachable_zones(
                                rec["zone"], packet["d_zone"], zones
                            )

                            next_node = util_routing.greedy_zcggr(
                                node, self.veh_table, self.bus_table,
                                packet, ch_candidates, candidate_zones, zones
                            )

                            if next_node is None:
                                next_node = util_routing.perimeter_zcggr(
                                    node, self.veh_table, self.bus_table,
                                    packet, ch_candidates, zones, candidate_zones=candidate_zones
                                )
                                self.n_perimeter += 1
                                if next_node is None:
                                    continue

                            # redirect to primary CH if exists
                            if "bus" not in str(next_node):
                                nxt_rec = self.veh_table.values(next_node)
                                if nxt_rec.get("primary_ch") is not None:
                                    next_node = nxt_rec["primary_ch"]

                            cache_key = (node, next_node)
                            if cache_key in path_cache:
                                path = path_cache[cache_key]
                            else:
                                try:
                                    path = nx.shortest_path(self.net_graph, source=node, target=next_node)
                                except (nx.NetworkXNoPath, nx.NodeNotFound):
                                    path = None
                                path_cache[cache_key] = path

                            if not path or len(path) < 2:
                                continue

                            hops = path[1:]  # [first_hop, ..., target]
                            first_hop = hops[0]
                            remaining = hops[1:]
                            remaining.reverse()
                            packet["gate_path"] = remaining

                            a, b = (node, first_hop) if node < first_hop else (first_hop, node)
                            cap = self.link_cap.setdefault((a, b), configs.link_limit)
                            if cap >= packet["size"]:
                                (self.veh_table, self.bus_table,
                                 self.nodes_with_pack,
                                 self.delivered_packets,
                                 self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                    node, first_hop,
                                    self.veh_table, self.bus_table,
                                    self.nodes_with_pack, self.delivered_packets,
                                    self.link_cap, any_pck_transmitted,
                                    packet, self.time
                                )
                            else:
                                packet["gate_path"].append(first_hop)

            if any_pck_transmitted is False:
                break

    def route_gpsr_rl(self, configs):

        # Build helper once per call (as you currently do)
        self.helper = QRoutingHelper(
            veh_table=self.veh_table,
            bus_table=self.bus_table,
            zones_dict={k: (self.zone_vehicles[k] | self.zone_buses[k]) for k in self.zone_vehicles},
            configs=configs,
            n_cols=self.n_zone_cols,
            max_dist=3000.0,
            max_zone_count_cap=50,
            loop_window_zones=4,
            delay_threshold_ticks=6,
        )

        # Ensure link_cap exists
        if not hasattr(self, "link_cap") or self.link_cap is None:
            self.link_cap = {}

        for h in range(configs.max_hop):
            any_pck_transmitted = False

            # Cache IDs once per hop for O(1) membership checks
            veh_ids = set(self.veh_table.ids())

            # Snapshot nodes safely (avoid concurrent modification)
            nodes_with_pack = list(self.nodes_with_pack)

            # If you need determinism, keep this; otherwise remove for speed
            nodes_with_pack.sort()

            for node in nodes_with_pack:
                rec = self.veh_table.values(node)
                packets = rec.get("packets_to_pass", [])

                # No packets -> remove from master set and continue
                if not packets:
                    if hasattr(self.nodes_with_pack, "discard"):
                        self.nodes_with_pack.discard(node)
                    else:
                        if node in self.nodes_with_pack:
                            self.nodes_with_pack.remove(node)
                    continue

                # Build neighbor set once per node
                ne_nodes = set()
                ne_nodes.update(rec.get("other_vehs", set()))
                ne_nodes.update(rec.get("other_chs", set()))

                primary_ch = rec.get("primary_ch")
                if primary_ch is not None:
                    ne_nodes.add(primary_ch)

                # If not cluster head: remove self and include cluster members (BUGFIX: use update)
                if rec.get("cluster_head") is not True:
                    ne_nodes.discard(node)
                    ne_nodes.update(rec.get("cluster_members", set()))

                if not ne_nodes:
                    continue

                # Iterate over a snapshot of packets (BUGFIX: safe against mutation)
                for pck in packets[:]:
                    dest = pck["dest"]
                    size = pck["size"]

                    # Destination left: move packet to left_dest_pack and remove from node safely
                    if dest not in veh_ids:
                        self.left_dest_pack.append(pck)
                        # Remove from the live list (not the snapshot)
                        if pck in rec["packets_to_pass"]:
                            rec["packets_to_pass"].remove(pck)
                        if not rec["packets_to_pass"]:
                            if hasattr(self.nodes_with_pack, "discard"):
                                self.nodes_with_pack.discard(node)
                            else:
                                if node in self.nodes_with_pack:
                                    self.nodes_with_pack.remove(node)
                        continue

                    # Direct neighbor delivery
                    if dest in ne_nodes:
                        a, b = (node, dest) if node < dest else (dest, node)
                        key = (a, b)
                        try:
                            cap = self.link_cap[key]
                        except KeyError:
                            self.link_cap[key] = configs.link_limit
                            cap = self.link_cap[key]
                        if cap >= size:
                            (self.veh_table, self.bus_table,
                             self.nodes_with_pack,
                             self.delivered_packets,
                             self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, dest,
                                self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted,
                                pck, self.time
                            )
                        continue

                    # Greedy GPSR
                    next_node = util_routing.greedy_gpsr(node, self.veh_table, pck, ne_nodes)

                    if next_node is not None:
                        a, b = (node, next_node) if node < next_node else (next_node, node)
                        key=(a,b)
                        try:
                            cap = self.link_cap[key]
                        except KeyError:
                            self.link_cap[key] = configs.link_limit
                            cap = self.link_cap[key]
                        if cap >= size:
                            (self.veh_table, self.bus_table,
                             self.nodes_with_pack,
                             self.delivered_packets,
                             self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, next_node,
                                self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted,
                                pck, self.time
                            )
                        continue

                    # Perimeter / RL mode if greedy fails
                    self.n_perimeter += 1

                    if self.train_mode is False:
                        # force pure greedy policy (no exploration)
                        self.agent.epsilon_start = 0.0
                        self.agent.epsilon_end = 0.0
                        self.agent.epsilon = 0.0

                    (self.agent, self.train_reward_log,
                     action, next_node) = util_routing.rl_perimeter_mode(
                        self.agent, node, pck, self.helper,
                        self.time, self.veh_table, self.bus_table,
                        configs, self.n_zone_cols, self.train_reward_log,
                        self.train_mode
                    )

                    # actions_review logging (cache zone once to avoid repeated lookups)
                    zone = rec.get("zone")
                    if zone not in self.actions_review:
                        self.actions_review[zone] = []
                    self.actions_review[zone].append((
                        configs.idx_to_zone[action],
                        util_routing.zone_name_retrieval(
                            node, self.n_zone_cols, configs,
                            self.veh_table, action
                        )
                    ))

                    if next_node is None:
                        continue

                    a, b = (node, next_node) if node < next_node else (next_node, node)
                    key = (a,b)
                    try:
                        cap = self.link_cap[key]
                    except KeyError:
                        self.link_cap[key] = configs.link_limit
                        cap = self.link_cap[key]
                    if cap >= size:
                        (self.veh_table, self.bus_table,
                         self.nodes_with_pack,
                         self.delivered_packets,
                         self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                            node, next_node,
                            self.veh_table, self.bus_table,
                            self.nodes_with_pack, self.delivered_packets,
                            self.link_cap, any_pck_transmitted,
                            pck, self.time
                        )

            if any_pck_transmitted is False:
                break

    import networkx as nx

    def route_smzcra(self, configs, clustering_name, zones):
        """
        SMZCA-ZRHR++ routing:
          - Uses packet-carried destination zone (packet['d_zone']) with periodic refresh via packet['des_update'].
          - CH-level routing uses ne_nodes only (your ch_candidates set).
          - Greedy stages: (1) zone-progress macro, (2) zone-relaxed geo greedy/perimeter, else (3) orbit-zone recovery.
          - Physical transmission uses gate_path (shortest path commitment) to suppress oscillations, like CGGR.

        Assumptions:
          - packet has keys: dest, size, gate_path(list), hops(list), actions(list), d_loc, d_zone, des_update,
                            last_dir, tabu_dir, tabu_zone
          - node "stand-alone" means (vehicle and primary_ch is None and cluster_head is False).
        """
        self.link_cap = {}

        for h in range(configs.max_hop):
            any_pck_transmitted = False
            veh_ids = set(self.veh_table.ids())
            nodes_with_pack = list(self.nodes_with_pack)

            # cache shortest paths inside this hop-loop
            path_cache = {}

            for node in nodes_with_pack:
                table = self.bus_table if "bus" in node else self.veh_table
                rec = table.values(node)
                packets = rec.get("packets_to_pass", [])
                if not packets:
                    continue

                is_ch = bool(rec.get("cluster_head"))
                primary_ch = rec.get("primary_ch")

                # -------------------------
                # Packet-level periodic destination-zone refresh
                # (HONORS your "low overhead address update every X ticks" claim)
                # -------------------------
                def refresh_dest_zone_if_due(pkt):
                    # decrement counter
                    pkt['des_update'] = pkt.get('des_update', configs.des_address_update) - 1
                    if pkt['des_update'] <= 0:
                        # refresh destination zone once per period
                        if pkt["dest"] in veh_ids:
                            pkt['d_zone'] = self.veh_table.values(pkt["dest"])['zone']
                            pkt['d_loc'] = {
                                "lat": self.veh_table.values(pkt["dest"])["lat"],
                                "long": self.veh_table.values(pkt["dest"])["long"],
                            }
                        pkt['des_update'] = configs.des_address_update

                # -------------------------
                # Case A: Non-CH with primary CH => send to CH (with gate_path support)
                # -------------------------
                if (is_ch is False) and (primary_ch is not None):
                    for packet in packets[:]:
                        refresh_dest_zone_if_due(packet)

                        if packet["dest"] not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        # 1) gate_path continuation first
                        if packet.get("gate_path"):
                            next_node = packet["gate_path"].pop()
                            if next_node in veh_ids:
                                a, b = (node, next_node) if node < next_node else (next_node, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table, self.nodes_with_pack,
                                     self.delivered_packets, self.link_cap,
                                     any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_node, self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted, packet, self.time
                                    )
                                    continue
                                else:
                                    packet["gate_path"].append(next_node)
                            else:
                                packet["gate_path"] = []

                        # 2) fallback: send to CH
                        a, b = (node, primary_ch) if node < primary_ch else (primary_ch, node)
                        cap = self.link_cap.setdefault((a, b), configs.link_limit)
                        if cap >= packet["size"]:
                            (self.veh_table, self.bus_table, self.nodes_with_pack,
                             self.delivered_packets, self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, primary_ch, self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted, packet, self.time
                            )
                    continue

                # -------------------------
                # Case B: Non-CH with no primary CH => local GPSR on other_vehs
                # -------------------------
                if (is_ch is False) and (primary_ch is None):
                    other_vehs = rec.get("other_vehs", set())
                    for packet in packets[:]:
                        refresh_dest_zone_if_due(packet)

                        if packet["dest"] not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        if not other_vehs:
                            continue

                        next_node = util_routing.greedy_gpsr(node, self.veh_table, packet, other_vehs)
                        if next_node is None:
                            next_node = util_routing.perimeter_gpsr(node, packet["dest"], other_vehs, self.veh_table)
                            if next_node is None:
                                continue

                        a, b = (node, next_node) if node < next_node else (next_node, node)
                        cap = self.link_cap.setdefault((a, b), configs.link_limit)
                        if cap >= packet["size"]:
                            (self.veh_table, self.bus_table, self.nodes_with_pack,
                             self.delivered_packets, self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, next_node, self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted, packet, self.time
                            )
                    continue

                # -------------------------
                # Case C: Cluster Head
                # -------------------------
                if is_ch:
                    other_chs_members = util_routing.other_chs_mem(node, table)
                    gate_gate_chs, gate_chs_members, other_other_vehs = util_routing.gate_chs_mem(
                        node, self.veh_table, self.bus_table
                    )

                    cluster_members = rec.get("cluster_members", set())
                    other_chs = rec.get("other_chs", set())
                    gate_chs = rec.get("gate_chs", set())
                    other_vehs = rec.get("other_vehs", set())

                    # ne_nodes pool (your "everything is in ne_nodes; don't use other_chs separately inside greedy/orbit")
                    ne_nodes = set(other_chs)
                    if clustering_name == 'SMZCA':
                        ne_nodes.update(gate_chs)
                        ne_nodes.update(gate_gate_chs)
                        ne_nodes.update(gate_chs_members)
                        ne_nodes.update(other_other_vehs)
                    ne_nodes.update(other_chs_members)
                    ne_nodes.update(cluster_members)
                    ne_nodes.update(other_vehs)

                    for packet in packets[:]:
                        refresh_dest_zone_if_due(packet)

                        dest = packet["dest"]
                        if dest not in veh_ids:
                            (self.left_dest_pack, self.nodes_with_pack,
                             self.veh_table, self.bus_table) = util_routing.left_dest(
                                node, packet, self.left_dest_pack,
                                self.nodes_with_pack, self.veh_table, self.bus_table
                            )
                            continue

                        # 1) gate_path continuation first
                        if packet.get("gate_path"):
                            next_hop = packet["gate_path"].pop()
                            if next_hop in veh_ids:
                                a, b = (node, next_hop) if node < next_hop else (next_hop, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table, self.nodes_with_pack,
                                     self.delivered_packets, self.link_cap,
                                     any_pck_transmitted) = util_routing.pass_packet(
                                        node, next_hop, self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted, packet, self.time
                                    )
                                    continue
                                else:
                                    packet["gate_path"].append(next_hop)
                            else:
                                packet["gate_path"] = []

                        # 2) direct delivery to member
                        if dest in cluster_members:
                            a, b = (node, dest) if node < dest else (dest, node)
                            cap = self.link_cap.setdefault((a, b), configs.link_limit)
                            if cap >= packet["size"]:
                                (self.veh_table, self.bus_table, self.nodes_with_pack,
                                 self.delivered_packets, self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                    node, dest, self.veh_table, self.bus_table,
                                    self.nodes_with_pack, self.delivered_packets,
                                    self.link_cap, any_pck_transmitted, packet, self.time
                                )
                            continue

                        # 3) destination is in gate region => build gate_path
                        # (keep your behavior)
                        if (dest in gate_chs) or (dest in gate_chs_members) or (dest in gate_gate_chs):
                            packet["gate_path"] = util_routing.find_gate_path(
                                node, gate_chs_members, self.veh_table, packet, self.net_graph
                            )
                            if packet.get("gate_path"):
                                first = packet["gate_path"].pop()
                                a, b = (node, first) if node < first else (first, node)
                                cap = self.link_cap.setdefault((a, b), configs.link_limit)
                                if cap >= packet["size"]:
                                    (self.veh_table, self.bus_table, self.nodes_with_pack,
                                     self.delivered_packets, self.link_cap,
                                     any_pck_transmitted) = util_routing.pass_packet(
                                        node, first, self.veh_table, self.bus_table,
                                        self.nodes_with_pack, self.delivered_packets,
                                        self.link_cap, any_pck_transmitted, packet, self.time
                                    )
                                else:
                                    packet["gate_path"].append(first)
                            continue

                        # 4) main decision: ZRHR++ greedy (zone-first, then zone-relaxed), else orbit
                        if not ne_nodes:
                            continue

                        # candidate zone cone around destination zone carried in packet
                        candidate_zones = util_routing.closest_reachable_zones(rec['zone'], packet['d_zone'], zones)

                        next_node = util_routing.greedy_smzcra(
                            node, self.veh_table, self.bus_table, packet,
                            ne_nodes, candidate_zones, zones
                        )

                        if next_node is None:
                            next_node = util_routing.orbit_smzcra(
                                node, self.veh_table, self.bus_table, packet,
                                ne_nodes, zones
                            )
                            if next_node is not None:
                                self.n_perimeter += 1  # orbit is a recovery-mode count
                            else:
                                continue

                        # redirect to primary CH (hierarchical enforcement)
                        if "bus" not in next_node:
                            nxt_rec = self.veh_table.values(next_node)
                            if nxt_rec.get("primary_ch") is not None:
                                next_node = nxt_rec["primary_ch"]

                        # commit to a path segment (CGGR-style stability)
                        cache_key = (node, next_node)
                        if cache_key in path_cache:
                            path = path_cache[cache_key]
                        else:
                            try:
                                path = nx.shortest_path(self.net_graph, source=node, target=next_node)
                            except (nx.NetworkXNoPath, nx.NodeNotFound):
                                path = None
                            path_cache[cache_key] = path

                        if not path or len(path) < 2:
                            continue

                        hops = path[1:]  # [first_hop, ..., next_node]
                        first_hop = hops[0]
                        remaining = hops[1:]  # after first hop
                        remaining.reverse()  # pop() yields next
                        packet["gate_path"] = remaining

                        a, b = (node, first_hop) if node < first_hop else (first_hop, node)
                        cap = self.link_cap.setdefault((a, b), configs.link_limit)
                        if cap >= packet["size"]:
                            (self.veh_table, self.bus_table, self.nodes_with_pack,
                             self.delivered_packets, self.link_cap, any_pck_transmitted) = util_routing.pass_packet(
                                node, first_hop, self.veh_table, self.bus_table,
                                self.nodes_with_pack, self.delivered_packets,
                                self.link_cap, any_pck_transmitted, packet, self.time
                            )
                        else:
                            packet["gate_path"].append(first_hop)

            if any_pck_transmitted is False:
                break