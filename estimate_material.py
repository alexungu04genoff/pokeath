"""Estimate solid PLA mass from the current production and prototype STL meshes.

This intentionally does not estimate sliced FDM mass: shells, infill, supports,
brims, layer height and purge behaviour are slicer settings, not STL properties.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import trimesh


ROOT = Path(__file__).resolve().parent
CANONICAL = ROOT / "output" / "canonical_chassis"
PROTOTYPE = ROOT / "output" / "sloped_lap_prototype"


def measure(path: Path, density_g_cm3: float) -> dict[str, object]:
    mesh = trimesh.load_mesh(path)
    if not mesh.is_watertight or mesh.volume <= 0:
        raise ValueError(f"Expected a positive watertight STL: {path}")
    volume_mm3 = float(mesh.volume)
    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "volume_mm3": volume_mm3,
        "solid_mass_g": volume_mm3 / 1000 * density_g_cm3,
    }


def add_record(records: list[dict[str, object]], path: Path, density: float,
               scope: str, component_type: str, board: str = "", quadrant: str = "") -> None:
    record = measure(path, density)
    record.update({"scope": scope, "board": board, "quadrant": quadrant,
                   "component_type": component_type,
                   "fdm_print_mass_g": "slicer required"})
    records.append(record)


def write_csv(records: list[dict[str, object]], destination: Path) -> None:
    fields = ["scope", "board", "quadrant", "component_type", "file",
              "volume_mm3", "solid_mass_g", "fdm_print_mass_g"]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({**row, "volume_mm3": f"{row['volume_mm3']:.3f}",
                             "solid_mass_g": f"{row['solid_mass_g']:.3f}"})


def write_report(records: list[dict[str, object]], density: float, destination: Path) -> None:
    production = [r for r in records if r["scope"] == "production"]
    prototype = [r for r in records if r["scope"] == "prototype"]
    by_board: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in production:
        by_board[str(record["board"])].append(record)
    by_prototype_type: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in prototype:
        by_prototype_type[str(record["component_type"])].append(record)

    def total(items: list[dict[str, object]], key: str) -> float:
        return sum(float(item[key]) for item in items)

    all_chassis_g = total(production, "solid_mass_g")
    prototype_g = total(prototype, "solid_mass_g")
    lines = [
        "# Material estimate",
        "",
        f"Generated from actual exported STL mesh volumes using PLA density **{density:.3f} g/cm³**.",
        "",
        "## What these numbers mean",
        "",
        "`Solid-mesh mass` is the theoretical mass if every watertight mesh volume were solid PLA. It is a useful upper bound for the model itself.",
        "",
        "`Actual FDM print mass` cannot be calculated from STL volume alone. Perimeters, top/bottom layers, infill pattern and percentage, supports, brim, purge, modifiers and slicer compensation determine it. Use Bambu Studio’s post-slice filament estimate for the selected profile. This report deliberately does not present a guessed FDM mass.",
        "",
        "## Production quadrants: solid-mesh upper bound",
        "",
        "| Board | Quadrant | Volume (cm³) | Solid-mesh mass (g) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for record in production:
        lines.append(f"| {record['board']} | {record['quadrant']} | {float(record['volume_mm3']) / 1000:.3f} | {float(record['solid_mass_g']):.2f} |")
    lines += ["", "## Production board totals: solid-mesh upper bound", "",
              "| Board | Quadrants | Volume (cm³) | Solid-mesh mass (g) |",
              "| --- | ---: | ---: | ---: |"]
    for board in ["Akala", "Melemele", "Poni", "Ulaula"]:
        items = by_board[board]
        lines.append(f"| {board} | {len(items)} | {total(items, 'volume_mm3') / 1000:.3f} | {total(items, 'solid_mass_g'):.2f} |")
    lines += [f"| **All four chassis** | **{len(production)}** | **{total(production, 'volume_mm3') / 1000:.3f}** | **{all_chassis_g:.2f}** |",
              "", "The four-board chassis solid-volume upper bound represents "
              f"**{all_chassis_g / 1000:.3f} standard 1 kg PLA rolls**; purchasing requires whole rolls, so round up to **{int(-(-all_chassis_g // 1000))} roll(s)** before allowance for slicing waste, supports, brims, retries or accessories.",
              "", "## Sloped 2×1 prototype kit: solid-mesh upper bound", "",
              "The combined one-plate STL is excluded here because it duplicates the individual parts.",
              "", "| Component type | Count | Volume (cm³) | Solid-mesh mass (g) |",
              "| --- | ---: | ---: | ---: |"]
    for kind in ["board part", "pin", "tile test"]:
        items = by_prototype_type[kind]
        lines.append(f"| {kind} | {len(items)} | {total(items, 'volume_mm3') / 1000:.3f} | {total(items, 'solid_mass_g'):.2f} |")
    lines += [f"| **Prototype kit total** | **{len(prototype)}** | **{total(prototype, 'volume_mm3') / 1000:.3f}** | **{prototype_g:.2f}** |",
              "", "## Re-running", "",
              "Run `python estimate_material.py` for the default 1.240 g/cm³ PLA density. Use `python estimate_material.py --density 1.27` for another material density. The script only reads STL files and writes this report plus `material_estimate.csv`; it never regenerates geometry."]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure solid mesh volume and PLA mass upper bounds.")
    parser.add_argument("--density", type=float, default=1.24, metavar="G_PER_CM3",
                        help="Material density in g/cm³; default: 1.24 for PLA.")
    parser.add_argument("--report", type=Path, default=ROOT / "MATERIAL_ESTIMATE.md")
    parser.add_argument("--csv", type=Path, default=ROOT / "material_estimate.csv")
    args = parser.parse_args()
    if args.density <= 0:
        parser.error("--density must be positive")

    records: list[dict[str, object]] = []
    for board in ["Akala", "Melemele", "Poni", "Ulaula"]:
        for number in range(1, 5):
            add_record(records, CANONICAL / board / f"quadrant_{number}.stl", args.density,
                       "production", "board quadrant", board, str(number))
    add_record(records, PROTOTYPE / "prototype_2x1_part_A.stl", args.density,
               "prototype", "board part")
    add_record(records, PROTOTYPE / "prototype_2x1_part_B.stl", args.density,
               "prototype", "board part")
    for path in sorted((PROTOTYPE / "pins").glob("*.stl")):
        add_record(records, path, args.density, "prototype", "pin")
    for path in sorted((PROTOTYPE / "tiles").glob("*.stl")):
        add_record(records, path, args.density, "prototype", "tile test")

    write_csv(records, args.csv)
    write_report(records, args.density, args.report)
    print(f"PASS: measured {len(records)} individual STL meshes at {args.density:.3f} g/cm³; "
          f"wrote {args.report.name} and {args.csv.name}.")


if __name__ == "__main__":
    main()
