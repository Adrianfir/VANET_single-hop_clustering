import csv
import json
from pathlib import Path

from configs import Config
from c_route import HeroRouter
from util import (
    extract_latlon_reference_from_messages,
    parse_messages,
    parse_sumo_net,
    parse_trace_xml,
)


def write_csv(path: Path, rows: list) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    cfg = Config()

    print("Parsing SUMO network...")
    edges_by_id, outgoing_edges_by_node, _ = parse_sumo_net(
        cfg.NET_XML_PATH,
        ignore_internal_edges=cfg.IGNORE_INTERNAL_EDGES,
    )
    print(f"Loaded {len(edges_by_id)} edges.")

    print("Parsing messages...")
    messages = parse_messages(cfg.MESSAGE_YAML_PATH)
    print(f"Loaded {len(messages)} message events.")

    ref_lat, ref_lon = extract_latlon_reference_from_messages(cfg.MESSAGE_YAML_PATH)

    print("Parsing SUMO trace...")
    vehicles_by_time = parse_trace_xml(
        cfg.TRACE_XML_PATH,
        ref_lat=ref_lat,
        ref_lon=ref_lon,
    )
    print(f"Loaded {len(vehicles_by_time)} timesteps.")

    router = HeroRouter(
        cfg=cfg,
        edges_by_id=edges_by_id,
        outgoing_edges_by_node=outgoing_edges_by_node,
        vehicles_by_time=vehicles_by_time,
        messages=messages,
        ref_lat=ref_lat,
        ref_lon=ref_lon,
    )

    print("Running simulation...")
    metrics = router.run()

    print("\n=== Packet-level metrics ===")
    print(json.dumps(metrics, indent=2))

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    write_csv(out_dir / "packet_results.csv", router.get_packet_rows())
    write_csv(out_dir / "forward_log.csv", router.get_forward_log_rows())

    print(f"\nSaved outputs to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()