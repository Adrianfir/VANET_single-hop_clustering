"""
This is the utils file including the small functions related to self.net_graph
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = []

import networkx as nx

def veh_add_edges(veh_id, veh_table, net_graph):
    """
    Note: in this function we wont consider the stand-alone vehicles and will remove them from the other_vehs
    :param veh_id:
    :param veh_table:
    :param net_graph:
    :return:
    """
    all_nearby = set()
    if veh_table.values(veh_id)['primary_ch'] is not None:
        net_graph.add_edges_from([(veh_id, veh_table.values(veh_id)['primary_ch']),
                                 (veh_table.values(veh_id)['primary_ch'], veh_id)])

    # Let's remove the stand_alone vehicles as they are not trustworthy to be considered as gates
    temp_other_vehs = set([i for i in veh_table.values(veh_id)['other_vehs']
                           if veh_table.values(i)['primary_ch'] is not None])

    all_nearby.update(all_nearby.union(all_nearby, veh_table.values(veh_id)['other_chs'],
                     temp_other_vehs
                                       )
                      )

    for i in all_nearby:
        net_graph.add_edges_from([(veh_id, i),
                                     (i, veh_id)])
    return net_graph

def ch_add_edges(veh_id, veh_table, net_graph):
    """

    :param veh_id:
    :param veh_table:
    :param net_graph:
    :return:
    """
    all_nearby = set()

    all_nearby.update(all_nearby.union(all_nearby, veh_table.values(veh_id)['other_chs'],
                     veh_table.values(veh_id)['other_vehs'], veh_table.values(veh_id)['cluster_members']))
    for i in all_nearby:
        net_graph.add_edges_from([(veh_id, i),
                                 (i, veh_id)])

    return net_graph
def bus_add_edges(bus_id, bus_table, net_graph):
    """

    :param bus_id:
    :param bus_table:
    :param net_graph:
    :return:
    """
    all_nearby = set()

    all_nearby.update(all_nearby.union(all_nearby, bus_table.values(bus_id)['other_chs'],
                     bus_table.values(bus_id)['other_vehs'], bus_table.values(bus_id)['cluster_members']))
    for i in all_nearby:
        net_graph.add_edges_from([(bus_id, i),
                                 (i, bus_id)])
    return net_graph