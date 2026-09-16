"""Independently verify exported chassis and universal socket-floor geometry."""
from pathlib import Path
import json
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from src.chassis.build_canonical_chassis import STANDARD, OUT, ROOT, preview
from src.chassis.build_printable_board import curved_rectangle


def main():
    data=json.loads((OUT/'finished_stl_bounds.json').read_text())
    checked=[]
    for path in sorted(OUT.rglob('*.stl')):
        mesh=trimesh.load_mesh(path)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,path
        assert np.all(np.bincount(mesh.edges_unique_inverse)==2),path
        assert len(mesh.split())==1,path
        assert np.isfinite(mesh.vertices).all(),path
        assert max(mesh.extents[:2])<=256,path
        checked.append({'file':str(path.relative_to(ROOT)), 'xyz_mm':mesh.extents.round(3).tolist(),
                        'manifold_edges':True,'watertight':True,'fits_A1':True})
    socket_count=0
    rim_checks=[]
    for board in data['boards']:
        assembled_models=[]
        projected_footprints=[]
        socket_references=[]
        for quadrant in board['quadrants']:
            mesh=trimesh.load_mesh(ROOT/quadrant['file'])
            assert max(mesh.extents[:2])<=248
            assert abs(mesh.extents[2]-10)<.001
            assert np.allclose(mesh.extents[:2],quadrant['stl_xy_mm'],atol=.001)
            mesh.apply_transform(np.linalg.inv(quadrant['assembly_to_print_transform']))
            assembled_models.append(mesh)
            triangles=mesh.triangles
            at_floor=np.all(np.isclose(triangles[:,:,2],7,atol=.0001),axis=1)
            floor=unary_union([Polygon(t[:,:2]) for t in triangles[at_floor]])
            expected=[]
            for x,y in quadrant['socket_centers_assembly_mm']:
                expected.append(curved_rectangle((x-18,y-18,x+18,y+18),[2]*4))
            reference=unary_union(expected)
            socket_references.append(expected)
            projected_footprints.append(unary_union([Polygon(t[:,:2]) for t in triangles[np.abs(mesh.face_normals[:,2])>.99]]))
            # 10 microns accommodates STL float32 and sub-2.5-micron cleanup.
            assert floor.buffer(.01).covers(reference),board['board']+' missing socket floor'
            assert reference.buffer(.01).covers(floor),board['board']+' non-universal socket floor'
            assert len(expected)==quadrant['socket_count']
            socket_count+=len(expected)
        for index,footprint in enumerate(projected_footprints):
            neighbours=unary_union([p for i,p in enumerate(projected_footprints) if i!=index])
            assert footprint.geom_type=='Polygon'
            exterior=footprint.exterior.difference(neighbours.buffer(.30))
            actual_rim=min(exterior.distance(p) for p in socket_references[index])
            assert actual_rim>=6-.01,(board['board'],index+1,actual_rim)
            rim_checks.append({'board':board['board'],'quadrant':index+1,
                               'finished_STL_minimum_external_rim_mm':round(actual_rim,3)})
        preview(assembled_models,[],OUT/board['board']/'underside_rails_exposed.png',
                board['board']+' | assembled underside | keys removed to expose rails',True)
    assert len(data['boards'])==4 and sum(len(b['quadrants']) for b in data['boards'])==16
    coupon=trimesh.load_mesh(OUT/'fit_test/four_identical_socket_coupon.stl')
    triangles=coupon.triangles
    mask=np.all(np.isclose(triangles[:,:,2],7,atol=.0001),axis=1)
    coupon_floor=unary_union([Polygon(t[:,:2]) for t in triangles[mask]])
    reference=unary_union([curved_rectangle((x,y,x+36,y+36),[2]*4) for y in [6,44] for x in [6,44]])
    assert coupon_floor.buffer(.01).covers(reference)
    assert reference.buffer(.01).covers(coupon_floor)
    for index,clearance in enumerate([.15,.20,.25,.30],1):
        tile=trimesh.load_mesh(OUT/f'fit_test/blank_test_tile_{clearance:.2f}mm_per_side_{index}_dots.stl')
        assert np.allclose(tile.extents,[36-2*clearance,36-2*clearance,2.8],atol=.005)
    assert STANDARD['final_tile_clearance_per_side_mm'] is None
    report={'passed':True,'finished_STLs_checked':len(checked),'universal_socket_floors_checked':socket_count,
            'floor_geometry_tolerance_mm':.01,'files':checked,
            'physical_tile_clearance_selected':False,'gameplay_tiles_generated':False}
    report['finished_STL_rim_measurements']=rim_checks
    (OUT/'independent_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    from PIL import Image
    overview=Image.new('RGB',(2400,1800),'white')
    for row,view in enumerate(['assembled_top.png','assembled_underside.png','underside_rails_exposed.png']):
        for col,board in enumerate(data['boards']):
            picture=Image.open(OUT/board['board']/view).convert('RGB')
            picture.thumbnail((600,600))
            overview.paste(picture,(col*600+(600-picture.width)//2,row*600+(600-picture.height)//2))
    overview.save(OUT/'all_boards_top_and_underside.png')
    import zipfile
    with zipfile.ZipFile(ROOT/'output/CURRENT/canonical_chassis_print_kit.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob('*')):
            if path.is_file(): archive.write(path,path.relative_to(OUT))
    print(f'PASS: {len(checked)} finished STLs; {socket_count} identical universal socket floors; all 16 quadrants <=248 mm.')


if __name__=='__main__':
    main()
