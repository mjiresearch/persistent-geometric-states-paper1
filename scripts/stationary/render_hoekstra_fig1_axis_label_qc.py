#!/usr/bin/env python3
"""Render only printed axis-label strips for Hoekstra 2001 Fig.1 QC.

Known panel R1C1 = NGC2903. We render its bottom x-axis numeric labels and its
right-hand HI surface-density numeric labels at high-resolution ASCII. The
raster is used only to read printed scale labels; scientific curve coordinates
remain source-EPS vectors.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import json
import pymupdf
URL="https://arxiv.org/pdf/astro-ph/0010569"
GRID=Path("validation/stationary/hoekstra2001_fig1_pdf_panel_grid_v1.json")
OUT=Path("validation/stationary/hoekstra2001_fig1_axis_label_ascii_v1.txt")
raw=urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype='pdf');p=doc[3];pix=p.get_pixmap(matrix=pymupdf.Matrix(8,8),colorspace=pymupdf.csGRAY,alpha=False)
grid=json.loads(GRID.read_text());panel=next(z for z in grid['panels'] if z['row']==1 and z['col']==1);scale=pix.width/p.rect.width

def ascii_rect(rect,W,H,thr1=100,thr2=190):
    x0,y0,x1,y1=rect;X0=max(0,int(x0*scale));X1=min(pix.width,int(x1*scale));Y0=max(0,int(y0*scale));Y1=min(pix.height,int(y1*scale));data=pix.samples;stride=pix.stride;out=[]
    for yy in range(H):
        ya=Y0+(Y1-Y0)*yy//H;yb=max(ya+1,Y0+(Y1-Y0)*(yy+1)//H);row=[]
        for xx in range(W):
            xa=X0+(X1-X0)*xx//W;xb=max(xa+1,X0+(X1-X0)*(xx+1)//W);mn=255
            for y in range(ya,yb):
                off=y*stride
                for x in range(xa,xb):
                    v=data[off+x]
                    if v<mn:mn=v
            row.append('#' if mn<thr1 else '+' if mn<thr2 else ' ')
        out.append(''.join(row).rstrip())
    return out

x0,y0,x1,y1=panel['rect'];w=x1-x0;h=y1-y0
# Cell boundaries approximate midpoints between panel centers. Expand bottom to capture labels, but crop away curves.
xstrip=(x0-0.06*w,y1-0.13*h,x1+0.05*w,y1+0.30*h)
# Right axis lies near/just beyond cell's right edge; include numeric labels but avoid most panel interior.
ystrip=(x1-0.18*w,y0-0.05*h,x1+0.25*w,y1+0.05*h)
lines=['=== R1C1 NGC2903 BOTTOM X AXIS LABEL STRIP ==='];lines+=ascii_rect(xstrip,110,20);lines+=['','=== R1C1 NGC2903 RIGHT HI AXIS LABEL STRIP ==='];lines+=ascii_rect(ystrip,55,40)
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(OUT)
