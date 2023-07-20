"""
This Class is for building a Graph to show the connections of the Cluster-Heads and Bridges.
Rhis Graoh is based on adjacency-List rather than a matrix as the number of vehicles in the
Greater Toronto Area (GTA) would affect the space complexity
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['Graph']

import networkx as nx

import hash


class Graph:

    def __init__(self, vertex, pos):
        self.adj_list = {vertex: {'pos': pos, 'edges': []}}

    def print_graph(self):
        for vertex in self.adj_list:
            print(vertex, ':', self.adj_list[vertex]['edges'])

    def add_vertex(self, vertex, pos):
        """
        this method is for adding a new vertex
        :param pos: location latitude and longitude
        :param vertex: the vertex is either a cluster-head or a bridge
        :return:
        """
        if vertex not in self.adj_list.keys():
            self.adj_list[vertex] = {'pos': pos, 'edges': []}

    def add_edge(self, v1, v2):
        """
        The edges would be between cluster heads in transmission range of each other, cluster-heads and their
        cluster-members, and cluster-heads and bridges
        :param v1:
        :param v2:
        :return:
        """
        if (v1 in self.adj_list.keys()) and \
                (v2 in self.adj_list.keys()):
            self.adj_list[v1]['edges'].append(v2)
            self.adj_list[v2]['edges'].append(v1)
            return True
        return False

    def remove_edge(self, v1, v2):
        if (v1 in self.adj_list.keys()) and \
                (v2 in self.adj_list.keys()):
            try:
                self.adj_list[v1]['edges'].remove(v2)
                self.adj_list[v2]['edges'].remove(v1)
            except ValueError:
                pass
            return True
        return False

    def remove_vertex(self, vertex):
        if vertex in self.adj_list.keys():
            edges = self.adj_list[vertex]['edges']
            for other_vertex in edges:
                self.adj_list[other_vertex]['edges'].remove(vertex)
            del self.adj_list[vertex]
            return True
        return False
