"""
This .py file is for adding arguments to argparse
"""

import argparse
import pathlib
import xml.dom.minidom


class Inputs:
    def __init__(self):
        # Constants that we need to pass as arguments
        trace_path = str(pathlib.Path(__file__).parent.parent.absolute().
                         joinpath('small_data_Richmondhill').joinpath('sumoTrace_geo.xml'))
        sumo_trace = xml.dom.minidom.parse(trace_path)
        fcd = sumo_trace.documentElement
        times = fcd.getElementsByTagName('timestep')
        area = dict(min_lat=43.586568,
                    min_long=-79.540771,
                    max_lat=44.012923,
                    max_long=-79.238069)

        parser = argparse.ArgumentParser()
        parser.add_argument('--xml_path', default=trace_path, type=str,
                            help='this is address to the SUMOTrace_geo.xml files')
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
        self.parser = parser

    def get_parser(self):
        """
        this methos can be used on order to return the parser and be used in config file
        :return: it returns the parser
        """
        return self.parser.parse_args()