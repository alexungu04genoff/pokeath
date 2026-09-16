"""Smooth board CAD with curved wells, separate paper art and snap-lock rails.

Coordinates are traced in a 1614 x 1536 reference view of the supplied PNG.
The original image is used at full resolution in the printed stickers.
Run with the dependencies in requirements-cad.txt.
"""
from pathlib import Path
from io import BytesIO
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import binary_fill_holes, gaussian_filter, gaussian_filter1d
import contourpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
import trimesh
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'paper_art'
SCALE = 0.23  # millimetres per reference pixel; preserves image proportions
BASE = 8.0
SEAM_GAP = 0.25
STICKER_DEPTH = 1.4
EFFECT_IDS = {3,8,11,19,20,21,22,23,25,32,33}
X = [150,283,416,549,680,809,941,1073,1204,1336,1468]
Y = [180,310,441,572,703,834,965,1096,1227,1358]
ROWS = {0:[2],1:[2],2:[0,1,2],3:[0,3,4,5,6,7,8],
        4:[0,3,8,9],5:[0,1,2,3,9],6:[2,7,8,9],
        7:[2,3,5,6,7],8:[3,4,5]}
COLORS = ['#b8ceca']*4


def extrude(poly, height, z=0):
    parts = list(poly.geoms) if poly.geom_type == 'MultiPolygon' else [poly]
    solids = []
    for part in parts:
        if part.area < 0.01:
            continue
        solid = trimesh.creation.extrude_polygon(part,height,engine='earcut')
        solid.apply_translation([0,0,z])
        solids.append(solid)
    return solids[0] if len(solids)==1 else trimesh.boolean.union(solids,engine='manifold')


def union(solids):
    return trimesh.boolean.union(solids,engine='manifold')


def difference(a,b):
    return trimesh.boolean.difference([a,b],engine='manifold')


def mm_poly(poly):
    return affinity.scale(poly,xfact=SCALE,yfact=SCALE,origin=(0,0))


def reference_outline(image):
    mask = binary_fill_holes(np.array(image)[:,:,3] > 127)
    outline=max(polygons_from_mask(mask,image).geoms,key=lambda p:p.area)
    # Smooth the actual contour in physical space, not just its tessellation.
    ring=LineString(outline.exterior.coords)
    samples=np.array([ring.interpolate(t).coords[0] for t in np.arange(0,ring.length,.25)])
    samples=gaussian_filter1d(samples,sigma=8,axis=0,mode='wrap')
    outline=Polygon(samples)
    assert outline.is_valid
    return affinity.scale(outline,1/SCALE,1/SCALE,origin=(0,0))


def curved_rectangle(rect,radii):
    """True circular corner arcs, clockwise TL/TR/BR/BL radii in reference pixels."""
    x0,y0,x1,y1=rect
    points=[]
    for (cx,cy),radius,start in zip(
            [(x0+radii[0],y0+radii[0]),(x1-radii[1],y0+radii[1]),
             (x1-radii[2],y1-radii[2]),(x0+radii[3],y1-radii[3])],
            radii,[180,270,0,90]):
        for angle in np.linspace(start,start+90,49):
            points.append((cx+radius*np.cos(np.deg2rad(angle)),cy+radius*np.sin(np.deg2rad(angle))))
    return Polygon(points)


def polygons_from_mask(mask,image):
    """Subpixel contour tracing with holes, light smoothing and 0.035 mm tolerance."""
    smooth=gaussian_filter(mask.astype(float),sigma=1.0)
    generator=contourpy.contour_generator(z=smooth,fill_type='OuterOffset')
    points,offsets=generator.filled(.5,1.1)
    polygons=[]
    for coordinates,rings in zip(points,offsets):
        paths=[coordinates[a:b] for a,b in zip(rings[:-1],rings[1:])]
        poly=Polygon(paths[0],paths[1:]).buffer(0)
        poly=affinity.scale(poly,1614/image.width*SCALE,1536/image.height*SCALE,origin=(0,0))
        poly=poly.simplify(.035,preserve_topology=True)
        # Round tiny pixel corners without erasing the drawn letter shapes.
        poly=poly.buffer(.06,quad_segs=8).buffer(-.06,quad_segs=8)
        if poly.area>=.18:
            polygons.extend(list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly])
    from shapely.geometry import MultiPolygon
    return MultiPolygon(polygons)


