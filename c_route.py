from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from configs import Config
from model import EdgeInfo, MessageEvent, Packet, VehicleState
from util import (
    build_edge_vehicle_index,
    direction_alignment_score,
    direction_toward_target_angle,
    euclidean,
    group_messages_by_time,
    invert_normalize,
    message_dest_xy_from_latlon,
    nearest_vehicle_distance_on_edge,
    normalize,
    point_to_polyline_distance,
    polyline_midpoint,
)


class HeroRouter:
    """
    Trace-driven adaptation of HERO:
      1) road-segment selection (inter-routing)
      2) vehicle selection (intra-routing)

    This implementation is packet-based.
    """

    def __init__(
        self,
        cfg: Config,
        edges_by_id: Dict[str, EdgeInfo],
        outgoing_edges_by_node: Dict[str, List[str]],
        vehicles_by_time: Dict[int, Dict[str, VehicleState]],
        messages: List[MessageEvent],
        ref_lat: float,
        ref_lon: float,
    ) -> None:
        self.cfg = cfg
        self.edges_by_id = edges_by_id
        self.outgoing_edges_by_node = outgoing_edges_by_node
        self.vehicles_by_time = vehicles_by_time
        self.messages = messages
        self.messages_by_time = group_messages_by_time(messages)

        self.ref_lat = ref_lat
        self.ref_lon = ref_lon

        self.active_packets: Dict[str, Packet] = {}
        self.finished_packets: Dict[str, Packet] = {}
        self.forward_log: List[dict] = []

        self.vehicle_load_by_time_holder = defaultdict(lambda: defaultdict(int))

    def run(self) -> dict:
        if not self.vehicles_by_time:
            return self._empty_metrics()

        t_min = self.cfg.START_TIME + self.cfg.ROUTING_START_AFTER
        t_max = self.cfg.START_TIME + (5/6 * (self.cfg.END_TIME - self.cfg.START_TIME))

        for t in range(t_min, t_max + 1):
            vehicles = self.vehicles_by_time.get(t, {})
            self._inject_new_packets(t, vehicles)
            self._step_packets(t, vehicles)

        # Drop remaining active packets after trace end
        for packet in self.active_packets.values():
            packet.dropped = True
            self.finished_packets[packet.packet_uid] = packet
        self.active_packets.clear()

        return self._compute_metrics()

    def _inject_new_packets(self, t: int, vehicles: Dict[str, VehicleState]) -> None:
        events = self.messages_by_time.get(t, [])
        if not events:
            return

        for event in events:
            # Source must exist in current timestep to inject packets
            if event.source not in vehicles:
                continue

            for pkt_name in event.packet_names:
                uid = f"{event.time}:{event.message_id}:{pkt_name}"
                packet = Packet(
                    packet_uid=uid,
                    message_id=event.message_id,
                    packet_name=pkt_name,
                    source=event.source,
                    dest=event.dest,
                    start_time=t,
                    current_holder=event.source,
                )

                if event.source in vehicles:
                    packet.mark_holder(event.source)

                packet.last_known_dest_xy = self._get_destination_xy(event, t, vehicles)
                self.active_packets[uid] = packet

                self.vehicle_load_by_time_holder[t][event.source] += 1

    def _step_packets(self, t: int, vehicles: Dict[str, VehicleState]) -> None:
        if not vehicles:
            for uid, packet in list(self.active_packets.items()):
                if t - packet.start_time > self.cfg.PACKET_TTL_SECONDS:
                    packet.dropped = True
                    self.finished_packets[uid] = packet
                    del self.active_packets[uid]
            return

        edge_vehicle_index = build_edge_vehicle_index(vehicles)

        for uid, packet in list(self.active_packets.items()):
            if packet.delivered or packet.dropped:
                continue

            if t - packet.start_time > self.cfg.PACKET_TTL_SECONDS:
                packet.dropped = True
                self.finished_packets[uid] = packet
                del self.active_packets[uid]
                continue

            # If holder vanished from current timestep, packet cannot move now.
            if packet.current_holder not in vehicles:
                continue

            holder = vehicles[packet.current_holder]

            # Immediate success if holder is destination
            if holder.veh_id == packet.dest:
                packet.delivered = True
                packet.delivery_time = t
                self.finished_packets[uid] = packet
                del self.active_packets[uid]
                continue

            hops_this_second = 0
            while hops_this_second < self.cfg.MAX_HOPS_PER_SECOND:
                current_holder_id = packet.current_holder
                if current_holder_id is None or current_holder_id not in vehicles:
                    break

                holder = vehicles[current_holder_id]

                # Destination direct delivery if within transmission range
                direct_delivery = self._try_direct_delivery(packet, holder, t, vehicles)
                if direct_delivery:
                    self.finished_packets[uid] = packet
                    del self.active_packets[uid]
                    break

                target_xy = self._resolve_packet_target_xy(packet, t, vehicles)
                if target_xy is None:
                    break

                selected_edge_id = self._select_next_edge(holder, target_xy, edge_vehicle_index)
                next_holder_id = self._select_next_vehicle(
                    packet=packet,
                    holder=holder,
                    selected_edge_id=selected_edge_id,
                    target_xy=target_xy,
                    vehicles=vehicles,
                )

                if next_holder_id is None or next_holder_id == current_holder_id:
                    break

                packet.hops += 1
                packet.mark_holder(next_holder_id)

                self.forward_log.append(
                    {
                        "time": t,
                        "packet_uid": packet.packet_uid,
                        "from_holder": current_holder_id,
                        "to_holder": next_holder_id,
                        "selected_edge": selected_edge_id,
                        "cum_hops": packet.hops,
                    }
                )

                hops_this_second += 1

                if next_holder_id == packet.dest:
                    packet.delivered = True
                    packet.delivery_time = t
                    self.finished_packets[uid] = packet
                    del self.active_packets[uid]
                    break

    def _try_direct_delivery(
        self,
        packet: Packet,
        holder: VehicleState,
        t: int,
        vehicles: Dict[str, VehicleState],
    ) -> bool:
        if packet.dest not in vehicles:
            return False

        dest_state = vehicles[packet.dest]
        if euclidean(holder.pos, dest_state.pos) <= self.cfg.COMMUNICATION_RANGE_M:
            packet.hops += 1
            packet.mark_holder(packet.dest)
            packet.delivered = True
            packet.delivery_time = t
            return True
        return False

    def _resolve_packet_target_xy(
        self,
        packet: Packet,
        t: int,
        vehicles: Dict[str, VehicleState],
    ) -> Optional[Tuple[float, float]]:
        if packet.dest in vehicles:
            packet.last_known_dest_xy = vehicles[packet.dest].pos
            return packet.last_known_dest_xy
        return packet.last_known_dest_xy

    def _get_destination_xy(
        self,
        event: MessageEvent,
        t: int,
        vehicles: Dict[str, VehicleState],
    ) -> Optional[Tuple[float, float]]:
        if event.dest in vehicles:
            return vehicles[event.dest].pos
        if self.cfg.FALLBACK_TO_DEST_LOCATION:
            return message_dest_xy_from_latlon(
                event.d_loc_lat,
                event.d_loc_lon,
                self.ref_lat,
                self.ref_lon,
            )
        return None

    def _select_next_edge(
        self,
        holder: VehicleState,
        target_xy: Tuple[float, float],
        edge_vehicle_index: Dict[str, List[VehicleState]],
    ) -> str:
        current_edge = self.edges_by_id.get(holder.edge_id)
        if current_edge is None:
            return holder.edge_id

        candidate_edge_ids = self.outgoing_edges_by_node.get(current_edge.to_node, [])
        if not candidate_edge_ids:
            return current_edge.edge_id

        sdd_raw = []
        cd_raw = []
        valid_candidates = []

        holder_to_target_angle = direction_toward_target_angle(holder.pos, target_xy)

        for edge_id in candidate_edge_ids:
            edge = self.edges_by_id.get(edge_id)
            if edge is None:
                continue

            valid_candidates.append(edge_id)

            # --- SDD-like terms ---
            midpoint = polyline_midpoint(edge.shape) if edge.shape else holder.pos
            dist_mid_to_target = euclidean(midpoint, target_xy)

            if edge.shape and len(edge.shape) >= 2:
                edge_dir_angle = direction_toward_target_angle(edge.shape[0], edge.shape[-1])
            else:
                edge_dir_angle = holder_to_target_angle

            angle_align = direction_alignment_score(edge_dir_angle, holder_to_target_angle)
            seg_len = edge.length

            # HERO paper uses shortest-distance-related components.
            # Here we make lower distance, better alignment, shorter segment favorable.
            sdd_raw.append((dist_mid_to_target, angle_align, seg_len))

            # --- CD-like terms ---
            vehs_on_edge = edge_vehicle_index.get(edge_id, [])
            density = len(vehs_on_edge) / max(edge.length, 1.0)
            nearest_gap = nearest_vehicle_distance_on_edge(vehs_on_edge)
            # Higher density good, smaller spacing bad only if too sparse.
            cd_raw.append((density, nearest_gap))

        if not valid_candidates:
            return current_edge.edge_id

        dist_vals = [x[0] for x in sdd_raw]
        align_vals = [x[1] for x in sdd_raw]
        len_vals = [x[2] for x in sdd_raw]

        inv_dist = invert_normalize(dist_vals)
        norm_align = normalize(align_vals)
        inv_len = invert_normalize(len_vals)

        density_vals = [x[0] for x in cd_raw]
        gap_vals = [x[1] for x in cd_raw]

        norm_density = normalize(density_vals)
        inv_gap = invert_normalize([g if g != float("inf") else 1e9 for g in gap_vals])

        best_edge = valid_candidates[0]
        best_score = -1.0

        for i, edge_id in enumerate(valid_candidates):
            sdd_score = 0.45 * inv_dist[i] + 0.35 * norm_align[i] + 0.20 * inv_len[i]
            cd_score = 0.65 * norm_density[i] + 0.35 * inv_gap[i]
            total_score = self.cfg.W_SDD * sdd_score + self.cfg.W_CD * cd_score

            if total_score > best_score:
                best_score = total_score
                best_edge = edge_id

        return best_edge

    def _select_next_vehicle(
        self,
        packet: Packet,
        holder: VehicleState,
        selected_edge_id: str,
        target_xy: Tuple[float, float],
        vehicles: Dict[str, VehicleState],
    ) -> Optional[str]:
        candidates = []

        holder_target_dist = euclidean(holder.pos, target_xy)
        heading_to_target = direction_toward_target_angle(holder.pos, target_xy)

        for cand in vehicles.values():
            if cand.veh_id == holder.veh_id:
                continue

            d = euclidean(holder.pos, cand.pos)
            if d > self.cfg.COMMUNICATION_RANGE_M:
                continue

            # Must provide some progress
            cand_target_dist = euclidean(cand.pos, target_xy)
            if cand_target_dist >= holder_target_dist and cand.veh_id != packet.dest:
                continue

            candidates.append(cand)

        if not candidates:
            return None

        rel_speed_vals = []
        direction_vals = []
        buffer_vals = []
        fading_vals = []
        edge_bonus_flags = []
        # revisit_flags = []

        for cand in candidates:
            rel_speed = abs(holder.speed - cand.speed)
            rel_speed_vals.append(rel_speed)

            direction_score = direction_alignment_score(cand.angle_deg, heading_to_target)
            direction_vals.append(direction_score)

            load = self.vehicle_load_by_time_holder[holder.time][cand.veh_id]
            available_buffer = max(
                0,
                self.cfg.VEHICLE_BUFFER_CAPACITY_PACKETS - load,
            )
            buffer_vals.append(available_buffer)

            distance = euclidean(holder.pos, cand.pos)
            fading_like = 1.0 / (1.0 + distance)
            fading_vals.append(fading_like)

            edge_bonus_flags.append(1.0 if cand.edge_id == selected_edge_id else 0.0)
            # revisit_flags.append(1.0 if cand.veh_id in packet.recent_holders else 0.0)

        inv_rel_speed = invert_normalize(rel_speed_vals)
        norm_direction = normalize(direction_vals)
        norm_buffer = normalize(buffer_vals)
        norm_fading = normalize(fading_vals)

        best_id = None
        best_score = -1.0

        for i, cand in enumerate(candidates):
            score = (
                self.cfg.W_REL_SPEED * inv_rel_speed[i]
                + self.cfg.W_DIRECTION * norm_direction[i]
                + self.cfg.W_BUFFER * norm_buffer[i]
                + self.cfg.W_FADING * norm_fading[i]
                + self.cfg.EDGE_MATCH_BONUS * edge_bonus_flags[i]
                # - self.cfg.REVISIT_PENALTY * revisit_flags[i]
            )

            if cand.veh_id == packet.dest:
                score += 1.0

            if score > best_score:
                best_score = score
                best_id = cand.veh_id

        if best_id is not None:
            self.vehicle_load_by_time_holder[holder.time][best_id] += 1

        return best_id

    def _empty_metrics(self) -> dict:
        return {
            "n_packets_total": 0,
            "n_packets_delivered": 0,
            "packet_delivery_ratio": 0.0,
            "average_end_to_end_delay_seconds": None,
            "average_hops_delivered_packets": None,
            "delivered_packet_uids": [],
            "dropped_packet_uids": [],
        }

    def _compute_metrics(self) -> dict:
        packets = list(self.finished_packets.values())

        n_total = len(packets)
        delivered = [p for p in packets if p.delivered]
        dropped = [p for p in packets if p.dropped]

        n_delivered = len(delivered)
        pdr = n_delivered / n_total if n_total else 0.0

        avg_delay = None
        if delivered:
            avg_delay = sum(p.delay() for p in delivered if p.delay() is not None) / len(delivered)

        avg_hops = None
        if delivered:
            avg_hops = sum(p.hops for p in delivered) / len(delivered)

        return {
            "n_packets_total": n_total,
            "n_packets_delivered": n_delivered,
            "packet_delivery_ratio": pdr,
            "average_end_to_end_delay_seconds": avg_delay,
            "average_hops_delivered_packets": avg_hops,
            "delivered_packet_uids": [p.packet_uid for p in delivered],
            "dropped_packet_uids": [p.packet_uid for p in dropped],
        }

    def get_packet_rows(self) -> List[dict]:
        rows = []
        for packet in self.finished_packets.values():
            rows.append(
                {
                    "packet_uid": packet.packet_uid,
                    "message_id": packet.message_id,
                    "packet_name": packet.packet_name,
                    "source": packet.source,
                    "dest": packet.dest,
                    "start_time": packet.start_time,
                    "delivered": packet.delivered,
                    "dropped": packet.dropped,
                    "delivery_time": packet.delivery_time,
                    "delay_seconds": packet.delay(),
                    "hops": packet.hops,
                    "path": "->".join(packet.path),
                }
            )
        return rows

    def get_forward_log_rows(self) -> List[dict]:
        return list(self.forward_log)