"""Recessed two-space PLA pin prototype: no external XY locking geometry.

Two stacked internal lugs per station fit below a 2.4 mm socket-floor roof.
The smooth pins enter from below; the table traps their recessed heads.
"""
import json
import shutil
import zipfile
import numpy as np
import trimesh
from shapely.geometry import box, Point, Polygon, LineString
from shapely.ops import unary_union, polygonize
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.textpath import TextPath
from src.chassis import build_printable_board as cad
from src.chassis.build_canonical_chassis import ROOT, STANDARD, export, removal
from src.prototypes.build_pin_joint_prototype import production_hashes, intersection_volume, render

OUT=ROOT/'output'/'archive'/'recessed_pin_prototype'
STATIONS=[(43.,14.,4.,4.4),(43.,34.,5.,5.4)]
LOW=1.2
LOW_TOP=2.8
HIGH=3.0
HIGH_TOP=4.4
CAVITY_TOP=4.6
ROOF=7-CAVITY_TOP


def revolve(profile):
    mesh=trimesh.creation.revolve(np.array(profile),sections=128)
    if mesh.volume<0: mesh.invert()
    return mesh


def internal_pin(diameter,family,dots):
    radius=diameter/2
    head=cad.extrude(cad.curved_rectangle((-5,-4,5,4),[1]*4),1.0,.2)
    profile=[(0,1.2),(radius+.6,1.2)]
    for angle in np.linspace(-np.pi/2,-np.pi,17):
        profile.append((radius+.6+.6*np.cos(angle),1.8+.6*np.sin(angle)))
    profile.extend([(radius,3.8),(radius-.4,4.2),(0,4.2)])
    shaft=revolve(profile)
    model=cad.union([head,shaft])
    glyph=Polygon()
    for ring in TextPath((-4,-1),str(int(family)),size=2.5).to_polygons():
        glyph=glyph.symmetric_difference(Polygon(ring))
    marks=[cad.extrude(glyph,.3,.1)]
    marks.extend(cad.extrude(Point(-.5+i,0).buffer(.25,quad_segs=24),.3,.1) for i in range(dots))
    # Only the exposed underside of the head is labelled; seating face is flat.
    return cad.difference(model,cad.union(marks))


def pin_bore(radius,start):
    cylinder=trimesh.creation.cylinder(radius=radius,height=4.6,sections=128)
    cylinder.apply_translation([0,0,2.1])  # -0.2 .. 4.4, no roof penetration
    chamfer=.7 if start==LOW else .3
    lead=revolve([(0,start-.1),(radius+chamfer,start-.1),(radius+chamfer,start),
                  (radius,start+chamfer),(0,start+chamfer)])
    return cad.union([cylinder,lead])


def norm(mesh):
    result=mesh.copy(); result.apply_translation(-result.bounds[0]); return result


def roof_shoulders(y,region):
    """45-degree side shoulders leave a 10 mm bridge across each cavity."""
    result=[]
    # Overlap existing walls/roof slightly to avoid tangent-only CAD unions.
    for poly in [Polygon([(y-6.02,3.58),(y-4.9,4.7),(y-6.02,4.7)]),
                 Polygon([(y+6.02,3.58),(y+4.9,4.7),(y+6.02,4.7)])]:
        wedge=cad.extrude(poly,15.6)
        wedge.vertices=wedge.vertices[:,[2,0,1]]
        wedge.apply_translation([35.2,0,0])
        clipped=trimesh.boolean.intersection([wedge,cad.extrude(region,10)],engine='manifold')
        result.append(clipped)
    return result


