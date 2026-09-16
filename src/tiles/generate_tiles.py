"""CLI for one or more parameterized universal gameplay-tile test exports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.tiles.universal_gameplay_tile import TileSpec, export_tile, filename_stem

ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate universal 36 mm gameplay-tile test meshes.")
    parser.add_argument("--clearance", type=float, action="append", required=True,
                        help="Per-side clearance in mm; repeat to create several tiles.")
    parser.add_argument("--category", choices=["normal", "special", "hidden-special", "blank-custom"],
                        default="blank-custom")
    parser.add_argument("--label", default="tile")
    parser.add_argument("--recessed-icon-area", action="store_true")
    parser.add_argument("--embossed-icon-area", action="store_true")
    parser.add_argument("--engraved-text")
    parser.add_argument("--engraved-icon", choices=["circle", "star"])
    parser.add_argument("--hidden-special-back-marker", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "CURRENT" / "tiles" / "examples")
    parser.add_argument("--manifest", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    records = []
    for clearance in args.clearance:
        spec = TileSpec(category=args.category, clearance_per_side_mm=clearance,
                        recessed_icon_area=args.recessed_icon_area, embossed_icon_area=args.embossed_icon_area,
                        engraved_text=args.engraved_text, engraved_icon=args.engraved_icon,
                        hidden_special_back_marker=args.hidden_special_back_marker)
        path = args.output / f"{filename_stem(spec, args.label)}.stl"
        mesh, record = export_tile(spec, path)
        record["xyz_mm"] = mesh.extents.round(3).tolist()
        records.append(record)
    manifest = args.manifest or args.output / "manifest.json"
    manifest.write_text(json.dumps({"generated": records, "clearance_selected": False}, indent=2) + "\n")
    print(f"PASS: generated {len(records)} parameterized test tile(s); clearance remains unselected.")


if __name__ == "__main__":
    main()
