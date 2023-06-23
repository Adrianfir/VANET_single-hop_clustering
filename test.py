if ('bus' in edge[0]) & ('bus' in edge[1]):
    folium.PolyLine(locations=locations, color='pink').add_to(edge_group)
elif ('veh' in edge[0]) & ('bus' in edge[1]):
    if self.veh_table.values(edge[0])['cluster_head'] is True:
        folium.PolyLine(locations=locations, color='pink').add_to(edge_group)
elif ('bus' in edge[0]) & ('veh' in edge[1]):
    if self.veh_table.values(edge[1])['cluster_head'] is True:
        folium.PolyLine(locations=locations, color='pink').add_to(edge_group)
elif ('veh' in edge[0]) & ('veh' in edge[1]):
    if self.veh_table.values(edge[0])['cluster_head'] is True:
        if self.veh_table.values(edge[1])['cluster_head'] is True:
            folium.PolyLine(locations=locations, color='pink').add_to(edge_group)
elif ('veh' in edge[0]) & ('veh' in edge[1]):
    if self.veh_table.values(edge[0])['primary_CH'] == edge[1]:
        folium.PolyLine(locations=locations, color='gray').add_to(edge_group)
elif ('veh' in edge[1]) & ('veh' in edge[1]):
    if self.veh_table.values(edge[1])['primary_CH'] == edge[0]:
        folium.PolyLine(locations=locations, color='gray').add_to(edge_group)
elif ('veh' in edge[0]) & ('bus' in edge[1]):
    if self.veh_table.values(edge[0])['primary_Ch'] == edge[1]:
        folium.PolyLine(locations=locations, color='gray').add_to(edge_group)
elif ('bus' in edge[0]) & ('veh' in edge[1]):
    if self.veh_table.values(edge[1])['primary_Ch'] == edge[0]:
        folium.PolyLine(locations=locations, color='gray').add_to(edge_group)
else:
    folium.PolyLine(locations=locations, color='green').add_to(edge_group)