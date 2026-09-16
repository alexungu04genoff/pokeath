"""Build all four boards at a shared pitch and measure finished print STLs.

Uses explicit traced track grids, 38 mm curved wells, >=3 mm outer rims,
the existing snap rails, and independently optimised print orientations.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from shapely.geometry import box, LineString, Polygon
from shapely import affinity
from shapely.ops import unary_union
import trimesh
import matplotlib.pyplot as plt
from src.chassis import build_printable_board as cad
from src.chassis import analyse_board_sizes as study

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'/'archive'/'final_sizing_40mm'
PITCH=40.0
WELL=PITCH-2.0
RIM=3.0
CONFIGS={
 'Akala':{'origin':(448,45),'rows':{0:list(range(1,7)),1:[1,6],2:[1,6],3:[1,6],4:[1,6],5:[0,1,5,6],6:[0,4,5],7:[0,4],8:[4],9:[1,2,3,4],10:[1]},'finish':(380,1359,580,1488)},
 'Melemele':{'origin':(150,310),'rows':{0:list(range(1,7)),1:[0,1,6,7],2:[0,7],3:[0,5,6,7],4:[0],5:[0,1,2,3,8,9],6:list(range(3,9))},'finish':(595,707,809,829)},
 'Poni':{'origin':(255,118),'rows':{0:[4],1:list(range(4,9)),2:[3,4,8,9],3:[3,9],4:[3,4,8,9],5:[0,1,2,4,8],6:[0,2,4,7,8],7:[0,2,3,4,7],8:[0,4,5,6,7]},'finish':(575,122,781,244)},
 'Ulaula':{'origin':(150,180),'rows':cad.ROWS,'finish':(216,184,416,306)},
}


def fit_mesh(mesh):
    from scipy.spatial import ConvexHull
    points=mesh.vertices[:,:2]
    points=points[ConvexHull(points).vertices]
    angles=np.deg2rad(np.arange(0,90.001,.02))
    u=points[:,0,None]*np.cos(angles)+points[:,1,None]*np.sin(angles)
    v=-points[:,0,None]*np.sin(angles)+points[:,1,None]*np.cos(angles)
    sizes=np.column_stack([np.ptp(u,axis=0),np.ptp(v,axis=0)])
    best=int(np.argmin(sizes.max(axis=1)))
    rotation=float(np.rad2deg(angles[best]))
    result=mesh.copy()
    result.apply_transform(trimesh.transformations.rotation_matrix(-angles[best],[0,0,1]))
    result.apply_translation(-result.bounds[0])
    return result,rotation


def export(mesh,path):
    mesh.export(path)
    loaded=trimesh.load_mesh(path)
    assert loaded.is_watertight and loaded.is_winding_consistent and loaded.volume>0
    assert len(loaded.split())==1,path
    assert np.isfinite(loaded.vertices).all()
    return loaded


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    prior=json.loads((ROOT/'output/archive/sizing/board_size_comparison.json').read_text())
    results=[]
    fig,axes=plt.subplots(2,2,figsize=(13,13))
    cad.SCALE=PITCH/study.PITCH
    for entry,ax in zip(prior['boards'],axes.flat):
        name=entry['board']; config=CONFIGS[name]
        file=next(b[1] for b in study.BOARDS if b[0]==name)
        image=Image.open(ROOT/file)
        shape=cad.mm_poly(cad.reference_outline(image))
        x0,y0=config['origin']
        wells=[]
        # Choose large corner arcs from proximity to the actual board outline.
        for row,cols in config['rows'].items():
            for col in cols:
                x=(x0+(col+.5)*study.PITCH)*cad.SCALE
                y=(y0+(row+.5)*study.PITCH)*cad.SCALE
                rect=(x-WELL/2,y-WELL/2,x+WELL/2,y+WELL/2)
                radii=[.8]*4
                corners=[(rect[0],rect[1]),(rect[2],rect[1]),(rect[2],rect[3]),(rect[0],rect[3])]
                from shapely.geometry import Point
                for index,point in enumerate(corners):
                    if shape.exterior.distance(Point(point))<2.7 or not shape.covers(Point(point)):
                        radii[index]=10
                well=cad.curved_rectangle(rect,radii)
                wells.append({'id':f'R{row}C{col}','poly':well})
        finish=tuple(v*cad.SCALE for v in config['finish'])
        wells.append({'id':'FINISH','poly':cad.curved_rectangle(finish,[18,.8,.8,18])})
        # Preserve the smoothed silhouette but add real material wherever the
        # artwork's drawn rim would leave less than the specified outer rim.
        outer=unary_union([shape,*[w['poly'].buffer(RIM,quad_segs=48) for w in wells]])
        outer=outer.buffer(.25,quad_segs=32).buffer(-.25,quad_segs=32)
        assert outer.geom_type=='Polygon'
        y=entry['primary_seam_reference_coordinate']*cad.SCALE
        assert entry['primary_seam_direction']=='horizontal'
        xt,xb=[v*cad.SCALE for v in entry['secondary_seam_reference_coordinates']]
        areas=[box(-100,-100,xt,y),box(xt,-100,1000,y),box(-100,y,xb,1000),box(xb,y,1000,1000)]
        # Detour a seam around any complete curved well, never through it.
        for well in wells:
            p=well['poly'].buffer(.35,join_style=2)
            owner=max(range(4),key=lambda i:areas[i].intersection(p).area)
            for i in range(4):
                areas[i]=areas[i].union(p) if i==owner else areas[i].difference(p)
            well['part']=owner
        footprints=[outer.intersection(a).buffer(-cad.SEAM_GAP/2,join_style=2) for a in areas]
        assert all(p.geom_type=='Polygon' for p in footprints)
        for well in wells:
            assert footprints[well['part']].covers(well['poly']),well['id']
        horizontal=outer.intersection(LineString([(-100,y),(1000,y)]))
        lower=outer.intersection(LineString([(xb,y),(xb,1000)]))
        locks=[('K1',np.array([horizontal.bounds[0],y]),np.array([1,0])),
               ('K2',np.array([horizontal.bounds[2],y]),np.array([-1,0])),
               ('K3',np.array([xb,lower.bounds[3]]),np.array([0,-1]))]
        cavities=[]; bars=[]; keys=[]
        key=cad.snap_key()
        for _,p,d in locks:
            cavities.append(cad.dovetail(p-d*7,d,37.8,True))
            bars.append(cad.catch_bar(p,d))
            keys.append(cad.place_connector(key,p-d*4,d))
        pocket=cad.union([cad.extrude(w['poly'],cad.STICKER_DEPTH+.2,cad.BASE-cad.STICKER_DEPTH) for w in wells])
        cuts=cad.union(cavities+[pocket])
        models=[]; rows=[]
        board_dir=OUT/name; board_dir.mkdir(exist_ok=True)
        for index,footprint in enumerate(footprints):
            raw=cad.extrude(footprint,cad.BASE)
            model=cad.difference(raw,cuts)
            catch=trimesh.boolean.intersection([cad.union(bars),raw],engine='manifold')
            if len(catch.faces): model=cad.union([model,catch])
            # Validate every playing floor, including START, is an unbroken plane.
            horizontal_faces=np.all(np.isclose(model.triangles[:,:,2],6.6,atol=1e-5),axis=1)
            floor=unary_union([Polygon(t[:,:2]) for t in model.triangles[horizontal_faces]])
            for w in wells:
                if w['part']==index:
                    assert floor.buffer(.001).covers(w['poly'].buffer(-.05)),name+w['id']
            models.append(model)
            print_model=model.copy(); print_model.apply_scale([1,-1,1])
            oriented,angle=fit_mesh(print_model)
            path=board_dir/f'quadrant_{index+1}.stl'
            loaded=export(oriented,path)
            rows.append({'quadrant':index+1,'file':str(path.relative_to(ROOT)),
                         'print_rotation_degrees':round(angle,2),
                         'stl_xy_mm':loaded.extents[:2].round(3).tolist(),
                         'z_mm':round(float(loaded.extents[2]),3)})
            print(name,rows[-1],flush=True)
        assembled=cad.union(models)
        for installed,(_,p,d) in zip(keys,locks):
            collision=trimesh.boolean.intersection([assembled,installed],engine='manifold')
            assert len(collision.faces)==0 or collision.volume<.001,name+' seated lock collision'
            moved=installed.copy(); moved.apply_translation([*-d*.9,0])
            stop=trimesh.boolean.intersection([assembled,moved],engine='manifold')
            assert stop.volume>.05,name+' no latch stop'
        for index,model in enumerate(models):
            applicable=[]
            for k in keys:
                overlap=trimesh.boolean.intersection([cad.extrude(footprints[index].buffer(.5),5),k],engine='manifold')
                if len(overlap.faces) and overlap.volume>.01:
                    applicable.append(k)
            if applicable:
                envelope=trimesh.util.concatenate([model,*applicable])
                envelope.apply_scale([1,-1,1])
                # Same rotation as actual STL: do not confuse assembled envelope
                # with the separate rail's print footprint.
                envelope.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-rows[index]['print_rotation_degrees']),[0,0,1]))
                rows[index]['xy_with_installed_loose_keys_mm']=envelope.extents[:2].round(3).tolist()
        rim=min(outer.exterior.distance(w['poly']) for w in wells)
        results.append({'board':name,'pitch_mm':PITCH,'nominal_well_mm':[WELL,WELL],
                        'internal_divider_mm':2,'minimum_outer_rim_mm':round(rim,3),
                        'quadrants':rows,'well_count_including_finish':len(wells)})
        ax.imshow(image,extent=(0,1614*cad.SCALE,1536*cad.SCALE,0))
        for i,p in enumerate(footprints):
            coords=np.array(p.exterior.coords)
            ax.plot(coords[:,0],coords[:,1],lw=1.4,color=['#00a3ad','#dbab25','#9b60c8','#32a366'][i])
            for w in wells:
                if w['part']==i:
                    coords=np.array(w['poly'].exterior.coords)
                    ax.plot(coords[:,0],coords[:,1],color='white',lw=.5)
        for label,p,d in locks:
            ax.annotate(label,xy=p,xytext=p-d*18,ha='center',fontsize=9,
                        arrowprops=dict(arrowstyle='->',color='#ff5634'))
        ax.set_title(name+' | finished 40 mm pitch geometry'); ax.axis('off')
    print_key=cad.snap_key(); print_key.apply_scale([1,1,-1]); print_key.apply_translation(-print_key.bounds[0])
    export(print_key,OUT/'snap_key_print_3_per_board.stl')
    # Existing test coupons use the exact same fixed-size connector geometry.
    for source in (ROOT/'output/archive/paper_art/stl').glob('fit_test_*.stl'):
        export(trimesh.load_mesh(source),OUT/source.name)
    largest=max(max(q['stl_xy_mm']) for b in results for q in b['quadrants'])
    data={'pitch_mm':PITCH,'brim_included':False,'stl_dimensions_include_all_integral_geometry':True,
          'keys_printed_separately':True,'largest_quadrant_xy_dimension_mm':largest,
          'recommendation':'Keep 40 mm pitch' if largest<=248 else 'Use 39 mm pitch',
          'boards':results,'limitations':['Measured from reloaded exported STLs, not a Bambu Studio slicing run.',
               'STL rotation is baked in. Import at 100% with no automatic reorientation.',
               'Snap elasticity, internal support removal and physical print fit remain untested.',
               'Outer rim retains smoothed artwork contour with a minimum 3 mm around playing wells.']}
    (OUT/'finished_stl_bounds.json').write_text(json.dumps(data,indent=2)+'\n')
    lines=['# Finished STL sizing at 40 mm pitch','',
           'All dimensions are millimetres. Measured from reloaded exported STLs at 100% scale. '
           'Print rotations are baked in; do not automatically reorient. No brim included.', '',
           '| Board | Grid pitch | Nominal well | Internal divider | Minimum outer rim | Largest quadrant XY |',
           '|---|---:|---|---:|---:|---|']
    for b in results:
        q=max(b['quadrants'],key=lambda q:max(q['stl_xy_mm']))
        lines.append(f"| {b['board']} | 40 | 38 x 38 | 2 | {b['minimum_outer_rim_mm']:.3f} | Q{q['quadrant']}: {q['stl_xy_mm'][0]:.3f} x {q['stl_xy_mm'][1]:.3f} |")
    lines.extend(['','Outer rims follow the artwork silhouette and have variable width; the reported width is the actual minimum distance from a playing well to the external board outline. Curved corners reduce the rectangular well footprint; START banners remain flat, with no engraved text. Finish wells follow their artwork proportions.', '',
                  '| Board | Quadrant | Finished print STL XY | Baked rotation | Envelope with loose keys installed* |',
                  '|---|---:|---|---:|---|'])
    for b in results:
        for q in b['quadrants']:
            x,y=q['stl_xy_mm']; a,c=q.get('xy_with_installed_loose_keys_mm',[x,y])
            lines.append(f"| {b['board']} | {q['quadrant']} | {x:.3f} x {y:.3f} | {q['print_rotation_degrees']:.2f} deg | {a:.3f} x {c:.3f} |")
    lines.extend(['','*Installed keys are separate components and also span neighbouring quadrants. This assembly envelope is not the quadrant print footprint. Print three separate keys per board.', '',
                  f'Largest finished STL axis: **{largest:.3f} mm**. Recommendation: **{data["recommendation"]}**.', '',
                  'Validation: all 16 quadrants reloaded as connected, watertight meshes with consistent winding and positive volume; wells stay wholly inside their assigned quadrant and have continuous flat floors. Installed keys clear the boards and encounter the latch stop on withdrawal.', '',
                  'Limitations: no Bambu Studio slicing run or physical snap-fit test; support removal and latch elasticity remain untested. Existing paper-art PDFs use the earlier scale and must be regenerated for these boards.'])
    (OUT/'SIZING_REPORT.md').write_text('\n'.join(lines)+'\n')
    fig.tight_layout(); fig.savefig(OUT/'final_geometry_plan.png',dpi=150); plt.close(fig)
    print('PASS. Largest finished quadrant dimension:',largest,flush=True)


if __name__=='__main__': main()
