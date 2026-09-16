"""Regression checks for canonical assets; designed for local use and CI."""
from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
BOARDS = ROOT / "output" / "CURRENT" / "boards"


def run(module: str) -> None:
    subprocess.run([sys.executable, "-m", module], cwd=ROOT, check=True)


def hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(BOARDS)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def main() -> None:
    # CI starts without ignored manufacturing files, so rebuild from the canonical source first.
    run("src.chassis.build_canonical_chassis")
    run("src.chassis.validate_canonical_chassis")
    run("src.tools.build_gameplay_space_manifest")
    run("src.tools.validate_gameplay_space_manifest")
    # Tile examples require explicit clearance candidates and are validated by their committed manifest.
    run("src.racers.generate_racer_prototypes")
    run("src.racers.validate_racer_prototypes")
    run("src.tools.build_board_catalog")

    baseline = json.loads((ROOT / "docs" / "GEOMETRY_HASH_BASELINE.json").read_text())
    quadrants = sorted(BOARDS.glob("*/quadrant_*.stl"))
    assert len(quadrants) == 16
    expected_hashes = {"/".join(Path(path).parts[-2:]): digest
                       for path, digest in baseline["canonical_production_quadrants"].items()}
    assert hashes(quadrants) == expected_hashes, "Canonical production geometry hash changed"
    for path in quadrants:
        mesh = trimesh.load_mesh(path)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, path
        assert max(mesh.extents[:2]) <= 256 and np.isclose(mesh.extents[2], 10.0, atol=.01), path

    finished = json.loads((BOARDS / "finished_stl_bounds.json").read_text())
    for board in finished["boards"]:
        for quadrant in board["quadrants"]:
            assert quadrant["usable_socket_mm"] == [36.0, 36.0]
            assert quadrant["z_mm"] == 10.0 and quadrant["fits_A1_256mm"]

    for module in ("src.chassis.build_canonical_chassis", "src.chassis.validate_canonical_chassis",
                   "src.tiles.universal_gameplay_tile", "src.racers.racer_prototypes",
                   "src.tools.build_gameplay_space_manifest", "src.tools.build_board_catalog"):
        importlib.import_module(module)
    current_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "output" / "CURRENT").rglob("*")
                             if path.suffix in {".json", ".md", ".html"})
    assert "output/archive/" not in current_text and "output\\archive\\" not in current_text
    print("PASS: canonical geometry, A1 fit, dimensions, manifests, racer sandbox, catalog, imports, and CURRENT references verified.")


if __name__ == "__main__":
    main()
