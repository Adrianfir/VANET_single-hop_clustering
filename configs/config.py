"""
This config.py will reflect the constants and inputs in options/constants.py
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

from options.constants import Inputs


class Configs:
    def __init__(self) -> object:
        consts = Inputs()
        self.config = consts.get_parser()
