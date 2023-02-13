"""
This .py file is for adding arguments to argparse
"""

import argparse
import pathlib


class GetConsts:
    def __init__(self):
        trace_path = pathlib.Path(__file__).parent.absolute().\
            joinpath('small_data_Richmondhill').joipath('sumoTrace_geo.xml')
        area = dict(min_lat=43.586568,
                    min_long=-79.540771,
                    max_lat=44.012923,
                    max_long=-79.238069)

        parser = argparse.ArgumentParser(decriptions="this is for gathering the parameters of VANET project")
        parser.add_argument('--xml_path', type='str', default=trace_path,
                            help='this is address to the SUMOTrace_geo.xml files')
        parser.add_argument('--area', type=dict, default=area,
                            help='this argument is the latitudes and longitudes of the understudied area')
        parser.add_argument('--n_cars', type=int, default=8000,
                            help='this is an assumption regarding the number of cars in order to create a HashTabel')

        self.parser = parser

    def get_parser(self):
        """
        this methos can be used on order to return the parser and be used in config file
        :return: it returns the parser
        """
        return self.parser.parse_args()