def placements():
    items = []
    # Large arcs follow the rounded outer track corners; others get a 0.8 mm fillet.
    track_corners={1:1,3:0,5:2,7:0,12:1,15:3,16:1,17:3,
                   20:2,25:2,26:3,28:0,30:2,31:3,33:2}
    for row,cols in ROWS.items():
        for col in cols:
            rect = (X[col]+4,Y[row]+4,X[col+1]-4,Y[row+1]-4)
            number=len(items)+1
            radii=[.8/SCALE]*4
            if number in track_corners:
                radii[track_corners[number]]=44
            items.append({'id':f'S{number:02}', 'rect':rect,
                          'poly':curved_rectangle(rect,radii),
                          'kind':'effect' if number in EFFECT_IDS else 'plain'})
    items.append({'id':'FINISH','rect':(216,184,409,306),
                  'poly':curved_rectangle((216,184,409,306),[61,3.5,3.5,61]),'kind':'finish'})
    return items


def regions():
    # Detour left of START, then continue down the border of the playing cells.
    left = Polygon([(0,0),(780,0),(780,565),(809,565),(809,1600),(0,1600)])
    right = box(0,0,1700,1600).difference(left)
    return [left.intersection(box(0,0,1700,834)),
            right.intersection(box(0,0,1700,834)),
            left.intersection(box(0,834,1700,1600)),
            right.intersection(box(0,834,1700,1600))]


def paper_art(outline,items,parts):
    zones=[('OBSERVATORY',box(562,280,803,558)),
           ('STADIUM',box(305,617,535,816)),
           ('MAP',unary_union([box(695,725,1320,957),box(690,953,1055,1080),
                              box(560,971,799,1090),box(697,1060,800,1210)])),
           ('START',box(799,435,1155,558))]
    protected=unary_union([mm_poly(i['poly']).buffer(.7) for i in items])
    art=[]
    for name,zone in zones:
        for index,part in enumerate(parts):
            poly=mm_poly(zone).intersection(mm_poly(part).buffer(-.4)).difference(protected)
            polygons=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]
            for section in polygons:
                if section.is_empty or section.area<8:
                    continue
                ref=affinity.scale(section,1/SCALE,1/SCALE,origin=(0,0))
                x0,y0,x1,y1=section.bounds
                art.append({'id':f'{name}-P{index+1}','poly':ref,'rect':ref.bounds,
                            'kind':'art','width_mm':x1-x0,'height_mm':y1-y0,'part':index+1})
    return art


def dovetail(start, direction, length, cavity=False):
    """Trapezoidal rail: narrow at underside, wide flange captured inside board."""
    d = np.array(direction,dtype=float)
    n = np.array([-d[1],d[0]])
    if cavity:
        levels = [(-0.1,2.7),(4.6,6.46)]
    else:
        levels = [(1.4,3.6),(3.4,5.2)]
    vertices = []
    for distance in [0,length]:
        for z,halfwidth in levels:
            for sign in [-1,1]:
                p = np.array(start)+d*distance+n*halfwidth*sign
                vertices.append([*p,z])
    return trimesh.convex.convex_hull(np.array(vertices))


def place_connector(mesh,origin,direction):
    d=np.array(direction,dtype=float)
    transform=np.eye(4)
    transform[:2,0]=d
    transform[:2,1]=[-d[1],d[0]]
    transform[:2,3]=origin
    result=mesh.copy()
    result.apply_transform(transform)
    return result


