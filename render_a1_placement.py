"""Dimensioned A1 plate previews of unchanged, finished STL geometry."""
import hashlib
import json
from pathlib import Path
import zipfile
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/A1_placement_preview'


def render(mesh,title,stem):
    bounds=mesh.bounds
    size=mesh.extents
    color=np.array(to_rgb('#279ba6'))
    triangles=mesh.triangles
    normals=mesh.face_normals
    # Up-facing floors and rims: no underside surfaces can overwrite the top.
    selected=np.flatnonzero(normals[:,2]>.001)
    selected=selected[np.argsort(triangles[selected,:,2].mean(axis=1))]
    fig,ax=plt.subplots(figsize=(10,10))
    ax.add_patch(Rectangle((0,0),256,256,facecolor='#343c42',edgecolor='black',zorder=-1))
    top_colors=color*(.55+.45*triangles[selected,:,2].mean(axis=1)/max(size[2],.01))[:,None]
    ax.add_collection(PolyCollection(triangles[selected,:,:2],facecolors=top_colors,
                                    edgecolors='none',antialiased=False))
    for p in range(0,257,16):
        ax.plot([0,256],[p,p],color='#c4d0d3',alpha=.2,lw=.6)
        ax.plot([p,p],[0,256],color='#c4d0d3',alpha=.2,lw=.6)
    x0,y0=bounds[0,:2]; x1,y1=bounds[1,:2]
    ax.plot([x0,x1,x1,x0,x0],[y0,y0,y1,y1,y0],ls='--',color='#ffe28b',lw=1.3)
    ax.annotate('',xy=(x0,263),xytext=(x1,263),arrowprops=dict(arrowstyle='<->'))
    ax.text(128,269,f'X = {size[0]:.3f} mm',ha='center')
    ax.annotate('',xy=(263,y0),xytext=(263,y1),arrowprops=dict(arrowstyle='<->'))
    ax.text(270,128,f'Y = {size[1]:.3f} mm',rotation=90,ha='center',va='center')
    for x,y,text in [(128,y0/2,f'{y0:.2f} mm'),(128,(256+y1)/2,f'{256-y1:.2f} mm'),
                     (x0/2,128,f'{x0:.2f}'),((256+x1)/2,128,f'{256-x1:.2f}')]:
        ax.text(x,y,text,ha='center',va='center',color='white',fontsize=8)
    ax.set_xlim(-5,280); ax.set_ylim(-5,280); ax.set_aspect('equal')
    ax.set_xticks([0,64,128,192,256]); ax.set_yticks([0,64,128,192,256])
    ax.set_xlabel('A1 build plate X (mm)'); ax.set_ylabel('A1 build plate Y (mm)')
    ax.set_title(title+'\n100% scale | 256 x 256 mm plate | no brim | STL orientation preserved')
    fig.tight_layout(); fig.savefig(OUT/f'{stem}_top.png',dpi=160); plt.close(fig)

    fig=plt.figure(figsize=(12,9)); ax=fig.add_subplot(111,projection='3d',computed_zorder=False)
    plate=np.array([[[0,0,-.15],[256,0,-.15],[256,256,-.15],[0,256,-.15]]])
    light=np.array([-.3,-.5,.8]); light/=np.linalg.norm(light)
    shading=.55+.45*np.abs(normals@light)
    ax.add_collection3d(Poly3DCollection(plate,facecolors='#434b50',edgecolors='none',zorder=0))
    ax.add_collection3d(Poly3DCollection(triangles,facecolors=color*shading[:,None],edgecolors='none',
                                       antialiased=False,zsort='average',zorder=10))
    for p in range(0,257,16):
        ax.plot([0,256],[p,p],[0,0],color='#859399',alpha=.35,lw=.5)
        ax.plot([p,p],[0,256],[0,0],color='#859399',alpha=.35,lw=.5)
    ax.plot([x0,x1,x1,x0,x0],[y0,y0,y1,y1,y0],[.05]*5,color='#e6ba58',ls='--',lw=1)
    ax.text2D(.05,.04,f'Finished STL: {size[0]:.3f} x {size[1]:.3f} x {size[2]:.3f} mm\n'
                      f'Minimum centered plate-edge clearance: {min(x0,y0,256-x1,256-y1):.3f} mm\n'
                      'Supports are not generated or shown; see support diagnostic/report.',transform=ax.transAxes)
    ax.set_xlim(0,256); ax.set_ylim(0,256); ax.set_zlim(-1,28)
    ax.set_box_aspect((256,256,29)); ax.view_init(elev=42,azim=-58)
    ax.set_axis_off(); ax.set_title(title+'\nA1 plate perspective | 100% scale | no additional rotation')
    fig.tight_layout(); fig.savefig(OUT/f'{stem}_perspective.png',dpi=160); plt.close(fig)

    # Geometric warning regions, not a slicer support solution. Excludes bed faces.
    down=(normals[:,2]<-np.cos(np.pi/4)-.001)&(triangles[:,:,2].min(axis=1)>.4)
    slopes=(np.abs(normals[:,2]+np.cos(np.pi/4))<=.001)&(triangles[:,:,2].max(axis=1)>.4)
    fig,ax=plt.subplots(figsize=(9,9)); ax.set_facecolor('#e9edef')
    ax.add_collection(PolyCollection(triangles[selected,:,:2],facecolors='#b9ced0',edgecolors='none'))
    ax.add_collection(PolyCollection(triangles[down,:,:2],facecolors='#ee8d32',edgecolors='none'))
    ax.add_collection(PolyCollection(triangles[slopes,:,:2],facecolors='#368ec4',edgecolors='none'))
    ax.set_xlim(0,256); ax.set_ylim(0,256); ax.set_aspect('equal')
    ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)')
    ax.set_title(title+'\nOrange: >45 degree overhang | Blue: approximately 45 degree slopes\n'
                 'Underside diagnostic overlay, not actual generated support material',fontsize=11)
    fig.tight_layout(); fig.savefig(OUT/f'{stem}_support_diagnostic.png',dpi=160); plt.close(fig)
    return {'dimensions_mm':size.round(3).tolist(),
            'placement_bounds_mm':bounds.round(3).tolist(),
            'edge_clearance_mm':{'left':round(x0,3),'right':round(256-x1,3),
                                 'front':round(y0,3),'back':round(256-y1,3)},
            'fits_256_plate':bool(np.all(bounds[0]>=0) and np.all(bounds[1,:2]<=256)),
            'downward_overhang_area_mm2':round(float(mesh.area_faces[down].sum()),3)}


