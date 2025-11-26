from typing import Any, Dict, List
import math


class QRoutingHelper:
    """
    Helper for building RL states and computing rewards for perimeter-mode routing,
    using a regular zone grid (zone0, zone1, ..., zoneK).

    Assumptions:
      - veh_table.values(veh_id) returns a dict with at least:
            {
                'lat': float,
                'long': float,
                'zone': str,        # e.g. 'zone400'
                # (you may have more fields, but these are used here)
            }

      - zones_dict[zone_id] = list of vehicle_ids currently in that zone

      - Zones form a regular grid with n_cols columns:
            zone indices: 0 .. N-1
            N  = k + n_cols
            S  = k - n_cols
            E  = k + 1
            W  = k - 1
            NE = k + n_cols + 1
            NW = k + n_cols - 1
            SE = k - n_cols + 1
            SW = k - n_cols - 1

      - configs.idx_to_zone: mapping from action index -> direction label
            e.g. {0:'N', 1:'NE', 2:'E', 3:'SE', 4:'S', 5:'SW', 6:'W', 7:'NW'}

      - packet dict contains at least:
            {
                'dest': <veh_id of destination>,
                'zones': [zone_id0, zone_id1, ...],   # zone history
                's_tick': <int tick when packet created>
            }
    """

    def __init__(
        self,
        veh_table,
        bus_table,
        zones_dict,
        configs,
        n_cols: int,
        max_dist: float = 3000.0,
        max_zone_count_cap: int = 50,
        loop_window_zones: int = 4,
        delay_threshold_ticks: int = 6,
        hop_penalty: float = -0.5,
        distance_weight: float = 3.0,
        loop_penalty: float = -8.0,
        delay_penalty_per_tick: float = -1.0,
    ):
        self.veh_table = veh_table
        self.bus_table = bus_table
        self.zones = zones_dict
        self.configs = configs
        self.n_cols = n_cols

        # normalization / shaping params
        self.max_dist = max_dist
        self.max_zone_count_cap = max_zone_count_cap
        self.loop_window_zones = loop_window_zones
        self.delay_threshold_ticks = delay_threshold_ticks

        # reward parameters
        self.hop_penalty = hop_penalty
        self.distance_weight = distance_weight
        self.loop_penalty = loop_penalty
        self.delay_penalty_per_tick = delay_penalty_per_tick

    # ------------------------------------------------------------------
    # PUBLIC: build state
    # ------------------------------------------------------------------

    def build_state(
        self,
        node_id: str,
        packet: Dict[str, Any],
        current_tick: int,
    ) -> List[float]:
        """
        Build state vector BEFORE taking the next action (zone choice).

        Features:
          - dist_norm: normalized distance to dest (0..1)
          - angle_sin, angle_cos: direction to dest (bearing)
          - neighbor_zone_counts_norm: 8 values (0..1),
                one per direction (N, NE, E, SE, S, SW, W, NW),
                based on how many vehicles are in each neighbor zone.
          - loop_flag_state: 1 if current zone was visited recently, else 0
          - age_norm: packet age (ticks / 60), clipped at 1.0
        """

        dest_id = packet["dest"]
        node_info = self.veh_table.values(node_id)

        # ---- distance to dest ----
        dist = self._distance_node_to_dest(node_id, dest_id) + 1e-6
        dist_norm = min(dist / self.max_dist, 1.0)

        # ---- angle to dest ----
        angle = self._bearing_node_to_dest(node_id, dest_id)
        angle_sin = math.sin(angle)
        angle_cos = math.cos(angle)

        # ---- neighbor counts per direction zone ----
        neighbor_counts_norm = self._neighbor_counts_per_zone(node_info)

        # ---- loop flag (state-side) ----
        current_zone_id = node_info["zone"]
        loop_flag = self._loop_flag_state(packet, current_zone_id)

        # ---- age ----
        age_ticks = current_tick - packet["s_time"]
        age_norm = min(age_ticks / 60.0, 1.0)

        state_vec: List[float] = [dist_norm, angle_sin, angle_cos]
        state_vec.extend(neighbor_counts_norm)
        state_vec.append(float(loop_flag))
        state_vec.append(age_norm)

        return state_vec

    # ------------------------------------------------------------------
    # PUBLIC: compute reward (after you move & update packet['zones'])
    # ------------------------------------------------------------------

    def compute_reward(
        self,
        prev_dist_norm: float,
        new_dist_norm: float,
        packet: Dict[str, Any],
        current_tick: int,
    ) -> float:
        """
        Compute per-step reward AFTER the packet moves to the next node,
        and AFTER you append the new zone to packet['zones'].

        Uses:
          - hop_penalty (negative)
          - distance shaping: prev_dist_norm - new_dist_norm
          - loop penalty if new zone was in the recent zone history
          - delay penalty if age > delay_threshold_ticks
        """
        reward = self.hop_penalty

        # distance shaping (positive if closer)
        dist_improvement = prev_dist_norm - new_dist_norm
        reward += self.distance_weight * dist_improvement

        # loop penalty (reward-side)
        if self._recent_zone_loop_flag(packet):
            reward += self.loop_penalty

        # delay penalty
        age_ticks = current_tick - packet["s_time"]
        if age_ticks > self.delay_threshold_ticks:
            reward += self.delay_penalty_per_tick

        return reward

    # ------------------------------------------------------------------
    # PUBLIC-ish helpers you may want to call from outside
    # ------------------------------------------------------------------

    def distance_to_dest_norm(self, node_id: str, dest_id: str) -> float:
        """Convenience: normalized distance node->dest in [0,1]."""
        d = self._distance_node_to_dest(node_id, dest_id) + 1e-6
        return min(d / self.max_dist, 1.0)

    # ------------------------------------------------------------------
    # INTERNAL: neighbor zone counts
    # ------------------------------------------------------------------

    def _zone_index(self, zone_id: Any) -> int:
        """
        Convert 'zone400' -> 400 (int).
        If you already store numeric indices separately, you can adjust this.
        """
        if isinstance(zone_id, int):
            return zone_id
        return int(str(zone_id).replace("zone", ""))

    def _neighbor_counts_per_zone(self, node_info: Dict[str, Any]) -> List[float]:
        """
        Use the regular grid structure:

          current zone index = k  (e.g., 400)
          N  = k + n_cols
          S  = k - n_cols
          E  = k + 1
          W  = k - 1
          NE = k + n_cols + 1
          NW = k + n_cols - 1
          SE = k - n_cols + 1
          SW = k - n_cols - 1

        For each direction (in configs.idx_to_zone order), we:
          - compute neighbor zone index
          - map it to 'zone<idx>'
          - get len(self.zones[zone_id]) as node count
          - normalize to [0,1] with max_zone_count_cap

        Returns:
          List[float] of length 8, in the order configs.idx_to_zone[0..7].
        """
        cur_zone_id = node_info["zone"]      # e.g. 'zone400'
        k = self._zone_index(cur_zone_id)
        n_cols = self.n_cols

        # numeric neighbor indices
        neighbor_idx_by_dir = {
            "N":  k + n_cols,
            "S":  k - n_cols,
            "E":  k + 1,
            "W":  k - 1,
            "NE": k + n_cols + 1,
            "NW": k + n_cols - 1,
            "SE": k - n_cols + 1,
            "SW": k - n_cols - 1,
        }

        # convert to zone ids
        neighbor_zone_by_dir = {
            dir_label: f"zone{idx}"
            for dir_label, idx in neighbor_idx_by_dir.items()
        }

        neighbor_counts_norm: List[float] = [0.0] * len(self.configs.idx_to_zone)

        # configs.idx_to_zone: {0:'N', 1:'NE', ...}
        for idx, dir_label in self.configs.idx_to_zone.items():
            z_id = neighbor_zone_by_dir.get(dir_label)
            if z_id is None:
                count = 0
            else:
                count = len(self.zones.get(z_id, []))

            capped = min(count, self.max_zone_count_cap)
            neighbor_counts_norm[idx] = capped / float(self.max_zone_count_cap)

        return neighbor_counts_norm

    # ------------------------------------------------------------------
    # INTERNAL: loop flags
    # ------------------------------------------------------------------

    def _loop_flag_state(
        self,
        packet: Dict[str, Any],
        current_zone_id: Any,
    ) -> int:
        """
        STATE-side loop feature.

        Called inside build_state BEFORE choosing an action.

        Returns 1 if current_zone_id appears in the recent zone history
        (last loop_window_zones entries BEFORE the current step), else 0.
        """
        zones: List[Any] = packet.get("zones", [])
        if len(zones) < 3:
            return 0

        # assuming zones[-1] is current zone, look back a short window before it
        recent = zones[-(self.loop_window_zones + 1) : -1]
        return 1 if current_zone_id in recent else 0

    def _recent_zone_loop_flag(self, packet: Dict[str, Any]) -> int:
        """
        REWARD-side loop detection.

        Called AFTER moving the packet and appending the new zone to packet['zones'].

        Returns 1 if the *current* zone (zones[-1]) appears in the last
        loop_window_zones zones BEFORE it; else 0.
        """
        zones: List[Any] = packet.get("zones", [])
        if len(zones) < 2:
            return 0

        current_zone = zones[-1]
        start_idx = max(0, len(zones) - 1 - self.loop_window_zones)
        recent_past = zones[start_idx:-1]

        return 1 if current_zone in recent_past else 0

    # ------------------------------------------------------------------
    # INTERNAL: distance / bearing helpers (lat/long)
    # ------------------------------------------------------------------

    def _bearing_node_to_dest(self, node_id: str, dest_id: str) -> float:
        node_info = self.veh_table.values(node_id)
        dest_info = self.veh_table.values(dest_id)
        return self._bearing_angle(
            node_info["lat"], node_info["long"],
            dest_info["lat"], dest_info["long"],
        )

    def _distance_node_to_dest(self, node_id: str, dest_id: str) -> float:
        node_info = self.veh_table.values(node_id)
        dest_info = self.veh_table.values(dest_id)
        return self._haversine(
            node_info["lat"], node_info["long"],
            dest_info["lat"], dest_info["long"],
        )

    @staticmethod
    def _bearing_angle(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Bearing from (lat1, lon1) -> (lat2, lon2), radians.
        0 = North, increasing clockwise.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        lam1 = math.radians(lon1)
        lam2 = math.radians(lon2)

        dlam = lam2 - lam1

        y = math.sin(dlam) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)

        return math.atan2(y, x)

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Haversine distance in meters between two lat/long points.
        """
        r = 6371000.0  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = phi2 - phi1
        dlam = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

        return r * c

    @staticmethod
    def get_state_dim() -> int:
        """
        Return the dimensionality of the state vector produced by build_state().

        Current features:
            1  - dist_norm
            1  - angle_sin
            1  - angle_cos
            8  - neighbor_counts_norm (N, NE, E, SE, S, SW, W, NW)
            1  - loop_flag_state
            1  - age_norm
        Total: 13
        """
        return int(13)