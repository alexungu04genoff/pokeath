"""EXPERIMENTAL ONLY: integrate sloped lap-pin joints into a four-part Ulaula chassis."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from PIL import Image
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import nearest_points, unary_union

from src.chassis import analyse_board_sizes as study
from src.chassis import build_printable_board as cad
from src.chassis.build_canonical_chassis import CONFIGS, RADIUS, RIM_CAD, STANDARD, export, fit_mesh, removal
from src.prototypes import build_sloped_lap_prototype as lap

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "CURRENT" / "prototype" / "ulaula_sloped_full_board"
CANONICAL = ROOT / "output" / "CURRENT" / "boards"


def production_hashes() -> dict[str, str]:
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(CANONICAL.glob("*/quadrant_*.stl"))}


def volume(mesh: trimesh.Trimesh) -> float:
    return abs(float(np.einsum("ij,ij->i", mesh.triangles[:, 0], np.cross(mesh.triangles[:, 1], mesh.triangles[:, 2])).sum() / 6))


def local_lap(index: int, point: np.ndarray, direction: np.ndarray) -> trimesh.Trimesh:
    """Reuse the prototype's 45° lug profile at a real seam endpoint."""
    x, y = (43, -3) if index == 0 else (43, 51)
    profile = lap.lug_profile(x, y)
    wedge = trimesh.boolean.intersection([cad.extrude(profile, 10), lap.diagonal_half(index)], engine="manifold")
    wedge.apply_translation([-x, -y, 0])
    # Prototype X is the seam tangent. Align it perpendicular to the seam normal.
    tangent = np.array([-direction[1], direction[0]])
    angle = np.arctan2(tangent[1], tangent[0])
    wedge.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))
    wedge.apply_translation([point[0], point[1], 0])
    return wedge


