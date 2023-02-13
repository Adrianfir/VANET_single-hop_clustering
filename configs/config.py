from options.constants import GetConsts


class Configs:
    def __init__(self) -> object:
        self.config = GetConsts.get_parser()


a = Configs()
