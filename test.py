import networkx as nx
import matplotlib.pyplot as plt

class Graph:
    def __init__(self, head):
        self.adj_list = {head: {'pos': (0, 0), 'edges': []}}

    def print_graph(self):
        for vertex in self.adj_list:
            print(vertex, ':', self.adj_list[vertex]['edges'])

    def add_vertex(self, vertex, pos):
        if vertex not in self.adj_list.keys():
            self.adj_list[vertex] = {'pos': pos, 'edges': []}

    def add_edge(self, v1, v2):
        if v1 in self.adj_list.keys() and v2 in self.adj_list.keys():
            self.adj_list[v1]['edges'].append(v2)
            self.adj_list[v2]['edges'].append(v1)
            return True
        return False

# Create an instance of the Graph class
graph = Graph("A")

# Add vertices and edges with coordinates
graph.add_vertex("A", (40.7128, -74.0060))  # New York
graph.add_vertex("B", (34.0522, -118.2437))  # Los Angeles
graph.add_vertex("C", (51.5074, -0.1278))  # London
graph.add_vertex("D", (48.8566, 2.3522))  # Paris

graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "D")

# Create a networkx graph
G = nx.Graph()

# Add nodes and edges with coordinates to the networkx graph
for vertex, data in graph.adj_list.items():
    G.add_node(vertex, pos=data['pos'])
    for edge in data['edges']:
        G.add_edge(vertex, edge)

# Extract positions from node attributes
pos = nx.get_node_attributes(G, 'pos')

# Plot the graph on a map
plt.figure(figsize=(10, 8))
nx.draw(G, pos, with_labels=True, node_size=500, font_weight='bold', alpha=0.7, node_color='lightblue', edge_color='gray', width=1.0)

# Show the plot
plt.show()