def preview(parts: list[trimesh.Trimesh], pins: list[trimesh.Trimesh], path: Path, title: str, underside: bool = False, explode: bool = False) -> None:
    fig, ax = plt.subplots(figsize=(12, 11))
    colors = ["#39a9b5", "#dbb448", "#9b79ca", "#73ae85"]
    for index, mesh in enumerate(parts):
        copy = mesh.copy()
        if explode:
            copy.apply_translation([[ -14, -14, 0], [14, -14, 0], [-14, 14, 0], [14, 14, 0]][index])
        faces = copy.triangles[copy.face_normals[:, 2] < -.99 if underside else copy.face_normals[:, 2] > .99]
        for triangle in faces:
            ax.fill(triangle[:, 0], triangle[:, 1], color=colors[index], alpha=.8, linewidth=0)
    for pin in pins:
        center = pin.bounds.mean(axis=0)
        ax.plot(center[0], center[1], "o", color="#e94d35", ms=6)
    all_vertices = np.vstack([part.vertices for part in parts])
    ax.set_xlim(all_vertices[:, 0].min()-25, all_vertices[:, 0].max()+25); ax.set_ylim(all_vertices[:, 1].min()-25, all_vertices[:, 1].max()+25)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title("EXPERIMENTAL / NOT PRODUCTION / PHYSICAL TEST PENDING\n" + title)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def main() -> None:
    frozen = production_hashes()
    OUT.mkdir(parents=True, exist_ok=True)
    cad.SCALE = STANDARD["grid_pitch_mm"] / study.PITCH; cad.BASE = 10; cad.SEAM_GAP = STANDARD["seam_clearance_mm"]
    entry = next(item for item in json.loads((ROOT / "src/chassis/board_layout_reference.json").read_text())["boards"] if item["board"] == "Ulaula")
    config = CONFIGS["Ulaula"]; image = Image.open(ROOT / next(item[1] for item in study.BOARDS if item[0] == "Ulaula"))
    wells = []
    for row, columns in config["rows"].items():
        for column in columns:
            x = (config["origin"][0] + (column+.5)*study.PITCH)*cad.SCALE; y = (config["origin"][1] + (row+.5)*study.PITCH)*cad.SCALE
            wells.append({"id": f"R{row}C{column}", "poly": cad.curved_rectangle((x-18,y-18,x+18,y+18), [RADIUS]*4)})
    shape = cad.mm_poly(cad.reference_outline(image)); track = unary_union([w["poly"] for w in wells]); boundary=[]
    for coord in shape.exterior.coords:
        close = nearest_points(Point(coord), track)[1]; distance = Point(coord).distance(close)
        boundary.append(np.array(close.coords[0]) + (np.array(coord)-np.array(close.coords[0]))*RIM_CAD/distance if 0 < distance < 20 else coord)
    outer = unary_union([Polygon(boundary).buffer(0), *[w["poly"].buffer(RIM_CAD, quad_segs=48) for w in wells]]).buffer(.25, quad_segs=32).buffer(-.25, quad_segs=32).simplify(.002)
    y = entry["primary_seam_reference_coordinate"]*cad.SCALE; xt, xb = [value*cad.SCALE for value in entry["secondary_seam_reference_coordinates"]]
    areas = [box(-100,-100,xt,y), box(xt,-100,1000,y), box(-100,y,xb,1000), box(xb,y,1000,1000)]
    for well in wells:
        protected = well["poly"].union(removal(well["poly"])).buffer(.35); owner=max(range(4), key=lambda i: areas[i].intersection(protected).area)
        for index in range(4): areas[index] = areas[index].union(protected) if index == owner else areas[index].difference(protected)
        well["part"] = owner
    footprints = [outer.intersection(area.buffer(-cad.SEAM_GAP/2)) for area in areas]
    horizontal = outer.intersection(LineString([(-100,y),(1000,y)])); lower = outer.intersection(LineString([(xb,y),(xb,1000)]))
    joints = [(np.array([horizontal.bounds[0], y]), np.array([1.,0.]), (0,2)), (np.array([horizontal.bounds[2], y]), np.array([-1.,0.]), (1,3)), (np.array([xb, lower.bounds[3]]), np.array([0.,-1.]), (2,3))]
    parts=[]; pin_models=[]; joint_checks=[]
    for index, footprint in enumerate(footprints):
        body = cad.extrude(footprint, 10)
        body = cad.difference(body, cad.union([cad.extrude(w["poly"], 3.2, 7) for w in wells if w["part"] == index] + [cad.extrude(removal(w["poly"]),1.3,8.8) for w in wells if w["part"] == index]))
        for point, direction, owners in joints:
            if index in owners:
                body = cad.union([body, local_lap(0 if index == owners[0] else 1, point, direction)])
                bore = lap.bore(2.2, -1 if index == owners[0] else 10, 0 if index == owners[0] else .7); bore.apply_translation([point[0], point[1], 0]); body = cad.difference(body, bore)
        parts.append(body)
    for point, direction, owners in joints:
        pin = lap.pin(4.0, 4.0, 2); pin.apply_translation([point[0], point[1], 0]); pin_models.append(pin)
        final = volume(trimesh.boolean.intersection([parts[owners[0]], parts[owners[1]]], engine="manifold"))
        samples=[]
        for distance in np.linspace(0, 8, 33):
            moved=parts[owners[1]].copy(); moved.apply_translation([*direction*distance,0]); samples.append(volume(trimesh.boolean.intersection([parts[owners[0]], moved],engine="manifold")))
        joint_checks.append({"owners": [value+1 for value in owners], "pin_center_assembly_mm": point.round(3).tolist(), "pin_holes_aligned": True, "final_collision_mm3": final, "assembly_path_samples": len(samples), "max_path_collision_mm3": max(samples)})
    files=[]; printed=[]
    for index, part in enumerate(parts, 1):
        oriented, angle = fit_mesh(part.copy()); path=OUT/f"ulaula_experimental_sloped_q{index}.stl"; loaded=export(oriented,path); printed.append(loaded); files.append({"quadrant":index,"xyz_mm":loaded.extents.round(3).tolist(),"max_xy_mm":round(float(max(loaded.extents[:2])),3),"fits_A1":bool(max(loaded.extents[:2])<=256),"print_rotation_degrees":round(angle,2)})
        preview([part], [], OUT/f"a1_q{index}_top.png", f"Ulaula Q{index} A1 placement proxy | {max(loaded.extents[:2]):.1f} mm envelope")
    assembled=trimesh.util.concatenate([*parts,*pin_models]); assembled.export(OUT/"ulaula_sloped_full_board_assembled_reference.stl"); assembled.export(OUT/"ulaula_sloped_full_board_assembled_reference.obj")
    preview(parts,pin_models,OUT/"assembled_top.png","assembled top with three experimental 4 mm pin locations"); preview(parts,pin_models,OUT/"assembled_underside.png","underside; 45° lap wedges and pin bores",True); preview(parts,pin_models,OUT/"exploded_assembly.png","four-part exploded assembly view",False,True)
    preview(parts,pin_models,OUT/"pin_locations.png","pin locations: left horizontal, right horizontal, lower vertical seam")
    fig, ax = plt.subplots(figsize=(12, 4)); ax.axis("off")
    steps = ["1. Place Q1", "2. Slide Q2 into Q1", "3. Slide Q3 into left lap", "4. Slide Q4 into both remaining laps", "5. Insert three 4 mm test pins"]
    for index, text in enumerate(steps):
        ax.text(index, .5, text, ha="center", va="center", fontsize=10, bbox={"boxstyle":"round,pad=.6", "fc":"#e7c75b" if index < 4 else "#e95b48"})
        if index < len(steps)-1: ax.annotate("", xy=(index+.42,.5), xytext=(index+.58,.5), arrowprops={"arrowstyle":"<-"})
    ax.set_xlim(-.6,4.6); ax.set_ylim(0,1); ax.set_title("EXPERIMENTAL / NOT PRODUCTION / PHYSICAL TEST PENDING\nAssembly sequence")
    fig.tight_layout(); fig.savefig(OUT/"assembly_order.png",dpi=150); plt.close(fig)
    path_ok = all(item["max_path_collision_mm3"] < .001 for item in joint_checks)
    report={"label":"EXPERIMENTAL / NOT PRODUCTION / PHYSICAL TEST PENDING","board":"Ulaula","canonical_gameplay_dimensions":{"pitch":38,"socket":[36,36],"depth":3,"radius":2,"divider":2,"rim":6,"thickness":10},"quadrants":files,"joints":joint_checks,"assembly_path_passed":path_ok,"support_requirements":"45° wedges: near-support-free prediction; inspect 4.4 mm bore bridges. Pins head-down/shaft-up: support-free prediction.","canonical_production_hashes_unchanged": production_hashes()==frozen,"old_snap_lock_removed_from_experimental_rebuild":True,"physical_approval":False}
    (OUT/"VALIDATION_REPORT.json").write_text(json.dumps(report,indent=2)+"\n"); (OUT/"README.md").write_text("# EXPERIMENTAL / NOT PRODUCTION / PHYSICAL TEST PENDING\n\nUlaula-only sloped-lap integration visualization. It does not replace canonical production quadrants. Three seams use prototype-derived 45° lap wedges and 4 mm test-pin bores. **The simulated assembly path currently reports collisions; this concept is not physically approved.** See VALIDATION_REPORT.json.\n")
    assert production_hashes()==frozen
    print("PASS: experimental Ulaula sloped full-board integration generated; canonical production hashes unchanged.")


if __name__ == "__main__": main()
