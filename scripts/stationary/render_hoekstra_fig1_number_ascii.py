#!/usr/bin/env python3
"""Render only the numeric suffix of each Hoekstra Fig.1 panel name for visual QC.

No OCR and no scientific curve values are read from the raster. The purpose is
only to map already-exact EPS vector panels to galaxy identities.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import json
import pymupdf
URL="https://arxiv.org/pdf/astro-ph/0010569"
GRID=Path("validation/stationary/hoekstra2001_fig1_pdf_panel_grid_v1.json")
OUT=Path("validation/stationary/hoekstra2001_fig1_number_ascii_v1.txt")
raw=urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype="pdf");p=doc[3];pix=p.get_pixmap(matrix=pymupdf.Matrix(6,6),colorspace=pymupdf.csGRAY,alpha=False)
grid=json.loads(GRID.read_text());scale=pix.width/p.rect.width
def art(rect,W=64,H=14):
    x0,y0,x1,y1=rect; w=x1-x0;h=y1-y0
    # Numeric suffix occupies the right half of the upper label strip.
    rx0=x0+0.50*w; rx1=x0+0.985*w; ry0=y0+0.035*h; ry1=y0+0.255*h
    data=pix.samples;stride=pix.stride;out=[]
    for yy in range(H):
        row=[]
        ya=int((ry0+(ry1-ry0)*yy/H)*scale);yb=max(ya+1,int((ry0+(ry1-ry0)*(yy+1)/H)*scale))
        for xx in range(W):
            xa=int((rx0+(rx1-rx0)*xx/W)*scale);xb=max(xa+1,int((rx0+(rx1-rx0)*(xx+1)/W)*scale))
            mn=255
            for y in range(max(0,ya),min(pix.height,yb)):
                off=y*stride
                for x in range(max(0,xa),min(pix.width,xb)):
                    v=data[off+x]
                    if v<mn:mn=v
            row.append('#' if mn<100 else '+' if mn<190 else ' ')
        out.append(''.join(row).rstrip())
    return out
lines=[]
for pan in grid['panels']:
    lines.append(f"\n=== ROW {pan['row']} COL {pan['col']} ===")
    lines.extend(art(pan['rect']))
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(OUT)