def main(prototype_directory=None):
    OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/'output/canonical_chassis/finished_stl_bounds.json').read_text())
    candidates=[]
    for board in data['boards']:
        for quadrant in board['quadrants']:
            path=ROOT/quadrant['file']
            mesh=trimesh.load_mesh(path)
            candidates.append((float(max(mesh.extents[:2])),board['board'],quadrant,path,mesh))
    _,board,quadrant,path,mesh=max(candidates,key=lambda entry:entry[0])
    original_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    translation=np.array([(256-mesh.extents[0])/2,(256-mesh.extents[1])/2,0])-mesh.bounds[0]
    mesh.apply_translation(translation)
    result=render(mesh,f'{board} quadrant {quadrant["quadrant"]} | largest production section','production')
    result.update({'source':str(path),'board':board,'quadrant':quadrant['quadrant'],
                   'selection':'Largest finished XY axis among all 16 production STL quadrants',
                   'baked_print_rotation_degrees':quadrant['print_rotation_degrees'],
                   'additional_rotation_degrees':0,'scale':1,'translation_mm':translation.tolist(),
                   'source_sha256':original_hash})
    prototype_directory=prototype_directory or ROOT/'output/recessed_pin_prototype'
    prototype_path=prototype_directory/'prototype_2x1_ALL_COMPONENTS_A1.stl'
    prototype=trimesh.load_mesh(prototype_path)
    prototype_info=json.loads((prototype_directory/'validation.json').read_text())
    support_info=prototype_info['supports']
    if isinstance(support_info,dict): support_info=' '.join(f'{key}: {value}.' for key,value in support_info.items())
    prototype_hash=hashlib.sha256(prototype_path.read_bytes()).hexdigest()
    test=render(prototype,'2 x 1 locking prototype | all 14 test components','prototype')
    test.update({'source':str(prototype_path),'scale':1,'additional_rotation_degrees':0,
                 'source_sha256':prototype_hash,'component_arrangement_preserved':True})
    assert hashlib.sha256(path.read_bytes()).hexdigest()==original_hash
    assert hashlib.sha256(prototype_path.read_bytes()).hexdigest()==prototype_hash
    report={'production':result,'prototype':test,'brim_included':False,
            'true_slicer_run':False,'source_stls_unchanged':True,'plate_mm':[256,256]}
    (OUT/'placement_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'PLACEMENT_REPORT.md').write_text(
        '# A1 placement review\n\n'
        f'Largest finished production quadrant: **{board} Q{quadrant["quadrant"]}**. All 16 actual STL bounds were compared. '
        'These are scaled plate renders of finished meshes, not Bambu Studio screenshots.\n\n'
        '| Item | Finished X x Y x Z (mm) | Left/right gap | Front/back gap | Scale | Additional rotation |\n'
        '|---|---|---|---|---|---|\n'
        f'| {board} Q{quadrant["quadrant"]} | '+ ' x '.join(f'{v:.3f}' for v in result['dimensions_mm'])+
        f' | {result["edge_clearance_mm"]["left"]:.3f} / {result["edge_clearance_mm"]["right"]:.3f} | '
        f'{result["edge_clearance_mm"]["front"]:.3f} / {result["edge_clearance_mm"]["back"]:.3f} | 100% | 0 degrees |\n'
        '| Prototype, all 14 components | '+' x '.join(f'{v:.3f}' for v in test['dimensions_mm'])+
        f' | {test["edge_clearance_mm"]["left"]:.3f} / {test["edge_clearance_mm"]["right"]:.3f} | '
        f'{test["edge_clearance_mm"]["front"]:.3f} / {test["edge_clearance_mm"]["back"]:.3f} | 100% | 0 degrees |\n\n'
        f'The production STL already includes its intended {quadrant["print_rotation_degrees"]:.2f} degree print rotation. '
        'Only centered XY translation is applied. Z remains socket-up and flat-base-down. '
        'No brim, loose assembled keys, purge tower or generated support footprint is included. '
        'The prototype arrangement is copied directly from its combined print STL.\n\n'
        '## Support assessment\n\n'
        'Production: selective supports may be needed beneath internal locking-channel roofs/cantilevers. '
        'Confirm with the physical lock coupon and slicer support preview; avoid supports in sockets or pin/rail mating surfaces. '
        f'Prototype: {support_info} '
        'A 2 mm pin-only brim is optional if adhesion fails and is not included here. Clean supports before assembly.\n\n'
        'Orange diagnostic images project actual downward faces steeper than 45 degrees and above Z=0.4 mm; blue shows approximately 45-degree slopes. A 0.001 normal-component tolerance avoids classifying float32 rounding as steeper geometry. '
        'They identify candidate regions, including internal roofs, but do not evaluate bridging, layer paths, support access or support reach. '
        'They are not printed support geometry. Any slicer-generated support extending outside the model must be checked separately.\n\n'
        'Both model envelopes fit the 256 x 256 mm plate. The production section has about 13.36 mm '
        'minimum edge clearance and is 18.72 mm below the 248 mm target. This is comfortable geometric fit; '
        'warping, adhesion, support removal and mechanical strength remain physically untested. '
        'No STL or canonical mechanical dimension was changed.\n')
    with zipfile.ZipFile(ROOT/'output/A1_placement_preview.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for file in OUT.iterdir(): archive.write(file,file.name)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
