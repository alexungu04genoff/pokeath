"""Validate neutral racer sandbox meshes and six-racer crowding scene."""
from __future__ import annotations

import json
from pathlib import Path
import trimesh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "CURRENT" / "racers"


def main() -> None:
    data = json.loads((OUT / "manifest.json").read_text())
    for record in data["records"]:
        mesh = trimesh.load_mesh(ROOT / record["stl"])
        assert max(mesh.extents[:2]) <= 256
        assert abs(mesh.bounds[0, 2]) < .001
        assert len(mesh.split()) == record["components"]
        for component in mesh.split():
            assert component.is_watertight and component.is_winding_consistent and component.volume > 0
    crowd = next(item for item in data["records"] if item["name"].startswith("crowding_test"))
    assert crowd["components"] == 7  # one socket frame plus six dummy racers
    (OUT / "validation.json").write_text(json.dumps({"passed": True, "a1_compatible": True,
        "six_racer_layout": "3 columns × 2 rows", "final_pokemon_artwork_generated": False}, indent=2) + "\n")
    print("PASS: racer sandbox meshes are watertight and the crowding scene contains six racers.")


if __name__ == "__main__":
    main()
