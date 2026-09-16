"""Arrange the fourteen existing prototype components into one A1 print STL."""
import json
from pathlib import Path
import numpy as np
import trimesh
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pin_joint_prototype'


def main(output_directory=None):
    OUT=output_directory if output_directory is not None else ROOT/'output/pin_joint_prototype'
    placements=[(OUT/'prototype_2x1_part_A.stl',0,0,'A'),
                (OUT/'prototype_2x1_part_B.stl',61,0,'B')]
    for i,path in enumerate(sorted((OUT/'tiles').glob('*.stl'))):
        placements.append((path,44*i,80,f'Tile {i+1}'))
    for row,family in enumerate([4,5]):
        for i,path in enumerate(sorted((OUT/'pins').glob(f'T_pin_{family}mm*.stl'))):
            placements.append((path,22*i,130+23*row,f'{family} / {i+1}'))
    assert len(placements)==14
    meshes=[]; boxes=[]; manifest=[]
    for path,x,y,label in placements:
        mesh=trimesh.load_mesh(path)
        mesh.apply_translation(-mesh.bounds[0])
        mesh.apply_translation([x,y,0])
        meshes.append(mesh); boxes.append(mesh.bounds[:,:2])
        manifest.append({'source':str(path.relative_to(OUT)),'label':label,'position_mm':[x,y,0]})
    minimum_gap=float('inf')
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            delta=np.maximum(np.maximum(a[0]-b[1],b[0]-a[1]),0)
            distance=float(np.linalg.norm(delta))
            assert distance>=8
            minimum_gap=min(minimum_gap,distance)
    plate=trimesh.util.concatenate(meshes)
    offset=(256-plate.extents[:2])/2-plate.bounds[0,:2]
    plate.apply_translation([*offset,0])
    path=OUT/'prototype_2x1_ALL_COMPONENTS_A1.stl'
    plate.export(path)
    loaded=trimesh.load_mesh(path)
    components=loaded.split()
    assert loaded.is_watertight and loaded.is_winding_consistent
    assert np.all(np.bincount(loaded.edges_unique_inverse)==2)
    assert len(components)==14
    assert all(m.is_watertight and m.volume>0 for m in components)
    assert max(loaded.extents[:2])<=256 and abs(loaded.bounds[0,2])<.0001
    report={'file':path.name,'component_count':14,'xyz_mm':loaded.extents.round(3).tolist(),
            'minimum_component_bounding_box_gap_mm':round(minimum_gap,3),
            'watertight_manifold':True,'fits_A1_256mm':True,'original_print_orientations_preserved':True,
            'placements_before_centering':manifest,'bed_centering_offset_mm':offset.round(3).tolist(),
            'supports':json.loads((OUT/'validation.json').read_text())['supports'] if (OUT/'validation.json').exists()
                       else 'Consult individual component print instructions; support settings are not stored in STL.',
            'instructions':'Import as one object at 100%, keep orientation and arrangement. The STL contains 14 disconnected closed components; do not union them. Support settings are not stored in STL.'}
    (OUT/'one_plate_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(9,9))
    ax.plot([0,256,256,0,0],[0,0,256,256,0],color='gray')
    for bounds,(_,_,_,label) in zip(boxes,placements):
        low,high=bounds+offset
        ax.add_patch(plt.Rectangle(low,*(high-low),facecolor='#d9eadf',edgecolor='#36765a'))
        ax.text(*(low+high)/2,label,ha='center',va='center',fontsize=9)
    ax.set_xlim(-5,261); ax.set_ylim(-5,261); ax.set_aspect('equal')
    ax.set_xlabel('Bed X, mm'); ax.set_ylabel('Bed Y, mm')
    ax.set_title('One A1 plate: A/B, four tile tests, eight T pins\nBounding-box layout; keep this arrangement')
    fig.tight_layout(); fig.savefig(OUT/'one_plate_layout.png',dpi=140); plt.close(fig)
    print('PASS:',report['xyz_mm'],'mm; 14 closed components; minimum gap',report['minimum_component_bounding_box_gap_mm'],'mm')


if __name__=='__main__':
    main()
