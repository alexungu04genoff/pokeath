"""Export Blender-editable reference geometry without touching production STL files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

import build_printable_board as cad
import build_sloped_lap_prototype as sloped
from build_canonical_chassis import export, removal


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "output" / "blender_sandbox"
PRODUCTION = ROOT / "output" / "canonical_chassis"
SOURCE = ROOT / "output" / "sloped_lap_prototype"

# The finished individual prototype STLs were normalized separately during export.
# These restore their shared source-space placement: two underlying spaces run
# from X=0..86, Y=0..48, with test lugs extending to Y=-8 and Y=56.
A_WORLD_OFFSET = np.array([0.0, -8.0, 0.0])
B_WORLD_OFFSET = np.array([38.2, -8.0, 0.0])
PIN_Z_OFFSET = 0.2


def hashes() -> dict[str, str]:
    paths = sorted(PRODUCTION.glob("*/quadrant_*.stl"))
    assert len(paths) == 16
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def load_translated(path: Path, offset: np.ndarray) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(path)
    mesh.apply_translation(offset)
    return mesh


def positive(mesh: trimesh.Trimesh, name: str) -> None:
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
    assert np.all(np.bincount(mesh.edges_unique_inverse) == 2), name
    assert abs(mesh.bounds[0, 2]) < .001, (name, mesh.bounds)


def write_pair(name: str, mesh: trimesh.Trimesh, output: Path, inventory: list[dict[str, object]], role: str,
               allow_multiple_components: bool = False) -> None:
    stl = output / f"{name}.stl"
    obj = output / f"{name}.obj"
    # Canonical exporter validates single disconnected-free components. The
    # assembled reference deliberately contains separately mating parts.
    if allow_multiple_components:
        mesh.export(stl)
        written = trimesh.load_mesh(stl)
        components = written.split()
        assert len(components) > 1
        for component in components:
            positive(component, name + " component")
    else:
        written = export(mesh, stl)
        positive(written, name)
    mesh.export(obj)
    obj_mesh = trimesh.load_mesh(obj)
    if allow_multiple_components:
        for component in obj_mesh.split():
            positive(component, name + " OBJ component")
    else:
        positive(obj_mesh, name + " OBJ")
    inventory.append({"name": name, "role": role, "stl": stl.name, "obj": obj.name,
                      "xyz_mm": written.extents.round(3).tolist(),
                      "bounds_mm": written.bounds.round(3).tolist(),
                      "volume_mm3": round(float(written.volume), 3)})


def generic_chassis(width: float, height: float, sockets: list[tuple[float, float]]) -> trimesh.Trimesh:
    outline = cad.curved_rectangle((0, 0, width, height), [8] * 4)
    body = cad.extrude(outline, 10)
    cuts = []
    for x, y in sockets:
        socket = cad.curved_rectangle((x, y, x + 36, y + 36), [2] * 4)
        cuts += [cad.extrude(socket, 3.2, 7), cad.extrude(removal(socket), 1.3, 8.8)]
    return cad.difference(body, cad.union(cuts))


def pin_reference(diameter: float, family: int, y: float) -> trimesh.Trimesh:
    # sloped.pin builds the assembly orientation: head on top, shaft down.
    mesh = sloped.pin(diameter, family, 2)
    mesh.apply_translation([43, y, -PIN_Z_OFFSET])
    return mesh


def lug_reference(index: int, hole: float) -> trimesh.Trimesh:
    x, y, _, _ = sloped.CENTERS[index]
    lug = sloped.lug_profile(x, y)
    lap = trimesh.boolean.intersection([cad.extrude(lug, 10), sloped.diagonal_half(index)], engine="manifold")
    bore = sloped.bore(hole / 2, -1 if index == 0 else 10, 0 if index == 0 else .7)
    bore.apply_translation([x, y, 0])
    mesh = cad.difference(lap, bore)
    # Keep the shared reference space; only Z must touch zero.
    return mesh


def exploded_png(parts: list[tuple[trimesh.Trimesh, str, str]], destination: Path) -> None:
    figure = plt.figure(figsize=(12, 8))
    axis = figure.add_subplot(111, projection="3d")
    for mesh, color, label in parts:
        axis.add_collection3d(Poly3DCollection(mesh.triangles, facecolors=color, edgecolors="none", alpha=.85))
        center = mesh.bounds.mean(axis=0)
        axis.text(*center, label, color="black")
    axis.set_xlim(-6, 105); axis.set_ylim(-24, 76); axis.set_zlim(-1, 26)
    axis.set_box_aspect((111, 100, 27)); axis.view_init(elev=28, azim=-58)
    axis.set_title("Blender sandbox exploded reference: A + B slide together; pins insert vertically")
    axis.set_axis_off()
    figure.tight_layout(); figure.savefig(destination, dpi=160); plt.close(figure)


def write_readme(output: Path, inventory: list[dict[str, object]]) -> None:
    rows = [
        "# Blender sandbox kit",
        "",
        "This folder is an editable, disposable Blender test kit. It is not an input to the production chassis generator or validation baseline. Manual edits made here must never be copied back to the real boards without a deliberate new engineering and validation pass.",
        "",
        "STL is unitless. Import and export every STL here as **millimetres** in Blender. OBJ files contain the same geometry and coordinates for convenience.",
        "",
        "## Coordinate convention",
        "",
        "All bottom surfaces are at Z=0. Generic pieces use a lower-left local XY origin. The sloped prototype references intentionally share one assembly coordinate system: the two ordinary board spaces occupy X=0..86 and Y=0..48; test lugs extend to Y=-8 and Y=56. `sloped_part_B_reference` therefore begins at X=38.2 rather than resetting to X=0. This makes A, B, isolated lugs, and assembled references line up when imported together.",
        "",
        "Standalone pin references have their own bottom at Z=0. In `sloped_assembled_reference`, pins are positioned 0.2 mm upward to reproduce their table-clearance position in the joint.",
        "",
        "## Canonical compatibility surfaces",
        "",
        "Keep these unchanged if an edited part might later need to interoperate with the canonical system:",
        "",
        "- Universal socket: 36 × 36 mm, 3 mm deep, R2 corners, with its current common top fingernail recess.",
        "- Grid pitch: 38 mm; normal divider: 2 mm; board thickness: 10 mm; ordinary outer track rim: 6 mm.",
        "- Tile interface: the socket floor and all four socket walls; tile clearance is not selected yet. The generic 36 × 36 tile is a nominal reference, not a confirmed print-fit tile.",
        "- Section seam: 0.25 mm. The production snap-key/rail system remains canonical; the sloped lap lock is experimental and must not be propagated yet.",
        "",
        "## Experimental sloped lock reference",
        "",
        "The current experimental lock uses 45-degree sloped lap faces with 0.4 mm vertical / 0.283 mm face-normal gap. It projects 8 mm locally outside the ordinary rim. A is below Z=47.8−X and B is above Z=48.2−X. Representative 4 mm and 5 mm pin families use 4.4 mm and 5.4 mm bores respectively; both shown pins use the 0.20 mm-per-side fit variant. Pin head: 12 × 8 × 2.4 mm with a 0.6 mm shaft/root fillet. The 5 mm bore has a 2.1 mm minimum bearing thickness at its limiting edge. These dimensions are test geometry only.",
        "",
        "## Files",
        "",
        "| File stem | Role | XYZ extent (mm) |",
        "| --- | --- | ---: |",
    ]
    for item in inventory:
        xyz = " × ".join(f"{value:.3f}" for value in item["xyz_mm"])
        rows.append(f"| {item['name']} | {item['role']} | {xyz} |")
    rows += ["", "`sloped_assembled_reference` is the only deliberately assembled multi-part reference mesh. All other files remain separate for editing.",
             "", "Production references: `sloped_part_A_reference`, `sloped_part_B_reference`, and the exported tile/socket dimensions. Disposable experiments: generic chassis pieces, isolated lugs, pins, generic tile, and all manual Blender edits."]
    (output / "BLENDER_SANDBOX_README.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export separate Blender sandbox reference meshes.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    before = hashes()
    inventory: list[dict[str, object]] = []

    part_a = load_translated(SOURCE / "prototype_2x1_part_A.stl", A_WORLD_OFFSET)
    part_b = load_translated(SOURCE / "prototype_2x1_part_B.stl", B_WORLD_OFFSET)
    positive(part_a, "prototype source A"); positive(part_b, "prototype source B")
    write_pair("sloped_part_A_reference", part_a, output, inventory, "production-reference prototype half A")
    write_pair("sloped_part_B_reference", part_b, output, inventory, "production-reference prototype half B")

    pin4 = pin_reference(4.0, 4, -3.0)
    pin5 = pin_reference(5.0, 5, 51.0)
    write_pair("pin_4mm_020_clearance_reference", pin4, output, inventory, "experimental 4 mm pin reference")
    write_pair("pin_5mm_020_clearance_reference", pin5, output, inventory, "experimental 5 mm pin reference")

    assembled = trimesh.util.concatenate([part_a, part_b, pin4, pin5])
    write_pair("sloped_assembled_reference", assembled, output, inventory,
               "assembled reference mesh: A + B + 4 mm and 5 mm pins", allow_multiple_components=True)

    for path in sorted((SOURCE / "tiles").glob("*.stl")):
        mesh = trimesh.load_mesh(path)
        write_pair(f"{path.stem}_reference", mesh, output, inventory, "tile-clearance test reference")

    generic_tile = cad.extrude(cad.curved_rectangle((0, 0, 36, 36), [2] * 4), 2.8)
    write_pair("generic_canonical_36mm_tile", generic_tile, output, inventory, "nominal generic tile; not a selected print fit")
    one_space = generic_chassis(48, 48, [(6, 6)])
    write_pair("generic_single_space_chassis", one_space, output, inventory, "generic single-space canonical chassis")
    two_by_two = generic_chassis(86, 86, [(6, 6), (44, 6), (6, 44), (44, 44)])
    write_pair("generic_2x2_chassis", two_by_two, output, inventory, "generic 2×2 canonical chassis")

    lower_lug = lug_reference(0, 4.4)
    upper_lug = lug_reference(1, 4.4)
    write_pair("sloped_lug_A_lower_4mm_reference", lower_lug, output, inventory, "isolated lower mating lug")
    write_pair("sloped_lug_B_upper_4mm_reference", upper_lug, output, inventory, "isolated upper mating lug")

    exploded_a = part_a.copy(); exploded_b = part_b.copy(); exploded_b.apply_translation([18, 0, 7])
    exploded_pin4 = pin4.copy(); exploded_pin4.apply_translation([0, 0, 14])
    exploded_pin5 = pin5.copy(); exploded_pin5.apply_translation([18, 0, 14])
    exploded_png([(exploded_a, "#a81332", "A"), (exploded_b, "#e3b12e", "B"),
                  (exploded_pin4, "#24a250", "4 mm pin"), (exploded_pin5, "#24a250", "5 mm pin")],
                 output / "blender_sandbox_exploded.png")
    write_readme(output, inventory)
    assert hashes() == before, "Production STL geometry changed"
    (output / "sandbox_validation.json").write_text(json.dumps({"passed": True, "exports": inventory,
        "production_hashes_unchanged": True, "units": "millimetres", "experimental_lock_not_production": True}, indent=2) + "\n")
    print(f"PASS: exported {len(inventory)} STL/OBJ pairs to {output}; production hashes unchanged.")


if __name__ == "__main__":
    main()
