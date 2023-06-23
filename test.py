import networkx as nx
import plotly.graph_objects as go

class Graph:
    def __init__(self, vertex, pos):
        self.adj_list = {vertex: {'pos': pos, 'edges': []}}

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

    def remove_edge(self, v1, v2):
        if v1 in self.adj_list.keys() and v2 in self.adj_list.keys():
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


# Create an instance of the Graph
graph = Graph("A", (40.7128, -74.0060))  # New York

# Add vertices and edges to the graph
graph.add_vertex("B", (34.0522, -118.2437))  # Los Angeles
graph.add_vertex("C", (51.5074, -0.1278))  # London
graph.add_vertex("D", (48.8566, 2.3522))  # Paris

graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "D")

# Create a new networkx graph
G = nx.Graph()

# Add nodes and edges to the networkx graph
for vertex, data in graph.adj_list.items():
    G.add_node(vertex, pos=data['pos'])
    for edge in data['edges']:
        G.add_edge(vertex, edge)

# Extract node positions
pos = nx.get_node_attributes(G, 'pos')

# Create edge trace
edge_trace = go.Scattergeo(
    lat=[pos[edge[0]][0] for edge in G.edges()],
    lon=[pos[edge[0]][1] for edge in G.edges()],
    mode='lines',
    line=dict(width=1, color='red'),
)

# Create node trace
node_trace = go.Scattergeo(
    lat=[pos[node][0] for node in G.nodes()],
    lon=[pos[node][1] for node in G.nodes()],
    mode='markers',
    marker=dict(size=10, color='lightblue'),
    text=list(G.nodes()),
    hoverinfo='text'
)

# Create figure
fig = go.Figure(data=[edge_trace, node_trace])

# Set layout
fig.update_layout(
    title_text='Graph on Map',
    showlegend=False,
    geo=dict(
        projection_type='natural earth'
    )
)

# Show the figure
fig.show()
