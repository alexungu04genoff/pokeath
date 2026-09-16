"""Geometry and metadata for removable tiles in canonical 36 mm sockets."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import trimesh

from src.chassis import build_printable_board as cad
from src.chassis.build_canonical_chassis import export

TileCategory = Literal["normal", "special", "hidden-special", "blank-custom"]
VALID_CATEGORIES = {"normal", "special", "hidden-special", "blank-custom"}
SOCKET_SIZE_MM = 36.0
SOCKET_RADIUS_MM = 2.0
TILE_THICKNESS_MM = 2.8
A1_SIZE_MM = 256.0


@dataclass(frozen=True)
class TileSpec:
    category: TileCategory = "blank-custom"
    clearance_per_side_mm: float = 0.20
    recessed_icon_area: bool = False
    embossed_icon_area: bool = False
    engraved_text: str | None = None
    engraved_icon: str | None = None
    hidden_special_back_marker: bool = False

    @property
    def width_mm(self) -> float:
        return SOCKET_SIZE_MM - 2 * self.clearance_per_side_mm

    def validate(self) -> None:
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Unsupported category: {self.category}")
        if not 0 < self.clearance_per_side_mm < SOCKET_SIZE_MM / 2:
            raise ValueError("clearance_per_side_mm must leave a positive tile size")
        if self.recessed_icon_area and self.embossed_icon_area:
            raise ValueError("Choose either a recessed or embossed icon area, not both")
        if self.engraved_icon and self.engraved_icon not in {"circle", "star"}:
            raise ValueError("engraved_icon must be 'circle' or 'star'")


def rounded_tile_outline(spec: TileSpec) -> Polygon:
    spec.validate()
    return cad.curved_rectangle((0, 0, spec.width_mm, spec.width_mm), [SOCKET_RADIUS_MM] * 4)


def icon_area(spec: TileSpec) -> Polygon:
    side = min(16.0, spec.width_mm - 8.0)
    start = (spec.width_mm - side) / 2
    return cad.curved_rectangle((start, start, start + side, start + side), [1.5] * 4)


def icon_polygon(spec: TileSpec, icon: str) -> Polygon:
    center = spec.width_mm / 2
    if icon == "circle":
        return Point(center, center).buffer(5.0, quad_segs=32)
    # Five-point star; deliberately generic so it is not gameplay artwork.
    import math
    vertices = []
    for index in range(10):
        radius = 5.5 if index % 2 == 0 else 2.5
        angle = math.radians(90 + index * 36)
        vertices.append((center + radius * math.cos(angle), center + radius * math.sin(angle)))
    return Polygon(vertices)


def text_polygon(spec: TileSpec, text: str) -> Polygon:
    path = TextPath((0, 0), text[:12], size=4.5)
    polygons = [Polygon(points) for points in path.to_polygons() if len(points) >= 3]
    if not polygons:
        raise ValueError("engraved_text did not produce printable outlines")
    glyphs = unary_union(polygons).buffer(0)
    minx, miny, maxx, maxy = glyphs.bounds
    limit = spec.width_mm - 8.0
    scale = min(1.0, limit / max(maxx - minx, maxy - miny))
    glyphs = affinity.scale(glyphs, xfact=scale, yfact=scale, origin=(minx, miny))
    minx, miny, maxx, maxy = glyphs.bounds
    return affinity.translate(glyphs, xoff=spec.width_mm / 2 - (minx + maxx) / 2,
                              yoff=spec.width_mm / 2 - (miny + maxy) / 2)


def build_tile(spec: TileSpec) -> trimesh.Trimesh:
    """Build one tile; category changes metadata only, never its base interface."""
    spec.validate()
    tile = cad.extrude(rounded_tile_outline(spec), TILE_THICKNESS_MM)
    cuts: list[trimesh.Trimesh] = []
    additions: list[trimesh.Trimesh] = []
    if spec.recessed_icon_area:
        cuts.append(cad.extrude(icon_area(spec), 0.45, TILE_THICKNESS_MM - 0.45))
    if spec.embossed_icon_area:
        additions.append(cad.extrude(icon_area(spec).buffer(-0.4), 0.45, TILE_THICKNESS_MM))
    if spec.engraved_text:
        cuts.append(cad.extrude(text_polygon(spec, spec.engraved_text), 0.35, TILE_THICKNESS_MM - 0.35))
    if spec.engraved_icon:
        cuts.append(cad.extrude(icon_polygon(spec, spec.engraved_icon), 0.35, TILE_THICKNESS_MM - 0.35))
    if spec.hidden_special_back_marker:
        # A fixed underside dot keeps the top face category-neutral.
        cuts.append(cad.extrude(Point(spec.width_mm / 2, spec.width_mm / 2).buffer(2.0, quad_segs=32), 0.30, 0))
    if cuts:
        tile = cad.difference(tile, cad.union(cuts))
    if additions:
        tile = cad.union([tile, *additions])
    tile.apply_translation(-tile.bounds[0])
    return tile


def filename_stem(spec: TileSpec, label: str = "tile") -> str:
    return f"{label}_{spec.category}_clearance_{spec.clearance_per_side_mm:.2f}mm"


def metadata(spec: TileSpec, path: Path | None = None) -> dict[str, object]:
    data = asdict(spec)
    data.update({"socket_size_mm": SOCKET_SIZE_MM, "socket_corner_radius_mm": SOCKET_RADIUS_MM,
                 "base_tile_thickness_mm": TILE_THICKNESS_MM, "tile_width_mm": spec.width_mm,
                 "a1_compatible": spec.width_mm <= A1_SIZE_MM})
    if path:
        try:
            path = path.relative_to(Path(__file__).resolve().parents[2])
        except ValueError:
            pass
        data["file"] = str(path).replace("\\", "/")
    return data


def export_tile(spec: TileSpec, destination: Path) -> tuple[trimesh.Trimesh, dict[str, object]]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    mesh = export(build_tile(spec), destination)
    return mesh, metadata(spec, destination)
