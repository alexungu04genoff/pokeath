"""Small neutral racer geometry for 36 mm socket crowding tests."""
from __future__ import annotations

from pathlib import Path

from shapely.geometry import box
import trimesh

from src.chassis import build_printable_board as cad
from src.chassis.build_canonical_chassis import export

ROOT = Path(__file__).resolve().parents[2]
BASE_THICKNESS_MM = 1.6


def racer_base(size_mm: float) -> trimesh.Trimesh:
    if size_mm not in {8.0, 9.0, 10.0}:
        raise ValueError("Supported racer base sizes are 8, 9, and 10 mm")
    return cad.extrude(cad.curved_rectangle((0, 0, size_mm, size_mm), [1.0] * 4), BASE_THICKNESS_MM)


def portrait_racer(size_mm: float = 8.0) -> trimesh.Trimesh:
    """A neutral upright panel on a base; intentionally contains no Pokémon artwork."""
    base = racer_base(size_mm)
    panel_width = size_mm - 2.0
    panel = cad.extrude(box((size_mm - panel_width) / 2, size_mm - 1.1,
                            (size_mm + panel_width) / 2, size_mm - .3), 8.0, BASE_THICKNESS_MM)
    return cad.union([base, panel])


def crowding_socket() -> trimesh.Trimesh:
    """A 36 mm socket with six 8 mm neutral upright racers in 3 × 2 formation."""
    outer = cad.extrude(cad.curved_rectangle((0, 0, 40, 40), [2.0] * 4), 3.0)
    inner = cad.extrude(cad.curved_rectangle((2, 2, 38, 38), [2.0] * 4), 3.1)
    floor = cad.extrude(cad.curved_rectangle((2, 2, 38, 38), [2.0] * 4), .5)
    frame = cad.union([cad.difference(outer, inner), floor])
    pieces = [frame]
    for y in (5.0, 23.0):
        for x in (6.0, 16.0, 26.0):
            racer = portrait_racer(8.0)
            racer.apply_translation([x, y, .5])
            pieces.append(racer)
    return trimesh.util.concatenate(pieces)


def export_single(mesh: trimesh.Trimesh, destination: Path) -> trimesh.Trimesh:
    destination.parent.mkdir(parents=True, exist_ok=True)
    return export(mesh, destination)


def export_scene(mesh: trimesh.Trimesh, destination: Path) -> trimesh.Trimesh:
    """Export a deliberately disconnected reference scene; validate each component."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(destination)
    loaded = trimesh.load_mesh(destination)
    for component in loaded.split():
        assert component.is_watertight and component.is_winding_consistent and component.volume > 0
    return loaded
