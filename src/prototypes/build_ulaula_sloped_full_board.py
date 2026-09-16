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
from src.chassis.build_canonical_chassis import CONFIGS, RADIUS, RIM_CAD, STANDARD, fit_mesh, removal
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


def joint_transform(point, direction):
    # Across the split toward the second owner; inward from the outer edge.
    tangent = np.array([0., 1.]) if direction[0] else np.array([1., 0.])
    matrix = np.eye(4)
    matrix[:2, 0] = tangent
    matrix[:2, 1] = direction
    matrix[:2, 3] = point
    return matrix


def joint_tools(point, direction):
    from shapely import affinity
    profile = affinity.translate(lap.lug_profile(43, -3), -43, 3)
    matrix = joint_transform(point, direction)
    footprint = cad.extrude(profile, 10)
    region = cad.extrude(profile.buffer(.25, quad_segs=48), 10)
    halves = []
    for index in range(2):
        half = lap.diagonal_half(index)
        half.apply_translation([-43, 0, 0])
        half.apply_transform(matrix)
        halves.append(half)
    footprint.apply_transform(matrix)
    region.apply_transform(matrix)
    return footprint, region, halves


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


def chassis_geometry():
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
    return footprints, wells, joints


def build_parts(footprints, wells, joints, corrected=False):
    parts=[]
    for index, footprint in enumerate(footprints):
        body = cad.extrude(footprint, 10)
        body = cad.difference(body, cad.union([cad.extrude(w["poly"], 3.2, 7) for w in wells if w["part"] == index] + [cad.extrude(removal(w["poly"]),1.3,8.8) for w in wells if w["part"] == index]))
        for point, direction, owners in joints:
            if index in owners:
                half_index = 0 if index == owners[0] else 1
                if corrected:
                    lug, region, halves = joint_tools(point, direction)
                    local = trimesh.boolean.intersection([cad.union([body, lug]), region, halves[half_index]], engine="manifold")
                    body = cad.union([cad.difference(body, region), local])
                else:
                    body = cad.union([body, local_lap(half_index, point, direction)])
                bore = lap.bore(2.2, -1 if index == owners[0] else 10, 0 if index == owners[0] else .7); bore.apply_translation([point[0], point[1], 0]); body = cad.difference(body, bore)
        parts.append(body)
    return parts


def export_experiment(mesh, path):
    # The canonical exporter's 2.5 micron edge collapse can open this lap mesh.
    # Direct float32 STL preserves its topology; verify rather than weld it.
    mesh.export(path)
    loaded = trimesh.load_mesh(path)
    assert loaded.is_watertight and loaded.is_winding_consistent and loaded.volume > 0
    assert len(loaded.split()) == 1 and np.all(loaded.nondegenerate_faces())
    assert np.all(np.bincount(loaded.edges_unique_inverse) == 2)
    assert np.isfinite(loaded.vertices).all()
    return loaded


def surface_preview(parts, pins, path, title, underside=False):
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb
    colors = ["#39a9b5", "#dbb448", "#9b79ca", "#73ae85"]
    triangles=[]; shades=[]
    for mesh, color in [*zip(parts,colors), *[(p,"#e85c30") for p in pins]]:
        mask = mesh.face_normals[:,2] < -1e-8 if underside else mesh.face_normals[:,2] > 1e-8
        faces=mesh.triangles[mask]
        height=np.clip(faces[:,:,2].mean(axis=1)/10,0,1)
        if underside: height=1-height
        shade=(.45+.55*height)*(.7+.3*np.abs(mesh.face_normals[mask,2]))
        triangles.extend(faces); shades.extend(np.asarray(to_rgb(color))[None,:]*shade[:,None])
    triangles=np.asarray(triangles); shades=np.asarray(shades)
    order=np.argsort(triangles[:,:,2].mean(axis=1))
    if underside: order=order[::-1]
    fig, ax=plt.subplots(figsize=(11,11))
    ax.add_collection(PolyCollection(triangles[order,:,:2], facecolors=shades[order],
                                     edgecolors="none", antialiaseds=False))
    points=np.vstack([m.vertices for m in [*parts,*pins]])
    ax.set_xlim(points[:,0].min()-12,points[:,0].max()+12)
    ax.set_ylim(points[:,1].max()+12,points[:,1].min()-12)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title,fontsize=11)
    fig.tight_layout(); fig.savefig(path,dpi=150); plt.close(fig)


