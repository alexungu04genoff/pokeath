"""Create a non-slicing A1 plate plan from current finished STL geometry.

The planner only reads STL bounds and writes Markdown/PNG planning artifacts.
It never transforms, exports, scales, or otherwise changes model geometry.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import trimesh


ROOT = Path(__file__).resolve().parent
PLATE_SIZE = 256.0


@dataclass
class Item:
    name: str
    path: Path
    quantity: int = 1
    category: str = ""
    baked_rotation: float = 0.0
    note: str = ""

    def __post_init__(self) -> None:
        mesh = trimesh.load_mesh(self.path)
        self.size = mesh.extents[:2].astype(float)
        self.height = float(mesh.extents[2])


@dataclass
class Placement:
    item: Item
    copy: int
    x: float
    y: float

    @property
    def label(self) -> str:
        return self.item.name if self.item.quantity == 1 else f"{self.item.name} #{self.copy}"

    @property
    def width(self) -> float:
        return float(self.item.size[0])

    @property
    def height(self) -> float:
        return float(self.item.size[1])


def rectangle_fit(width: float, height: float, spacing: float) -> bool:
    return width <= PLATE_SIZE and height <= PLATE_SIZE and spacing >= 0


def pack_rows(items: list[Item], spacing: float) -> list[Placement]:
    """Simple deterministic shelf pack; preserves all STL orientations."""
    placements: list[Placement] = []
    x = y = 0.0
    row_height = 0.0
    for item in items:
        for copy in range(1, item.quantity + 1):
            width, height = item.size
            if x + width > PLATE_SIZE:
                x = 0.0
                y += row_height + spacing
                row_height = 0.0
            if y + height > PLATE_SIZE:
                raise ValueError(f"Cannot fit {item.name} on this plate while keeping {spacing:g} mm spacing")
            placements.append(Placement(item, copy, x, y))
            x += width + spacing
            row_height = max(row_height, height)
    return center(placements)


def center(placements: list[Placement]) -> list[Placement]:
    min_x = min(p.x for p in placements)
    min_y = min(p.y for p in placements)
    max_x = max(p.x + p.width for p in placements)
    max_y = max(p.y + p.height for p in placements)
    dx = (PLATE_SIZE - (max_x - min_x)) / 2 - min_x
    dy = (PLATE_SIZE - (max_y - min_y)) / 2 - min_y
    for p in placements:
        p.x += dx
        p.y += dy
    return placements


def margins(placements: list[Placement]) -> dict[str, float]:
    return {
        "left": min(p.x for p in placements),
        "right": min(PLATE_SIZE - (p.x + p.width) for p in placements),
        "front": min(p.y for p in placements),
        "back": min(PLATE_SIZE - (p.y + p.height) for p in placements),
    }


def validate(placements: list[Placement], spacing: float) -> None:
    for p in placements:
        assert p.x >= 0 and p.y >= 0
        assert p.x + p.width <= PLATE_SIZE and p.y + p.height <= PLATE_SIZE
    for i, first in enumerate(placements):
        for second in placements[i + 1:]:
            gap_x = max(first.x - (second.x + second.width), second.x - (first.x + first.width), 0)
            gap_y = max(first.y - (second.y + second.height), second.y - (first.y + first.height), 0)
            assert max(gap_x, gap_y) >= spacing - 1e-6, (first.label, second.label)


def preview(number: int, title: str, placements: list[Placement], spacing: float, directory: Path) -> Path:
    figure, axis = plt.subplots(figsize=(9, 9))
    axis.add_patch(Rectangle((0, 0), PLATE_SIZE, PLATE_SIZE, facecolor="#30393f", edgecolor="black"))
    for line in range(0, 257, 16):
        axis.plot([0, PLATE_SIZE], [line, line], color="#809096", alpha=.3, linewidth=.5)
        axis.plot([line, line], [0, PLATE_SIZE], color="#809096", alpha=.3, linewidth=.5)
    palette = {"prototype": "#28a6b8", "production": "#f0bb3d", "accessory": "#85b85c"}
    for placement in placements:
        color = palette.get(placement.item.category, "#cccccc")
        axis.add_patch(Rectangle((placement.x, placement.y), placement.width, placement.height,
                                 facecolor=color, edgecolor="white", linewidth=1.2))
        rotation = f"baked {placement.item.baked_rotation:.2f}°" if placement.item.baked_rotation else "baked 0°"
        axis.text(placement.x + placement.width / 2, placement.y + placement.height / 2,
                  f"{placement.label}\n{placement.width:.1f} × {placement.height:.1f}\n{rotation}",
                  ha="center", va="center", fontsize=7, wrap=True)
    axis.set_xlim(0, PLATE_SIZE); axis.set_ylim(0, PLATE_SIZE); axis.set_aspect("equal")
    axis.set_xticks([0, 64, 128, 192, 256]); axis.set_yticks([0, 64, 128, 192, 256])
    axis.set_xlabel("A1 plate X (mm)"); axis.set_ylabel("A1 plate Y (mm)")
    axis.set_title(f"Plate {number:02d} | {title}\n256 × 256 mm, 100% scale, {spacing:g} mm minimum disconnected-part spacing")
    figure.tight_layout()
    target = directory / f"plate_{number:02d}.png"
    figure.savefig(target, dpi=160)
    plt.close(figure)
    return target


def component_item(name: str, path: Path, category: str, **kwargs: object) -> Item:
    if not path.is_file():
        raise FileNotFoundError(path)
    return Item(name, path, category=category, **kwargs)


def build_plan(spacing: float) -> list[tuple[str, list[Placement]]]:
    canonical = ROOT / "output" / "canonical_chassis"
    prototype = ROOT / "output" / "sloped_lap_prototype"
    bounds = json.loads((canonical / "finished_stl_bounds.json").read_text())
    plan: list[tuple[str, list[Placement]]] = []

    # The combined STL intentionally preserves a tested arrangement of its 14 disconnected pieces.
    prototype_plate = component_item("Sloped 2×1 prototype test kit (14 disconnected parts)",
                                    prototype / "prototype_2x1_ALL_COMPONENTS_A1.stl", "prototype",
                                    note="Print this plate before any production board.")
    plan.append(("Print first: experimental sloped 2×1 prototype", pack_rows([prototype_plate], spacing)))

    accessories = [
        component_item("Four-socket tile-fit coupon", canonical / "fit_test" / "four_identical_socket_coupon.stl", "accessory"),
        component_item("Tile test 0.15 mm/side", canonical / "fit_test" / "blank_test_tile_0.15mm_per_side_1_dots.stl", "accessory"),
        component_item("Tile test 0.20 mm/side", canonical / "fit_test" / "blank_test_tile_0.20mm_per_side_2_dots.stl", "accessory"),
        component_item("Tile test 0.25 mm/side", canonical / "fit_test" / "blank_test_tile_0.25mm_per_side_3_dots.stl", "accessory"),
        component_item("Tile test 0.30 mm/side", canonical / "fit_test" / "blank_test_tile_0.30mm_per_side_4_dots.stl", "accessory"),
        component_item("Lock coupon left", canonical / "fit_test_lock_left.stl", "accessory"),
        component_item("Lock coupon right", canonical / "fit_test_lock_right.stl", "accessory"),
        component_item("Snap key", canonical / "snap_key_print_3_per_board.stl", "accessory", quantity=3,
                       note="Three separate keys are needed per production board."),
    ]
    plan.append(("Canonical fit tests and sample production keys", pack_rows(accessories, spacing)))

    board_items: dict[str, list[Item]] = {}
    for board in bounds["boards"]:
        board_items[board["board"]] = []
        for quad in board["quadrants"]:
            board_items[board["board"]].append(component_item(
                f"{board['board']} Q{quad['quadrant']}", ROOT / quad["file"], "production",
                baked_rotation=float(quad["print_rotation_degrees"]),
                note="Baked orientation preserved; no additional rotation."))

    # These two are the only production quadrants that fit together with the default gap.
    melemele_small = sorted(board_items["Melemele"][:2], key=lambda item: item.name)
    plan.append(("Production: Melemele Q1 + Q2 share one plate", pack_rows(melemele_small, spacing)))
    for board in ["Akala", "Melemele", "Poni", "Ulaula"]:
        for item in board_items[board]:
            if item in melemele_small:
                continue
            plan.append((f"Production: {item.name} alone", pack_rows([item], spacing)))
    return plan


def write_report(plan: list[tuple[str, list[Placement]]], spacing: float, destination: Path, preview_dir: Path) -> None:
    lines = ["# Bambu Lab A1 print plan", "",
             f"Plate size: **{PLATE_SIZE:.0f} × {PLATE_SIZE:.0f} mm**. Scale: **100%**. Minimum disconnected-part spacing: **{spacing:g} mm**.",
             "", "This is a placement plan, not G-code and not a slicer-time/material estimate. Every item retains its STL’s baked orientation; the plan applies no additional rotation or scaling.",
             "", "**Print Plate 01 first.** The sloped 2×1 lap-pin kit is experimental and must pass physical testing before its lock is considered for production. It is not propagated to the production board quadrants.", ""]
    for number, (title, placements) in enumerate(plan, 1):
        boundary = margins(placements)
        footprint_x = max(p.x + p.width for p in placements) - min(p.x for p in placements)
        footprint_y = max(p.y + p.height for p in placements) - min(p.y for p in placements)
        closest = min(boundary.values())
        edge_status = "close (under 10 mm)" if closest < 10 else "comfortable (10 mm or more)"
        lines += [f"## Plate {number:02d}: {title}", "",
                  f"Footprint: **{footprint_x:.3f} × {footprint_y:.3f} mm**. "
                  f"Margins L/R/F/B: **{boundary['left']:.3f} / {boundary['right']:.3f} / {boundary['front']:.3f} / {boundary['back']:.3f} mm**. "
                  f"Plate edge: **{edge_status}**.", "",
                  f"![Plate {number:02d}](output/a1_print_plan/plate_{number:02d}.png)", "",
                  "| Component | Quantity | STL XY footprint (mm) | Required rotation |", "| --- | ---: | ---: | --- |"]
        grouped: dict[str, list[Placement]] = {}
        for placement in placements:
            grouped.setdefault(placement.item.name, []).append(placement)
        for name, entries in grouped.items():
            item = entries[0].item
            rotation = f"Baked {item.baked_rotation:.2f}°; no additional rotation" if item.baked_rotation else "Baked 0°; no additional rotation"
            lines.append(f"| {name} | {len(entries)} | {item.size[0]:.3f} × {item.size[1]:.3f} | {rotation} |")
        lines.append("")
    lines += ["## Planning notes", "",
              "The prototype combined STL contains fourteen disconnected parts whose internal 8.3 mm spacing is already validated. The plan does not auto-arrange its internal pieces.",
              "",
              "Melemele Q1 and Q2 are the only production quadrants intentionally paired. Their shared plate is geometrically valid at the configured spacing but has a close edge margin; every other quadrant remains alone to preserve its baked orientation and give reliable adhesion room.",
              "",
              "The canonical fit-test and key plate is for setup and mechanical checks. The three sample snap keys do not replace the production quantity requirement of three keys per complete board.",
              "",
              "Open every plate in Bambu Studio with the intended filament/profile to review supports, adhesion, seam placement and the slicer’s final collision check before printing."]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan current STL files on fixed-orientation A1 plates.")
    parser.add_argument("--spacing", type=float, default=8.0, help="Minimum gap in mm; default: 8.")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "a1_print_plan")
    parser.add_argument("--report", type=Path, default=ROOT / "A1_PRINT_PLAN.md")
    args = parser.parse_args()
    if args.spacing < 0:
        parser.error("--spacing must be non-negative")
    plan = build_plan(args.spacing)
    args.output.mkdir(parents=True, exist_ok=True)
    for number, (title, placements) in enumerate(plan, 1):
        validate(placements, args.spacing)
        preview(number, title, placements, args.spacing, args.output)
    write_report(plan, args.spacing, args.report, args.output)
    total_components = sum(len(placements) for _, placements in plan)
    print(f"PASS: {len(plan)} A1 plates; {total_components} placed component instances; all within 256 × 256 mm at 100% scale.")


if __name__ == "__main__":
    main()
