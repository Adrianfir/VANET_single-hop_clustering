"""
This .py file is for adding arguments to argparse
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import argparse
import pathlib
import xml.dom.minidom


class Inputs:
    def __init__(self):
        # Constants that we need to pass as arguments
        trace_path = str(pathlib.Path(__file__).parent.parent.absolute().
                         joinpath('small_data_Richmondhill', 'sumoTrace_geo.xml'))
        # trace_path_big_data = str(pathlib.Path(__file__).parent.parent.parent.absolute().
        #                           joinpath('big_data_Richmondhill', 'sumoTrace_geo.xml'))
        sumo_trace = xml.dom.minidom.parse(trace_path)
        fcd = sumo_trace.documentElement
        times = fcd.getElementsByTagName('timestep')
        area = dict(min_lat=43.586568,
                    min_long=-79.540771,
                    max_lat=44.012923,
                    max_long=-79.238069)
        trans_range = 300
        start_time = 0
        counter = 5
        map_zoom = 15.3
        center_loc = [43.868283, -79.441418]
        fps = 10

        parser = argparse.ArgumentParser()
        parser.add_argument('--area', type=dict, default=area,
                            help='this argument is the latitudes and longitudes of the understudied area')
        parser.add_argument('--n_cars', type=int, default=8000,
                            help='this is an assumption regarding the number of cars in order to create a HashTabel')
        parser.add_argument('--sumo_trace', type=xml.dom.minidom.Document, default=sumo_trace,
                            help='This is the sumo_trace file that includes all the data we need from the traffic')
        parser.add_argument('--fcd', type=xml.dom.minidom.Element, default=fcd,
                            help='Floating Car Data (FCD) from sumoTrace.xml file')
        parser.add_argument('--times', type=xml.dom.minidom.NodeList, default=times,
                            help='includes data for all seconds')
        parser.add_argument('--trans_range', type=int, default=trans_range,
                            help='this is the transmission range considered in this project and it can be up to 2000')
        parser.add_argument('--start_time', type=int, default=start_time,
                            help='This is the time that the initial values would be extract from sumo_trace.xml file')
        parser.add_argument('--counter', type=int, default=counter,
                            help='This is the a counter for vehicle to make themselves as CH if they can not'
                                 ' find any Ch or nearby stand-alone vehicles to create a cluster')
        parser.add_argument('--map_zoom', type=float, default=map_zoom,
                            help='This is the amount to have a specific zoom on the map')
        parser.add_argument('--center_loc', type=float, default=center_loc,
                            help='The specific center location of the map')
        parser.add_argument('--fps', type=float, default=fps, help='frame per second')
        self.parser = parser

    def get_parser(self):
        """
        this methods can be used on order to return the parser and be used in config file
        :return: it returns the parser
        """
        return self.parser.parse_args()