def verify_socket_floors(mesh, wells, owner):
    triangles = mesh.triangles
    mask = np.all(np.isclose(triangles[:,:,2], 7, atol=.0001, rtol=0), axis=1)
    floor = unary_union([Polygon(t[:,:2]) for t in triangles[mask]])
    expected = unary_union([w["poly"] for w in wells if w["part"] == owner])
    assert floor.buffer(.001).covers(expected) and expected.buffer(.001).covers(floor)
    return {"passed": True, "xy_tolerance_mm": .001,
            "symmetric_difference_mm2": floor.symmetric_difference(expected).area}


def exported_pin():
    (OUT/"pins").mkdir(exist_ok=True)
    model = lap.pin(4.,4.,2)
    rotated = model.copy()
    rotation = trimesh.transformations.rotation_matrix(np.pi, [1,0,0])
    rotated.apply_transform(rotation)
    loaded = export_experiment(lap.print_pin(model), OUT/"pins"/"smooth_4mm_pin.stl")
    loaded.apply_translation(rotated.bounds[0])
    loaded.apply_transform(np.linalg.inv(rotation))
    return loaded


def a1_preview(mesh, index):
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb
    triangles = mesh.triangles[mesh.face_normals[:,2] > 1e-8]
    order = np.argsort(triangles[:,:,2].mean(axis=1))
    shade = .45+.55*np.clip(triangles[:,:,2].mean(axis=1)/10,0,1)
    colors = np.asarray(to_rgb("#39a9b5"))[None,:]*shade[:,None]
    offset = (256-mesh.extents[:2])/2
    fig, ax = plt.subplots(figsize=(7,7))
    ax.add_patch(plt.Rectangle((0,0),256,256,fill=False,lw=2))
    ax.add_collection(PolyCollection(triangles[order,:,:2]+offset,facecolors=colors[order],
                                     edgecolors="none",antialiaseds=False))
    ax.set(xlim=(-5,261),ylim=(-5,261),aspect="equal",
           title=f"Experimental Q{index} | A1 256 x 256 mm\n{mesh.extents[0]:.3f} x {mesh.extents[1]:.3f} x 10 mm")
    fig.tight_layout(); fig.savefig(OUT/f"a1_q{index}_top.png",dpi=140); plt.close(fig)


def frozen_hashes():
    paths = list(CANONICAL.rglob("*")) + list((OUT.parent / "sloped_lap_2x1").rglob("*"))
    paths.append(ROOT / "src/prototypes/build_sloped_lap_prototype.py")
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}


def intersect(*meshes):
    return trimesh.boolean.intersection(list(meshes), engine="manifold")


def diagnose(parts, footprints, joints):
    records = []
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    for ax, (point, direction, owners) in zip(axes, joints):
        collision = intersect(*(parts[k] for k in owners))
        collision.export(OUT / f"old_collision_q{owners[0]+1}_q{owners[1]+1}.stl")
        components = []
        for half, owner in enumerate(owners):
            other = owners[1-half]
            component = intersect(collision, local_lap(half, point, direction), cad.extrude(footprints[other], 10))
            components.append({"lug_quadrant": owner+1, "chassis_quadrant": other+1,
                               "volume_mm3": volume(component), "bounds_mm": component.bounds.tolist()})
            for triangle in component.triangles:
                ax.fill(triangle[:, 0], triangle[:, 1], color=["#dc4141", "#7c38bc"][half], alpha=.12, linewidth=0)
        ax.set_aspect("equal"); ax.set_title(f"Q{owners[0]+1} / Q{owners[1]+1}: {volume(collision):.3f} mm³")
        ax.set_xlabel("Assembly X (mm)"); ax.set_ylabel("Assembly Y (mm)")
        records.append({"owners": [k+1 for k in owners], "original_pin_center_mm": point.tolist(),
                        "final_collision_mm3": volume(collision), "components": components,
                        "lug_lug_collision_mm3": volume(intersect(*(local_lap(i, point, direction) for i in range(2)))),
                        "chassis_chassis_collision_mm3": volume(intersect(*(cad.extrude(footprints[k],10) for k in owners)))})
    fig.suptitle("Original seated interference | red: first lug / other chassis; purple: second lug / other chassis")
    fig.tight_layout(); fig.savefig(OUT / "old_collision_debug.png", dpi=160); plt.close(fig)
    return records


