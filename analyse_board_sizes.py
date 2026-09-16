"""Compare four grid-aligned board partitions and in-plane print rotations.

Sizing study only: grid lines are traced from artwork and final CAD seams still
need to be constructed and checked against exact space and label footprints.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes
import contourpy
from shapely.geometry import Polygon, box
from shapely import affinity
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'/'sizing'
BED=250.0  # 3 mm nominal reserve per side on the A1
PITCH=131.5
BOARDS=[
    ('Akala','Board_AkalaAdventureSCALED.png',448,45,8,12),
    ('Melemele','Board_MelemeleMileSCALED.png',150,310,11,8),
    ('Poni','Board_PoniPassSCALED.png',255,118,11,10),
    ('Ulaula','Board_UlaulaUproarSCALED (1).png',150,180,11,10),
]
ANGLES=np.deg2rad(np.arange(0,90.01,.5))
COS,SIN=np.cos(ANGLES),np.sin(ANGLES)


def fit(poly):
    coords=np.array(poly.convex_hull.exterior.coords)
    u=coords[:,0,None]*COS+coords[:,1,None]*SIN
    v=-coords[:,0,None]*SIN+coords[:,1,None]*COS
    widths=np.ptp(u,axis=0)
    heights=np.ptp(v,axis=0)
    spans=np.maximum(widths,heights)
    index=int(np.argmin(spans))
    return float(spans[index]),float(np.rad2deg(ANGLES[index])),[float(widths[index]),float(heights[index])]


def outline(image):
    alpha=np.array(image.resize((1614,1536)))[:,:,3]
    z=binary_fill_holes(alpha>127).astype(float)
    contours=contourpy.contour_generator(z=z).lines(.5)
    return max((Polygon(p).buffer(0) for p in contours),key=lambda p:p.area).simplify(.8)


def optimise(poly,xlines,ylines,extent=(1614,1536)):
    best=None
    # A horizontal space-border seam, with independent vertical seams above
    # and below it. This is less restrictive than equal image quadrants.
    for y in ylines:
        candidates=[]
        for y0,y1 in [(0,y),(y,extent[1])]:
            row_best=None
            for x in xlines:
                parts=[poly.intersection(box(0,y0,x,y1)),poly.intersection(box(x,y0,extent[0],y1))]
                if any(p.geom_type!='Polygon' or p.area<1000 for p in parts):
                    continue
                fits=[fit(p) for p in parts]
                span=max(f[0] for f in fits)
                if row_best is None or span<row_best['span']:
                    row_best={'span':span,'x':x,'parts':parts,'fits':fits}
            candidates.append(row_best)
        if any(c is None for c in candidates):
            continue
        span=max(c['span'] for c in candidates)
        if best is None or span<best['span']:
            best={'span':span,'y':y,'rows':candidates}
    return best


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    fig,axes=plt.subplots(2,2,figsize=(13,13))
    for (name,file,x,y,nx,ny),ax in zip(BOARDS,axes.flat):
        image=Image.open(ROOT/file)
        shape=outline(image)
        xs=[x+i*PITCH for i in range(1,nx) if x+i*PITCH<1570]
        ys=[y+i*PITCH for i in range(1,ny) if y+i*PITCH<1490]
        best=optimise(shape,xs,ys)
        primary='horizontal'
        swapped=affinity.affine_transform(shape,[0,1,1,0,0,0])
        vertical=optimise(swapped,ys,xs,extent=(1536,1614))
        if vertical['span']<best['span']:
            best=vertical
            primary='vertical'
            for row in best['rows']:
                row['parts']=[affinity.affine_transform(p,[0,1,1,0,0,0]) for p in row['parts']]
                row['fits']=[fit(p) for p in row['parts']]
        pitch=BED/best['span']*PITCH
        # A common 2 mm rim inset at each side gives equal nominal floor widths.
        well=pitch-4
        dimensions=[(shape.bounds[2]-shape.bounds[0])*BED/best['span'],
                    (shape.bounds[3]-shape.bounds[1])*BED/best['span']]
        result={'board':name,'max_nominal_pitch_mm':round(pitch,2),
                'nominal_well_width_mm_with_2mm_rims':round(well,2),
                'assembled_dimensions_at_individual_limit_mm':np.round(dimensions,1).tolist(),
                'primary_seam_direction':primary,'primary_seam_reference_coordinate':best['y'],
                'secondary_seam_reference_coordinates':[c['x'] for c in best['rows']],
                'section_print_bounding_boxes_at_40mm_pitch':[
                    np.round(np.array(f[2])*40/PITCH,2).tolist()
                    for c in best['rows'] for f in c['fits']],
                'print_rotations_degrees':[f[1] for c in best['rows'] for f in c['fits']]}
        results.append(result)
        ax.imshow(image,extent=(0,1614,1536,0))
        colors=['#26a6ae','#dfaa30','#955bc5','#49a958']
        for part,color in zip([p for c in best['rows'] for p in c['parts']],colors):
            coords=np.array(part.exterior.coords)
            ax.plot(coords[:,0],coords[:,1],color=color,lw=2)
        ax.set_title(f'{name}: approximately {well:.1f} mm wells at its own limit',fontsize=13)
        ax.axis('off')
        print(json.dumps(result),flush=True)
    shared=min(r['nominal_well_width_mm_with_2mm_rims'] for r in results)
    data={'bed_envelope_mm':BED,'rim_inset_each_edge_mm':2,
          'shared_nominal_well_limit_mm':shared,'boards':results,
          'limitations':['Search evaluates horizontal and vertical grid-aligned T-shaped four-part partitions and 0.5 degree rotations.',
                        'Grid traces are approximate; label detours and connectors are not modelled.',
                        'This is a feasible sizing estimate, not a proof of a global optimum.',
                        'Corner wells share nominal width but lose floor area to their curves.']}
    (OUT/'board_size_comparison.json').write_text(json.dumps(data,indent=2)+'\n')
    fig.suptitle('Four-board sizing study | 250 mm print envelope | provisional space-border seams',fontsize=16)
    fig.tight_layout(rect=(0,.015,1,.96))
    fig.savefig(OUT/'four_board_sizing.png',dpi=130,facecolor='white')
    plt.close(fig)


if __name__=='__main__':
    main()