def snap_key():
    """Captured rail with a central 1 mm spring tongue and underside-release hook."""
    body=dovetail((0,0),(1,0),34)
    cuts=[]
    # Rounded slit ends reduce the sharp corner at the tongue root.
    for y in [-2.2,2.2]:
        slit=LineString([(-1,y),(29.2,y)]).buffer(.4,quad_segs=16)
        cuts.append(extrude(slit,6,-1))
    cuts.append(extrude(box(-1,-2.6,6,2.6),6,-1))
    cuts.append(extrude(box(6,-1.801,29.6,1.801),3.4,-1))
    body=difference(body,union(cuts))
    # Vertical trailing face is the positive stop; the leading ramp cams up.
    profile=[(8,.4),(10,.4),(15,2.4),(15,3.4),(8,3.4)]
    hook=trimesh.convex.convex_hull(np.array([[x,y,z] for x,z in profile for y in [-1.8,1.8]]))
    return union([body,hook])


def catch_bar(origin,direction):
    bar=extrude(box(1,-6.8,3.5,6.8),1.2)
    return place_connector(bar,origin,direction)


def effect_stickers(items):
    stickers=[]
    for item in items:
        if item['kind']!='effect' and item['id']!='S09':
            continue
        x0,y0,x1,y1=item['rect']
        x,y=(x0+x1)/2,(y0+y1)/2
        size=22/SCALE
        sticker=dict(item)
        if item['id']=='S09':
            sticker['kind']='start'
        sticker['poly']=box(x-size/2,y-size/2,x+size/2,y+size/2)
        sticker['width_mm']=sticker['height_mm']=22
        stickers.append(sticker)
    # Two small square finish/ranking labels preserve both scoring positions.
    for name,crop,center in [('F1',(216,184,339,306),(277.5,245)),
                              ('F2',(343,184,409,306),(376,245))]:
        size=14/SCALE if name=='F2' else 18/SCALE
        x,y=center
        stickers.append({'id':name,'rect':crop,'poly':box(x-size/2,y-size/2,x+size/2,y+size/2),
                         'kind':'finish','width_mm':size*SCALE,'height_mm':size*SCALE})
    return stickers


def foot_seats(items):
    # Two 8 mm adhesive pad seats per section; labels refer to spaces above them.
    selected={'S01','S06','S10','S16','S17','S26','S24','S30'}
    return [(item['id'],mm_poly(item['poly']).centroid.buffer(4.1,quad_segs=48))
            for item in items if item['id'] in selected]