def sections(models,installed):
    fig,axes=plt.subplots(1,2,figsize=(15,7))
    for ax,(x,y,family,hole),p in zip(axes,STATIONS,installed):
        for model,color in [(models[0],'#a81332'),(models[1],'#e3b12e'),(p,'#24a250')]:
            section=model.section(plane_origin=[x,y,0],plane_normal=[0,1,0])
            lines=[LineString(section.vertices[e.points][:,[0,2]]) for e in section.entities]
            for polygon in polygonize(unary_union(lines)):
                ax.fill(*polygon.exterior.xy,color=color,alpha=.85)
        # Actual socket floor and reference roof/cavity planes.
        ax.plot([31,42],[7,7],color='black',lw=1.5)
        ax.plot([44,55],[7,7],color='black',lw=1.5)
        ax.annotate('Socket floor Z=7',xy=(35,7),xytext=(29,8.1),fontsize=9,arrowprops=dict(arrowstyle='->'))
        ax.annotate('',xy=(35.5,4.6),xytext=(35.5,7),arrowprops=dict(arrowstyle='<->'))
        ax.text(34.9,5.7,'2.4 mm solid roof',rotation=90,va='center',ha='right',fontsize=9)
        ax.annotate('Upper B lug: 1.4 mm cross-seam thickness',xy=(41,3.7),xytext=(30,11.2),fontsize=9,arrowprops=dict(arrowstyle='->'))
        ax.annotate('Lower A lug: 1.6 mm',xy=(45,2.1),xytext=(43,9.2),fontsize=9,arrowprops=dict(arrowstyle='->'))
        ax.annotate('Head bottom Z=0.2, table traps head',xy=(43,.2),xytext=(30,-1.4),fontsize=9,arrowprops=dict(arrowstyle='->'))
        ax.axhline(0,color='#555555',lw=1); ax.text(54,.1,'Table',ha='right',fontsize=9)
        ax.set_xlim(28,57); ax.set_ylim(-2,12.5); ax.set_aspect('equal')
        ax.set_xlabel('X, mm'); ax.set_ylabel('Z, mm')
        ax.set_title(f'{family:.0f} mm family | bore {hole:.1f} mm | pin entirely below floor')
    fig.suptitle('Actual mesh cross-sections: internal lugs, pin, intact sockets and roof')
    fig.tight_layout(); fig.savefig(OUT/'internal_pin_socket_cross_section.png',dpi=160); plt.close(fig)

    # A perpendicular section exposes the actual 45-degree roof shoulders.
    fig,ax=plt.subplots(figsize=(10,7))
    section=models[0].section(plane_origin=[40,14,0],plane_normal=[1,0,0])
    lines=[LineString(section.vertices[e.points][:,[1,2]]-[14,0]) for e in section.entities]
    for poly in polygonize(unary_union(lines)):
        ax.fill(*poly.exterior.xy,color='#a81332',alpha=.85)
    ax.annotate('45 degree roof shoulder',xy=(-5.5,4.1),xytext=(-8,8.8),
                arrowprops=dict(arrowstyle='->'))
    ax.annotate('',xy=(-5,4.6),xytext=(5,4.6),arrowprops=dict(arrowstyle='<->'))
    ax.text(0,5.05,'10 mm central bridge span',ha='center',fontsize=10)
    ax.annotate('Lug underside: selective support remains',xy=(0,1.2),xytext=(-8,-1.4),
                arrowprops=dict(arrowstyle='->'),fontsize=10)
    ax.axhline(0,color='gray',lw=1)
    ax.set_xlim(-8.5,8.5); ax.set_ylim(-2,10); ax.set_aspect('equal')
    ax.set_xlabel('Y relative to pin station (mm)'); ax.set_ylabel('Z (mm)')
    ax.set_title('Actual Part A STL section at X=40 mm\nRoof shoulders reduce bridging; lug cantilevers still need support')
    fig.tight_layout(); fig.savefig(OUT/'roof_shoulder_print_section.png',dpi=160); plt.close(fig)


def top_plan(chassis,wells,housings):
    fig,ax=plt.subplots(figsize=(11,7))
    ax.fill(*chassis.exterior.xy,color='#d8dedb')
    for w in wells:
        ax.fill(*w.exterior.xy,color='white',edgecolor='#444444')
        ax.text(w.centroid.x,w.centroid.y,'36 x 36\nR2 / depth 3',ha='center',va='center')
    for housing,(_,y,f,h) in zip(housings,STATIONS):
        ax.plot(*housing.exterior.xy,color='#277244',ls='--')
        ax.text(43,y,f'{f:.0f} mm\ninternal',ha='center',va='center',color='#277244',fontsize=9)
    ax.plot([43,43],[0,48],color='gray',ls='--')
    ax.annotate('',xy=(0,52),xytext=(86,52),arrowprops=dict(arrowstyle='<->'))
    ax.text(43,56,'86 mm outline: ZERO added XY footprint',ha='center')
    ax.annotate('',xy=(-4,0),xytext=(-4,48),arrowprops=dict(arrowstyle='<->'))
    ax.text(-8,24,'48 mm',rotation=90,ha='center',va='center')
    ax.set_ylim(60,-5); ax.set_xlim(-12,91); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Canonical outline and sockets; dashed cavities are hidden underneath')
    fig.tight_layout(); fig.savefig(OUT/'zero_footprint_dimension_plan.png',dpi=160); plt.close(fig)


