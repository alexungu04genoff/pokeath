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
import build_printable_board as cad
from build_canonical_chassis import STANDARD, removal, export

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'/'pin_joint_prototype'
GAP=STANDARD['seam_clearance_mm']
HEIGHT=STANDARD['board_thickness_mm']
LOWER=(HEIGHT-GAP)/2
UPPER=(HEIGHT+GAP)/2
PIN_THICKNESS=2.4
HEAD_Z=HEIGHT
PIN_BOTTOM=.2
LUG_RADIUS=7.0
HEAD_SIZE=(12.0,6.0,PIN_THICKNESS)
CENTERS=[(43.0,-3.0,4.0,4.4),(43.0,51.0,5.0,5.4)]
CLEARANCES=[.15,.20,.25,.30]


def production_hashes():
    files=sorted((ROOT/'output/canonical_chassis').glob('*/quadrant_*.stl'))
    assert len(files)==16
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def lug_profile(x,y):
    disk=Point(x,y).buffer(LUG_RADIUS,quad_segs=96)
    if y<0:
        neck=cad.curved_rectangle((x-8,-.5,x+8,3.5),[2]*4)
    else:
        neck=cad.curved_rectangle((x-8,44.5,x+8,48.5),[2]*4)
    # Closing rounds the reentrant disk-to-neck root with a 2 mm fillet.
    return disk.union(neck).buffer(2,quad_segs=48).buffer(-2,quad_segs=48).simplify(.001)


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
             (radius,HEAD_Z-.4)]
    # Small head/shaft root fillet clears the 0.5 mm entry chamfer.
    for angle in np.linspace(np.pi,np.pi/2,17):
        profile.append((radius+.4+.4*np.cos(angle),HEAD_Z-.4+.4*np.sin(angle)))
    profile.append((0,HEAD_Z))
    shaft=revolved(profile)
    head=cad.extrude(cad.curved_rectangle((-6,-3,6,3),[1.5]*4),PIN_THICKNESS,HEAD_Z)
    result=cad.union([shaft,head])
    glyph=Polygon()
    for polygon in TextPath((-4.8,-1.3),str(int(nominal)),size=3).to_polygons():
        glyph=glyph.symmetric_difference(Polygon(polygon))
    marks=[cad.extrude(glyph,.5,12.0)]
    marks.extend(cad.extrude(Point(-.5+i*1.3,0).buffer(.28,quad_segs=24),.5,12.0) for i in range(dots))
    return cad.difference(result,cad.union(marks))


def normalize(mesh):
    result=mesh.copy(); result.apply_translation(-result.bounds[0]); return result


def print_pin(mesh,horizontal=True):
    result=mesh.copy()
    if horizontal:
        result.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
    else:
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


def cross_section(parts,pin_mesh):
    fig,ax=plt.subplots(figsize=(12,6))
    for mesh,color,label in [(parts[0],'#a81332','A: lower lug'),(parts[1],'#e9b92e','B: upper lug'),
                             (pin_mesh,'#20a650','smooth T pin')]:
        section=mesh.section(plane_origin=[43,-3,0],plane_normal=[0,1,0])
        assert section is not None
        lines=[LineString(section.vertices[entity.points][:,[0,2]]) for entity in section.entities]
        for polygon in polygonize(unary_union(lines)):
            ax.fill(*polygon.exterior.xy,color=color,alpha=.85)
        ax.plot([],[],color=color,lw=6,label=label)
    ax.axhline(LOWER,color='gray',ls='--',lw=.6); ax.axhline(UPPER,color='gray',ls='--',lw=.6)
    ax.annotate('0.25 mm vertical lap clearance',xy=(49,(LOWER+UPPER)/2),xytext=(52,5.8),
                arrowprops=dict(arrowstyle='->'),fontsize=10)
    ax.annotate('Head rests on upper lug; pull upward to remove',xy=(43,12.4),xytext=(33,15),
                arrowprops=dict(arrowstyle='->'),fontsize=10)
    ax.annotate('Bottom tip remains 0.2 mm above table',xy=(43,.2),xytext=(32,-2.5),
                arrowprops=dict(arrowstyle='->'),fontsize=10)
    ax.set_xlim(31,62); ax.set_ylim(-3.5,17); ax.set_aspect('equal')
    ax.set_xlabel('X, mm'); ax.set_ylabel('Z, mm'); ax.legend(loc='upper right',fontsize=9)
    ax.set_title('Actual mesh section through 4 mm-family pin and stepped seam lugs (Y = -3 mm)')
    fig.tight_layout(); fig.savefig(OUT/'pin_and_seam_cross_section.png',dpi=160); plt.close(fig)


