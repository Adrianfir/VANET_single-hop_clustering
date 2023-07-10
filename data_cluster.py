"""

This Module is coded for extracting data from XML file related to SUMO and putting them to a Hash table.
There are methods in the main DataTable class to initiate and update the vehicles and buses coming to the
understudied area and creating and updating the clusters using recursion.

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import networkx as nx
import folium
from folium.plugins import MarkerCluster
import webbrowser

from Graph import Graph
import utils.util as util
import Hash


def det_graphnet():
    return True


class DataTable:
    # This class is determined for defining the hash_table, updating data, routing messages,
    # and defining IP addresses by using trace (which is sumo_trace)

    def __init__(self, config, zones):
        """

        :param config: look at options.py and config.py
        :param zones: all the zones of the area
        """

        self.bus_table = Hash.HashTable(config.n_cars * 100)
        self.veh_table = Hash.HashTable(config.n_cars * 100)

        self.zone_vehicles = dict(zip(zones.zone_hash.ids(),
                                      [set() for j in range(len(zones.zone_hash.ids()))]
                                      )
                                  )
        self.zone_buses = dict(zip(zones.zone_hash.ids(),
                                   [set() for j in range(len(zones.zone_hash.ids()))]
                                   )
                               )
        self.zone_CH = dict(zip(zones.zone_hash.ids(),
                                [set() for j in range(len(zones.zone_hash.ids()))]
                                )
                            )
        self.zone_stand_alone = dict(zip(zones.zone_hash.ids(),
                                         [set() for j in range(len(zones.zone_hash.ids()))]
                                         )
                                     )
        self.stand_alone = set()
        self.all_CHs = set()
        self.time = config.start_time
        self.understudied_area = zones.understudied_area()
        self.init_count = 0  # this counter is just for defining the self.net_graph for the very first time
        self.edge_color = ''
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
                # Here the buses will be added to zone_buses
                self.zone_buses[zone_id].add(veh.getAttribute('id'))
                self.zone_CH[zone_id].add(veh.getAttribute('id'))
                self.all_CHs.add(veh.getAttribute('id'))

                # the veh_table will be initiated here for the very first time self.understudied_area))
            else:
                self.veh_table.set_item(veh.getAttribute('id'), util.initiate_new_veh(veh, zones, zone_id, config,
                                                                                      self.understudied_area))
                # Here the vehicles will be added to zone_vehicles
                self.zone_vehicles[zone_id].add(veh.getAttribute('id'))
                self.stand_alone.add(veh.getAttribute('id'))
                self.zone_stand_alone[self.veh_table.values(veh.getAttribute('id'))['zone']].add(veh.getAttribute('id'))

            # create the self.net_graph or add the new vertex
            if self.init_count == 1:
                self.net_graph = Graph(veh.getAttribute('id'), (float(veh.getAttribute('y')),
                                                                float(veh.getAttribute('x'))
                                                                )
                                       )
            else:
                self.net_graph.add_vertex(veh.getAttribute('id'), (float(veh.getAttribute('y')),
                                                                   float(veh.getAttribute('x'))
                                                                   )
                                          )

    def update(self, config, zones):
        """
        this method updates the bus_table and veh_table values for the current interval.
        Attention: The properties related to clusters and IP addresses are going to be updated here
        :return:
        """
        self.time += 1
        print(self.time)
        bus_ids = set()
        veh_ids = set()
        # self.stand_alone = set()
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )

            # update the bus_table for the time step
            if 'bus' in veh.getAttribute('id'):
                bus_ids.add(veh.getAttribute('id'))
                self.bus_table, self.zone_buses, self.zone_CH = util.update_bus_table(veh, self.bus_table, zone_id,
                                                                                      self.understudied_area, zones,
                                                                                      config, self.zone_buses,
                                                                                      self.zone_CH)
                self.all_CHs.add(veh.getAttribute('id'))

            else:
                veh_ids.add(veh.getAttribute('id'))
                self.veh_table, self.zone_vehicles, self.zone_CH, self.stand_alone, \
                self.zone_stand_alone = util.update_veh_table(veh, self.veh_table, zone_id, self.understudied_area,
                                                              zones, config, self.zone_vehicles, self.zone_CH,
                                                              self.stand_alone, self.zone_stand_alone)
                if self.veh_table.values(veh.getAttribute('id'))['cluster_head'] is True:
                    self.all_CHs.add(veh.getAttribute('id'))
            # add the vertex to the graph
            self.net_graph.add_vertex(veh.getAttribute('id'), (float(veh.getAttribute('y')),
                                                               float(veh.getAttribute('x'))
                                                               )
                                      )
        # removing the buses, that have left the understudied area, from self.bus_table and self.zone_buses
        for k in (self.bus_table.ids() - bus_ids):
            for m in self.bus_table.values(k)['cluster_members']:
                if m in veh_ids:  # this must be veh_ids not self.veh_table.ids()
                    self.veh_table.values(m)['primary_CH'] = None
                    self.veh_table.values(m)['counter'] = config.counter
                    self.stand_alone.add(m)
                    self.zone_stand_alone[self.veh_table.values(m)['zone']].add(m)

            self.zone_buses[self.bus_table.values(k)['zone']].remove(k)
            self.zone_CH[self.bus_table.values(k)['zone']].remove(k)
            self.all_CHs.remove(k)

            self.bus_table.remove(k)
            self.net_graph.remove_vertex(k)

        # removing the vehicles, that have left the understudied area, from self.veh_table and self.zone_vehicles
        for k in (self.veh_table.ids() - veh_ids):
            if self.veh_table.values(k)['cluster_head'] is True:
                for m in self.veh_table.values(k)['cluster_members']:
                    if m in veh_ids:  # this must be veh_ids not self.veh_table.ids()
                        self.veh_table.values(m)['primary_CH'] = None
                        self.veh_table.values(m)['counter'] = config.counter
                        self.stand_alone.add(m)
                        self.zone_stand_alone[self.veh_table.values(m)['zone']].add(m)
                self.zone_CH[self.veh_table.values(k)['zone']].remove(k)
                self.veh_table.values(k)['cluster_head'] = False
                self.all_CHs.remove(k)

            elif self.veh_table.values(k)['primary_CH'] is not None:
                if self.veh_table.values(k)['primary_CH'] in veh_ids:
                    k_ch = self.veh_table.values(k)['primary_CH']
                    self.veh_table.values(k_ch)['cluster_members'].remove(k)
                elif self.veh_table.values(k)['primary_CH'] in bus_ids:
                    k_ch = self.veh_table.values(k)['primary_CH']
                    self.bus_table.values(k_ch)['cluster_members'].remove(k)

            elif k in self.stand_alone:
                self.stand_alone.remove(k)
                self.zone_stand_alone[self.veh_table.values(k)['zone']].remove(k)

            self.zone_vehicles[self.veh_table.values(k)['zone']].remove(k)
            self.veh_table.remove(k)
            self.net_graph.remove_vertex(k)

    def update_cluster(self, veh_ids, config, zones):

        """
        This method is designed for finding a cluster for veh_id
        :return: cluster heads and connection between them including through the gate_CHs
        """
        for veh_id in veh_ids:
            self.veh_table.values(veh_id)['other_CHs'] = set()
            self.veh_table.values(veh_id)['gates'] = dict()
            self.veh_table.values(veh_id)['gate_CHs'] = set()
            # determining the buses and cluster_head in neighbor zones
            bus_candidates, ch_candidates = util.det_near_ch(veh_id, self.veh_table, self.bus_table,
                                                             self.zone_buses, self.zone_vehicles)
            if (len(bus_candidates) == 0) and (len(ch_candidates) == 0) and \
                    (self.veh_table.values(veh_id)['in_area'] is True) and \
                    (self.veh_table.values(veh_id)['primary_CH'] is None) and \
                    (self.veh_table.values(veh_id)['cluster_head'] is False):
                if self.veh_table.values(veh_id)['counter'] >= 1:
                    self.veh_table.values(veh_id)['counter'] -= 1
                    self.stand_alone.add(veh_id)
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].add(veh_id)
                    continue
                else:
                    self.veh_table.values(veh_id)['cluster_head'] = True
                    self.all_CHs.add(veh_id)
                    self.zone_CH[self.veh_table.values(veh_id)['zone']].add(veh_id)
                    self.veh_table.values(veh_id)['counter'] = config.counter
                    self.stand_alone.remove(veh_id)
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                    continue

            elif (self.veh_table.values(veh_id)['in_area'] is True) and \
                    (self.veh_table.values(veh_id)['primary_CH'] is None) and \
                    (self.veh_table.values(veh_id)['cluster_head'] is True):

                temp_mem = self.veh_table.values(veh_id)['cluster_members'].copy()
                for m in temp_mem:
                    dist = util.det_dist(veh_id, self.veh_table, m, self.veh_table)

                    if dist > config.trans_range:
                        self.veh_table.values(veh_id)['cluster_members'].remove(m)
                        self.veh_table.values(m)['primary_CH'] = None
                        self.stand_alone.add(m)
                        self.zone_stand_alone[self.veh_table.values(m)['zone']].add(m)
                        self.net_graph.remove_edge(veh_id, m)

                # if the veh_id is a CH and does not have any member, after changing its zone, it won't remain as a CH
                # unless get selected by another vehicles or can't find a cluster head after the counter
                if len(self.veh_table.values(veh_id)['cluster_members']) == 0:
                    if self.veh_table.values(veh_id)['zone'] != self.veh_table.values(veh_id)['prev_zone']:
                        self.veh_table.values(veh_id)['cluster_members'] = set()
                        self.veh_table.values(veh_id)['cluster_head'] = False
                        self.zone_CH[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                        self.all_CHs.remove(veh_id)
                        self.stand_alone.add(veh_id)
                        self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].add(veh_id)
                        self.update_cluster([veh_id, ], config, zones)

                self.veh_table.values(veh_id)['other_CHs'].update(self.veh_table.values(veh_id)['other_CHs'].
                                                                  union(bus_candidates))
                self.veh_table.values(veh_id)['other_CHs'].update(self.veh_table.values(veh_id)['other_CHs'].
                                                                  union(ch_candidates))
                self.zone_CH[self.veh_table.values(veh_id)['zone']].add(veh_id)
                self.all_CHs.add(veh_id)
                for other_ch in self.veh_table.values(veh_id)['other_CHs']:
                    self.net_graph.add_edge(veh_id, other_ch)
                continue
            # checking if the vehicle is understudied-area and still in transmission range of its current primary_CH
            # or is not in its transmission_range anymore
            elif (self.veh_table.values(veh_id)['in_area'] is True) and \
                    (self.veh_table.values(veh_id)['cluster_head'] is False) and \
                    (self.veh_table.values(veh_id)['primary_CH'] is not None):
                if 'bus' in self.veh_table.values(veh_id)['primary_CH']:
                    temp_table = self.bus_table
                else:
                    temp_table = self.veh_table
                    # print(veh_id, ',', self.veh_table.values(veh_id)['primary_CH'])
                dist_to_primaryCH = util.det_dist(veh_id, self.veh_table,
                                                  self.veh_table.values(veh_id)['primary_CH'], temp_table)

                if dist_to_primaryCH <= min(self.veh_table.values(veh_id)['trans_range'],
                                            temp_table.values(self.veh_table.values(veh_id)['primary_CH'])
                                            ['trans_range']):
                    self.veh_table.values(veh_id)['other_CHs'].update(self.veh_table.values(veh_id)['other_CHs'].
                                                                      union(bus_candidates))
                    self.veh_table.values(veh_id)['other_CHs'].update(self.veh_table.values(veh_id)['other_CHs'].
                                                                      union(ch_candidates))
                    self.veh_table.values(veh_id)['other_CHs'].remove(self.veh_table.values(veh_id)['primary_CH'])

                    # updating 'gates' and 'gate_CHs' considering if the primary_CH is bus or vehicle-ch
                    if 'bus' in self.veh_table.values(veh_id)['primary_CH']:
                        self.bus_table.values(self.veh_table.values(veh_id)['primary_CH'])['gates'][veh_id] = \
                            self.veh_table.values(veh_id)['other_CHs']
                        self.bus_table.values(self.veh_table.values(veh_id)['primary_CH'])['gate_CHs']. \
                            update(self.bus_table.values(self.veh_table.values(veh_id)['primary_CH'])['gate_CHs'].
                                   union(self.veh_table.values(veh_id)['other_CHs']))
                    else:
                        self.veh_table.values(self.veh_table.values(veh_id)['primary_CH'])['gates'][veh_id] = \
                            self.veh_table.values(veh_id)['other_CHs']
                        self.veh_table.values(self.veh_table.values(veh_id)['primary_CH'])['gate_CHs']. \
                            update(self.veh_table.values(self.veh_table.values(veh_id)['primary_CH'])['gate_CHs'].
                                   union(self.veh_table.values(veh_id)['other_CHs']))
                    for other_ch in self.veh_table.values(veh_id)['other_CHs']:
                        self.net_graph.add_edge(veh_id, other_ch)
                    continue
                # here the 'primary_CH' will be changed to None and recursion is applied
                else:
                    ch_id = self.veh_table.values(veh_id)['primary_CH']
                    if 'bus' in ch_id:
                        self.bus_table.values(ch_id)['cluster_members'].remove(veh_id)
                    elif 'veh' in ch_id:
                        self.veh_table.values(ch_id)['cluster_members'].remove(veh_id)
                    self.net_graph.remove_edge(ch_id, veh_id)
                    self.veh_table.values(veh_id)['primary_CH'] = None
                    self.stand_alone.add(veh_id)
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].add(veh_id)
                    self.update_cluster([veh_id, ], config, zones)

            # checking if the vehicle is in the understudied-area and if it's not in any cluster and if it's not a CH
            elif (self.veh_table.values(veh_id)['in_area'] is True) and \
                    (self.veh_table.values(veh_id)['primary_CH'] is None) and \
                    (self.veh_table.values(veh_id)['cluster_head'] is False):

                if len(bus_candidates) > 0:
                    if len(bus_candidates) == 1:
                        bus_ch = list(bus_candidates)[0]
                    else:
                        bus_ch = util.choose_ch(self.bus_table, self.veh_table.values(veh_id), zones,
                                                bus_candidates)  # determine the most suitable from bus_candidates

                    self.veh_table.values(veh_id)['primary_CH'] = bus_ch
                    self.veh_table.values(veh_id)['counter'] = config.counter
                    bus_candidates.remove(bus_ch)
                    self.veh_table.values(veh_id)['other_CHs']. \
                        update(self.veh_table.values(veh_id)['other_CHs'].union(bus_candidates))
                    self.veh_table.values(veh_id)['other_CHs']. \
                        update(self.veh_table.values(veh_id)['other_CHs'].union(ch_candidates))
                    self.bus_table.values(bus_ch)['cluster_members'].add(veh_id)
                    self.bus_table.values(bus_ch)['gates'][veh_id] = self.veh_table.values(veh_id)['other_CHs']
                    self.bus_table.values(bus_ch)['gate_CHs']. \
                        update(self.bus_table.values(bus_ch)['gate_CHs'].
                               union(self.veh_table.values(veh_id)['other_CHs']))
                    self.stand_alone.remove(veh_id)
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                    self.net_graph.add_edge(bus_ch, veh_id)
                    for other_ch in self.veh_table.values(veh_id)['other_CHs']:
                        self.net_graph.add_edge(other_ch, veh_id)

                    continue
                elif (len(bus_candidates) == 0) and (len(ch_candidates) > 0):
                    if len(ch_candidates) == 1:
                        veh_ch = list(ch_candidates)[0]
                    else:
                        veh_ch = util.choose_ch(self.veh_table, self.veh_table.values(veh_id),
                                                zones,
                                                ch_candidates)  # determine the most suitable from bus_candidates

                    self.veh_table.values(veh_id)['primary_CH'] = veh_ch
                    self.veh_table.values(veh_id)['counter'] = config.counter
                    ch_candidates.remove(veh_ch)
                    self.veh_table.values(veh_id)['other_CHs']. \
                        update(self.veh_table.values(veh_id)['other_CHs'].union(ch_candidates))
                    self.veh_table.values(veh_ch)['cluster_members'].add(veh_id)
                    self.veh_table.values(veh_ch)['gates'][veh_id] = self.veh_table.values(veh_id)['other_CHs']
                    self.veh_table.values(veh_ch)['gate_CHs'].\
                        update(self.veh_table.values(veh_ch)['gate_CHs'].
                               union(self.veh_table.values(veh_id)['other_CHs']))
                    self.stand_alone.remove(veh_id)
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                    self.net_graph.add_edge(veh_ch, veh_id)
                    for other_ch in self.veh_table.values(veh_id)['other_CHs']:
                        self.net_graph.add_edge(other_ch, veh_id)

                    continue

        # finding buses' other_CHs
        for bus in self.bus_table.ids():
            self.bus_table.values(bus)['other_CHs'] = set()
            print(veh_id, bus)
            nearby_chs = util.det_buses_other_CH(bus, self.veh_table, self.bus_table,
                                                 self.zone_buses, self.zone_CH)
            self.bus_table.values(bus)['other_CHs'] = self.bus_table.values(bus)['other_CHs'].union(nearby_chs)
            for node in self.bus_table.values(bus)['other_CHs']:
                self.net_graph.add_edge(bus, node)

    def stand_alones_cluster(self, configs, zones):
        near_sa = dict()
        n_near_sa = dict()
        pot_ch = dict()
        for veh_id in self.stand_alone:
            near_sa[veh_id] = util.det_near_sa(veh_id, self.veh_table,
                                               self.stand_alone, self.zone_stand_alone
                                               )
            n_near_sa[veh_id] = len(near_sa[veh_id])

        for veh_id in near_sa.keys():
            if n_near_sa[veh_id] > 0:
                pot_ch[veh_id] = veh_id
                for mem in near_sa[veh_id]:
                    if mem in near_sa.keys():
                        if n_near_sa[mem] > n_near_sa[pot_ch[veh_id]]:
                            pot_ch[veh_id] = mem
            else:
                continue

        unique_pot_ch = set(pot_ch.values())
        selected_chs = set()
        temp = self.stand_alone.copy()
        for veh_id in temp:
            if (self.veh_table.values(veh_id)['cluster_head'] is True) or \
                    (self.veh_table.values(veh_id)['primary_CH'] is not None):
                continue
            if (n_near_sa[veh_id] == 1) and (list(near_sa[veh_id])[0] in near_sa.keys()):
                if n_near_sa[list(near_sa[veh_id])[0]] == 1:
                    veh_id_2 = list(near_sa[veh_id])[0]
                    print(self.stand_alone)
                    print(self.zone_stand_alone[self.veh_table.values(veh_id)['zone']])
                    print(self.zone_stand_alone[self.veh_table.values(veh_id_2)['zone']])
                    self.veh_table.values(veh_id)['cluster_head'] = True
                    self.veh_table.values(veh_id_2)['cluster_head'] = True
                    self.veh_table.values(veh_id)['counter'] = configs.counter
                    self.veh_table.values(veh_id_2)['counter'] = configs.counter
                    self.veh_table.values(veh_id)['other_CHs'].add(veh_id_2)
                    self.veh_table.values(veh_id_2)['other_CHs'].add(veh_id)
                    self.zone_CH[self.veh_table.values(veh_id)['zone']].add(veh_id)
                    self.zone_CH[self.veh_table.values(veh_id_2)['zone']].add(veh_id_2)
                    self.all_CHs.add(veh_id)
                    self.all_CHs.add(veh_id_2)
                    self.stand_alone.remove(veh_id)
                    self.stand_alone.remove(veh_id_2)
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                    self.zone_stand_alone[self.veh_table.values(veh_id_2)['zone']].remove(veh_id_2)
                    self.net_graph.add_edge(veh_id, veh_id_2)
                    continue

            if len(unique_pot_ch.intersection(near_sa[veh_id])) > 1:
                ch = util.choose_ch(self.veh_table, self.veh_table.values(veh_id), zones,
                                    unique_pot_ch.intersection(near_sa[veh_id])
                                    )
                selected_chs.add(ch)
                if ch == veh_id:
                    if n_near_sa[veh_id] == 0:
                        if self.veh_table.values(veh_id)['counter'] == 0:
                            self.veh_table.values(veh_id)['cluster_head'] = True
                            self.veh_table.values(veh_id)['counter'] = configs.counter
                            self.all_CHs.add(veh_id)
                            self.zone_CH[self.veh_table.values(veh_id)['zone']].add(veh_id)
                            self.stand_alone.remove(veh_id)
                            self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                        else:
                            self.veh_table.values(veh_id)['counter'] -= 1
                            continue
                    # if just 2 vehicles are in trans_range of each other
                    elif n_near_sa[veh_id] == 1:
                        self.veh_table.values(veh_id)['cluster_head'] = True
                        self.veh_table.values(veh_id)['counter'] = configs.counter
                        self.veh_table.values(near_sa[veh_id][0])['counter'] = configs.counter
                        self.veh_table.values(veh_id)['cluster_members'].add(near_sa[veh_id][0])
                        self.veh_table.values(veh_id)['cluster_members'].add(near_sa[veh_id][0])
                        self.veh_table.values(near_sa[veh_id][0])['primary_CH'] = veh_id
                        self.all_CHs.add(veh_id)
                        self.zone_CH[self.veh_table.values(veh_id)['zone']].add(veh_id)
                        self.net_graph.add_edge(veh_id, near_sa[veh_id][0])
                        self.stand_alone.remove(veh_id)
                        self.stand_alone.remove(near_sa[veh_id][0])
                        self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                        self.zone_stand_alone[self.veh_table.values(near_sa[veh_id][0])['zone']]. \
                            remove(near_sa[veh_id][0])

                if (ch != veh_id) and (ch != ''):
                    self.veh_table.values(ch)['cluster_head'] = True
                    self.veh_table.values(ch)['cluster_members'].add(veh_id)
                    self.veh_table.values(veh_id)['primary_CH'] = ch
                    self.veh_table.values(veh_id)['counter'] = configs.counter
                    self.veh_table.values(ch)['counter'] = configs.counter
                    self.net_graph.add_edge(ch, veh_id)
                    self.all_CHs.add(ch)
                    self.zone_CH[self.veh_table.values(ch)['zone']].add(ch)
                    self.stand_alone.remove(veh_id)
                    self.zone_stand_alone[self.veh_table.values(veh_id)['zone']].remove(veh_id)
                    try:
                        self.stand_alone.remove(ch)
                        self.zone_stand_alone[self.veh_table.values(ch)['zone']].remove(ch)
                    except KeyError:
                        pass
                    continue

        for k in selected_chs:
            try:
                self.stand_alone.remove(k)
                self.zone_stand_alone[self.veh_table.values(k)['zone']].remove(k)
            except KeyError:
                pass

        # Determining the updating self.veh_tale and self.net_graph
        for k in near_sa.keys():
            self.veh_table, self.net_graph = util.update_sa_net_graph(self.veh_table, k, near_sa, self.net_graph)

        self.update_cluster(self.veh_table.ids(), configs, zones)

    def show_graph(self):
        """
        this function will illustrate the self.net_graph
        :return: Graph
        """
        G = nx.Graph()

        # Add nodes and edges with coordinates to the networkx graph
        node_colors = dict()
        for vertex, data in self.net_graph.adj_list.items():
            G.add_node(vertex, pos=data['pos'])
            for edge in data['edges']:
                G.add_edge(vertex, edge)

        # Extract positions from node attributes
        pos = nx.get_node_attributes(G, 'pos')

        # Create a folium map centered around the first node
        map_center = list(pos.values())[0]
        m = folium.Map(location=map_center, zoom_start=15.5, tiles='cartodbpositron')

        # Create a MarkerCluster group for the networkx graph nodes
        marker_cluster = MarkerCluster(name='VANET')

        # Add nodes to the MarkerCluster group
        for node, node_pos in pos.items():
            if 'bus' in node:
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
        marker_cluster.add_to(m)

        # Create a feature group for the networkx graph edges
        edge_group = folium.FeatureGroup(name='Graph Edges')

        # Add edges to the feature group
        for edge in G.edges():
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
                    if self.veh_table.values(edge[0])['primary_CH'] == edge[1]:
                        self.edge_color = 'green'
                    else:
                        self.edge_color = 'gray'
            elif ('bus' in edge[0]) and ('veh' in edge[1]):
                if self.veh_table.values(edge[1])['cluster_head'] is True:
                    self.edge_color = 'pink'
                else:
                    if self.veh_table.values(edge[1])['primary_CH'] == edge[0]:
                        self.edge_color = 'green'
                    else:
                        self.edge_color = 'gray'
            elif ('veh' in edge[0]) and ('veh' in edge[1]):
                if self.veh_table.values(edge[0])['cluster_head'] is True:
                    if self.veh_table.values(edge[1])['cluster_head'] is True:
                        self.edge_color = 'pink'
                    elif (self.veh_table.values(edge[1])['cluster_head'] is False) and \
                            (self.veh_table.values(edge[1])['primary_CH'] == edge[0]):
                        self.edge_color = 'green'
                    else:
                        self.edge_color = 'gray'
                else:
                    if self.veh_table.values(edge[1])['cluster_head'] is True:
                        if self.veh_table.values(edge[0])['primary_CH'] == edge[1]:
                            self.edge_color = 'green'
                        else:
                            self.edge_color = 'gray'
            folium.PolyLine(locations=locations, color=self.edge_color).add_to(edge_group)

        # Create a feature group for the networkx graph nodes
        node_group = folium.FeatureGroup(name='Graph Nodes')

        # Add nodes to the feature group
        for node, node_pos in pos.items():
            folium.Marker(location=node_pos,
                          icon=folium.DivIcon(html=f'<div style="font-size: 10pt; color: blue;">{node}</div>')).add_to(
                node_group)

        # Add the feature group to the map
        node_group.add_to(m)
        # Add the edge group to the map
        edge_group.add_to(m)

        # Add the map layer control
        folium.LayerControl().add_to(m)

        # Save the map as an HTML file
        m.save("graph_map.html")

        # Open the HTML file in a web browser
        webbrowser.open("graph_map.html")

    def print_table(self):
        self.bus_table.print_hash_table()
        self.veh_table.print_hash_table()
