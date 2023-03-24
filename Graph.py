"""
This Class is for building a Graph to show the connections of the Cluster-Heads and Bridges.
Rhis Graoh is based on adjacency-List rather than a matrix as the number of vehicles in the
Greater Toronto Area (GTA) would affect the space complexity
"""
__author__ = "Pouya 'Adrian' Firouzmakan"
__all__ = []


class Graph:

    def __init__(self):
        self.adj_list = {}

    def print_graph(self):
        for vertex in self.adj_list:
            print(vertex, ':', self.adj_list[vertex])

    def add_vertex(self, vertex):
        """
        :param vertex: the vertex is either a cluster-head or a bridge
        :return:
        """
        for v in vertex:
            if v not in self.adj_list.keys():
                self.adj_list[v] = []
                return True
            return False

    def add_edge(self, v1, v2):
        """
        The edges would be between cluster heads in transmission range of each other, cluster-heads and their
        cluster-members, and cluster-heads and bridges
        :param v1:
        :param v2:
        :return:
        """
        if v1 in self.adj_list.keys() and v2 in self.adj_list.keys():
            self.adj_list[v1].append(v2)
            self.adj_list[v2].append(v1)
            return True
        return False

    def remove_edge(self, v1, v2):
        if v1 in self.adj_list.keys() and v2 in self.adj_list.keys():
            try:
                self.adj_list[v1].remove(v2)
                self.adj_list[v2].remove(v1)
            except ValueError:
                pass
            return True
        return False

    def remove_vertex(self, vertex):
        if vertex in self.adj_list.keys():
            for other_vertex in self.adj_list[vertex]:
                self.adj_list[other_vertex].remove(vertex)
            del self.adj_list[vertex]
            return True
        return False


# a = Graph()
# a.print_graph()
# a.add_vertex(['a', 'b'])
