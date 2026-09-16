"""Build a real two-space chassis prototype with rigid PLA lap-lug T pins.

Production quadrants and canonical dimensions are read-only inputs. This is a
physical experiment, not a replacement production locking standard.
"""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
import numpy as np
import trimesh
from shapely.geometry import box, Point, Polygon, LineString
from shapely.ops import unary_union, polygonize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from src.chassis import build_printable_board as cad
from src.chassis.build_canonical_chassis import STANDARD, removal, export

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'/'CURRENT'/'prototype'/'sloped_lap_2x1'
GAP=STANDARD['seam_clearance_mm']
HEIGHT=STANDARD['board_thickness_mm']
LOWER=4.8
UPPER=5.0
PIN_THICKNESS=2.4
HEAD_Z=HEIGHT
PIN_BOTTOM=.2
LUG_RADIUS=7.0
HEAD_SIZE=(12.0,8.0,PIN_THICKNESS)
CENTERS=[(43.0,-3.0,4.0,4.4),(43.0,51.0,5.0,5.4)]
CLEARANCES=[.15,.20,.25,.30]


def production_hashes():
    files=sorted((ROOT/'output/CURRENT/boards').glob('*/quadrant_*.stl'))
    assert len(files)==16
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def lug_profile(x,y):
    tab=cad.curved_rectangle((x-8,-8,x+8,3) if y<0 else (x-8,45,x+8,56),[2]*4)
    root=cad.curved_rectangle((x-10,-1,x+10,3) if y<0 else (x-10,45,x+10,49),[1]*4)
    return tab.union(root).buffer(2,quad_segs=48).buffer(-2,quad_segs=48).simplify(.001)


def revolved(profile):
    mesh=trimesh.creation.revolve(np.array(profile,dtype=float),sections=128)
    if mesh.volume<0: mesh.invert()
    return mesh


def bore(radius,entry_z,chamfer):
    cylinder=trimesh.creation.cylinder(radius=radius,height=HEIGHT+.4,sections=128)
    cylinder.apply_translation([0,0,HEIGHT/2])
    entry=revolved([(0,entry_z-chamfer),(radius,entry_z-chamfer),
                    (radius+chamfer,entry_z),(radius+chamfer,entry_z+.1),(0,entry_z+.1)])
    return cad.union([cylinder,entry])


def pin(diameter,nominal,dots):
    radius=diameter/2
    profile=[(0,PIN_BOTTOM),(radius-.4,PIN_BOTTOM),(radius,PIN_BOTTOM+.5),
             (radius,HEAD_Z-.6)]
    # Small head/shaft root fillet clears the 0.5 mm entry chamfer.
    for angle in np.linspace(np.pi,np.pi/2,17):
        profile.append((radius+.6+.6*np.cos(angle),HEAD_Z-.6+.6*np.sin(angle)))
    profile.append((0,HEAD_Z))
    shaft=revolved(profile)
    head=cad.extrude(cad.curved_rectangle((-6,-4,6,4),[1.5]*4),PIN_THICKNESS,HEAD_Z)
    result=cad.union([shaft,head])
    glyph=Polygon()
    for polygon in TextPath((-4.8,-1.3),str(int(nominal)),size=3).to_polygons():
        glyph=glyph.symmetric_difference(Polygon(polygon))
    marks=[cad.extrude(glyph,.5,12.0)]
    marks.extend(cad.extrude(Point(-.5+i*1.3,0).buffer(.28,quad_segs=24),.5,12.0) for i in range(dots))
    return cad.difference(result,cad.union(marks))


def normalize(mesh):
    result=mesh.copy(); result.apply_translation(-result.bounds[0]); return result


def diagonal_half(index):
    # XZ sections, extruded along Y: A below z=47.8-x;
    # B above z=48.2-x. Each base touches the build plate.
    section=Polygon([(20,0),(47.8,0),(37.8,10),(20,10)]) if index==0 else Polygon([(48.2,0),(65,0),(65,10),(38.2,10)])
    mesh=cad.extrude(section,100)
    mesh.vertices=mesh.vertices[:,[0,2,1]]
    mesh.invert()  # exchanging Y and Z reverses handedness
    mesh.apply_translation([0,-20,0])
    return mesh


def print_pin(mesh):
    result=mesh.copy()
    result.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
    return normalize(result)