def assembly_diagram(parts, sequence):
    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    colors = ["#39a9b5", "#dbb448", "#9b79ca", "#73ae85"]
    for position, ax in enumerate(axes):
        for q in sequence["order"][:position+1]:
            mesh = parts[q-1]
            for triangle in mesh.triangles[mesh.face_normals[:,2] < -.99]:
                ax.fill(triangle[:,0], triangle[:,1], color=colors[q-1], linewidth=0, antialiased=False)
            center = mesh.bounds.mean(axis=0)
            ax.text(*center[:2], f"Q{q}", ha="center")
        q = sequence["order"][position]
        if position:
            candidate = next(c for c in sequence["steps"][position-1]["candidates"] if c["passed"])
            v = np.asarray(candidate["outward_unit_vector"][:2])
            center = parts[q-1].bounds.mean(axis=0)[:2]
            ax.annotate("", xy=center, xytext=center+v*85, arrowprops={"arrowstyle":"->", "lw":3, "color":"#d33727"})
            ax.set_title(f"{position+1}. Add Q{q}: " + {(0.,1.):"slide up (-Y)",(1.,0.):"slide left (-X)",(0.,-1.):"slide down (+Y)"}.get(tuple(v), str(-v)))
        else: ax.set_title(f"1. Place Q{q}")
        ax.set_xlim(0,460); ax.set_ylim(430,30); ax.set_aspect("equal"); ax.axis("off")
    fig.suptitle("Continuous planar assembly, pins removed | insert all three pins vertically after seating")
    fig.tight_layout(); fig.savefig(OUT / "assembly_order.png", dpi=160); plt.close(fig)


