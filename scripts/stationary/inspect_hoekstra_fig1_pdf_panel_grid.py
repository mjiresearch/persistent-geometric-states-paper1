#!/usr/bin/env python3
"""Inspect Hoekstra 2001 compiled PDF Fig.1 panel layout without OCR.

Red vector drawing objects identify the HI-profile paths. We cluster their
bounding boxes into the 4x6 panel grid. A low-resolution monochrome ASCII view
of each panel is emitted only to read panel labels/layout visually; numerical
profile values are never extracted from the raster. Exact curve recovery, if
accepted, remains EPS-vector based.
"""
from __future__ import annotations
from urllib.request import Request,urlopen
from pathlib import Path
import json, math
import pymupdf

URL="https://arxiv.org/pdf/astro-ph/0010569"
OUT=Path("validation/stationary/hoekstra2001_fig1_pdf_panel_grid_v1.json")
TXT=Path("validation/stationary/hoekstra2001_fig1_panel_ascii_v1.txt")

def cluster(vals,k):
    # deterministic 1-D kmeans initialized by quantiles
    s=sorted(vals); centers=[s[round((i+.5)*len(s)/k-.5)] for i in range(k)]
    for _ in range(50):
        groups=[[] for _ in range(k)]
        for v in vals:
            j=min(range(k),key=lambda z:abs(v-centers[z]));groups[j].append(v)
        new=[sum(g)/len(g) if g else centers[i] for i,g in enumerate(groups)]
        if max(abs(new[i]-centers[i]) for i in range(k))<1e-6:break
        centers=new
    return sorted(centers)

def ascii_crop(pix,rect,w=72,h=22):
    # pix is grayscale 1-channel at 3x page scale; rect in page coords.
    scale=pix.width/PAGE_RECT.width
    x0=max(0,int(rect.x0*scale));x1=min(pix.width,int(rect.x1*scale));y0=max(0,int(rect.y0*scale));y1=min(pix.height,int(rect.y1*scale))
    if x1<=x0 or y1<=y0:return []
    # sample minimum (darkest) in bins so thin glyph strokes survive downsampling
    stride=pix.stride; data=pix.samples
    out=[]
    for yy in range(h):
        ya=y0+(y1-y0)*yy//h; yb=y0+(y1-y0)*(yy+1)//h; yb=max(yb,ya+1)
        row=[]
        for xx in range(w):
            xa=x0+(x1-x0)*xx//w; xb=x0+(x1-x0)*(xx+1)//w; xb=max(xb,xa+1)
            mn=255
            for y in range(ya,min(yb,pix.height)):
                off=y*stride
                for x in range(xa,min(xb,pix.width)):
                    v=data[off+x]
                    if v<mn:mn=v
            row.append("#" if mn<100 else "+" if mn<190 else " ")
        out.append("".join(row).rstrip())
    return out

raw=urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype="pdf");page=doc[3];PAGE_RECT=page.rect
draws=page.get_drawings(); reds=[]
for d in draws:
    col=d.get("color")
    if col and len(col)>=3 and col[0]>0.75 and col[1]<0.35 and col[2]<0.35:
        r=d.get("rect")
        reds.append({"rect":[r.x0,r.y0,r.x1,r.y1],"center":[(r.x0+r.x1)/2,(r.y0+r.y1)/2],"dashes":d.get("dashes"),"width":d.get("width"),"items":len(d.get("items",[]))})
# Use substantial red paths only; tiny red fragments/glyphs are excluded by dimensions/items.
major=[z for z in reds if (z["rect"][2]-z["rect"][0])>8 and len(z.get("dashes") or "")>0]
if len(major)<20: major=[z for z in reds if (z["rect"][2]-z["rect"][0])>8]
xs=cluster([z["center"][0] for z in major],4);ys=cluster([z["center"][1] for z in major],6)
# panel cells from center midpoints; extend outer cells by half neighboring spacing
xb=[xs[0]-(xs[1]-xs[0])/2]+[(xs[i]+xs[i+1])/2 for i in range(3)]+[xs[-1]+(xs[-1]-xs[-2])/2]
yb=[ys[0]-(ys[1]-ys[0])/2]+[(ys[i]+ys[i+1])/2 for i in range(5)]+[ys[-1]+(ys[-1]-ys[-2])/2]
pix=page.get_pixmap(matrix=pymupdf.Matrix(3,3),colorspace=pymupdf.csGRAY,alpha=False)
panels=[]; lines=[]
for row in range(6):
    for col in range(4):
        cell=pymupdf.Rect(max(0,xb[col]),max(0,yb[row]),min(PAGE_RECT.width,xb[col+1]),min(PAGE_RECT.height,yb[row+1]))
        # Include full cell; labels and axes are visual QC only.
        art=ascii_crop(pix,cell,72,22)
        panels.append({"row":row+1,"col":col+1,"rect":[cell.x0,cell.y0,cell.x1,cell.y1],"ascii":art})
        lines.append(f"\n=== ROW {row+1} COL {col+1} ===")
        lines.extend(art)
result={"status":"HOEKSTRA2001_FIG1_PANEL_GRID_QC_COMPLETE","pdf_page_index":3,"page_rect":[PAGE_RECT.x0,PAGE_RECT.y0,PAGE_RECT.x1,PAGE_RECT.y1],"n_drawings":len(draws),"n_red_drawings":len(reds),"n_major_red_paths":len(major),"x_centers":xs,"y_centers":ys,"major_red_paths":major,"panels":panels,"boundary":"Panel identity/layout QC only. Raster is not used to obtain scientific coordinates; no OCR."}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");TXT.write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps({"n_red":len(reds),"n_major":len(major),"x_centers":xs,"y_centers":ys},indent=2))
