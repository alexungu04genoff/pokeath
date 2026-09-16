"""Read-only validation for universal gameplay-tile exports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh

from src.tiles.universal_gameplay_tile import A1_SIZE_MM, SOCKET_SIZE_MM, TILE_THICKNESS_MM

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated universal tile meshes.")
    parser.add_argument("--manifest", type=Path, default=ROOT / "output" / "CURRENT" / "tiles" / "examples" / "manifest.json")
    parser.add_argument("--report", type=Path, default=ROOT / "output" / "CURRENT" / "tiles" / "validation.json")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text())
    checks = []
    for record in data["generated"]:
        path = Path(record["file"])
        mesh = trimesh.load_mesh(path)
        expected = SOCKET_SIZE_MM - 2 * float(record["clearance_per_side_mm"])
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, path
        assert len(mesh.split()) == 1, path
        assert np.allclose(mesh.extents[:2], [expected, expected], atol=.01), path
        assert mesh.bounds[0, 2] >= -.001 and mesh.extents[2] >= TILE_THICKNESS_MM - .01, path
        assert max(mesh.extents[:2]) <= A1_SIZE_MM, path
        checks.append({"file": record["file"], "xyz_mm": mesh.extents.round(3).tolist(),
                       "watertight": True, "a1_compatible": True})
    report = {"passed": True, "clearance_selected": False, "tiles": checks}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: validated {len(checks)} universal tiles; no clearance selected.")


if __name__ == "__main__":
    main()
