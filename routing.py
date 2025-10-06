"""
This class is design for implementing routing in clustered urban VANETs
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

from IPython.core.magic import on_off

import utils.util_routing as util_routing


class Routing:
    def __init__(self, cluster, configs):
        self.cluster = cluster
        self.configs = configs
        self.senders = list()
        self.receivers = list()
        self.passers = dict()
        self.drops = list()
        self.sent_messages = list()
        self.on_way_packets = dict()
        self.pck_queue = 0
        self.delivered_packets = list()
        self.delivered_messages = list()
        self.link_cap = dict()
        self.pack_queue = 0


    def gen_message(self, veh_table, s_id, d_id):
        message = util_routing.gen_message(veh_table, s_id, d_id, self.cluster.time)
        self.cluster.values(s_id)['messages_sent'].add(dict(mess=message,
                                                               source=s_id,
                                                               dest=d_id,
                                                               s_time=self.cluster.time,
                                                               d_time=None,
                                                               del_check=0,
                                                               hops=0
                                                               ))

        self.sent_messages.append(dict(mess=message,
                                       source=s_id,
                                       dest=d_id,
                                       s_time=self.cluster.time,
                                       d_time=None,
                                       del_check=0,
                                       hops=0
                                       ))

        pck_dict = dict()
        for i in range(len(message)):
            pck_dict[i] = dict(pck=message[i],
                               source=s_id,
                               dest=d_id,
                               s_time=self.cluster.time,
                               d_time=None,
                               hops=0)
            self.cluster.values(s_id)['packets_to_pass'][self.cluster.values(s_id)['pck_queue']]:pck_dict[i]
            self.cluster.values(s_id)['pck_queue'] += 1

            self.on_way_packets[self.pck_queue] = dict(current_node=s_id, pck=pck_dict[i])
            self.pck_queue += 1

    def routing(self):
        self.link_cap = dict(zip(self.cluster.net_graph.edges(),
                                 [self.configs.link_limit for l in range(len(self.cluster.net_graph.edges()))]))

        on_way_packets =
        for pack in on_way_packets:
            if pack['check'] == 1:
                self.on_way_packets.get()

        return self