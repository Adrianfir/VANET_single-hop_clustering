import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from graph import Graph


def show_graph(self):
    """
    This function will illustrate the self.net_graph
    :return: Graph
    """
    G = nx.Graph()
    # Add nodes and edges with coordinates to the networkx graph
    node_colors = dict()
    for vertex, data in self.net_graph.adj_list.items():
        G.add_node(vertex, pos=data['pos'])
        for edge in list(set(data['edges'])):
            G.add_edge(vertex, edge)

    # Extract positions from node attributes
    pos = nx.get_node_attributes(G, 'pos')

    # Create a GeoDataFrame from the graph node positions
    gdf_nodes = gpd.GeoDataFrame(pos.items(), columns=['node', 'geometry'])
    gdf_nodes['x'] = gdf_nodes['geometry'].apply(lambda geom: geom.x)
    gdf_nodes['y'] = gdf_nodes['geometry'].apply(lambda geom: geom.y)

    # Create a GeoDataFrame from the graph edges
    gdf_edges = gpd.GeoDataFrame(list(G.edges()), columns=['start', 'end'])
    gdf_edges = gdf_edges.merge(gdf_nodes, left_on='start', right_on='node').merge(gdf_nodes, left_on='end', right_on='node')
    gdf_edges['geometry'] = gpd.points_from_xy(gdf_edges['x'], gdf_edges['y'])
    gdf_edges = gpd.GeoDataFrame(gdf_edges, geometry='geometry')

    # Plot the graph using GeoPandas
    fig, ax = plt.subplots()
    gdf_edges.plot(ax=ax, color='gray')
    gdf_nodes.plot(ax=ax, markersize=10, color='lightblue')
    plt.title('Graph')
    plt.axis('off')
    plt.show()