def underside_plan(models,installed):
    """Orthographic underside projection without 3D painter-order artifacts."""
    triangles=[]; colors=[]
    for model,color in [(models[0],'#a81332'),(models[1],'#e3b12e'),*[(p,'#24a250') for p in installed]]:
        for triangle in model.triangles:
            projected=triangle[:,:2]
            area=abs(np.linalg.det(np.stack([projected[1]-projected[0],projected[2]-projected[0]])))
            if area>1e-8:
                triangles.append(triangle); colors.append(color)
    order=np.argsort([-t[:,2].mean() for t in triangles])
    fig,ax=plt.subplots(figsize=(11,7))
    ax.add_collection(PolyCollection([triangles[i][:,:2] for i in order],
                                    facecolors=[colors[i] for i in order],edgecolors='none'))
    for _,y,family,_ in STATIONS:
        ax.annotate(f'{family:.0f} mm pin family\nhead recessed 0.2 mm',xy=(43,y),xytext=(96,y),
                    va='center',fontsize=10,arrowprops=dict(arrowstyle='->'))
    ax.text(15,24,'Part A',ha='center',color='white',fontsize=12)
    ax.text(71,24,'Part B',ha='center',fontsize=12)
    ax.set_xlim(-3,125); ax.set_ylim(51,-3); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Underside plan | actual STL projection | all joints inside 86 x 48 mm outline')
    fig.tight_layout(); fig.savefig(OUT/'underside_plan.png',dpi=160); plt.close(fig)


