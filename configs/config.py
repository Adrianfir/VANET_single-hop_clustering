from options.constants import Inputs


class Configs:
    def __init__(self) -> object:
        consts = Inputs()
        self.config = consts.get_parser()