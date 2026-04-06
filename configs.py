from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Config:
    # File paths
    NET_XML_PATH: str = "/Users/pouyafirouzmakan/Desktop/traffic_data/final_data_Richmondhill_midsize/osm.net.xml"
    TRACE_XML_PATH: str = "/Users/pouyafirouzmakan/Desktop/traffic_data/final_data_Richmondhill_midsize/sumoTrace_no_bus_and_rsu.xml"
    MESSAGE_YAML_PATH: str = "/Users/pouyafirouzmakan/Desktop/traffic_data/Generated_messages/testing_RL/messages_midsize.yaml"

    # Simulation
    MAX_HOPS_PER_SECOND: int = 5
    COMMUNICATION_RANGE_M: float = 200.0
    PACKET_TTL_SECONDS: int = 120
    RANDOM_SEED: int = 42

    START_TIME = 1600
    ROUTING_START_AFTER = 5
    END_TIME = 1800
    ROUTING_ENDS_RATIO = 5/6

    # HERO-style weighting
    # Inter-road selection
    W_SDD: float = 0.55
    W_CD: float = 0.45

    # Intra-road vehicle selection
    W_REL_SPEED: float = 0.25
    W_DIRECTION: float = 0.35
    W_BUFFER: float = 0.15
    W_FADING: float = 0.25

    # Simplified buffer model
    VEHICLE_BUFFER_CAPACITY_PACKETS: int = 300

    # Packet loop control
    # RECENT_HOLDER_MEMORY: int = 8

    # If destination vehicle is absent from current trace, use d_loc from YAML
    FALLBACK_TO_DEST_LOCATION: bool = True

    # Debug / output
    VERBOSE: bool = True

    # Optional penalties
    # REVISIT_PENALTY: float = 0.35
    EDGE_MATCH_BONUS: float = 0.20

    # Trace parsing
    TRACE_TIME_IS_INT: bool = True

    # Ignore internal SUMO edges starting with ':'
    IGNORE_INTERNAL_EDGES: bool = True

    # Reserved for future extensions
    EXTRA: Dict = field(default_factory=dict)