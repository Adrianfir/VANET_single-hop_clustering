import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import yaml

from model import EdgeInfo, MessageEvent, VehicleState


EARTH_RADIUS_M = 6371000.0


def latlon_to_local_xy(
    lat: float,
    lon: float,
    ref_lat: float,
    ref_lon: float,
) -> Tuple[float, float]:
    """
    Simple local tangent-plane approximation.
    Good enough for a small SUMO study area.
    """
    x = math.radians(lon - ref_lon) * EARTH_RADIUS_M * math.cos(math.radians(ref_lat))
    y = math.radians(lat - ref_lat) * EARTH_RADIUS_M
    return x, y


def euclidean(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def safe_div(num: float, den: float, default: float = 0.0) -> float:
    return num / den if den != 0 else default


def normalize(values: List[float]) -> List[float]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if math.isclose(vmax, vmin):
        return [1.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


def invert_normalize(values: List[float]) -> List[float]:
    n = normalize(values)
    return [1.0 - v for v in n]


def vector_angle_deg(vx: float, vy: float) -> float:
    ang = math.degrees(math.atan2(vy, vx))
    if ang < 0:
        ang += 360.0
    return ang


def angle_diff_deg(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def direction_alignment_score(angle_a_deg: float, angle_b_deg: float) -> float:
    """
    1 means same direction, 0 means opposite direction.
    """
    diff = angle_diff_deg(angle_a_deg, angle_b_deg)
    return 1.0 - diff / 180.0


def direction_toward_target_angle(
    src_xy: Tuple[float, float],
    dst_xy: Tuple[float, float],
) -> float:
    return vector_angle_deg(dst_xy[0] - src_xy[0], dst_xy[1] - src_xy[1])


def polyline_midpoint(shape: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not shape:
        return (0.0, 0.0)
    if len(shape) == 1:
        return shape[0]
    total = 0.0
    segs = []
    for i in range(len(shape) - 1):
        a, b = shape[i], shape[i + 1]
        d = euclidean(a, b)
        segs.append((a, b, d))
        total += d
    if total == 0:
        return shape[0]
    acc = 0.0
    target = total / 2.0
    for a, b, d in segs:
        if acc + d >= target:
            ratio = safe_div(target - acc, d, 0.0)
            x = a[0] + ratio * (b[0] - a[0])
            y = a[1] + ratio * (b[1] - a[1])
            return (x, y)
        acc += d
    return shape[-1]


def point_to_segment_distance(
    p: Tuple[float, float],
    a: Tuple[float, float],
    b: Tuple[float, float],
) -> float:
    ax, ay = a
    bx, by = b
    px, py = p

    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay

    ab2 = abx * abx + aby * aby
    if ab2 == 0:
        return euclidean(p, a)

    t = clamp((apx * abx + apy * aby) / ab2, 0.0, 1.0)
    qx = ax + t * abx
    qy = ay + t * aby
    return math.hypot(px - qx, py - qy)


def point_to_polyline_distance(
    p: Tuple[float, float],
    shape: List[Tuple[float, float]],
) -> float:
    if not shape:
        return float("inf")
    if len(shape) == 1:
        return euclidean(p, shape[0])
    best = float("inf")
    for i in range(len(shape) - 1):
        d = point_to_segment_distance(p, shape[i], shape[i + 1])
        if d < best:
            best = d
    return best


def parse_shape(shape_str: str) -> List[Tuple[float, float]]:
    pts = []
    if not shape_str:
        return pts
    for token in shape_str.strip().split():
        x_str, y_str = token.split(",")
        pts.append((float(x_str), float(y_str)))
    return pts


def lane_to_edge_id(lane_id: str) -> str:
    if "_" in lane_id:
        return lane_id.rsplit("_", 1)[0]
    return lane_id


def parse_sumo_net(
    net_xml_path: str,
    ignore_internal_edges: bool = True,
) -> Tuple[
    Dict[str, EdgeInfo],
    Dict[str, List[str]],
    Dict[str, List[str]],
]:
    """
    Returns:
      edges_by_id,
      outgoing_edges_by_node,
      incoming_edges_by_node
    """
    tree = ET.parse(net_xml_path)
    root = tree.getroot()

    edges_by_id: Dict[str, EdgeInfo] = {}
    outgoing_edges_by_node = defaultdict(list)
    incoming_edges_by_node = defaultdict(list)

    for edge_elem in root.findall("edge"):
        edge_id = edge_elem.attrib.get("id", "")
        if ignore_internal_edges and edge_id.startswith(":"):
            continue

        from_node = edge_elem.attrib.get("from")
        to_node = edge_elem.attrib.get("to")
        if from_node is None or to_node is None:
            continue

        lanes = edge_elem.findall("lane")
        if not lanes:
            continue

        num_lanes = len(lanes)
        length = max(float(lanes[0].attrib.get("length", "0")), 1.0)
        speed_limit = float(lanes[0].attrib.get("speed", "13.89"))
        priority = int(edge_elem.attrib.get("priority", "1"))
        shape = parse_shape(lanes[0].attrib.get("shape", ""))

        edges_by_id[edge_id] = EdgeInfo(
            edge_id=edge_id,
            from_node=from_node,
            to_node=to_node,
            length=length,
            priority=priority,
            num_lanes=num_lanes,
            speed_limit=speed_limit,
            shape=shape,
        )

        outgoing_edges_by_node[from_node].append(edge_id)
        incoming_edges_by_node[to_node].append(edge_id)

    return edges_by_id, dict(outgoing_edges_by_node), dict(incoming_edges_by_node)


def parse_trace_xml(
    trace_xml_path: str,
    ref_lat: float,
    ref_lon: float,
) -> Dict[int, Dict[str, VehicleState]]:
    """
    SUMO FCD format assumption:
    <fcd-export>
      <timestep time="1001.00">
        <vehicle id="veh..." x="..." y="..." angle="..." speed="..." lane="..."/>
      </timestep>
    </fcd-export>

    IMPORTANT:
    In your trace, x/y are geographic-looking lon/lat values, so we convert them
    to local metric coordinates using the same reference used for message d_loc.
    """
    tree = ET.parse(trace_xml_path)
    root = tree.getroot()

    by_time: Dict[int, Dict[str, VehicleState]] = {}

    for ts in root.findall("timestep"):
        time_raw = float(ts.attrib["time"])
        t = int(round(time_raw))
        vehs: Dict[str, VehicleState] = {}

        for veh in ts.findall("vehicle"):
            veh_id = veh.attrib["id"]
            lane_id = veh.attrib.get("lane", "")
            edge_id = lane_to_edge_id(lane_id)

            raw_x = float(veh.attrib.get("x", "0"))  # actually lon in your trace
            raw_y = float(veh.attrib.get("y", "0"))  # actually lat in your trace

            # Convert lon/lat -> local x/y in meters
            x_m, y_m = latlon_to_local_xy(
                lat=raw_y,
                lon=raw_x,
                ref_lat=ref_lat,
                ref_lon=ref_lon,
            )

            speed = float(veh.attrib.get("speed", "0"))
            angle_deg = float(veh.attrib.get("angle", "0"))

            vehs[veh_id] = VehicleState(
                veh_id=veh_id,
                time=t,
                x=x_m,
                y=y_m,
                speed=speed,
                angle_deg=angle_deg,
                lane_id=lane_id,
                edge_id=edge_id,
            )

        by_time[t] = vehs

    return by_time

def extract_latlon_reference_from_messages(message_yaml_path: str) -> Tuple[float, float]:
    with open(message_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    lats = []
    lons = []
    for _, bucket in data.items():
        if not bucket:
            continue
        for _, msg in bucket.items():
            d_loc = msg.get("d_loc")
            if d_loc:
                lat = d_loc.get("lat")
                lon = d_loc.get("long")
                if lat is not None and lon is not None:
                    lats.append(float(lat))
                    lons.append(float(lon))

    if not lats or not lons:
        return 0.0, 0.0

    return sum(lats) / len(lats), sum(lons) / len(lons)


def parse_messages(
    message_yaml_path: str,
) -> List[MessageEvent]:
    with open(message_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    events: List[MessageEvent] = []

    for time_key, bucket in data.items():
        t = int(time_key)
        if not bucket:
            continue

        for msg_id, msg in bucket.items():
            d_loc = msg.get("d_loc", {})
            packet_names = list(msg.get("mess", []))

            # Fallback if "mess" missing but "length" is present
            if not packet_names:
                length = int(msg.get("length", 0))
                packet_names = [f"packet{i}" for i in range(length)]

            events.append(
                MessageEvent(
                    time=t,
                    message_id=str(msg_id),
                    source=str(msg.get("source")),
                    dest=str(msg.get("dest")),
                    d_loc_lat=float(d_loc["lat"]) if d_loc and "lat" in d_loc else None,
                    d_loc_lon=float(d_loc["long"]) if d_loc and "long" in d_loc else None,
                    packet_names=packet_names,
                )
            )

    events.sort(key=lambda e: (e.time, e.message_id))
    return events


def group_messages_by_time(events: List[MessageEvent]) -> Dict[int, List[MessageEvent]]:
    grouped = defaultdict(list)
    for e in events:
        grouped[e.time].append(e)
    return dict(grouped)


def build_edge_vehicle_index(
    vehicles: Dict[str, VehicleState],
) -> Dict[str, List[VehicleState]]:
    edge_map = defaultdict(list)
    for v in vehicles.values():
        edge_map[v.edge_id].append(v)
    return dict(edge_map)


def nearest_vehicle_distance_on_edge(
    vehicles_on_edge: List[VehicleState],
) -> float:
    """
    Approximate spacing indicator using nearest x,y Euclidean distance.
    """
    if len(vehicles_on_edge) < 2:
        return float("inf")

    best = float("inf")
    for i in range(len(vehicles_on_edge)):
        for j in range(i + 1, len(vehicles_on_edge)):
            d = euclidean(vehicles_on_edge[i].pos, vehicles_on_edge[j].pos)
            if d < best:
                best = d
    return best


def message_dest_xy_from_latlon(
    lat: Optional[float],
    lon: Optional[float],
    ref_lat: float,
    ref_lon: float,
) -> Optional[Tuple[float, float]]:
    if lat is None or lon is None:
        return None
    return latlon_to_local_xy(lat, lon, ref_lat, ref_lon)