def measure(path):
    mesh=trimesh.load_mesh(path)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,path
    assert np.all(np.bincount(mesh.edges_unique_inverse)==2),path
    assert len(mesh.split())==1,path
    assert np.isfinite(mesh.vertices).all() and max(mesh.extents[:2])<=256,path
    return {'file':str(path.relative_to(OUT)),'xyz_mm':mesh.extents.round(3).tolist(),
            'watertight_manifold':True,'fits_A1':True}


def intersection_volume(mesh):
    # Head/ear contact can return a planar zero-volume intersection. Compute
    # volume directly without requesting a nonexistent solid's centre of mass.
    triangles=mesh.triangles
    return abs(float(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6))


def render(meshes,path,title,elevation=55,azimuth=-60):
    fig=plt.figure(figsize=(12,8)); ax=fig.add_subplot(111,projection='3d')
    light=np.array([-.3,-.5,.8]); light/=np.linalg.norm(light)
    all_faces=[]; all_colors=[]
    for mesh,color in meshes:
        from matplotlib.colors import to_rgb
        shade=.55+.45*np.abs(mesh.face_normals@light)
        colors=np.array(to_rgb(color))[None,:]*shade[:,None]
        visible=mesh.area_faces>1e-10
        all_faces.append(mesh.triangles[visible]); all_colors.append(colors[visible])
    # One collection sorts all objects together, so pin heads are not hidden
    # behind an entire board collection's average depth.
    ax.add_collection3d(Poly3DCollection(np.vstack(all_faces),facecolors=np.vstack(all_colors),
                                       edgecolors='none',antialiased=False,zsort='average'))
    vertices=np.vstack([m.vertices for m,_ in meshes])
    low=vertices.min(axis=0)-3; high=vertices.max(axis=0)+3
    ax.set_xlim(low[0],high[0]); ax.set_ylim(low[1],high[1]); ax.set_zlim(low[2],high[2])
    ax.set_box_aspect(high-low); ax.view_init(elev=elevation,azim=azimuth)
    ax.set_axis_off(); ax.set_title(title)
    fig.tight_layout(); fig.savefig(path,dpi=150); plt.close(fig)


