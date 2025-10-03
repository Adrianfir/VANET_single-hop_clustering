"""

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"


from configs.config import Configs as configs
import utils.util as util
import utils.util_routing as util_routing
class Route:
    def __init__(self, cluster):
        self.cluster = cluster
        self.configs = configs
        self.senders = list()
        self.receivers = list()
        self.passers = list()
        self.drops = list()
        self.drop_time = 10
    def gen_message(self, veh_table, s_id, d_id):
        return util_routing.gen_message(veh_table, s_id, d_id, self.cluster.time)

    def route


