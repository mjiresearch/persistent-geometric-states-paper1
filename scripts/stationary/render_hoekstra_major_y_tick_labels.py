#!/usr/bin/env python3
"""Render only outer printed major-y-tick labels from Hoekstra Fig.1.

No curve pixels are included. These crops are for reading axis numbers only.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import pymupdf
URL='https://arxiv.org/pdf/astro-ph/0010569'
OUT=Path('validation/stationary/hoekstra2001_major_y_tick_label_ascii_v1.txt')
raw=urlopen(Request(URL,headers={'User-Agent':'Mozilla/5.0 PersistenceFrameworkPaperI/1.0'}),timeout=120).read();doc=pymupdf.open(stream=raw,filetype='pdf');p=doc[3];pix=p.get_pixmap(matrix=pymupdf.Matrix(10,10),colorspace=pymupdf.csGRAY,alpha=False);scale=pix.width/p.rect.width
# Bottom-row panel frame shared y values from native vector tick audit.
YS=[469.8979797363281,495.2209777832031,520.3280029296875]
# Left edge of col1 frame = 105.361; estimated right edge of col4 = 484.125 from vector grid.
regions={'LEFT_OUTER':(82.0,104.8),'RIGHT_OUTER':(484.3,510.0)}
def art(xa,xb,yc,W=70,H=14):
    ya=yc-5.5;yb=yc+5.5;X0=max(0,int(xa*scale));X1=min(pix.width,int(xb*scale));Y0=max(0,int(ya*scale));Y1=min(pix.height,int(yb*scale));data=pix.samples;stride=pix.stride;out=[]
    for yy in range(H):
        y0=Y0+(Y1-Y0)*yy//H;y1=max(y0+1,Y0+(Y1-Y0)*(yy+1)//H);row=[]
        for xx in range(W):
            x0=X0+(X1-X0)*xx//W;x1=max(x0+1,X0+(X1-X0)*(xx+1)//W);mn=255
            for y in range(y0,y1):
                off=y*stride
                for x in range(x0,x1):
                    v=data[off+x]
                    if v<mn:mn=v
            row.append('#' if mn<100 else '+' if mn<190 else ' ')
        out.append(''.join(row).rstrip())
    return out
lines=[]
for side,(xa,xb) in regions.items():
    for y in YS:
        lines.append(f'\n=== {side} Y={y:.3f} ===');lines.extend(art(xa,xb,y))
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(OUT)
