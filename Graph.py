"""
This Class is for building a Graph to show the connections of the Cluster-Heads and Bridges.
Rhis Graoh is based on adjacency-List rather than a matrix as the number of vehicles in the
Greater Toronto Area (GTA) would affect the space complexity
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"
__all__ = ['Graph']

import Hash


class Graph:

    def __init__(self, head):
        self.adj_list = {head: []}

    def print_graph(self):
        for vertex in self.adj_list:
            print(vertex, ':', self.adj_list[vertex])

    def add_vertex(self, vertex):
        """
        this method is for adding a a new vertex
        :param vertex: the vertex is either a cluster-head or a bridge
        :return:
        """
        if vertex not in self.adj_list.keys():
            self.adj_list[vertex] = []

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

# a = Graph('test1')
# a.add_vertex('test2')
# a.add_edge('test', 'test1')
# a.print_graph()
# b = Hash.HashTable(20)
# b.set_item('bus01', {'a': 12, 'g': a})
# b.print_hash_table()

# import networkx as nx
# import matplotlib.pyplot as plt
#
# # Create an instance of the Graph class
# graph = Graph("A")
#
# # Add vertices and edges
# graph.add_vertex("B")
# graph.add_vertex("C")
# graph.add_vertex("D")
# graph.add_edge("A", "B")
# graph.add_edge("B", "C")
# graph.add_edge("C", "D")
# graph.add_edge("D", "A")
#
# # Create a networkx graph
# G = nx.Graph(graph.adj_list)
#
# # Plot the graph
# nx.draw(G, with_labels=True, node_color='lightblue', node_size=500, font_weight='bold')
#
# # Display the graph
# plt.show()


###### To plot based on the locations


# import networkx as nx
# import matplotlib.pyplot as plt
#
# class Graph:
#     def __init__(self, head):
#         self.adj_list = {head: {'pos': (0, 0), 'edges': []}}
#
#     def print_graph(self):
#         for vertex in self.adj_list:
#             print(vertex, ':', self.adj_list[vertex]['edges'])
#
#     def add_vertex(self, vertex, pos):
#         if vertex not in self.adj_list.keys():
#             self.adj_list[vertex] = {'pos': pos, 'edges': []}
#
#     def add_edge(self, v1, v2):
#         if v1 in self.adj_list.keys() and v2 in self.adj_list.keys():
#             self.adj_list[v1]['edges'].append(v2)
#             self.adj_list[v2]['edges'].append(v1)
#             return True
#         return False
#
# # Create an instance of the Graph class
# graph = Graph("A")
#
# # Add vertices and edges with coordinates
# graph.add_vertex("A", (40.7128, -74.0060))  # New York
# graph.add_vertex("B", (34.0522, -118.2437))  # Los Angeles
# graph.add_vertex("C", (51.5074, -0.1278))  # London
# graph.add_vertex("D", (48.8566, 2.3522))  # Paris
#
# graph.add_edge("A", "B")
# graph.add_edge("B", "C")
# graph.add_edge("C", "D")
#
# # Create a networkx graph
# G = nx.Graph()
#
# # Add nodes and edges with coordinates to the networkx graph
# for vertex, data in graph.adj_list.items():
#     G.add_node(vertex, pos=data['pos'])
#     for edge in data['edges']:
#         G.add_edge(vertex, edge)
#
# # Extract positions from node attributes
# pos = nx.get_node_attributes(G, 'pos')
#
# # Plot the graph on a map
# plt.figure(figsize=(10, 8))
# nx.draw(G, pos, with_labels=True, node_size=500, font_weight='bold', alpha=0.7, node_color='lightblue', edge_color='gray', width=1.0)
#
# # Show the plot
# plt.show()
