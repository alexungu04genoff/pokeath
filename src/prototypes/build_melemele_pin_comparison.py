"""Rebuild one full-size comparison board with provisional rigid T-pin lugs.

The canonical production quadrants remain read-only. This experiment inherits
their socket positions and silhouette, but rebuilds solids without snap rails.
"""
import json
import hashlib
import zipfile
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon, LineString, Point
from shapely import affinity
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from src.chassis import build_printable_board as cad
from src.chassis.build_canonical_chassis import ROOT, STANDARD, export, fit_mesh, removal
from src.prototypes.build_pin_joint_prototype import lug_profile, bore, pin, print_pin, intersection_volume, render, production_hashes, LOWER, UPPER

OUT=ROOT/'output'/'archive'/'Melemele_pin_comparison'


def checked_export(mesh,path,expected=1):
    if expected==1:
        loaded=export(mesh,path)
    else:
        mesh.export(path); loaded=trimesh.load_mesh(path)
    assert loaded.is_watertight and loaded.is_winding_consistent
    assert np.all(np.bincount(loaded.edges_unique_inverse)==2)
    assert len(loaded.split())==expected
    return loaded


def main():
    hashes=production_hashes(); OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/'output/CURRENT/boards/finished_stl_bounds.json').read_text())
    board=next(b for b in data['boards'] if b['board']=='Melemele')
    study=json.loads((ROOT/'output/archive/sizing/board_size_comparison.json').read_text())
    layout=next(b for b in study['boards'] if b['board']=='Melemele')
    footprints=[]; wells=[]
    for q in board['quadrants']:
        mesh=trimesh.load_mesh(ROOT/q['file'])
        mesh.apply_transform(np.linalg.inv(q['assembly_to_print_transform']))
        triangles=mesh.triangles[np.abs(mesh.face_normals[:,2])>.99]
        footprint=unary_union([Polygon(t[:,:2]) for t in triangles]).simplify(.002)
        assert footprint.geom_type=='Polygon'
        footprint=Polygon(footprint.exterior).buffer(.005).buffer(-.005).simplify(.002)
        footprints.append(footprint)
        wells.append([cad.curved_rectangle((x-18,y-18,x+18,y+18),[2]*4) for x,y in q['socket_centers_assembly_mm']])
    silhouette=unary_union(footprints).buffer(.13).buffer(-.13)
    scale=38/131.5
    y=layout['primary_seam_reference_coordinate']*scale
    xb=layout['secondary_seam_reference_coordinates'][1]*scale
    cross=silhouette.intersection(LineString([(-100,y),(1000,y)]))
    lower=silhouette.intersection(LineString([(xb,y),(xb,1000)]))
    ports=[(np.array([cross.bounds[0],y]),np.array([-1.,0]),0,2),
           (np.array([cross.bounds[2],y]),np.array([1.,0]),1,3),
           (np.array([xb,lower.bounds[3]]),np.array([0.,1]),2,3)]
    lugs=[]; centers=[]
    all_wells=[w for group in wells for w in group]
    for origin,outward,a,b in ports:
        local=lug_profile(0,-3)
        across=np.array([-outward[1],outward[0]])
        inward=-outward
        transformed=affinity.affine_transform(local,[across[0],inward[0],across[1],inward[1],*origin])
        minimum=min(transformed.buffer(.25).distance(w) for w in all_wells)
        assert minimum>1.7,('Lug too close to socket',minimum)
        lugs.append(transformed); centers.append(origin+outward*3)
    models=[]; records=[]
    for index,footprint in enumerate(footprints):
        own=[(lug,a,b) for lug,(_,_,a,b) in zip(lugs,ports) if index in [a,b]]
        low=footprint; mid=footprint; high=footprint
        for lug,a,b in own:
            clear=lug.buffer(.25,quad_segs=48)
            mid=mid.difference(clear)
            if index==a:
                low=low.union(lug); high=high.difference(clear)
            else:
                low=low.difference(clear); high=high.union(lug)
        layers=[cad.extrude(low.simplify(.001),LOWER),
                cad.extrude(mid.simplify(.001),UPPER-LOWER,LOWER),
                cad.extrude(high.simplify(.001),10-UPPER,UPPER)]
        for level,layer in enumerate(layers):
            assert layer.is_volume,('Invalid layer',index,level,layer.is_watertight,layer.volume)
        model=cad.union(layers)
        cuts=[]
        for well in wells[index]:
            cuts.extend([cad.extrude(well,3.2,7),cad.extrude(removal(well),1.3,8.8)])
        for center,(_,_,a,b) in zip(centers,ports):
            if index not in [a,b]: continue
            tool=bore(2.7,LOWER if index==a else 10,.4 if index==a else .5)
            tool.apply_translation([*center,0]); cuts.append(tool)
        model=cad.difference(model,cad.union(cuts))
        printing=model.copy(); printing.apply_scale([1,-1,1])
        printing,angle=fit_mesh(printing)
        path=OUT/f'Melemele_comparison_quadrant_{index+1}.stl'
        loaded=checked_export(printing,path)
        assert max(loaded.extents[:2])<=248
        records.append({'quadrant':index+1,'xyz_mm':loaded.extents.round(3).tolist(),
                        'maximum_xy_mm':round(float(max(loaded.extents[:2])),3),
                        'baked_print_rotation_degrees':angle,'fits_A1':True,'watertight_manifold':True,
                        'whole_socket_count':len(wells[index])})
        triangles=model.triangles
        floor=unary_union([Polygon(t[:,:2]) for t in triangles[np.all(np.isclose(triangles[:,:,2],7,atol=1e-5),axis=1)]])
        reference=unary_union(wells[index])
        assert floor.buffer(.005).covers(reference) and reference.buffer(.005).covers(floor)
        models.append(model)
    for index,a in enumerate(models):
        for b in models[index+1:]:
            assert intersection_volume(trimesh.boolean.intersection([a,b],engine='manifold'))<.001
    pin_model=pin(5,5,2)
    installed=[]
    for center,(_,_,a,b) in zip(centers,ports):
        placed=pin_model.copy(); placed.apply_translation([*center,0]); installed.append(placed)
        for index in [a,b]:
            assert intersection_volume(trimesh.boolean.intersection([models[index],placed],engine='manifold'))<.001
    copies=[]
    for i in range(3):
        copy=print_pin(pin_model); copy.apply_translation([i*22,0,0]); copies.append(copy)
    checked_export(trimesh.util.concatenate(copies),OUT/'three_5mm_T_pins_one_plate.stl',3)
    assembly=trimesh.util.concatenate(models)
    # A single file for viewing the actual complete size, not an A1 print file.
    checked_export(assembly,OUT/'Melemele_assembled_SIZE_REFERENCE_NOT_FOR_A1.stl',4)
    colors=['#3ba9b0','#e0b647','#9573bd','#72ad8c']
    render([*zip(models,colors),*[(p,'#20a650') for p in installed]],OUT/'assembled_top.png','Melemele | full-size T-pin comparison board')
    render([*zip(models,colors),*[(p,'#20a650') for p in installed]],OUT/'assembled_underside.png','Melemele | underside with provisional T pins',-50,-60)
    sizing_diagram(models,wells,lugs)
    assert production_hashes()==hashes
    envelope=trimesh.util.concatenate([*models,*installed]).extents
    report={'board':'Melemele','canonical_standard':STANDARD,'production_quadrants_unchanged':True,
            'assembled_chassis_xyz_mm':assembly.extents.round(3).tolist(),
            'assembled_with_pins_xyz_mm':envelope.round(3).tolist(),'quadrants':records,
            'socket_count':sum(len(g) for g in wells),'shaft_mm':5,'bore_mm':5.4,
            'pin_clearance_per_side_mm':.2,'lock_status':'Provisional; no physical fit results selected',
            'all_socket_floors_whole_and_universal':True,
            'minimum_lug_cutout_to_socket_mm':round(min(l.buffer(.25).distance(w) for l in lugs for w in all_wells),3),
            'supports':'Only beneath raised upper lugs and horizontal T-pin shafts; avoid wells and bores.',
            'limitations':['Gravity-retained pins are not captive against lifting or inversion.',
                           'Dimensions are measured from meshes, not a Bambu Studio slicing run.',
                           'This is an experimental comparison board; no tile or pin tolerance is frozen.']}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Melemele full-size comparison board','',
           'This is a separate experiment with the miniature prototype\'s rigid stepped-lug mechanism. The 16 canonical production quadrants are unchanged. No physical fit results have been supplied; 5 mm shafts / 5.4 mm bores / 0.20 mm per-side clearance are provisional.', '',
           f'Assembled chassis: {assembly.extents[0]:.2f} x {assembly.extents[1]:.2f} x 10 mm. With T heads: {envelope[0]:.2f} x {envelope[1]:.2f} x {envelope[2]:.2f} mm.', '',
           'Same 38 mm pitch, 36 x 36 x 3 mm sockets, R2, 2 mm dividers, 6 mm nominal external track rim, canonical removal recess and 0.25 mm section seam gap. Lugs adapt the exterior only; no socket is split or shrunk. Existing scenery silhouette and socket positions are inherited from Melemele.', '',
           '| Quadrant | Finished XYZ, mm | Maximum XY | A1 / manifold |','|---|---|---:|---|']
    for q in records:
        x,y,z=q['xyz_mm']; lines.append(f'| {q["quadrant"]} | {x:.3f} x {y:.3f} x {z:.3f} | {q["maximum_xy_mm"]:.3f} | Pass |')
    lines.extend(['','Print the four quadrant files separately at 100% with the baked orientations. Print `three_5mm_T_pins_one_plate.stl` once for three identical pins. `Melemele_assembled_SIZE_REFERENCE_NOT_FOR_A1.stl` is for viewing the full size only: it does not fit an A1 bed as one object.', '',
                  'Use the prototype print instructions: body layers 0.125 mm including the first layer preserve the 0.25 mm vertical lap gap; pins can use 0.20 mm layers. Supports are required under upper lugs and horizontal pin shafts. Make lugs/pins solid. Gravity retains pins; support all sections when lifting.', '',
                  'Validation: all four sections are watertight, fit below 248 mm and preserve all 29 socket floors. Section solids do not intersect and inserted pins clear their paired lugs. Full-size plan compares this board with the 86 x 68 mm two-space prototype on one millimetre scale. No gameplay tiles are generated.'])
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    with zipfile.ZipFile(ROOT/'output/Melemele_pin_comparison_print_kit.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if path.is_file(): archive.write(path,path.name)
    print('PASS: assembled',assembly.extents.round(2).tolist(),'mm; with pins',envelope.round(2).tolist(),'mm; four printable quadrants.')


def sizing_diagram(models,wells,lugs):
    fig,ax=plt.subplots(figsize=(13,8))
    points=np.vstack([m.vertices for m in models]); origin=points.min(axis=0)[:2]
    width,height=np.ptp(points,axis=0)[:2]
    for index,model in enumerate(models):
        triangles=model.triangles[np.abs(model.face_normals[:,2])>.99]
        shape=unary_union([Polygon(t[:,:2]) for t in triangles])
        coords=np.array(shape.exterior.coords)-origin
        ax.fill(coords[:,0],coords[:,1],color=['#3ba9b0','#e0b647','#9573bd','#72ad8c'][index],alpha=.65)
        for well in wells[index]:
            coords=np.array(well.exterior.coords)-origin
            ax.fill(coords[:,0],coords[:,1],color='white',alpha=.85)
    offset=np.array([width+35,height/2-24])
    mini=cad.curved_rectangle((0,0,86,48),[8]*4).union(lug_profile(43,-3)).union(lug_profile(43,51))
    coords=np.array(mini.exterior.coords)+offset
    ax.fill(coords[:,0],coords[:,1],color='#a7b9ab')
    for rect in [(6,6,42,42),(44,6,80,42)]:
        coords=np.array(cad.curved_rectangle(rect,[2]*4).exterior.coords)+offset
        ax.fill(coords[:,0],coords[:,1],color='white')
    ax.text(width+78,height/2+50,'2 x 1 prototype\n86 x 68 mm\nSame 36 mm sockets',ha='center')
    ax.annotate('',xy=(0,-20),xytext=(width,-20),arrowprops=dict(arrowstyle='<->'))
    ax.text(width/2,-25,f'{width:.1f} mm ({width/10:.1f} cm)',ha='center',va='bottom')
    ax.annotate('',xy=(-20,0),xytext=(-20,height),arrowprops=dict(arrowstyle='<->'))
    ax.text(-28,height/2,f'{height:.1f} mm ({height/10:.1f} cm)',ha='center',va='center',rotation=90)
    ax.set_aspect('equal'); ax.set_ylim(height+25,-50); ax.axis('off')
    ax.set_title('Melemele full board and miniature prototype | shared millimetre scale\nFull board shown assembled; four separate sections for A1 printing')
    fig.tight_layout(); fig.savefig(OUT/'actual_size_comparison.png',dpi=160); plt.close(fig)


if __name__=='__main__':
    main()
