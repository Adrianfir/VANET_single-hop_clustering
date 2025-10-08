"""
This class is design for implementing routing in clustered urban VANETs
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import utils.util_routing as util_routing


class Routing:
    def __init__(self, cluster, configs):
        self.cluster = cluster
        self.configs = configs
        # self.senders = list()
        # self.receivers = list()
        self.drops = list()
        self.sent_messages = dict()
        self.message_id = 0
        self.on_way_packets = dict()
        self.pck_queue = 0
        self.delivered_packets = list()
        self.delivered_messages = list()
        self.link_cap = dict()


    def gen_message(self, s_id, d_id):
        message = ("Hey!" + "I" + " am" + " at " + str(self.cluster.veh_table.values(s_id)['lat'],
                                                       self.cluster.veh_table.values(s_id)['long']) + "! I" +  "'ll" +
                   " be" + " there" + " soon!!")
        self.cluster.values(s_id)['messages_sent']['message_id'] = dict(mess=message, source=s_id, dest=d_id,
                                                                        s_time=self.cluster.time, d_time=None,
                                                                        hops=0
                                                                        )


        self.sent_messages['message_id'] = dict(mess=message, source=s_id, dest=d_id, s_time=self.cluster.time,
                                                d_time=None, hops=0
                                                )


        pck_dict = dict()
        for i in range(len(message)):
            pck_dict[i] = dict(pck=message[i], message_id=self.message_id, source=s_id, dest=d_id, current_node=s_id,
                               s_time=self.cluster.time, d_time=None, del_check=0, hops=list())

            self.cluster.values(s_id)['packets_to_pass'][self.cluster.values(s_id)['pck_queue']] = pck_dict[i]
            self.on_way_packets[self.pck_queue] = pck_dict[i]
            self.pck_queue += 1
            self.message_id += 1

    def routing(self):
        self.link_cap = dict(zip(self.cluster.net_graph.edges(),
                                 [self.configs.link_limit for l in range(len(self.cluster.net_graph.edges()))]))

        on_way_packets = self.on_way_packets.copy()
        for pack in on_way_packets.keys():
            current_node = on_way_packets[pack]['current_node']
            if current_node in self.cluster.stand_alone: # if the node is a SAV now, have the packets in its buffer
                continue
            if current_node is on_way_packets[pack]['source']:
                ch_id = self.cluster.values(current_node)['primary_ch']
                if self.link_cap[sorted((current_node, ch_id))] > 0:
                    if 'bus' in ch_id:
                        q_link = util_routing.intra_q_link(current_node, ch_id, self.cluster.veh_table,
                                                           self.cluster.bus_table, self.configs)
                        if q_link >= self.configs.qol_thresh:
                            (current_node, self.cluster.veh_table,
                             self.cluster.bus_table) = util_routing.pass_packet(current_node, self.cluster.veh_table,
                                                           self.cluster.bus_table, self.configs)
                    else:
                        (current_node, self.cluster.veh_table,
                         self.cluster.bus_table) = util_routing.extra_pass_packet(current_node, self.cluster.veh_table,
                                                       self.cluster.bus_table, self.configs)

                    self.link_cap[sorted((current_node, ch_id))] -= 1

                else:
                    pass

            check_receiver = util_routing.check_receiver(on_way_packets, pack, self.cluster.veh_table,
                                                         self.cluster.bus_table, current_node)
            if check_receiver == 1:
                util_routing.pack_delivered(self.cluster.veh_table, self.cluster.bus_table, pack, self.on_way_packets,
                                                self.delivered_packets)

            elif check_receiver == 0:
                util_routing.pack_delivered(self.cluster.veh_table, self.cluster.bus_table, pack, self.on_way_packets,
                                            self.delivered_packets)