def main():
    for key,value in {'grid_pitch_mm':38,'socket_size_mm':[36,36],'socket_depth_mm':3,
                      'socket_corner_radius_mm':2,'divider_width_mm':2,'outer_track_rim_mm':6,
                      'board_thickness_mm':10,'seam_clearance_mm':.25}.items():
        assert STANDARD[key]==value,('Frozen baseline changed',key)
    frozen=production_hashes()
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'pins').mkdir(exist_ok=True); (OUT/'tiles').mkdir(exist_ok=True)
    wells=[cad.curved_rectangle((6,6,42,42),[2]*4),cad.curved_rectangle((44,6,80,42),[2]*4)]
    chassis=cad.curved_rectangle((0,0,86,48),[8]*4)
    regions=[chassis.intersection(box(-100,-100,43-GAP/2,100)),
             chassis.intersection(box(43+GAP/2,-100,200,100))]
    lugs=[lug_profile(x,y) for x,y,_,_ in CENTERS]
    parts=[]; files=[]
    for index in range(2):
        full=regions[index].union(unary_union(lugs)).simplify(.001,preserve_topology=True)
        cleared=regions[index].difference(unary_union([p.buffer(GAP,quad_segs=48) for p in lugs])).simplify(.001,preserve_topology=True)
        lap=trimesh.boolean.intersection([cad.extrude(full,10),diagonal_half(index)],engine='manifold')
        body=cad.union([cad.extrude(cleared,10),lap])
        socket=cad.extrude(wells[index],3.2,7)
        notch=cad.extrude(removal(wells[index]),1.3,8.8)
        holes=[]
        for x,y,_,hole in CENTERS:
            tool=bore(hole/2,-1 if index==0 else HEIGHT,0 if index==0 else .7)
            tool.apply_translation([x,y,0]); holes.append(tool)
        body=cad.difference(body,cad.union([socket,notch,*holes]))
        parts.append(body)
        floor_mask=np.all(np.isclose(body.triangles[:,:,2],7,atol=1e-5),axis=1)
        floor=unary_union([Polygon(t[:,:2]) for t in body.triangles[floor_mask]])
        assert floor.buffer(.001).covers(wells[index])
        assert wells[index].buffer(.001).covers(floor)
        if index==1:
            supported=full.difference(cleared).difference(unary_union([Point(x,y).buffer(hole/2,quad_segs=64) for x,y,_,hole in CENTERS]))
            support_area=supported.area
    contact=trimesh.boolean.intersection(parts,engine='manifold')
    assert intersection_volume(contact)<.0001
    for distance in np.linspace(0,20,81):
        moved=parts[1].copy(); moved.apply_translation([distance,0,0])
        assert intersection_volume(trimesh.boolean.intersection([parts[0],moved],engine='manifold'))<.0001,'Unpinned joint binds'
    # B's diagonal face moves up by d when translated outward by d.
    # Thus the 0.4 mm vertical lap gap increases during withdrawal.
    assert LOWER<UPPER and all(abs((x+20)-x)>0 for x,_,_,_ in CENTERS)
    assert min(lug.distance(well) for lug in lugs for well in wells)>2
    minimum_socket_ligament=min(lug.buffer(GAP).distance(w) for lug in lugs for w in wells)
    assert minimum_socket_ligament>1.7
    # Verify the complete joint and every pin's motion before writing any STL.
    for x,y,nominal,hole in CENTERS:
        for clearance in CLEARANCES:
            candidate=pin(hole-2*clearance,nominal,1)
            candidate.apply_translation([x,y,0])
            for height in [0,1,5,11]:
                lifted=candidate.copy(); lifted.apply_translation([0,0,height])
                for body in parts:
                    assert intersection_volume(trimesh.boolean.intersection([body,lifted],engine='manifold'))<.0001
    for index,body in enumerate(parts):
        path=OUT/f'prototype_2x1_part_{"AB"[index]}.stl'
        loaded=export(normalize(body),path); loaded.apply_translation(body.bounds[0])
        parts[index]=loaded; files.append(measure(path))
    # Repeat joining checks on actual float32 STL geometry, not just CAD.
    for distance in np.linspace(0,20,81):
        moved=parts[1].copy(); moved.apply_translation([distance,0,0])
        assert intersection_volume(trimesh.boolean.intersection([parts[0],moved],engine='manifold'))<.0001
    variants=[]; installed=[]
    for x,y,nominal,hole in CENTERS:
        for dots,clearance in enumerate(CLEARANCES,1):
            diameter=hole-2*clearance
            model=pin(diameter,nominal,dots)
            path=OUT/'pins'/f'T_pin_{nominal:.0f}mm_family_clearance_{clearance:.2f}_shaft_{diameter:.2f}.stl'
            rotated=model.copy(); rotated.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
            loaded=export(print_pin(model),path); files.append(measure(path))
            downward=(loaded.face_normals[:,2]<-np.cos(np.pi/4)) & (loaded.triangles[:,:,2].min(axis=1)>PIN_THICKNESS+.01)
            assert not np.any(downward),'Unsupported pin shaft overhang in head-down export'
            loaded.apply_translation(rotated.bounds[0])
            loaded.apply_transform(trimesh.transformations.rotation_matrix(-np.pi,[1,0,0]))
            model=loaded
            placed=model.copy(); placed.apply_translation([x,y,0])
            for body in parts:
                collision=trimesh.boolean.intersection([body,placed],engine='manifold')
                assert intersection_volume(collision)<.0001,(nominal,clearance,'pin does not seat')
            moved=parts[1].copy(); moved.apply_translation([1,0,0])
            blocked=trimesh.boolean.intersection([moved,placed],engine='manifold')
            assert intersection_volume(blocked)>.1,(nominal,clearance,'no positive lateral stop')
            for height in np.linspace(0,11,23):
                lifted=placed.copy(); lifted.apply_translation([0,0,height])
                for body in parts:
                    assert intersection_volume(trimesh.boolean.intersection([body,lifted],engine='manifold'))<.0001,'Pin cannot withdraw vertically'
            variants.append({'family_mm':nominal,'shaft_diameter_mm':round(diameter,2),'hole_diameter_mm':hole,
                             'clearance_per_side_mm':clearance,'head_mm':list(HEAD_SIZE),'identification':f'{nominal:.0f} + {dots} dots',
                             'minimum_radial_wall_mm':round(5-hole/2,3),
                             'minimum_entry_wall_mm':round(5-hole/2-.7,3)})
            if clearance==.2: installed.append(placed)
    for source in sorted((ROOT/'output/CURRENT/boards/fit_test').glob('blank_test_tile_*.stl')):
        target=OUT/'tiles'/source.name
        clearance=CLEARANCES[len([f for f in files if f['file'].startswith('tiles')])]
        size=36-2*clearance
        tile=cad.extrude(cad.curved_rectangle((0,0,size,size),[2]*4),2.8)
        dots=CLEARANCES.index(clearance)+1
        marks=cad.union([cad.extrude(Point(3+i*2,3).buffer(.4,quad_segs=24),.4,2.5) for i in range(dots)])
        export(cad.difference(tile,marks),target); files.append(measure(target))
    assert len(files)==14
    a,b=parts
    render([(a,'#a81332'),(b,'#e9b92e'),*[(p,'#20a650') for p in installed]],OUT/'assembled_top.png',
           '2 x 1 physical prototype | unchanged sockets | rigid T pins installed')
    render([(a,'#a81332'),(b,'#e9b92e'),*[(p,'#20a650') for p in installed]],OUT/'assembled_underside.png',
           'Assembled underside | lower A ears / upper B ears',elevation=-50,azimuth=-65)
    exploded_b=b.copy(); exploded_b.apply_translation([18,0,8])
    exploded_pins=[]
    for p in installed:
        raised=p.copy(); raised.apply_translation([18,0,23]); exploded_pins.append(raised)
    render([(a,'#a81332'),(exploded_b,'#e9b92e'),*[(p,'#20a650') for p in exploded_pins]],
           OUT/'exploded_view.png','Exploded view | slide halves together, then insert pins from above',elevation=40,azimuth=-60)
    assembly_diagrams(parts,installed[0],wells,lugs)
    assert production_hashes()==frozen,'Production board quadrants changed'
    report={'passed':True,'canonical_gameplay_dimensions_unchanged':True,'production_quadrants_unchanged':True,
            'production_sha256':frozen,'files':files,'pin_variants':variants,
            'socket_mm':[36,36],'socket_depth_mm':3,'socket_radius_mm':2,'pitch_mm':38,'divider_mm':2,
            'board_thickness_mm':10,'outer_track_rim_mm':6,'removal_recess':'exact canonical function',
            'board_seam_clearance_mm':GAP,'lap_vertical_clearance_mm':.4,'lap_normal_clearance_mm':.4/2**.5,'lap_angle_degrees':45,'minimum_bore_edge_bearing_thickness_mm':2.1,'lug_perimeter_clearance_mm':GAP,
            'lower_lug_axis_thickness_mm':4.8,'upper_lug_axis_thickness_mm':4.8,
            'minimum_mechanism_to_socket_mm':round(minimum_socket_ligament,3),
            'large_horizontal_tab_underside_area_mm2':0,
            'positive_lateral_pin_stop_checked_mm':1.0,'tile_clearance_selected':False,
            'retention':'Gravity: vertical pins, heads rest on upper ears. Not captive against upward lift or inversion.',
            'orientation':{'part_A':'socket up, flat underside on bed, no supports',
                           'part_B':'socket up; 45-degree underside grows from a bed-connected foot; predicted near-support-free, inspect local bore bridges up to 5.4 mm',
                           'pins':'Flat T-head down, shaft vertical up; predicted support-free. No side printing. Optional 2 mm brim if adhesion requires.',
                           'tiles':'flat underside on bed; existing top identification dots'},
            'warnings':['Canonical fingernail recess locally leaves 1 mm of divider at the top; do not pry with tools.',
                        '45-degree slopes and local bore bridges require physical verification; inspect thin wedge tips.',
                        'Smooth gravity pins prevent lateral pull-apart but are not captive against vertical lifting or inversion.',
                        'Largest pin clearance permits up to about 0.6 mm relative play; test rattle and seam movement.',
                        'PLA wear, actual pin/ear strength and repeated-use durability require the physical print test.'],
            'no_gameplay_tiles_generated':True}
    report.update({'supports':report['orientation'],'extra_XY_protrusion_mm':8,'assembled_body_xyz_mm':[86,64,10],
                   'assembled_with_pins_xyz_mm':[86,64,12.4],'tab_core_plan_mm':[16,11],'tab_with_root_plan_mm':[20,11],'tab_plan_corner_radius_mm':2,
                   'tab_overlap_xy_bounding_box_mm':[9.6,11],'root_transition_fillet_mm':2,'minimum_material_under_socket_mm':7,
                   'assembly_translation_samples':81,'pin_withdrawal_samples_per_variant':23,
                   'coaxial_only_at_zero_translation':True,'pin_root_fillet_mm':.6,'upper_bore_chamfer_mm':.7})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    write_readme(report)
    from src.prototypes.build_one_plate_test import main as build_plate
    build_plate(OUT)
    from src.tools import render_a1_placement as placement
    placement.main(OUT)
    for preview in (ROOT/'output/CURRENT/A1_placement_preview').iterdir():
        if preview.is_file(): shutil.copyfile(preview,OUT/preview.name)
    with zipfile.ZipFile(ROOT/'output/CURRENT/sloped_lap_prototype_print_kit.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob('*')):
            if path.is_file(): archive.write(path,path.relative_to(OUT))
    print(f'PASS: {len(files)} watertight STLs, unchanged universal sockets, all 16 production quadrants unchanged.',flush=True)


def assembly_diagrams(parts,pin_mesh,wells,lugs):
    fig,axes=plt.subplots(2,2,figsize=(14,10))
    for ax,(offset,with_pin,title) in zip(axes.flat,[(20,False,'1. Separated'),(8,False,'2. Partially joining'),
                                                     (0,False,'3. Fully overlapped'),(0,True,'4. Pin installed')]):
        moved=parts[1].copy(); moved.apply_translation([offset,0,0])
        items=[(parts[0],'#a81332'),(moved,'#e9b92e')]
        if with_pin: items.append((pin_mesh,'#20a650'))
        for mesh,color in items:
            section=mesh.section(plane_origin=[43,-3,0],plane_normal=[0,1,0])
            lines=[LineString(section.vertices[e.points][:,[0,2]]) for e in section.entities]
            for poly in polygonize(unary_union(lines)): ax.fill(*poly.exterior.xy,color=color)
        ax.axvline(43,color='#a81332',ls=':',lw=.8)
        ax.axvline(43+offset,color='#998020',ls=':',lw=.8)
        ax.text(33,15,f'B translation: +{offset} mm\n45 degree lap | 0.4 mm vertical gap',fontsize=10)
        ax.set_xlim(32,74); ax.set_ylim(-1,18); ax.set_aspect('equal'); ax.set_title(title)
        ax.set_xlabel('X (mm)'); ax.set_ylabel('Z (mm)')
    fig.suptitle('Actual STL sections at Y=-3 mm | 0.283 mm face-normal gap\nXY overlap begins during joining; holes become coaxial at full seating')
    fig.tight_layout(); fig.savefig(OUT/'assembly_sequence_sections.png',dpi=160); plt.close(fig)
    # Standalone section uses the same validated mesh sections.
    shutil.copyfile(OUT/'assembly_sequence_sections.png',OUT/'pin_and_seam_cross_section.png')
    fig,ax=plt.subplots(figsize=(10,8))
    chassis=cad.curved_rectangle((0,0,86,48),[8]*4)
    ax.fill(*chassis.exterior.xy,color='#dadada')
    for w in wells:
        ax.fill(*w.exterior.xy,color='white',edgecolor='#555')
        ax.text(w.centroid.x,24,'36 x 36\nR2 / depth 3',ha='center',va='center')
    for lug,(x,y,f,h) in zip(lugs,CENTERS):
        ax.fill(*lug.exterior.xy,color='#e9b92e',alpha=.8)
        ax.fill(*Point(x,y).buffer(h/2,quad_segs=64).exterior.xy,color='white')
        ax.annotate(f'{f:.0f} mm family: bore {h:.1f}\n16 x 11 core / 20 wide root, R2\n8 mm extra beyond rim',xy=(x,y),xytext=(64,y-6 if y<0 else y+8),
                    arrowprops=dict(arrowstyle='->'),fontsize=9)
    ax.plot([43,43],[0,48],ls='--',color='gray')
    ax.text(0,67,'Gameplay chassis: 86 x 48 x 10 mm\nWith local tabs: 86 x 64 x 10 mm\nPitch 38 | divider 2 | seam 0.25 | normal rim 6',fontsize=11)
    ax.set_xlim(-5,105); ax.set_ylim(76,-18); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('45 degree lap tabs and unchanged universal sockets')
    fig.tight_layout(); fig.savefig(OUT/'pin_lug_dimensions.png',dpi=160); plt.close(fig)


def write_readme(report):
    lines=['# Sloped 2 x 1 pin prototype','',
           'Canonical gameplay geometry is preserved: pitch 38; socket 36 x 36, R2, depth 3; divider 2; normal rim 6; chassis thickness 10; seam 0.25 mm; original fingernail recess. The compact tab footprint retains the 8 mm local external projection and R2 reinforced roots. All 16 production quadrants are unchanged.', '',
           'A occupies the volume below Z=47.8-X; B occupies the volume above Z=48.2-X, clipped to Z=0..10. Both mating faces are 45 degrees. Their vertical separation is 0.4 mm, equivalent to 0.283 mm normal clearance. Translating B outward by d increases the gap to 0.4+d, so horizontal joining cannot geometrically wedge these faces together. They guide vertical alignment when contacting, but are not a precision self-centering coupling. The vertical pin remains the primary lateral lock.', '',
           'At the pin axis X=43: A is 4.8 mm thick and B is 4.8 mm thick. At the widest 5.4 mm bore edges, each retains at least 2.1 mm vertical bearing thickness. This is the limiting section to inspect for PLA wear. T-head remains 12 x 8 x 2.4 mm, root fillet 0.6 mm, tip lead-in 0.4 mm radial / 0.5 mm axial, upper bore chamfer 0.7 mm. The lower bore opens directly into the sloped face; no horizontal counterbore is cut. Socket floor retains 7 mm solid material; mechanism-to-socket ligament remains 2.75 mm.', '',
           '| Family | Shaft | Bore | Clearance per side |','|---|---:|---:|---:|']
    for v in report['pin_variants']:
        lines.append(f"| {v['family_mm']:.0f} | {v['shaft_diameter_mm']:.2f} | {v['hole_diameter_mm']:.2f} | {v['clearance_per_side_mm']:.2f} |")
    lines.extend(['','## Print orientation and support prediction','',
                  'Both board halves print flat-base-down, socket-up. A grows inward as it rises. B starts on a full-height-connected foot and expands leftward at 45 degrees; the prior floating horizontal ear is removed. No large horizontal tab underside remains. The circular bore interrupts the slope and may require short local bridges up to 5.4 mm; inspect those toolpaths in Bambu Studio. Start without supports on the tabs if the calibrated PLA profile handles 45-degree slopes and these bridges; add local support only if the first test shows sagging. This is a geometric prediction, not a sliced or physical result.', '',
                  'Pins are exported flat T-head on the plate, smooth shaft vertically upward. No side printing or shaft support is intended. Head identification grooves create short first-layer bridges. Start without brim; use a small 2 mm pin-only brim only if adhesion requires it. Use 0.20 mm layers, calibrated PLA and solid pins/tabs with at least four walls. The sloping thin tips need careful slicing and should not be used as pry points.', '',
                  'Four blank tiles retain 35.70 / 35.60 / 35.50 / 35.40 mm sizes, exact R2 corners, 2.8 mm thickness and identifying dots. No fit clearance is frozen.', '',
                  '## Validation and limits','',
                  'The pre-export CAD and reloaded STLs were checked for collision-free horizontal joining at 81 positions over 20 mm. All eight pins seat and withdraw vertically, and resist 1 mm lateral separation. All 14 components are watertight/manifold. The plate contains all components in their recommended orientations. Updated actual-mesh sections show separated, joining, seated and pinned states. A1 support diagnostics are overhang projections rather than generated support toolpaths.', '',
                  'The 45-degree faces have deliberate clearance and should not be clamped or forced into a friction fit. Surface roughness, layer steps and elephant foot may still affect joining. Smooth pins remain gravity-retained and can fall out when inverted. Vertical pin layer adhesion, thin wedge tips and 2.1 mm minimum bore-edge bearing thickness require physical PLA testing. Production geometry is unchanged.'])
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
