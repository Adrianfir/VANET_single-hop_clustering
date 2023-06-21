"""

This Module is coded for extracting data from XML file related to SUMO and putting them to a Hash table.
There are methods in the main DataTable class to initiate and update the vehicles and buses coming to the
understudied area and creating and updating the clusters using recursion.

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import haversine as hs
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
        self.stand_alone = set()
        self.all_CHs = set()
        self.time = config.start_time
        self.understudied_area = zones.understudied_area()
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )
            # the bus_table will be initiated here for the very first time
            if 'bus' in veh.getAttribute('id'):
                self.bus_table.set_item(veh.getAttribute('id'), util.initiate_new_bus(veh, zones, zone_id, config,
                                                                                      self.understudied_area))
                # Here the buses will be added to zone_buses
                self.zone_buses[zone_id].add(veh.getAttribute('id'))

                # the veh_table will be initiated here for the very first time self.understudied_area))
            else:
                self.veh_table.set_item(veh.getAttribute('id'), util.initiate_new_veh(veh, zones, zone_id, config,
                                                                                      self.understudied_area))
                # Here the vehicles will be added to zone_vehicles
                self.zone_vehicles[zone_id].add(veh.getAttribute('id'))

    def update(self, config, zones):
        """
        this method updates the bus_table and veh_table values for the current interval.
        Attention: The properties related to clusters and IP addresses are going to be updated here
        :return:
        """
        self.time += 1
        bus_ids = set()
        veh_ids = set()
        self.all_CHs = set()
        for veh in config.sumo_trace.documentElement.getElementsByTagName('timestep')[self.time].childNodes[
                   1::2]:
            zone_id = zones.det_zone(float(veh.getAttribute('y')),  # determine the zone_id of the car (bus | veh)
                                     float(veh.getAttribute('x'))
                                     )

            # update the bus_table for the time step
            if 'bus' in veh.getAttribute('id'):
                bus_ids.add(veh.getAttribute('id'))
                self.bus_table, self.zone_buses = util.update_bus_table(veh, self.bus_table, zone_id,
                                                                        self.understudied_area, zones,
                                                                        config, self.zone_buses)
                self.all_CHs.add(veh.getAttribute('id'))
            else:
                veh_ids.add(veh.getAttribute('id'))
                self.veh_table, self.zone_vehicles = util.update_veh_table(veh, self.veh_table, zone_id,
                                                                           self.understudied_area, zones,
                                                                           config, self.zone_vehicles)
        # removing the buses, that have left the understudied area, from self.bus_table and self.zone_buses
        for k in (self.bus_table.ids() - bus_ids):
            self.zone_buses[self.bus_table.values(k)['zone']].remove(k)
            self.bus_table.remove(k)

        # removing the vehicles, that have left the understudied area, from self.veh_table and self.zone_vehicles
        for k in (self.veh_table.ids() - veh_ids):
            self.zone_vehicles[self.veh_table.values(k)['zone']].remove(k)
            self.veh_table.remove(k)

    def update_cluster(self, config, zones):

        """
        This method is designed for finding a cluster for veh_id
        :return: cluster heads and connection between them including through the gate_CHs
        """
        for veh_id in self.veh_table.ids():
            self.veh_table.values(veh_id)['other_CHs'] = set()
            # determining the buses and cluster_head in neighbor zones
            bus_candidates, ch_candidates = util.det_near_ch(veh_id, self.veh_table, self.bus_table,
                                                             self.zone_buses, self.zone_vehicles)
            if len(bus_candidates) == 0 & len(ch_candidates) == 0 & \
                    (self.veh_table.values(veh_id)['primary_CH'] is None) & \
                    (self.veh_table.values(veh_id)['cluster_head'] is False):
                self.stand_alone.add(veh_id)

            elif (self.veh_table.values(veh_id)['in_area'] is True) & \
                    (self.veh_table.values(veh_id)['primary_CH'] is None) & \
                    (self.veh_table.values(veh_id)['cluster_head'] is True):

                for m in self.veh_table.values(veh_id).adj_list:
                    dist = hs.haversine((self.veh_table.values(veh_id)["lat"],
                                         self.veh_table.values(veh_id)["long"]),
                                        (self.veh_table.values(self.veh_table.values(m))['lat'],
                                         self.veh_table.values(self.veh_table.values(m))['long']
                                         ), unit=hs.Unit.METERS)
                    if dist > config.trans_range:
                        self.veh_table.values(veh_id)['cluster_members'].remove_edge(veh_id, m)

                # if the veh_id is a CH and does not have any member, after changing its zone, it won't remain as a CH
                # unless get selected by another vehicles or can't find a cluster head after the counter
                if len(self.veh_table.values(veh_id))['cluster_members'].adj_list == 1:
                    if self.veh_table.values(veh_id)['zone'] != self.veh_table.values(veh_id)['prev_zone']:
                        self.veh_table.values(veh_id)['cluster_members'].remove_edge(veh_id)
                        self.veh_table.values(veh_id)['cluster_head'] = False
                        self.zone_CH[self.veh_table.values('zone')].remove(veh_id)
                        self.update_cluster(veh_id)

                self.veh_table.values(veh_id)['other_CHs'].add(bus_candidates)
                self.veh_table.values(veh_id)['other_CHs'].add(ch_candidates)
                self.zone_CH[self.veh_table.values('zone')].add(veh_id)
                self.all_CHs.add(veh_id)

            # checking if the vehicle is understudied-area and still in transmission range of its current primary_CH
            # or is not in its transmission_range anymore
            elif (self.veh_table.values(veh_id)['in_area'] is True) & \
                    (self.veh_table.values(veh_id)['primary_CH'] is not None):
                dist_to_primaryCH = hs.haversine((self.veh_table.values(veh_id)["lat"],
                                                  self.veh_table.values(veh_id)["long"]),
                                                 (self.bus_table.values(self.veh_table.values(veh_id)['primary_CH'])[
                                                      'lat'],
                                                  self.bus_table.values(self.veh_table.values(veh_id)['primary_CH'])[
                                                      'long']
                                                  ), unit=hs.Unit.METERS)
                if dist_to_primaryCH <= min(self.veh_table.values(veh_id)['trans_range'],
                                            self.bus_table.values(self.veh_table.values(veh_id)
                                                                  ['primary_CH'])['trans_range']):
                    continue
                # here the 'primary_CH' will be changed to None and recursion is applied
                else:
                    ch_id = self.veh_table.values(veh_id)['primary_CH']
                    if 'bus' in ch_id:
                        self.bus_table.values(ch_id)['cluster_members'].remove_vertex(ch_id, veh_id)
                        self.bus_table.values(ch_id)['cluster_members'].remove_edge(ch_id)
                    else:
                        self.veh_table.values(ch_id)['cluster_members'].remove_vertex(ch_id, veh_id)
                        self.veh_table.values(ch_id)['cluster_members'].remove_edge(ch_id)
                    self.veh_table.values(veh_id)['primary_CH'] = None
                    self.update_cluster(veh_id)

            # checking if the vehicle is in the understudied-area & if it's not in any cluster & if it's not a CH
            elif (self.veh_table.values(veh_id)['in_area'] is True) & \
                    (self.veh_table.values(veh_id)['primary_CH'] is None) & \
                    (self.veh_table.values(veh_id)['cluster_head'] is False):

                if len(bus_candidates) > 0:
                    if len(bus_candidates) == 1:
                        bus_ch = list(bus_candidates)[0]
                        self.veh_table.values(veh_id)['primary_CH'] = bus_ch
                        self.veh_table.values(veh_id)['counter'] = config.counter
                        self.bus_table.values(bus_ch)['cluster_members'].\
                            add_vertex(veh_id, (self.veh_table.values(veh_id)['lat'],
                                                self.veh_table.values(veh_id)['long']))
                        self.bus_table.values(bus_ch)['cluster_members'].add_edge(bus_ch, veh_id)
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
                        self.bus_table.values(bus_ch)['cluster_members'].\
                            add_vertex(veh_id, (self.veh_table.values(veh_id)['lat'],
                                       self.veh_table.values(veh_id)['long']))
                        self.bus_table.values(bus_ch)['cluster_members'].add_edge(bus_ch, veh_id)
                        # updating the gate_CHs of the bus_ch: if a=self.bus_table.values(bus_ch)['gate_CHs'], and
                        # b=self.veh_table.values(veh_id)['other_CHs']
                        # then a.update(a.union(b.difference(a)))
                        # then update the bus_ch's gates
                        if len(self.veh_table.values(veh_id)['other_CHs']) > 0:
                            self.bus_table.values(bus_ch)['gate_CHs'].update(
                                self.bus_table.values(bus_ch)['gate_CHs'].
                                union(self.veh_table.values(veh_id)['other_CHs'].
                                      difference(self.bus_table.values(bus_ch)['gate_CHs'])))
                            self.bus_table.values(bus_ch)['gates'][veh_id] = self.veh_table.values(veh_id)['other_CHs']
                    continue
                elif len(ch_candidates) > 0:
                    if len(ch_candidates) == 1:
                        veh_ch = list(ch_candidates)[0]
                        self.veh_table.values(veh_id)['primary_CH'] = veh_ch
                        self.veh_table.values(veh_id)['counter'] = config.counter
                        self.veh_table.values(veh_ch)['cluster_members'].\
                            add_vertex(veh_id, (self.veh_table.values(veh_id)['lat'],
                                                self.veh_table.values(veh_id)['long']))
                        self.veh_table.values(veh_ch)['cluster_members'].add_edge(veh_ch, veh_id)
                    else:
                        veh_ch = util.choose_ch(self.veh_table, self.veh_table.values(veh_id),
                                                zones,
                                                ch_candidates)  # determine the most suitable from bus_candidates

                        self.veh_table.values(veh_id)['primary_CH'] = veh_ch
                        self.veh_table.values(veh_id)['counter'] = config.counter
                        bus_candidates.remove(veh_ch)
                        self.veh_table.values(veh_id)['other_CHs']. \
                            update(self.veh_table.values(veh_id)['other_CHs'].union(ch_candidates))
                        self.bus_table.values(veh_ch)['cluster_members'].\
                            add_vertex(veh_id, (self.veh_table.values(veh_id)['lat'],
                                                self.veh_table.values(veh_id)['long']))
                        self.bus_table.values(veh_ch)['cluster_members'].add_edge(veh_ch, veh_id)
                        # updating the gate_CHs of the CH: if a=self.veh_table.values(veh_ch)['gate_CHs'], and
                        # b=self.veh_table.values(veh_id)['other_CHs']
                        # then a.update(a.union(b.difference(a)))
                        # then update the veh_ch's gates
                        if len(self.veh_table.values(veh_id)['other_CHs']) > 0:
                            self.veh_table.values(veh_ch)['gate_CHs'].update(
                                self.veh_table.values(veh_ch)['gate_CHs'].
                                union(self.veh_table.values(veh_id)['other_CHs'].
                                      difference(self.veh_table.values(veh_ch)['gate_CHs'])))
                            self.veh_table.values(veh_ch)['gates'][veh_id] = self.veh_table.values(veh_id)['other_CHs']
                    continue
                else:
                    if self.veh_table.values(veh_id)['counter'] > 1:
                        self.veh_table.values(veh_id)['counter'] -= 1
                        self.stand_alone.add(veh_id)
                    else:
                        self.veh_table.values(veh_id)['cluster_head'] = True
                        self.veh_table.values(veh_id)['counter'] = config.counter
                        self.veh_table.values(veh_id)['cluster_members'] = Graph(veh_id,
                                                                                 (self.veh_table.values(veh_id)['lat'],
                                                                                  self.veh_table.values(veh_id)['long'])
                                                                                 )
                        self.stand_alone.remove(veh_id)
        # finding buses' other_CHs
        for bus in self.bus_table.ids():
            self.bus_table.values(bus)['other_CHs'] = set()
            nearby_chs = util.det_buses_other_CH(bus, self.veh_table, self.bus_table,
                                                 self.zone_buses, self.zone_CH)
            self.bus_table.values(bus)['other_CHs'] = self.bus_table.values(bus)['other_CHs'].union(nearby_chs)

    # def create_cluster(self):
    #     near_veh = dict()
    #     if len(self.stand_alone()) > 1:
    #         for i in self.stand_alone:
    #             near_veh[i:[]]

    def print_table(self):
        self.bus_table.print_hash_table()
        self.veh_table.print_hash_table()