def sticker_image(image,item):
    x0,y0,x1,y1=item['rect']
    crop=image.crop((round(x0*image.width/1614),round(y0*image.height/1536),
                     round(x1*image.width/1614),round(y1*image.height/1536)))
    if item['kind']=='art':
        crop=Image.alpha_composite(Image.new('RGBA',crop.size,'white'),crop)
        return crop.resize((800,800),Image.Resampling.LANCZOS).convert('RGB')
    crop=ImageOps.contain(crop,(800,800),Image.Resampling.LANCZOS)
    tile=Image.new('RGBA',(800,800),'white')
    tile.alpha_composite(crop,((800-crop.width)//2,(800-crop.height)//2))
    return tile.convert('RGB')


def connector_locations(outline):
    shape = mm_poly(outline)
    horizontal = shape.intersection(LineString([(0,834*SCALE),(1700*SCALE,834*SCALE)]))
    vertical = shape.intersection(LineString([(809*SCALE,0),(809*SCALE,1600*SCALE)]))
    return [('K1',np.array([horizontal.bounds[0],834*SCALE]),(1,0)),
            ('K2',np.array([horizontal.bounds[2],834*SCALE]),(-1,0)),
            ('K3',np.array([809*SCALE,vertical.bounds[3]]),(0,-1))]


def save_stl(mesh,name,print_orientation=True):
    result = mesh.copy()
    # Reference image has downward Y. Mirror to preserve handedness of the art
    # when looking down on the printed top face. Trimesh updates face winding.
    if print_orientation:
        result.apply_scale([1,-1,1])
    result.apply_translation(-result.bounds[0])
    path = OUT/'stl'/name
    result.export(path)
    loaded = trimesh.load_mesh(path)
    assert loaded.is_watertight and loaded.is_winding_consistent and loaded.volume>0,name
    assert len(loaded.split())==1,name+' has detached bodies'
    assert np.all(loaded.extents[:2]<=174.01),name+' exceeds reserved bed area'
    return {'file':name,'dimensions_mm':loaded.extents.round(3).tolist(),
            'volume_mm3':round(loaded.volume,2),'watertight':True,'connected':True}


def plot_plan(image,outline,parts,items,connectors):
    fig,ax = plt.subplots(figsize=(11,10))
    ax.imshow(image,extent=(0,1614,1536,0))
    for i,part in enumerate(parts):
        coords = np.asarray(part.exterior.coords)
        ax.fill(coords[:,0],coords[:,1],color=COLORS[i],alpha=0.15)
        ax.plot(coords[:,0],coords[:,1],color=COLORS[i],lw=2.2)
    ax.plot([780,780,809,809],[140,565,565,1400],color='#ff5b37',lw=2.5)
    ax.axhline(834,color='#ff5b37',lw=2.5)
    for item in items:
        x,y = item['poly'].centroid.coords[0]
        label=item['id']+(' *' if item['kind']=='effect' else '')
        ax.text(x,y,label,ha='center',va='center',fontsize=7,
                bbox=dict(facecolor='white',alpha=.92,edgecolor='none',pad=1.5))
    for name,p,d in connectors:
        q=p/SCALE
        ax.annotate(name,xy=q,xytext=q-np.array(d)*100,
                    color='#223344',weight='bold',ha='center',
                    arrowprops=dict(arrowstyle='->',color='#223344',lw=2))
    for i,(px,py) in enumerate([(315,365),(1260,485),(310,1140),(1235,1185)]):
        ax.text(px,py,f'PART {i+1}',fontsize=12,weight='bold',
                bbox=dict(facecolor='white',edgecolor=COLORS[i],pad=4))
    ax.set(xlim=(40,1580),ylim=(1450,90),aspect='equal')
    ax.axis('off')
    fig.suptitle('ULAULA UPROAR | four shaped sections',fontsize=19,weight='bold')
    fig.text(.5,.03,'Orange: space-border seams   |   * = effect sticker   |   K1-K3: snap-lock rails',ha='center',fontsize=11)
    fig.savefig(OUT/'assembly_plan.png',dpi=160,facecolor='white',bbox_inches='tight')
    plt.close(fig)


def preview(meshes,items,image,bottom=False):
    """Orthographic Z-buffer render; avoids painter-order artifacts on long triangles."""
    faces=[]
    colors=[]
    textured=[]
    for mesh,color in zip(meshes,COLORS+['#df8352']*3):
        vertices = mesh.triangles.copy()
        vertices[:,:,1] *= -1
        vertices=vertices[:,[0,2,1],:]
        faces.extend(vertices)
        colors.extend([matplotlib.colors.to_rgb(color)]*len(vertices))
        textured.extend([-1]*len(vertices))
    for item_index,item in enumerate(items):
        xy,indices=trimesh.creation.triangulate_polygon(mm_poly(item['poly']),engine='earcut')
        z=BASE+.02 if item['kind']=='art' else BASE-STICKER_DEPTH+.02
        vertices=np.column_stack([xy[:,0],-xy[:,1],np.full(len(xy),z)])
        triangles=vertices[indices][:,[0,2,1],:]
        faces.extend(triangles)
        colors.extend([(1,1,1)]*len(triangles))
        textured.extend([item_index]*len(triangles))
    faces=np.array(faces)
    view=np.array([.25,-.55,-.8 if bottom else .8]); view/=np.linalg.norm(view)
    right=np.cross([0,0,1],view); right/=np.linalg.norm(right)
    up=np.cross(view,right)
    projected=faces@np.array([right,up,view]).T
    low=projected[:,:,:2].min(axis=(0,1)); high=projected[:,:,:2].max(axis=(0,1))
    width,height=1500,1450
    zoom=min((width-140)/(high[0]-low[0]),(height-250)/(high[1]-low[1]))
    projected[:,:,0]=(projected[:,:,0]-low[0])*zoom+70
    projected[:,:,1]=height-120-(projected[:,:,1]-low[1])*zoom
    rgb=np.full((height,width,3),248,dtype=np.uint8)
    depth=np.full((height,width),-np.inf)
    light=np.array([-.3,-.4,1]); light/=np.linalg.norm(light)
    textures=[np.array(sticker_image(image,item)) for item in items]
    for index,(tri,world) in enumerate(zip(projected,faces)):
        normal=np.cross(world[1]-world[0],world[2]-world[0])
        length=np.linalg.norm(normal)
        if length<1e-10:
            continue
        normal/=length
        if np.dot(normal,view)<=0:
            continue
        xmin=max(0,int(np.floor(tri[:,0].min()))); xmax=min(width-1,int(np.ceil(tri[:,0].max())))
        ymin=max(0,int(np.floor(tri[:,1].min()))); ymax=min(height-1,int(np.ceil(tri[:,1].max())))
        xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
        a,b,c=tri
        denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator)<1e-10:
            continue
        u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denominator
        v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denominator
        w=1-u-v
        z=u*a[2]+v*b[2]+w*c[2]
        tile=depth[ymin:ymax+1,xmin:xmax+1]
        visible=(u>=-1e-7)&(v>=-1e-7)&(w>=-1e-7)&(z>tile)
        if not visible.any():
            continue
        tile[visible]=z[visible]
        target=rgb[ymin:ymax+1,xmin:xmax+1]
        shade=.55+.45*max(0,np.dot(normal,light))
        if textured[index]>=0:
            coords=u[visible,None]*world[0]+v[visible,None]*world[1]+w[visible,None]*world[2]
            item=items[textured[index]]
            x0,y0,x1,y1=mm_poly(item['poly']).bounds
            tx=np.clip(((coords[:,0]-x0)/(x1-x0)*800).astype(int),0,799)
            ty=np.clip(((-coords[:,1]-y0)/(y1-y0)*800).astype(int),0,799)
            target[visible]=(textures[textured[index]][ty,tx]*shade).astype(np.uint8)
        else:
            target[visible]=np.array(colors[index])*255*shade
    result=Image.fromarray(rgb)
    draw=ImageDraw.Draw(result)
    from matplotlib import font_manager
    fontpath=font_manager.findfont('DejaVu Sans')
    title=ImageFont.truetype(fontpath,34)
    font=ImageFont.truetype(fontpath,21)
    draw.text((65,38),'ULAULA UPROAR | '+('snap-lock underside' if bottom else 'smooth board with paper artwork'),fill='#183139',font=title)
    description='with release-tab rails installed' if bottom else ('with separate artwork and effect stickers overlaid' if items else 'without paper artwork: curved wells and flat START areas')
    draw.text((65,88),'Actual mesh geometry '+description,fill='#56666c',font=font)
    draw.text((65,height-58),'Press the spring tab upward to release. Round seats accept optional non-slip pads.' if bottom else 'Single-colour model. Ordinary space colours can be painted or assigned in the slicer.',fill='#56666c',font=font)
    output=OUT/('underside_preview.png' if bottom else ('board_preview.png' if items else 'bare_board_preview.png'))
    encoded=BytesIO()
    result.save(encoded,format='PNG')
    # Update existing previews without the truncate-on-open mode rejected by
    # some Windows preview/file providers. Encode fully before opening the file.
    with output.open('r+b' if output.exists() else 'wb') as stream:
        stream.write(encoded.getvalue())
        stream.truncate()


def sticker_pdf(image,items,art):
    pdf = canvas.Canvas(str(OUT/'paper_artwork_A4.pdf'),pagesize=(210*mm,297*mm))
    pdf.setTitle('Ulaula Uproar - separate paper artwork and effects')
    pdf.setFont('Helvetica-Bold',16)
    pdf.drawString(15*mm,281*mm,'ULAULA UPROAR / EFFECT STICKERS')
    pdf.setFont('Helvetica',10)
    pdf.drawString(15*mm,271*mm,'100% / Actual size. 11 effects, optional S09 start marker, 2 finish labels.')
    for n,item in enumerate(items):
        draw_sticker(pdf,image,item,(20+(n%4)*45)*mm,(229-(n//4)*38)*mm)
    for n,line in enumerate(['Match S-numbers to assembly_plan.png; centre effects in their wells.',
                             'F1 = first place; F2 = second place (14 mm square).',
                             'Ordinary spaces need no stickers. Paint their colours if required.',
                             'S09 is optional paper: its arrows are not engraved in the floor.',
                             'IDs and dimensions sit outside the cut lines.']):
        pdf.drawString(15*mm,(83-n*7)*mm,line)
    pdf.line(15*mm,31*mm,65*mm,31*mm)
    pdf.drawString(15*mm,24*mm,'Calibration: exactly 50 mm. Do not use Fit to page.')
    pdf.showPage()
    page=1
    def header():
        pdf.setFont('Helvetica-Bold',15)
        pdf.drawString(15*mm,281*mm,f'SEPARATE MAP ARTWORK / {page}')
        pdf.setFont('Helvetica',9)
        pdf.drawString(15*mm,272*mm,'Print at 100%. Cut along outlines. P1-P4 identifies the board section.')
        pdf.line(15*mm,20*mm,65*mm,20*mm)
        pdf.drawString(15*mm,14*mm,'50 mm calibration. Glue artwork to the flat, non-playing areas.')
    header()
    cursor_x,top,row_height=15,250,0
    for item in art:
        width,height=item['width_mm'],item['height_mm']
        cell_width=max(width,60)
        if cursor_x+cell_width>195:
            cursor_x=15
            top-=row_height+17
            row_height=0
        if top-height<38:
            pdf.showPage()
            page+=1
            header()
            cursor_x,top,row_height=15,250,0
        draw_art(pdf,image,item,cursor_x*mm,(top-height)*mm)
        cursor_x+=cell_width+8
        row_height=max(row_height,height)
    pdf.save()


def draw_art(pdf,image,item,x,y):
    x0,y0,x1,y1=item['rect']
    path=pdf.beginPath()
    for ring in [item['poly'].exterior,*item['poly'].interiors]:
        coords=list(ring.coords)
        path.moveTo(x+(coords[0][0]-x0)*SCALE*mm,y+(y1-coords[0][1])*SCALE*mm)
        for px,py in coords[1:]:
            path.lineTo(x+(px-x0)*SCALE*mm,y+(y1-py)*SCALE*mm)
        path.close()
    pdf.saveState()
    pdf.clipPath(path,stroke=0,fill=0)
    pdf.drawImage(ImageReader(image),x-x0*SCALE*mm,y-(1536-y1)*SCALE*mm,
                  1614*SCALE*mm,1536*SCALE*mm,mask='auto')
    pdf.restoreState()
    pdf.setLineWidth(.25)
    pdf.drawPath(path,stroke=1,fill=0)
    pdf.setFont('Helvetica',8)
    pdf.drawString(x,y-4*mm,item['id'])


def draw_sticker(pdf,image,item,x,y):
    width,height=item['width_mm'],item['height_mm']
    pdf.drawImage(ImageReader(sticker_image(image,item)),x,y,width*mm,height*mm)
    pdf.setLineWidth(.25)
    pdf.rect(x,y,width*mm,height*mm)
    pdf.setFont('Helvetica',8)
    pdf.drawString(x,y-4*mm,f"{item['id']}  {width:.2f} x {height:.2f} mm")


def lock_diagram():
    fig,ax=plt.subplots(figsize=(11,4.5))
    ax.fill([0,35,35,30.8,30.8,0],[4.6,4.6,0,0,4.6,4.6],color='#b8ceca')
    ax.add_patch(plt.Rectangle((0,4.6),35,3.4,color='#b8ceca'))
    ax.add_patch(plt.Rectangle((1,0),2.5,1.2,color='#df8352'))
    ax.fill([2,25.6,25.6,2],[2.4,2.4,3.4,3.4],color='#46686d')
    ax.fill([4,6,11,11,4],[.4,.4,2.4,3.4,3.4],color='#46686d')
    ax.annotate('PRESS UP to release',xy=(5,.5),xytext=(13,-2),
                arrowprops=dict(arrowstyle='->'),ha='center',fontsize=11)
    ax.annotate('Stop blocks withdrawal',xy=(3.5,.9),xytext=(-1,-3.5),
                arrowprops=dict(arrowstyle='->'),ha='left',fontsize=11)
    ax.annotate('1 mm spring tongue',xy=(20,3.2),xytext=(17,10),
                arrowprops=dict(arrowstyle='->'),fontsize=11)
    ax.annotate('Room for upward flex',xy=(15,4),xytext=(26,1.9),
                arrowprops=dict(arrowstyle='->'),fontsize=10)
    ax.text(-2,6,'BOARD',weight='bold',fontsize=11)
    ax.set(xlim=(-3,39),ylim=(-4.7,11),aspect='equal')
    ax.axis('off')
    fig.suptitle('Snap-lock rail | centre section through the spring',fontsize=16,weight='bold')
    fig.text(.5,.02,'Outer dovetail rails capture the seam. This section shows the axial latch only.',ha='center',fontsize=10)
    fig.savefig(OUT/'lock_section.png',dpi=170,bbox_inches='tight',facecolor='white')
    plt.close(fig)


def main():
    (OUT/'stl').mkdir(parents=True,exist_ok=True)
    image = Image.open(ROOT/'Board_UlaulaUproarSCALED.png')
    outline=reference_outline(image)
    items=placements()
    areas=regions()
    parts=[outline.intersection(p) for p in areas]
    assert all(p.geom_type=='Polygon' for p in parts),'Disconnected board section'
    for item in items:
        owners=[i+1 for i,p in enumerate(areas) if p.covers(item['poly'])]
        assert len(owners)==1,f"Seam crosses {item['id']}"
        assert outline.buffer(2).covers(item['poly']),f"Sticker outside outline: {item['id']}"
        item['part']=owners[0]
    assert areas[1].covers(box(816,455,1135,548)),'START is split'
    connectors=connector_locations(outline)
    cavities=[]
    catches=[]
    placed_keys=[]
    key=snap_key()
    for name,p,d in connectors:
        d=np.array(d)
        cavities.append(dovetail(p-d*7,d,37.8,cavity=True))
        catches.append(catch_bar(p,d))
        placed_keys.append(place_connector(key,p-d*4,d))
    models=[]
    report=[]
    pockets=union([extrude(mm_poly(item['poly']).buffer(.15,join_style=2),
                           STICKER_DEPTH+.2,BASE-STICKER_DEPTH) for item in items])
    seats=foot_seats(items)
    feet_cut=union([extrude(poly,.7,-.1) for _,poly in seats])
    for i,part in enumerate(parts):
        # Remove half the physical seam gap from every section boundary. This
        # also gives the silhouette a small, harmless edge inset.
        footprint=mm_poly(part).buffer(-SEAM_GAP/2,join_style=2)
        assert footprint.geom_type=='Polygon'
        for item in items:
            if item['part']==i+1:
                assert footprint.covers(mm_poly(item['poly']).buffer(.15,join_style=2)),item['id']+' pocket crosses part edge'
        raw=extrude(footprint,BASE)
        result=difference(raw,union(cavities+[pockets,feet_cut]))
        bars=trimesh.boolean.intersection([union(catches),extrude(footprint,BASE)],engine='manifold')
        if len(bars.faces):
            result=union([result,bars])
        models.append(result)
        assert abs(result.bounds[1,2]-BASE)<1e-5,'Unexpected raised feature'
        horizontal=np.all(np.isclose(result.triangles[:,:,2],BASE-STICKER_DEPTH,atol=1e-5),axis=1)
        floor=unary_union([Polygon(t[:,:2]) for t in result.triangles[horizontal]])
        for item in items:
            if item['part']==i+1:
                assert floor.buffer(.001).covers(mm_poly(item['poly']).buffer(-.05)),item['id']+' floor is not flat'
        report.append(save_stl(result,f'board_{i+1}.stl'))
        print(report[-1],flush=True)
    assembled=union(models)
    for placed,(_,_,direction) in zip(placed_keys,connectors):
        collision=trimesh.boolean.intersection([assembled,placed],engine='manifold')
        assert len(collision.faces)==0 or collision.volume<.001,'Seated snap key collides'
        sample=placed.copy()
        sample.apply_translation([*-np.array(direction)*.9,0])
        stop=trimesh.boolean.intersection([assembled,sample],engine='manifold')
        assert stop.volume>.05,'No positive latch engagement'
    # Wide flange/tongue top down: the relief hook grows upward during printing.
    print_key=key.copy()
    print_key.apply_scale([1,1,-1])
    report.append(save_stl(print_key,'snap_key_print_3.stl',False))
    # Small, representative test pair: same base, seam and pocket cross section.
    cavity=dovetail((-7,0),(1,0),37.8,True)
    for name,poly in [('left',box(0,-13,34,-SEAM_GAP/2)),
                      ('right',box(0,SEAM_GAP/2,34,13))]:
        coupon=difference(extrude(poly,BASE),cavity)
        bar=trimesh.boolean.intersection([catch_bar((0,0),(1,0)),extrude(poly,BASE)],engine='manifold')
        coupon=union([coupon,bar])
        report.append(save_stl(coupon,f'fit_test_{name}.stl'))
    stickers=effect_stickers(items)
    for sticker in stickers:
        owner=next(item for item in items if item['id']==sticker['id']) if sticker['kind']!='finish' else items[-1]
        assert owner['poly'].covers(sticker['poly']),sticker['id']+' sticker crosses curved well'
    art=paper_art(outline,items,parts)
    plot_plan(image,outline,parts,items,connectors)
    preview(models,stickers+art,image)
    preview(models,[],image)
    preview(models+placed_keys,[],image,bottom=True)
    lock_diagram()
    sticker_pdf(image,stickers,art)
    bounds=np.array(mm_poly(outline).bounds)
    data={'board_dimensions_mm':(bounds[2:]-bounds[:2]).round(2).tolist(),
          'base_thickness_mm':BASE,'seam_gap_mm':SEAM_GAP,'sticker_pocket_depth_mm':STICKER_DEPTH,'parts':report,
          'space_count':len(items)-1,'effect_sticker_count':11,'optional_start_marker':1,'finish_sticker_count':2,
          'outline_vertices':len(outline.exterior.coords),'outline_smoothing_mm':2.0,
          'arc_segments_per_corner':48,'paper_art_patches':len(art),
          'non_slip_pad_seats':len(seats),'snap_engagement_mm':.8,
          'sticker_ownership':[{'id':i['id'],'part':i['part'],'rect_reference_px':i['rect']} for i in items],
          'checks':{'all_stickers_whole':True,'all_playing_floors_flat':True,'no_raised_artwork':True,
                    'seated_keys_clear':True,'withdrawal_blocked_without_release':True,
                    'elastic_flex_simulated':False,'physical_print_tested':False}}
    (OUT/'validation.json').write_text(json.dumps(data,indent=2)+'\n')
    print('PASS: watertight models, whole curved wells, flat floors, no relief, seated fit and latch stop.',flush=True)


if __name__=='__main__':
    main()
