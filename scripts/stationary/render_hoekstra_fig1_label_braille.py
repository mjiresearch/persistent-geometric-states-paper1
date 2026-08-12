#!/usr/bin/env python3
"""Render only Fig.1 panel name strips as Unicode braille for visual QC, no OCR."""
from urllib.request import Request,urlopen
from pathlib import Path
import json, math
import pymupdf
URL="https://arxiv.org/pdf/astro-ph/0010569"
GRID=Path("validation/stationary/hoekstra2001_fig1_pdf_panel_grid_v1.json")
OUT=Path("validation/stationary/hoekstra2001_fig1_label_braille_v1.txt")
raw=urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype="pdf");p=doc[3];pix=p.get_pixmap(matrix=pymupdf.Matrix(5,5),colorspace=pymupdf.csGRAY,alpha=False)
grid=json.loads(GRID.read_text()); scale=pix.width/p.rect.width
# Braille bits: (0,0)=1,(0,1)=2,(0,2)=3,(1,0)=4,(1,1)=5,(1,2)=6,(0,3)=7,(1,3)=8
bits={(0,0):1,(0,1):2,(0,2):4,(1,0):8,(1,1):16,(1,2):32,(0,3):64,(1,3):128}
def braille(rect,cols=70,rows=10):
    # focus on upper central/right label strip, skipping left y-axis and very top border
    x0,y0,x1,y1=rect; w=x1-x0;h=y1-y0
    rx0=x0+0.20*w;rx1=x0+0.98*w; ry0=y0+0.04*h; ry1=y0+0.27*h
    # target raster 2*cols by 4*rows using min/dark sample per bin
    W=cols*2;H=rows*4; vals=[[False]*W for _ in range(H)]
    data=pix.samples;stride=pix.stride
    for yy in range(H):
        ya=int((ry0+(ry1-ry0)*yy/H)*scale); yb=max(ya+1,int((ry0+(ry1-ry0)*(yy+1)/H)*scale))
        for xx in range(W):
            xa=int((rx0+(rx1-rx0)*xx/W)*scale); xb=max(xa+1,int((rx0+(rx1-rx0)*(xx+1)/W)*scale))
            mn=255
            for y in range(max(0,ya),min(pix.height,yb)):
                off=y*stride
                for x in range(max(0,xa),min(pix.width,xb)):
                    v=data[off+x]
                    if v<mn:mn=v
            vals[yy][xx]=mn<125
    out=[]
    for br in range(rows):
        chars=[]
        for bc in range(cols):
            code=0
            for dx in range(2):
                for dy in range(4):
                    if vals[br*4+dy][bc*2+dx]:code|=bits[(dx,dy)]
            chars.append(chr(0x2800+code) if code else " ")
        out.append("".join(chars).rstrip())
    return out
lines=[]
for pan in grid["panels"]:
    lines.append(f"\n=== ROW {pan['row']} COL {pan['col']} ===")
    lines.extend(braille(pan["rect"]))
OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
print(OUT)
