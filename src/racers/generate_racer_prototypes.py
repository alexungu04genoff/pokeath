"""Generate geometry-only racer sandbox references."""
from __future__ import annotations

import json
from pathlib import Path

from src.racers.racer_prototypes import crowding_socket, export_scene, export_single, portrait_racer, racer_base

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "CURRENT" / "racers"
BLENDER = ROOT / "output" / "CURRENT" / "blender" / "racers"


def write_pair(name: str, mesh, scene: bool = False) -> dict[str, object]:
    stl = OUT / f"{name}.stl"
    obj = BLENDER / f"{name}.obj"
    loaded = export_scene(mesh, stl) if scene else export_single(mesh, stl)
    BLENDER.mkdir(parents=True, exist_ok=True)
    mesh.export(obj)
    return {"name": name, "stl": str(stl.relative_to(ROOT)).replace("\\", "/"),
            "obj": str(obj.relative_to(ROOT)).replace("\\", "/"),
            "xyz_mm": loaded.extents.round(3).tolist(), "components": len(loaded.split())}


def main() -> None:
    records = [write_pair(f"dummy_racer_base_{int(size)}mm", racer_base(size)) for size in (8.0, 9.0, 10.0)]
    records.append(write_pair("dummy_racer_portrait_panel_8mm", portrait_racer()))
    records.append(write_pair("crowding_test_36mm_socket_six_8mm_dummy_racers", crowding_socket(), scene=True))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps({"purpose": "geometry-only racer size and crowding sandbox",
        "final_pokemon_artwork_generated": False, "records": records}, indent=2) + "\n")
    print(f"PASS: generated {len(records)} neutral racer sandbox exports.")


if __name__ == "__main__":
    main()
