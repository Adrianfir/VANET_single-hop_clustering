"""

"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

from queue import Queue
import random

from configs.config import Configs as configs
import utils.util as util
import utils.util_routing as util_routing


class Routing:
    def __init__(self, cluster):
        self.cluster = cluster
        self.configs = configs
        self.senders = list()
        self.receivers = list()
        self.passers = list()
        self.drops = list()
        self.sent_messages = list()
        self.on_way_packets = Queue()
        self.delivered_packets = list()
        self.delivered_messages = list()


    def gen_message(self, veh_table, s_id, d_id):
        message = util_routing.gen_message(veh_table, s_id)
        self.cluster.values(s_id)['messages_to_send'].add(dict(mess=message, source=s_id, dest=d_id,
                                                               s_time=self.cluster.time, d_time=None, hops=0))
        self.sent_messages.add(dict(mess=message, source=s_id, dest=d_id,
                                    s_time=self.cluster.time, d_time=None, hops=0))

        pck_dict = dict()
        for i in range(len(message)):
            pck_dict[i] = dict(pck=message[i], source=s_id, dest=d_id, s_time=self.cluster.time, d_time=None, hops=0)
            self.cluster.values(s_id)['packets_to_sent'].put(pck_dict[i])
            self.on_way_packets.put(dict(current_node=s_id, pck=pck_dict[i]))

    def routing(self):
        for pack in self.on_way_packets:

        return self