#!/usr/bin/env python3
"""Isolate printed major H I y-axis numeral glyphs in Hoekstra Fig.1.

This is axis-label QC only. No curve pixels/coordinates are measured or digitized.
The rightmost panel axis is found from native full-height vector segments; small
raster crops immediately outside that axis are binarized and emitted as enlarged
ASCII glyphs for direct visual verification of the printed tick values.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import json
import pymupdf

URL='https://arxiv.org/pdf/astro-ph/0010569'
OUT=Path('validation/stationary/hoekstra2001_hi_axis_major_glyphs_v1.txt')
META=Path('validation/stationary/hoekstra2001_hi_axis_major_glyphs_v1.json')
raw=urlopen(Request(URL,headers={'User-Agent':'Mozilla/5.0 PersistenceFrameworkPaperI/1.0'}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype='pdf');p=doc[3]
# Identify all long vertical black frame sides in Fig.1 region.
xs=[]
for d in p.get_drawings():
    col=d.get('color')
    if not col or max(col)>0.05: continue
    for it in d.get('items',[]):
        if it[0]!='l': continue
        a,b=it[1],it[2]
        if abs(a.x-b.x)<0.02 and abs(a.y-b.y)>55 and 80<a.x<520 and 130<min(a.y,b.y)<530:
            xs.append(a.x)
# Deduplicate; rightmost is outer H I axis of column 4.
uniq=[]
for x in sorted(xs):
    if not uniq or abs(x-uniq[-1])>0.1: uniq.append(x)
right=max(uniq)
# Bottom-row major tick y coordinates from native-vector audit. The same vertical scale repeats in all panels.
ys=[469.8979797363281,495.2209777832031,520.3280029296875]
pix=p.get_pixmap(matrix=pymupdf.Matrix(14,14),colorspace=pymupdf.csGRAY,alpha=False);scale=pix.width/p.rect.width

def glyph(yc):
    # Printed numerals lie immediately right of the outer frame. Exclude frame itself.
    xa=right+1.0; xb=right+25.0; ya=yc-5.2; yb=yc+5.2
    X0=max(0,int(xa*scale));X1=min(pix.width,int(xb*scale));Y0=max(0,int(ya*scale));Y1=min(pix.height,int(yb*scale))
    data=pix.samples;stride=pix.stride
    # native binary mask
    mask=[]
    for y in range(Y0,Y1):
        off=y*stride;mask.append([data[off+x]<150 for x in range(X0,X1)])
    # trim blank margins
    rows=[i for i,r in enumerate(mask) if any(r)]; cols=[j for j in range(len(mask[0])) if any(r[j] for r in mask)] if mask else []
    if rows and cols: mask=[r[min(cols):max(cols)+1] for r in mask[min(rows):max(rows)+1]]
    # Downsample by minimum/occupancy into a generous ASCII canvas preserving shape.
    H=24;W=72;out=[]
    if not mask:return [],None
    mh=len(mask);mw=len(mask[0])
    for yy in range(H):
        row=[]
        ya0=yy*mh//H;yb0=max(ya0+1,(yy+1)*mh//H)
        for xx in range(W):
            xa0=xx*mw//W;xb0=max(xa0+1,(xx+1)*mw//W)
            n=sum(mask[y][x] for y in range(ya0,min(yb0,mh)) for x in range(xa0,min(xb0,mw)))
            den=max(1,(min(yb0,mh)-ya0)*(min(xb0,mw)-xa0))
            row.append('#' if n/den>0.34 else '+' if n>0 else ' ')
        out.append(''.join(row).rstrip())
    return out,{'crop_page':[xa,ya,xb,yb],'trimmed_pixels':[mw,mh]}

lines=[];meta=[]
for y in ys:
    a,m=glyph(y);lines.append(f'\n=== MAJOR TICK Y={y:.3f} ===');lines.extend(a);meta.append({'y':y,**(m or {})})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
META.write_text(json.dumps({'status':'HOEKSTRA2001_HI_AXIS_MAJOR_GLYPHS_COMPLETE','frame_x_positions':uniq,'right_outer_axis_x':right,'major_ticks':meta,'boundary':'Printed axis-label glyph QC only; no scientific curve raster digitization.'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'frame_x_positions':uniq,'right_outer_axis_x':right,'major_ticks':meta},indent=2))