def main():
    before=production_hashes()
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'pins').mkdir(exist_ok=True); (OUT/'tiles').mkdir(exist_ok=True)
    chassis=cad.curved_rectangle((0,0,86,48),[8]*4)
    regions=[chassis.intersection(box(-1,-1,42.875,49)),chassis.intersection(box(43.125,-1,87,49))]
    wells=[cad.curved_rectangle((6,6,42,42),[2]*4),cad.curved_rectangle((44,6,80,42),[2]*4)]
    housings=[cad.curved_rectangle((33,y-6,53,y+6),[2]*4) for _,y,_,_ in STATIONS]
    models=[]; records=[]
    for index in range(2):
        # Main chassis retains the full original top and both socket floors.
        model=cad.extrude(regions[index],10)
        pockets=cad.union([cad.extrude(h,CAVITY_TOP+.1,-.1) for h in housings])
        model=cad.difference(model,pockets)
        pieces=[model]
        for h,(_,y,_,hole) in zip(housings,STATIONS):
            if index==0:
                # Broad A backbone; B lug passes to its right with 0.25 mm gap.
                backbone=h.buffer(.02).intersection(box(32,y-7,37.75,y+7))
                lower=cad.curved_rectangle((33,y-5,48,y+5),[1]*4)
                pieces.extend([cad.extrude(backbone,CAVITY_TOP+.02),cad.extrude(lower,1.6,LOW)])
            else:
                backbone=h.buffer(.02).intersection(box(48.25,y-7,54,y+7))
                upper=cad.curved_rectangle((38,y-5,53,y+5),[1]*4)
                # Own-half roof connection adds 0.2 mm; cross-seam lug clears A roof.
                roof_root=h.buffer(.02).intersection(box(43.125,y-7,54,y+7))
                pieces.extend([cad.extrude(backbone,CAVITY_TOP+.02),cad.extrude(upper,1.4,HIGH),
                               cad.extrude(roof_root,.22,HIGH_TOP)])
            pieces.extend(roof_shoulders(y,regions[index]))
        model=cad.union(pieces)
        cuts=[cad.extrude(wells[index],3.2,7),cad.extrude(removal(wells[index]),1.3,8.8)]
        for x,y,_,hole in STATIONS:
            tool=pin_bore(hole/2,LOW if index==0 else HIGH)
            tool.apply_translation([x,y,0]); cuts.append(tool)
        model=cad.difference(model,cad.union(cuts))
        path=OUT/f'prototype_2x1_part_{"AB"[index]}.stl'
        loaded=export(norm(model),path); loaded.apply_translation(model.bounds[0]); models.append(loaded)
        records.append({'file':path.name,'xyz_mm':trimesh.load_mesh(path).extents.round(3).tolist()})
        triangles=loaded.triangles
        floor=unary_union([Polygon(t[:,:2]) for t in triangles[np.all(np.isclose(triangles[:,:,2],7,atol=.0001),axis=1)]])
        assert floor.buffer(.005).covers(wells[index]) and wells[index].buffer(.005).covers(floor)
        projection=unary_union([Polygon(t[:,:2]) for t in triangles[np.abs(loaded.face_normals[:,2])>.99]])
        assert chassis.buffer(.005).covers(projection),'External XY protrusion'
    assert intersection_volume(trimesh.boolean.intersection(models,engine='manifold'))<.001
    installed=[]; variants=[]
    for x,y,family,hole in STATIONS:
        for dots,clearance in enumerate([.15,.20,.25,.30],1):
            diameter=hole-2*clearance
            model=internal_pin(diameter,family,dots)
            path=OUT/'pins'/f'T_pin_{family:.0f}mm_clearance_{clearance:.2f}_shaft_{diameter:.2f}.stl'
            loaded=export(norm(model),path); loaded.apply_translation(model.bounds[0])
            # Exported orientation is head-down. Above the supported head there
            # must be no downward-facing shaft surface requiring supports.
            downward=(loaded.face_normals[:,2]<-np.cos(np.pi/4)) & (loaded.triangles[:,:,2].min(axis=1)>1.21)
            assert not np.any(downward),'Pin shaft has an unsupported overhang'
            placed=loaded.copy(); placed.apply_translation([x,y,0])
            for part in models:
                assert intersection_volume(trimesh.boolean.intersection([part,placed],engine='manifold'))<.001,'Pin will not seat'
            moved=models[1].copy(); moved.apply_translation([1,0,0])
            assert intersection_volume(trimesh.boolean.intersection([moved,placed],engine='manifold'))>.05,'No lateral pin stop'
            for offset in [.2,1,4]:
                withdrawn=placed.copy(); withdrawn.apply_translation([0,0,-offset])
                for part in models:
                    assert intersection_volume(trimesh.boolean.intersection([part,withdrawn],engine='manifold'))<.001,'Pin cannot pull out'
            variants.append({'family_mm':family,'shaft_mm':round(diameter,2),'hole_mm':hole,
                             'clearance_per_side_mm':clearance,'head_mm':[10,8,1],
                             'minimum_lug_wall_at_entry_mm':round(5-hole/2-.7,2),
                             'identification':f'{family:.0f} and {dots} dots on underside of head'})
            variants[-1].update({'export_orientation':'flat head down, vertical shaft up',
                                  'unsupported_shaft_overhang_faces':int(np.count_nonzero(downward))})
            records.append({'file':str(path.relative_to(OUT)),'xyz_mm':trimesh.load_mesh(path).extents.round(3).tolist()})
            if clearance==.20: installed.append(placed)
    for source in sorted((ROOT/'output/CURRENT/boards/fit_test').glob('blank_test_tile_*.stl')):
        target=OUT/'tiles'/source.name; shutil.copyfile(source,target)
        assert target.read_bytes()==source.read_bytes()
        records.append({'file':str(target.relative_to(OUT)),'xyz_mm':trimesh.load_mesh(target).extents.round(3).tolist()})
    assert len(records)==14
    for record in records:
        mesh=trimesh.load_mesh(OUT/record['file'])
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        assert np.all(np.bincount(mesh.edges_unique_inverse)==2) and len(mesh.split())==1
        record.update({'watertight_manifold':True,'fits_A1':bool(max(mesh.extents[:2])<=256)})
    render([(models[0],'#a81332'),(models[1],'#e3b12e')],OUT/'assembled_top.png','Recessed pin prototype | unchanged 86 x 48 mm outline')
    render([(models[0],'#a81332'),(models[1],'#e3b12e'),*[(p,'#24a250') for p in installed]],
           OUT/'assembled_underside.png','Underside | recessed pin heads and internal bearing lugs',-60,-60)
    render([(models[0],'#a81332'),(models[1],'#e3b12e')],OUT/'underside_pins_removed.png',
           'Underside | pins removed to expose interleaved internal lugs',-60,-60)
    b=models[1].copy(); b.apply_translation([15,0,0])
    removed=[]
    for p in installed:
        copy=p.copy(); copy.apply_translation([0,0,-7]); removed.append(copy)
    render([(models[0],'#a81332'),(b,'#e3b12e'),*[(p,'#24a250') for p in removed]],OUT/'exploded_underside.png',
           'Internal joint exploded | smooth pins insert upward from underneath',-50,-60)
    sections(models,installed); top_plan(chassis,wells,housings)
    underside_plan(models,installed)
    assert production_hashes()==before
    report={'passed':True,'files':records,'variants':variants,'assembled_chassis_xyz_mm':[86,48,10],
            'external_XY_footprint_added_mm':0,'production_quadrants_unchanged':True,
            'socket_size_mm':[36,36],'socket_depth_mm':3,'socket_radius_mm':2,'pitch_mm':38,
            'divider_mm':2,'outer_rim_mm':6,'seam_clearance_mm':.25,'internal_vertical_lug_clearance_mm':.2,
            'cavity_top_z_mm':4.6,'socket_floor_z_mm':7,'minimum_solid_roof_mm':2.4,
            'lower_A_lug_thickness_mm':1.6,'upper_B_lug_cross_seam_thickness_mm':1.4,
            'upper_B_lug_own_half_thickness_mm':1.6,'head_bottom_z_mm':.2,'head_top_z_mm':1.2,
            'pin_tip_z_mm':4.2,'head_mm':[10,8,1],'shaft_length_mm':3,
            'pin_root_fillet_mm':.6,'lower_bore_entry_chamfer_mm':.7,'upper_bore_entry_chamfer_mm':.3,
            'roof_shoulder_angle_degrees':45,'remaining_roof_bridge_span_mm':10,
            'print_orientation':{'bodies':'Flat base down, sockets up; original STL orientation.',
                                 'pins':'Flat head down on plate, smooth shaft vertically up. Never side-print.',
                                 'tiles':'Flat base down.'},
            'pin_brim':'None initially; optional 2 mm brim only if adhesion fails. Not included in STL bounds.',
            'retention':'Head is 0.2 mm above the underside plane; the tabletop traps it. Pins are not captive off the table.',
            'supports':'Pins and blank tiles: predicted support-free, head/base down. Bodies: selective supports still required below interleaving lug cantilevers; 45-degree roof shoulders need none. The remaining 10 mm two-sided roof span is a bridge candidate; test bridging and inspect in slicer, support locally if needed. Avoid bores, mating surfaces and sockets. Remove supports before assembly.',
            'PLA_risks':['1.4 mm upper lug and 1.0 mm pin head are the limiting thin features; print solid and test wear/strength.',
                         'Printed vertical pins depend on layer adhesion in shear; short 3 mm shafts reduce bending leverage, but strength is untested.',
                         'Do not lift by one half; hold/support pins when lifting because gravity does not retain underside pins.',
                         'Support cleanup inside the cavities is necessary; scars can change fit.'],
            'no_gameplay_tiles_generated':True,'tile_clearance_selected':False}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    write_readme(report)
    # Reuse the existing one-plate arrangement with this prototype's files.
    from src.prototypes.build_one_plate_test import main as build_plate
    build_plate(OUT)
    with zipfile.ZipFile(ROOT/'output/recessed_pin_prototype_print_kit.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob('*')):
            if path.is_file(): archive.write(path,path.relative_to(OUT))
    print('PASS: zero additional XY footprint; roof 2.4 mm; 14 manifold test components; production unchanged.')


def write_readme(report):
    lines=['# Fully recessed underside pin prototype','',
           'The canonical chassis envelope is 86 x 48 x 10 mm, with R8 exterior corners. All locking geometry and seated heads remain within it. Wells remain 36 x 36 mm, R2, 3 mm deep; pitch 38, dividers 2, outside rim 6, seam gap 0.25 mm. Both floors remain whole. Four blank 2.8 mm tile tests are copied unchanged. No production quadrant is modified.', '',
           'Two compact clevis-style stations use one lower A lug and one interleaving upper B lug each, supported by broad internal backbones. This depth budget uses two bearing lugs per station. Both pin axes are under the divider, but neither bore nor pin reaches it or either socket: the cavities stop at Z=4.6 mm, below floors at Z=7 mm, leaving **2.4 mm solid roof** under the sockets.', '',
           'Each housing is 20 x 12 mm, R2, centred at X=43 and Y=14 / 34 mm. A lower lug spans Z=1.2..2.8 (1.6 mm); B upper lug crosses the seam at Z=3.0..4.4 (1.4 mm), with 0.2 mm vertical clearance. Both lug footprints are 10 mm wide with R1 corners. B connects upward to its own roof at Z=4.6. Backbones and opposing lugs retain 0.25 mm XY clearance. The upper lug clears the opposite roof by 0.2 mm. Internal CAD roots overlap surrounding solid by 0.02 mm for robust manifold unions; this does not reduce the minimum 2.4 mm socket roof or change joint clearances.', '',
           '45-degree shoulders along the central 15.6 mm of each cavity roof narrow the horizontal span from 12 to 10 mm. The rounded end regions retain short portions of the original ceiling. The shoulders rise from approximately Z=3.6 to Z=4.6 and do not collide with the interleaving lugs. The central ceiling is a two-sided bridge candidate, not a guaranteed support-free surface.', '',
           'Pin head: 10 x 8 x 1 mm, bottom Z=0.2, top Z=1.2. Shaft: Z=1.2..4.2, length 3 mm, generous 0.6 mm root fillet and 0.4 mm tip lead-in. Lower bore entry has a matching 0.7 mm 45-degree chamfer; upper entry remains 0.3 mm. Minimum lower-entry lug wall is reported below. Pin heads seat against the underside of A\'s lower lug. No threads, spring, hook or snap feature is present.', '',
           '| Family | Shaft | Hole | Clearance per side | Minimum entry wall |','|---|---:|---:|---:|---:|']
    for v in report['variants']:
        lines.append(f"| {v['family_mm']:.0f} | {v['shaft_mm']:.2f} | {v['hole_mm']:.2f} | {v['clearance_per_side_mm']:.2f} | {v['minimum_lug_wall_at_entry_mm']:.2f} |")
    lines.extend(['','Family numeral and one-to-four dots are on the exposed underside of each head, outside seating/mating surfaces. Existing tile dots identify clearances 0.15 / 0.20 / 0.25 / 0.30 per side, giving 35.70 / 35.60 / 35.50 / 35.40 mm tiles, thickness 2.8 mm.', '',
                  '## Print and assembly','',
                  'Use the combined `prototype_2x1_ALL_COMPONENTS_A1.stl` for one session. Import at 100% without auto-arranging. Use 0.20 mm layers, a 0.4 mm nozzle and your calibrated PLA profile. Make the lug regions and pins solid PLA; use four or more walls. Bodies are flat-base-down, sockets-up. Pins are exported flat T-head on the bed, smooth shaft vertically upward. Do not lay pins on their sides. The shaft narrows upward through its fillet; the head identification engravings involve only small first-layer bridges. Pins and flat tiles are predicted support-free. Start without brim; a 2 mm pin-only brim is optional if adhesion fails. No brim is included in the geometry or placement bounds.', '',
                  report['supports'], '',
                  'Remaining cross-seam lug undersides are one-sided cantilevers, not printable two-sided bridges. Selectively support these; 45-degree roof shoulders need no support. Trial the 10 mm central roof bridges and inspect the rounded ceiling end regions in the slicer, adding local roof supports if necessary. Support cleanup is possible through the open underside and seam before assembly; avoid bores, mating faces and sockets. No slicer toolpath, bridging test or physical support-removal test has been performed.', '',
                  'Join both halves on their sides or upside down, then push the smooth pins upward from the underside until heads seat. Set the board on a flat table. Heads are recessed 0.2 mm and the table traps them, allowing only 0.2 mm downward travel, leaving at least 1 mm upper-lug shaft engagement. They are not captive when the board is lifted. Hold the heads/support the assembly when lifting; expose the underside and pull the head to remove. No repeated flexing is required.', '',
                  '## Validation and limits','',
                  'Both exported socket floors match the universal rounded square; all 14 STLs are connected, watertight/manifold and fit the A1. Part A and B do not overlap. All eight pin variants seat, pull out downward without collision and block 1 mm lateral separation. Locking projections remain inside the canonical XY outline. Production hashes are unchanged. Previews include underside with/without pins and actual mesh sections through both pin stations, showing the socket floors and 2.4 mm roof.', '',
                  '**PLA risk:** the 1.4 mm cross-seam upper lug and 1.0 mm head are thin relative to a larger external joint. Their broad roots and short shaft reduce leverage, but repeated-use durability is not established. Print solid, avoid prying and test wear. The head retains 0.8 mm beneath its 0.2 mm identification engraving. Vertical pin layer adhesion remains a strength limit; these pins must stay head-down, shaft-up.', '',
                  'STL bounds are measured geometrically; no Bambu Studio slicing run, strength simulation or physical fit test has been performed. No pin/tile clearance is frozen and no gameplay tiles are generated.'])
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    main()
