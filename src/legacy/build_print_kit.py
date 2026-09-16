"""Parametric STL and paper-template source. Run with Pillow and ReportLab installed."""
from pathlib import Path
import math
import struct
from collections import Counter
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output'
BOARD_WIDTH = 340.0
THICKNESS = 3.0


def mesh(name, xs, ys, zs, occupied):
    """Emit only boundary faces of a small conforming rectilinear cell grid."""
    triangles = []
    for i, j, k in occupied:
        x, X = xs[i:i+2]
        y, Y = ys[j:j+2]
        z, Z = zs[k:k+2]
        faces = [
            ((-1,0,0), [(x,y,z),(x,y,Z),(x,Y,Z),(x,Y,z)]),
            ((1,0,0), [(X,y,z),(X,Y,z),(X,Y,Z),(X,y,Z)]),
            ((0,-1,0), [(x,y,z),(X,y,z),(X,y,Z),(x,y,Z)]),
            ((0,1,0), [(x,Y,z),(x,Y,Z),(X,Y,Z),(X,Y,z)]),
            ((0,0,-1), [(x,y,z),(x,Y,z),(X,Y,z),(X,y,z)]),
            ((0,0,1), [(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]),
        ]
        for (di,dj,dk), q in faces:
            if (i+di,j+dj,k+dk) not in occupied:
                triangles.extend([(q[0],q[1],q[2]), (q[0],q[2],q[3])])
    edges = Counter()
    directed = Counter()
    volume = 0
    with (OUT / 'stl' / name).open('wb') as f:
        f.write(b'Pokemon Athletes; units mm'.ljust(80,b'\0'))
        f.write(struct.pack('<I',len(triangles)))
        for a,b,c in triangles:
            u = [b[t]-a[t] for t in range(3)]
            v = [c[t]-a[t] for t in range(3)]
            n = [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            length = math.sqrt(sum(t*t for t in n))
            assert length > 0
            f.write(struct.pack('<12fH',*[t/length for t in n],*a,*b,*c,0))
            volume += (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
            for p,q in [(a,b),(b,c),(c,a)]:
                edges[tuple(sorted((p,q)))] += 1
                directed[(p,q)] += 1
    assert all(count == 2 for count in edges.values()), 'Non-manifold boundary'
    assert all(directed[(q,p)] == count for (p,q),count in directed.items())
    assert volume > 0
    assert xs[-1]-xs[0] <= 180 and ys[-1]-ys[0] <= 180
    print(f'{name}: watertight, consistent winding, volume {volume:.2f} mm3')


def main():
    (OUT / 'stl').mkdir(parents=True,exist_ok=True)
    (OUT / 'pdf').mkdir(parents=True,exist_ok=True)
    board = Image.open(ROOT / 'assets' / 'boards' / 'ulaula_uproar.png')
    height = BOARD_WIDTH * board.height / board.width
    w,h = BOARD_WIDTH/2,height/2
    mesh('board_quarter_print_4.stl',[0,w],[0,h],[0,THICKNESS],{(0,0,0)})
    for gap in [0.4,0.6,0.8]:
        cells = {(0,j,0) for j in range(3)} | {(0,0,1),(0,2,1)}
        mesh(f'racer_base_slot_{gap:.1f}mm.stl',[0,18],[0,7-gap/2,7+gap/2,14],[0,2,5],cells)
    pdf = canvas.Canvas(str(OUT/'pdf'/'paper_templates_A4.pdf'),pagesize=(210*mm,297*mm))
    pdf.setTitle('Ulaula Uproar - actual-size board and racer templates')
    for index,label in enumerate(['TOP LEFT','TOP RIGHT','BOTTOM LEFT','BOTTOM RIGHT']):
        pdf.setFont('Helvetica-Bold',15)
        pdf.drawString(20*mm,277*mm,f'{index+1} / 4   {label}')
        pdf.setFont('Helvetica',10)
        pdf.drawString(20*mm,267*mm,'Print at 100% / Actual size. Disable Fit to page.')
        x,y = 20*mm,75*mm
        pdf.saveState()
        path = pdf.beginPath()
        path.rect(x,y,w*mm,h*mm)
        pdf.clipPath(path,stroke=0)
        # Draw the complete image through each quadrant window: no pixel rounding at seams.
        col,row = index%2,index//2
        pdf.drawImage(ImageReader(board),x-col*w*mm,y-(1-row)*h*mm,
                      BOARD_WIDTH*mm,height*mm,mask='auto')
        pdf.restoreState()
        pdf.setLineWidth(0.2)
        for cx in [x,x+w*mm]:
            for cy in [y,y+h*mm]:
                sx = -1 if cx==x else 1
                sy = -1 if cy==y else 1
                pdf.line(cx+sx*mm,cy,cx+sx*4*mm,cy)
                pdf.line(cx,cy+sy*mm,cx,cy+sy*4*mm)
        pdf.drawString(20*mm,58*mm,f'Trim to {w:.2f} x {h:.4f} mm. Glue to one 3 mm panel.')
        pdf.line(20*mm,40*mm,70*mm,40*mm)
        pdf.drawString(20*mm,34*mm,'This line must measure 50 mm.')
        pdf.showPage()
    pdf.setFont('Helvetica-Bold',15)
    pdf.drawString(20*mm,277*mm,'RACER INSERTS - ALOLAN RAICHU')
    pdf.setFont('Helvetica',10)
    lines = ['Print at 100%. Each rectangle is 24 x 29 mm.',
             'Glue front and back to cardstock; trim the rectangle or the silhouette.',
             'Keep the bottom 3 mm tab intact and slide it into the base slot.',
             'Aim for 0.3-0.7 mm total thickness; test the three slot sizes first.',
             'The reverse repeats the same artwork. Make three double-sided racers.']
    for i,line in enumerate(lines):
        pdf.drawString(20*mm,(265-i*6)*mm,line)
    racer = Image.open(ROOT/'assets'/'racers'/'alolan_raichu.png')
    racer = racer.crop(racer.getbbox())
    for row in range(3):
        for col in range(2):
            x,y = (35+col*55)*mm,(175-row*45)*mm
            pdf.setLineWidth(0.2)
            pdf.rect(x,y,24*mm,29*mm)
            pdf.drawImage(ImageReader(racer),x+mm,y+4*mm,22*mm,22*mm,mask='auto',preserveAspectRatio=True)
            pdf.setDash(2,2)
            pdf.line(x,y+3*mm,x+24*mm,y+3*mm)
            pdf.setDash()
    pdf.line(20*mm,35*mm,70*mm,35*mm)
    pdf.drawString(20*mm,29*mm,'Calibration: 50 mm. Dashed line marks insertion depth.')
    pdf.save()
    print(f'Board: {BOARD_WIDTH} x {height:.4f} mm; quarter: {w} x {h:.4f} mm')


if __name__ == '__main__':
    main()