def main() -> None:
    from itertools import combinations, permutations
    from src.prototypes.validate_ulaula_sloped_assembly import enumerate_orders, swept_collision, VOLUME_TOLERANCE
    expected = {"grid_pitch_mm":38, "socket_size_mm":[36,36], "socket_depth_mm":3,
                "socket_corner_radius_mm":2, "divider_width_mm":2, "outer_track_rim_mm":6,
                "board_thickness_mm":10, "seam_clearance_mm":.25}
    assert all(STANDARD[key] == value for key, value in expected.items())
    frozen = frozen_hashes()
    OUT.mkdir(parents=True, exist_ok=True)
    footprints, wells, original_joints = chassis_geometry()
    original = build_parts(footprints, wells, original_joints)
    diagnosis = diagnose(original, footprints, original_joints)
    # Every ordering is impossible in the original seated state, irrespective of path.
    old_orders = [{"order": [q+1 for q in order], "passed": False,
                   "reason": "Required seated state has real lug/chassis overlap"}
                  for order in permutations(range(4))]
    joints = [(point-2*direction, direction, owners) for point, direction, owners in original_joints]
    parts = build_parts(footprints, wells, joints, corrected=True)
    baseline = build_parts(footprints, wells, [])
    regions = [joint_tools(p,d)[1] for p,d,_ in joints]
    all_regions = cad.union(regions)
    # The entire frozen chassis outside the local joint masks is identical.
    for before, after in zip(baseline, parts):
        assert volume(cad.difference(cad.difference(before, after), all_regions)) < VOLUME_TOLERANCE
        assert volume(cad.difference(cad.difference(after, before), all_regions)) < VOLUME_TOLERANCE
    protected = cad.union([cad.extrude(w["poly"].union(removal(w["poly"])),10) for w in wells])
    assert volume(intersect(protected, all_regions)) < VOLUME_TOLERANCE, "Relief reaches gameplay geometry"
    files=[]; reloaded=[]
    for index, part in enumerate(parts, 1):
        oriented, angle = fit_mesh(part.copy())
        rotation = trimesh.transformations.rotation_matrix(-np.deg2rad(angle), [0,0,1])
        rotated = part.copy(); rotated.apply_transform(rotation)
        transform = rotation.copy(); transform[:3,3] = -rotated.bounds[0]
        loaded = export_experiment(oriented, OUT/f"ulaula_experimental_sloped_q{index}.stl")
        assert np.all(np.bincount(loaded.edges_unique_inverse)==2)
        assert max(loaded.extents[:2]) < 248
        files.append({"quadrant":index, "xyz_mm":loaded.extents.round(3).tolist(),
                      "max_xy_mm":float(max(loaded.extents[:2])), "fits_A1":True,
                      "below_248_mm":True, "watertight_manifold_single_solid":True,
                      "print_rotation_degrees":angle, "assembly_to_print_transform":transform.tolist()})
        a1_preview(loaded, index)
        loaded.apply_transform(np.linalg.inv(transform))
        files[-1]["socket_floor_check"] = verify_socket_floors(loaded, wells, index-1)
        reloaded.append(loaded)
    parts = reloaded
    pair_checks = [{"owners":[a+1,b+1], "final_collision_mm3":volume(intersect(parts[a],parts[b]))}
                   for a,b in combinations(range(4),2)]
    assert all(c["final_collision_mm3"] < VOLUME_TOLERANCE for c in pair_checks)
    sequences = enumerate_orders(parts)
    (OUT/"assembly_search.json").write_text(json.dumps({"original":old_orders,"corrected":sequences},indent=2)+"\n")
    valid = next((s for s in sequences if s["passed"]), None)
    assert valid is not None, "No certified planar sequence; do not mark digitally validated"
    pin_models=[]; joint_checks=[]
    pin_template = exported_pin()
    for old, (point,direction,owners) in zip(diagnosis,joints):
        pin = pin_template.copy(); pin.apply_translation([*point,0]); pin_models.append(pin)
        pin_checks = [swept_collision(pin, part, [0,0,15]) for part in parts]
        assert all(c["passed"] for c in pin_checks), "Pin binds on vertical insertion/withdrawal"
        # Both bore axes are constructed from precisely this center. Planar
        # displacement changes their separation by the displacement magnitude.
        joint_checks.append({"owners":[k+1 for k in owners], "pin_center_assembly_mm":point.tolist(),
                             "before_collision_mm3":old["final_collision_mm3"],
                             "final_collision_mm3":volume(intersect(*(parts[k] for k in owners))),
                             "coaxial_only_at_zero_relative_xy_translation":True,
                             "bore_diameter_mm":4.4,"shaft_diameter_mm":4.,
                             "continuous_vertical_pin_checks":pin_checks})
    assembled=trimesh.util.concatenate([*parts,*pin_models])
    assembled.export(OUT/"ulaula_sloped_full_board_assembled_reference.stl")
    assembled.export(OUT/"ulaula_sloped_full_board_assembled_reference.obj")
    label="DIGITALLY VALIDATED EXPERIMENT / PHYSICAL TEST STILL REQUIRED"
    surface_preview(parts,pin_models,OUT/"assembled_top.png",label)
    surface_preview(parts,pin_models,OUT/"assembled_underside.png",label,True)
    exploded=[]
    for index,part in enumerate(parts):
        copy=part.copy(); copy.apply_translation([[-18,-18,0],[18,-18,0],[-18,18,0],[18,18,0]][index]); exploded.append(copy)
    surface_preview(exploded,[],OUT/"exploded_assembly.png",label+"\nExploded illustration; follow assembly_order.png for actual motion")
    preview(parts,pin_models,OUT/"pin_locations.png","three vertical removable pins")
    assembly_diagram(parts,valid)
    assert frozen_hashes()==frozen, "Frozen production or 2x1 files changed"
    report={"label":label,"board":"Ulaula","passed":True,"physical_approval":False,
            "canonical_gameplay_dimensions": {"pitch":38,"socket":[36,36],"depth":3,"radius":2,"divider":2,"rim":6,"thickness":10},
            "quadrants":files,"joints":joint_checks,"all_six_seated_pairs":pair_checks,
            "assembly_path_passed":True,"valid_assembly_order":valid["order"],
            "valid_order_count":sum(s["passed"] for s in sequences),
            "assembly_steps": [{"quadrant":s["quadrant"], **next(c for c in s["candidates"] if c["passed"])} for s in valid["steps"]],
            "collision_tolerance_mm3":VOLUME_TOLERANCE,
            "path_method":"Continuous leading-triangle swept prisms plus initial solid; aggregate intersection upper bound <= tolerance. Eight planar directions per step, 600 mm free start, all 24 orders. Actual float32 STLs transformed back to assembly coordinates.",
            "pin_path_method":"Same continuous sweep, 15 mm vertical stroke, against all four quadrants; pins inserted only after all quadrants seat.",
            "joint_changes":{"pin_center_outward_shift_mm":2,"maximum_local_outward_projection_mm":7,"lap_angle_degrees":45,"vertical_face_gap_mm":.4,"local_relief_buffer_mm":.25},
            "gameplay_and_recess_masks_clear_of_modifications":True,
            "chassis_identical_outside_local_joint_regions":True,
            "canonical_production_hashes_unchanged":True,"sloped_lap_2x1_hashes_unchanged":True,
            "frozen_sha256":frozen,
            "support_requirements":"Flat base down, sockets up. 45 degree ramps; local 4.4 mm bore bridges require slicer/physical inspection with 0.4 mm nozzle. Pins flat head down. No sliced or physical support certification.",
            "warnings":["Experimental only; no production approval or propagation.","Physical PLA fit, thin tips, bearing strength and wear untested.","Smooth pins are gravity-retained and not captive on inversion.","The search certifies listed straight planar paths; it does not exhaust all possible motion planning."]}
    (OUT/"original_collision_diagnosis.json").write_text(json.dumps(diagnosis,indent=2)+"\n")
    (OUT/"VALIDATION_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    write_diagnostic_report(report,diagnosis)
    print("PASS:",label,"order",valid["order"],flush=True)


def write_diagnostic_report(report, diagnosis):
    lines=["# "+report["label"],"", "Ulaula only. Production boards and the existing 2×1 experiment are byte-for-byte unchanged. No gameplay tiles were generated.","",
           "## Original collision diagnosis", "",
           "The original builder unioned complementary wedges into intact 10 mm chassis material. Unlike the 2×1 builder, it omitted the local chassis relief. Neither wedge/wedge nor chassis/chassis intersections contribute any seated volume. Every reported collision is one wedge penetrating the opposite quadrant's chassis, including its inward/root region. The independently measured component volumes below include the actual bore subtraction.","",
           "At the right edge the old tangent points toward -Y, reversing which owner receives the full-height end of each wedge. This explains its much larger overlap. The two old profiles also came from opposite prototype edges, so their root projections were mirrored rather than sharing one consistently inward-oriented footprint. These are transplant errors, not boolean noise or a collision with a distant lock.","",
           "| Joint | Before mm³ | After mm³ | Exact old material intersections |","|---|---:|---:|---|"]
    for old,new in zip(diagnosis,report["joints"]):
        components="; ".join(f"Q{c['lug_quadrant']} wedge into Q{c['chassis_quadrant']} chassis: {c['volume_mm3']:.6f} mm³" for c in old["components"])
        lines.append(f"| {new['owners']} | {new['before_collision_mm3']:.6f} | {new['final_collision_mm3']:.9f} | {components} |")
    lines.extend(["", "Exact assembly-space bounding boxes are in original_collision_diagnosis.json. old_collision_debug.png colors the two contributing regions separately; old_collision_q*_q*.stl preserves the original intersection solids.","",
                  "## Local correction", "",
                  "Use one common profile with its reinforced root pointing inward and its slope coordinate pointing from the first owner to the second. Within a 0.25 mm buffered joint mask, partition chassis plus lug with the complementary 45° half-spaces. Their planes remain z=4.8-u and z=5.2-u, giving 0.4 mm vertical clearance. Move each pin center 2 mm outward to keep the entire relief clear of sockets and fingernail recesses; local outward projection is 7 mm. No board scaling or gameplay dimensions change. Set-difference checks prove that material outside those local masks is identical to the frozen chassis rebuild.","",
                  "## Four-piece assembly", "",
                  "All 24 original orders are impossible because their required final state already contains interference. Changing validation direction cannot fix that. The old validator's 8 mm direction follows the edge inward vector, not the wedge's slope coordinate, and cannot establish sequential assembly.","",
                  f"The corrected exported STLs have {report['valid_order_count']} certified orders among all 24 tested. Use **{' → '.join('Q'+str(q) for q in report['valid_assembly_order'])}**, with all pins removed:",""])
    lines.extend(["Q3 enters from below (-Y insertion), Q4 from the right (-X insertion), and Q2 from above (+Y insertion). Adding Q4 last in Q1-Q2-Q3-Q4 fails all eight tested directions: Q2 obstructs the rightward withdrawal, Q3 obstructs the downward withdrawal, and the diagonals also collide. Leaving Q2 until last removes that constraint.", ""])
    for step in report["assembly_steps"]:
        outward=np.array(step["outward_unit_vector"])
        lines.append(f"- Add Q{step['quadrant']} from XY offset {np.round(step['start_offset_mm'][:2],3).tolist()} mm; translate toward its seated position in direction {(-outward[:2]).tolist()}, against every already-installed quadrant.")
    lines.extend(["", "Then lower all three smooth 4 mm pins vertically. Their 4.4 mm bore axes coincide only at zero relative planar displacement; clearance permits small play and does not imply an infinitely precise seating detector. Vertical insertion and withdrawal over 15 mm are continuously checked against all four bodies. See assembly_order.png and assembly_search.json for diagrams and every candidate's results.","",
                  "## Validation and numerical limits", "",
                  "Motion checks cover the complete translation, not isolated samples: the initial solid plus every leading boundary triangle's swept prism contains the swept solid. Each prism is intersected with each obstacle. The sum of intersection volumes is a conservative bound because prisms can overlap. A bound at most 0.001 mm³ is accepted as boolean/tessellation noise; meaningful interference fails. Start offsets are 600 mm, beyond the complete assembly's XY diagonal, so incoming quadrants start fully separated. Reversing the certified outward sweep yields the insertion path. Eight cardinal/diagonal directions are tested at every step of every ordering. A failed direction is not a proof against arbitrary curved paths.","",
                  "All six seated quadrant pairs pass, not just the three locks. The shared exporter's 2.5 micron edge-collapse cleanup opened these meshes during development; this experiment directly exports float32 STL and verifies topology instead of welding vertices. All four reloaded float32 STL quadrants are watertight, consistently wound, single solids with two incident faces per edge. Gameplay/socket/recess masks are disjoint from the local changes. Frozen hashes cover every production-board file, every existing 2×1 file, and its builder source.","",
                  "| Quadrant | A1 placement X × Y × Z mm | Below 248 mm |", "|---|---|---|"])
    for q in report["quadrants"]: lines.append(f"| Q{q['quadrant']} | {' × '.join(f'{v:.3f}' for v in q['xyz_mm'])} | Yes |")
    lines.extend(["", "## Print and physical limits", "",report["support_requirements"],"",
                  "The 45° half-space construction preserves the approved-for-testing mechanical principle. Rigid PLA, no springs, snap tabs or flexing features. Slopes, thin tips, bore bridges, pin fit and wear still require slicing and physical testing. Smooth pins are gravity-retained and can fall out when inverted. This is not production-approved; Akala, Melemele and Poni are unchanged.","",
                  "Reproduce from repository root: `python -m src.prototypes.build_ulaula_sloped_full_board` with requirements-cad.txt. Generated STL/OBJ/PNG assets follow the repository's ignore policy; reports and generators are versioned."])
    (OUT/"README.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