def dimensional_diagram(wells,lugs):
    fig,axes=plt.subplots(1,3,figsize=(16,6))
    ax=axes[0]
    x,y=cad.curved_rectangle((0,0,86,48),[8]*4).exterior.xy
    ax.fill(x,y,color='#dddddd')
    for index,w in enumerate(wells):
        x,y=w.exterior.xy; ax.fill(x,y,color=['#a81332','#e9b92e'][index],alpha=.6)
        ax.text(w.centroid.x,w.centroid.y,f'{"AB"[index]}\n36 x 36\nR2 / depth 3',ha='center',va='center')
    for lug,(x,y,nominal,hole) in zip(lugs,CENTERS):
        xx,yy=lug.exterior.xy; ax.fill(xx,yy,color='#e9b92e',alpha=.65)
        xx,yy=Point(x,y).buffer(hole/2,quad_segs=64).exterior.xy; ax.fill(xx,yy,color='white')
    ax.axvline(43,color='black',ls='--',lw=.6)
    ax.annotate('',xy=(24,43),xytext=(62,43),arrowprops=dict(arrowstyle='<->'))
    ax.text(43,46,'38 mm pitch / 2 mm divider',ha='center',fontsize=8)
    ax.text(43,62,'86 x 48 mm gameplay chassis\nExtra outboard lugs; total envelope about 86 x 68 mm',ha='center',fontsize=8)
    ax.set_xlim(-5,91); ax.set_ylim(66,-15); ax.set_aspect('equal'); ax.axis('off'); ax.set_title('Two real spaces, seam between sockets')
    for ax,lug,(x,y,nominal,hole) in zip(axes[1:],lugs,CENTERS):
        xx,yy=lug.exterior.xy; ax.fill(np.array(xx)-x,np.array(yy)-y,color='#e9b92e',alpha=.7)
        xx,yy=Point(0,0).buffer(hole/2,quad_segs=64).exterior.xy; ax.fill(xx,yy,color='white')
        ax.annotate('',xy=(-hole/2,0),xytext=(hole/2,0),arrowprops=dict(arrowstyle='<->'))
        ax.text(0,-1,f'Bore {hole:.2f} mm',ha='center',fontsize=10)
        ax.text(0,11,f'R7 outer support / R2 roots\n4.875 mm ear thickness\nEntry chamfer: 0.5 mm\nMin entry wall: {7-hole/2-.5:.2f} mm',ha='center',fontsize=10)
        ax.set_xlim(-11,11); ax.set_ylim(15,-10); ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(f'{nominal:.0f} mm shaft family')
    fig.suptitle('Canonical two-space chassis and stepped-lug dimensions',y=.97)
    fig.subplots_adjust(top=.80,bottom=.12,wspace=.22)
    fig.savefig(OUT/'pin_lug_dimensions.png',dpi=160); plt.close(fig)


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
        if index==0:
            body=cad.union([cad.extrude(full,LOWER),cad.extrude(cleared,HEIGHT-LOWER,LOWER)])
        else:
            body=cad.union([cad.extrude(cleared,UPPER),cad.extrude(full,HEIGHT-UPPER,UPPER)])
        socket=cad.extrude(wells[index],3.2,7)
        notch=cad.extrude(removal(wells[index]),1.3,8.8)
        holes=[]
        for x,y,_,hole in CENTERS:
            tool=bore(hole/2,LOWER if index==0 else HEIGHT,.4 if index==0 else .5)
            tool.apply_translation([x,y,0]); holes.append(tool)
        body=cad.difference(body,cad.union([socket,notch,*holes]))
        path=OUT/f'prototype_2x1_part_{"AB"[index]}.stl'
        loaded=export(normalize(body),path)
        loaded.apply_translation(body.bounds[0])
        body=loaded
        files.append(measure(path)); parts.append(body)
        floor_mask=np.all(np.isclose(body.triangles[:,:,2],7,atol=1e-5),axis=1)
        floor=unary_union([Polygon(t[:,:2]) for t in body.triangles[floor_mask]])
        assert floor.buffer(.001).covers(wells[index])
        assert wells[index].buffer(.001).covers(floor)
        if index==1:
            supported=full.difference(cleared).difference(unary_union([Point(x,y).buffer(hole/2,quad_segs=64) for x,y,_,hole in CENTERS]))
            support_area=supported.area
    contact=trimesh.boolean.intersection(parts,engine='manifold')
    assert intersection_volume(contact)<.0001
    for distance in [.25,.5,1,2,4,8,16]:
        moved=parts[1].copy(); moved.apply_translation([distance,0,0])
        assert intersection_volume(trimesh.boolean.intersection([parts[0],moved],engine='manifold'))<.0001,'Unpinned joint binds'
    assert min(lug.distance(well) for lug in lugs for well in wells)>2
    minimum_socket_ligament=min(lug.buffer(GAP).distance(w) for lug in lugs for w in wells)
    assert minimum_socket_ligament>1.7
    variants=[]; installed=[]
    for x,y,nominal,hole in CENTERS:
        for dots,clearance in enumerate(CLEARANCES,1):
            diameter=hole-2*clearance
            model=pin(diameter,nominal,dots)
            path=OUT/'pins'/f'T_pin_{nominal:.0f}mm_family_clearance_{clearance:.2f}_shaft_{diameter:.2f}.stl'
            rotated=model.copy(); rotated.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
            loaded=export(print_pin(model),path); files.append(measure(path))
            loaded.apply_translation(rotated.bounds[0])
            loaded.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]))
            model=loaded
            placed=model.copy(); placed.apply_translation([x,y,0])
            for body in parts:
                collision=trimesh.boolean.intersection([body,placed],engine='manifold')
                assert intersection_volume(collision)<.0001,(nominal,clearance,'pin does not seat')
            moved=parts[1].copy(); moved.apply_translation([1,0,0])
            blocked=trimesh.boolean.intersection([moved,placed],engine='manifold')
            assert intersection_volume(blocked)>.1,(nominal,clearance,'no positive lateral stop')
            for height in [.5,3,6,11]:
                lifted=placed.copy(); lifted.apply_translation([0,0,height])
                for body in parts:
                    assert intersection_volume(trimesh.boolean.intersection([body,lifted],engine='manifold'))<.0001,'Pin cannot withdraw vertically'
            variants.append({'family_mm':nominal,'shaft_diameter_mm':round(diameter,2),'hole_diameter_mm':hole,
                             'clearance_per_side_mm':clearance,'head_mm':list(HEAD_SIZE),'identification':f'{nominal:.0f} + {dots} dots',
                             'minimum_radial_wall_mm':round(LUG_RADIUS-hole/2,3),
                             'minimum_entry_wall_mm':round(LUG_RADIUS-hole/2-.5,3)})
            if clearance==.2: installed.append(placed)
    for source in sorted((ROOT/'output/canonical_chassis/fit_test').glob('blank_test_tile_*.stl')):
        target=OUT/'tiles'/source.name; shutil.copyfile(source,target); files.append(measure(target))
        assert source.read_bytes()==target.read_bytes()
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
    cross_section(parts,installed[0]); dimensional_diagram(wells,lugs)
    assert production_hashes()==frozen,'Production board quadrants changed'
    report={'passed':True,'canonical_gameplay_dimensions_unchanged':True,'production_quadrants_unchanged':True,
            'production_sha256':frozen,'files':files,'pin_variants':variants,
            'socket_mm':[36,36],'socket_depth_mm':3,'socket_radius_mm':2,'pitch_mm':38,'divider_mm':2,
            'board_thickness_mm':10,'outer_track_rim_mm':6,'removal_recess':'exact canonical function',
            'board_seam_clearance_mm':GAP,'lap_vertical_clearance_mm':GAP,'lug_perimeter_clearance_mm':GAP,
            'lower_lug_thickness_mm':LOWER,'upper_lug_thickness_mm':HEIGHT-UPPER,
            'minimum_mechanism_to_socket_mm':round(minimum_socket_ligament,3),
            'part_B_supported_ear_area_mm2_approx':round(support_area,1),
            'positive_lateral_pin_stop_checked_mm':1.0,'tile_clearance_selected':False,
            'retention':'Gravity: vertical pins, heads rest on upper ears. Not captive against upward lift or inversion.',
            'orientation':{'part_A':'socket up, flat underside on bed, no supports',
                           'part_B':'socket up; paint supports only under raised lug ears at Z=5.125 mm, avoid bores and sockets',
                           'pins':'STLs oriented horizontally for PLA strength; light supports under shaft. Head-down vertical print is support-free but weaker in bending.',
                           'tiles':'flat underside on bed; existing top identification dots'},
            'warnings':['Canonical fingernail recess locally leaves 1 mm of divider at the top; do not pry with tools.',
                        'Upper B ears are unsupported during printing without painted supports; remove support scars carefully.',
                        'Smooth gravity pins prevent lateral pull-apart but are not captive against vertical lifting or inversion.',
                        'Largest pin clearance permits up to about 0.6 mm relative play; test rattle and seam movement.',
                        'PLA wear, actual pin/ear strength and repeated-use durability require the physical print test.'],
            'no_gameplay_tiles_generated':True}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    write_readme(report)
    with zipfile.ZipFile(ROOT/'output/pin_joint_prototype_print_kit.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob('*')):
            if path.is_file(): archive.write(path,path.relative_to(OUT))
    print(f'PASS: {len(files)} watertight STLs, unchanged universal sockets, all 16 production quadrants unchanged.',flush=True)


def write_readme(report):
    lines=['# Two-space PLA pin-joint physical prototype','',
           'Part A and B form two adjacent canonical spaces. Push horizontally together, then insert one vertical pin through each outboard stepped lug. Red A has lower ears; yellow B has upper ears. T heads rest on B and retain pins by gravity. Pull heads upward to remove. Both pins are recommended for a rigid joint; test either size alone to compare. Hold both halves when lifting: this is not a captive transport lock.', '',
           'Gameplay chassis: 86 x 48 x 10 mm, plus outboard lug projections. Wells: 36 x 36 mm, 3 mm deep, R2; pitch 38 mm, nominal dividers 2 mm, external track rim 6 mm. The fingernail recess is unchanged. The lug footprint is outside the sockets; only local rim/staging volume changes. No socket is intersected by a seam or bore.', '',
           '| Family | Shaft diameter | Bore diameter | Clearance per side | Head marking |',
           '|---|---:|---:|---:|---|']
    for p in report['pin_variants']:
        lines.append(f"| {p['family_mm']:.0f} mm | {p['shaft_diameter_mm']:.2f} | {p['hole_diameter_mm']:.2f} | {p['clearance_per_side_mm']:.2f} | {p['identification']} |")
    lines.extend(['','Bores remain fixed at 4.40 and 5.40 mm, so changing the actual shaft diameter tests fit on the same pair of bodies. The 0.20 mm-per-side variants have exactly 4.00 and 5.00 mm shafts. All mating shafts are smooth, with no threads, hooks or spring features.', '',
                  f'T heads: 12 x 6 x 2.4 mm, R1.5 plan corners, 0.4 mm shaft/head root fillet. Shaft engagement length 9.8 mm; bottom tip is 0.2 mm above the table. Bottom lead-in: 0.4 mm radial / 0.5 mm axial. Bore lead-in: 0.4 mm on A and 0.5 mm on B. Both solid ears are {LOWER:.3f} mm thick, with 0.25 mm vertical clearance and 0.25 mm mating outline clearance. Lug supports use R7 lobes and R2 neck/root fillets.', '',
                  'Minimum wall around the straight bore: 4.80 mm (4 mm family), 4.30 mm (5 mm family). Minimum at the widest entry chamfer: 4.30 / 3.80 mm respectively.',
                  f'Minimum material between locking cutouts and a tile socket: **{report["minimum_mechanism_to_socket_mm"]:.3f} mm**. All lug outlines are outside the tile socket projections.', '',
                  '## Print and test','',
                  'Use PLA, 0.4 mm nozzle and 100% scale. For the two bodies, use 0.125 mm layers including the first layer: 4.875 mm and 5.125 mm then land exactly on layer boundaries, preserving the 0.25 mm lap gap. Using 0.20 mm body layers is possible but quantizes the vertical lap clearance. Pins and tiles can use 0.20 mm layers. Use four or more walls and solid infill in lugs and pins (local modifiers for lugs); verify load-bearing sections in the slicer. Do not auto-orient the supplied STLs. No brim is included in dimensions.', '',
                  'Part A: socket up, underside flat on the bed, no support needed. Part B: socket up, painted supports under the two raised ears only. They start at Z=5.125 mm; total supported ear underside is about '+str(report['part_B_supported_ear_area_mm2_approx'])+' mm². Keep support out of bores and wells. Inspect and clean those mating undersides before assembling.', '',
                  'Pins are supplied horizontally to improve PLA bending strength along the shaft. Add light supports below the round shaft and root fillet. Remove scars without changing the fit diameter. For an initial support-free fit-only print, rotate shaft vertical with the flat T-head top on the bed; this orientation is weaker for repeated joint loading. Vertical bore orientation in the bodies needs no internal support.', '',
                  'Reuse the four included 2.8 mm blank tile tests: 35.70 / 35.60 / 35.50 / 35.40 mm, respectively 0.15 / 0.20 / 0.25 / 0.30 mm clearance per side. Existing one-to-four top dots identify them. They sit 0.2 mm below the dividers.', '',
                  'Test tile insertion/removal in both sockets and four rotations, repeated swapping/flipping, rattle, feel of the recess/dividers, seam flushness, pin insertion/removal, lateral joint rigidity with one and both pins, and visible PLA wear after repeated assembly. Start with 0.20 mm pin clearance; compare all four before selecting either pin or tile tolerance.', '',
                  '## Digital validation','',
                  'Both socket floors match the canonical rounded square, with no pin/lug intrusion. Assembled parts do not intersect; all pin variants seat without interference. Translating B 1 mm outward with either seated pin fixed encounters solid interference, demonstrating a positive lateral stop. Every exported STL reloads as a connected, watertight mesh with consistent winding, two incident faces per edge, positive volume and an A1-compatible XY envelope. Production quadrant SHA-256 hashes are unchanged.', '',
                  '| STL | X x Y x Z, mm | Manifold / A1 fit |','|---|---|---|'])
    for file in report['files']:
        x,y,z=file['xyz_mm']; lines.append(f"| {file['file']} | {x:.3f} x {y:.3f} x {z:.3f} | Pass |")
    lines.extend(['','## Limits and PLA risks',''])
    lines.extend('- '+warning for warning in report['warnings'])
    lines.extend(['','No thin spring, hook, cantilevered latch or repeated-flex retention is present. The raised B lugs are thick structural ears, but require printing support. Digital collision tests do not predict PLA fatigue, layer adhesion or print tolerances. Dimensions come from exported meshes, not an actual Bambu Studio slicing run. No tolerance or production-lock change is frozen by this prototype. No colored/gameplay-effect tiles are generated.'])
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    main()
