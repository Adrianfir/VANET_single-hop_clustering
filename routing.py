"""
This class is design for implementing routing in clustered urban VANETs
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

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
        self.message_id = 0
        self.on_way_packets = dict()
        self.pck_queue = 0
        self.delivered_packets = list()
        self.delivered_messages = list()
        self.link_cap = dict()
        self.pack_queue = 0


    def gen_message(self, s_id, d_id):
        message = ("Hey!" + "I" + " am" + " at " + str(self.cluster.veh_table.values(s_id)['lat'],
                                                       self.cluster.veh_table.values(s_id)['long']) + "! I" +  "'ll" +
                   " be" + " there" + " soon!!")
        self.cluster.values(s_id)['messages_sent'].append(dict(mess=message, message_id =self.message_id, source=s_id,
                                                               dest=d_id, s_time=self.cluster.time, d_time=None,
                                                               del_check=0, hops=0
                                                               )
                                                          )

        self.sent_messages.append(dict(mess=message, message_id=self.message_id, source=s_id, dest=d_id,
                                       s_time=self.cluster.time, d_time=None, del_check=0, hops=0
                                       )
                                  )

        pck_dict = dict()
        for i in range(len(message)):
            pck_dict[i] = dict(pck=message[i], message_id=self.message_id, source=s_id, dest=d_id,
                               s_time=self.cluster.time, d_time=None, del_check=0, hops=0)

            self.cluster.values(s_id)['packets_to_pass'][self.cluster.values(s_id)['pck_queue']]:pck_dict[i]
            self.cluster.values(s_id)['pck_queue'] += 1

            self.on_way_packets[self.pck_queue] = dict(current_node=s_id, pck=pck_dict[i])
            self.pck_queue += 1
            self.message_id += 1

    def routing(self):
        self.link_cap = dict(zip(self.cluster.net_graph.edges(),
                                 [self.configs.link_limit for l in range(len(self.cluster.net_graph.edges()))]))

        on_way_packets = self.on_way_packets.copy()
        for pack in on_way_packets.keys():
            if pack['del_check'] == 1:
                self.on_way_packets.pop(pack)

            else:
                current_node = on_way_packets[pack]['current_node']
                if current_node is on_way_packets[pack]['pack']['s_id']:
                    (current_node, self.cluster.veh_table,
                     self.cluster.bus_table) = util_routing.intra_pass_packet(current_node, self.cluster.veh_table,
                                                   self.cluster.bus_table, self.configs)
                else:
                    (current_node, self.cluster.veh_table,
                     self.cluster.bus_table) = util_routing.extra_pass_packet(current_node, self.cluster.veh_table,
                                                   self.cluster.bus_table, self.configs)

        return self