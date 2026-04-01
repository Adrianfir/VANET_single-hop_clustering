from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class EdgeInfo:
    edge_id: str
    from_node: str
    to_node: str
    length: float
    priority: int
    num_lanes: int
    speed_limit: float
    shape: List[Tuple[float, float]]


@dataclass
class VehicleState:
    veh_id: str
    time: int
    x: float
    y: float
    speed: float
    angle_deg: float
    lane_id: str
    edge_id: str

    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class MessageEvent:
    time: int
    message_id: str
    source: str
    dest: str
    d_loc_lat: Optional[float]
    d_loc_lon: Optional[float]
    packet_names: List[str]


@dataclass
class Packet:
    packet_uid: str
    message_id: str
    packet_name: str
    source: str
    dest: str
    start_time: int

    current_holder: Optional[str] = None
    delivered: bool = False
    dropped: bool = False
    delivery_time: Optional[int] = None
    hops: int = 0

    last_known_dest_xy: Optional[Tuple[float, float]] = None

    path: List[str] = field(default_factory=list)
    # recent_holders: List[str] = field(default_factory=list)

    def mark_holder(self, veh_id: str, memory: int = 0) -> None:
        self.current_holder = veh_id
        self.path.append(veh_id)

    def delay(self) -> Optional[int]:
        if self.delivered and self.delivery_time is not None:
            return self.delivery_time - self.start_time
        return None