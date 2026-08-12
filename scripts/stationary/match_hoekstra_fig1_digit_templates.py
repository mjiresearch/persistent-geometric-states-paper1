#!/usr/bin/env python3
"""Match Hoekstra Fig.1 numeric panel-label glyphs using only known top-row templates.

This is NOT scientific-data OCR. It segments the printed galaxy-name glyphs only.
Digit templates are learned from four panel identities already read directly from
the publication layout: R1C1=2903, R1C2=5033, R1C3=6503, R1C4=2885.
The purpose is to locate the unique panel whose numeric suffix begins 53, i.e.
NGC5371, before mapping exact EPS H I paths to galaxies.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import json, math
import pymupdf

URL="https://arxiv.org/pdf/astro-ph/0010569"
GRID=Path("validation/stationary/hoekstra2001_fig1_pdf_panel_grid_v1.json")
OUT=Path("validation/stationary/hoekstra2001_fig1_digit_template_match_v1.json")
KNOWN={(1,1):"2903",(1,2):"5033",(1,3):"6503",(1,4):"2885"}

raw=urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype="pdf");p=doc[3];pix=p.get_pixmap(matrix=pymupdf.Matrix(8,8),colorspace=pymupdf.csGRAY,alpha=False)
grid=json.loads(GRID.read_text());scale=pix.width/p.rect.width

def label_binary(rect):
    x0,y0,x1,y1=rect;w=x1-x0;h=y1-y0
    # Upper label strip, excluding axes. Keep full name so rightmost runs are digits.
    rx0=x0+0.18*w;rx1=x0+0.985*w;ry0=y0+0.025*h;ry1=y0+0.27*h
    X0=max(0,int(rx0*scale));X1=min(pix.width,int(rx1*scale));Y0=max(0,int(ry0*scale));Y1=min(pix.height,int(ry1*scale))
    data=pix.samples;stride=pix.stride
    a=[]
    for y in range(Y0,Y1):
        row=[];off=y*stride
        for x in range(X0,X1):row.append(data[off+x] < 140)
        a.append(row)
    return a

def trim(a):
    if not a:return a
    ys=[i for i,row in enumerate(a) if any(row)]
    xs=[j for j in range(len(a[0])) if any(row[j] for row in a)]
    if not ys or not xs:return []
    return [row[min(xs):max(xs)+1] for row in a[min(ys):max(ys)+1]]

def x_runs(a):
    if not a:return []
    on=[any(row[x] for row in a) for x in range(len(a[0]))]
    # Fill only tiny anti-alias gaps <=2 px; inter-glyph spaces are much larger at 8x.
    for i in range(len(on)):
        if on[i]:continue
        l=i-1
        while l>=0 and not on[l]:l-=1
        r=i+1
        while r<len(on) and not on[r]:r+=1
        if l>=0 and r<len(on) and r-l-1<=2:on[i]=True
    runs=[];i=0
    while i<len(on):
        if not on[i]:i+=1;continue
        j=i
        while j+1<len(on) and on[j+1]:j+=1
        if j-i+1>=3:runs.append((i,j))
        i=j+1
    return runs

def norm(g,H=28,W=20):
    g=trim(g)
    if not g:return [[0.0]*W for _ in range(H)]
    h=len(g);w=len(g[0]);out=[]
    for yy in range(H):
        row=[];ya=yy*h/H;yb=(yy+1)*h/H
        for xx in range(W):
            xa=xx*w/W;xb=(xx+1)*w/W
            # area/sample occupancy using nearest pixels on a fine 3x3 grid
            v=0
            for sy in (1/6,3/6,5/6):
                iy=min(h-1,int(ya+(yb-ya)*sy))
                for sx in (1/6,3/6,5/6):
                    ix=min(w-1,int(xa+(xb-xa)*sx));v+=1 if g[iy][ix] else 0
            row.append(v/9)
        out.append(row)
    return out

def dist(a,b):return sum((a[y][x]-b[y][x])**2 for y in range(len(a)) for x in range(len(a[0])))

def digit_glyphs(rect,n_digits=None):
    a=label_binary(rect);runs=x_runs(a)
    # Galaxy number is the rightmost N glyph runs. For unknown panels test suffixes later.
    if n_digits is None:return a,runs
    rr=runs[-n_digits:]
    return [norm([row[x0:x1+1] for row in a]) for x0,x1 in rr],runs

pan={(z['row'],z['col']):z for z in grid['panels']}
templates={}
known_diag={}
for key,num in KNOWN.items():
    glyphs,runs=digit_glyphs(pan[key]['rect'],len(num))
    known_diag[str(key)]={'number':num,'n_runs':len(runs),'runs':runs}
    if len(glyphs)!=len(num):continue
    for ch,g in zip(num,glyphs):templates.setdefault(ch,[]).append(g)
# Average template per digit.
avg={}
for ch,gs in templates.items():
    H=len(gs[0]);W=len(gs[0][0]);avg[ch]=[[sum(g[y][x] for g in gs)/len(gs) for x in range(W)] for y in range(H)]

results=[]
for key,z in sorted(pan.items()):
    a,runs=digit_glyphs(z['rect'],None)
    # Evaluate rightmost 4 runs as four-digit suffix when available; most relevant NGC targets have 4 digits.
    suffix=runs[-4:] if len(runs)>=4 else runs
    dec=[];scores=[]
    for x0,x1 in suffix:
        g=norm([row[x0:x1+1] for row in a])
        ranked=sorted((dist(g,t),ch) for ch,t in avg.items())
        dec.append(ranked[0][1] if ranked else '?')
        scores.append(ranked[:4])
    results.append({'row':key[0],'col':key[1],'n_runs':len(runs),'runs':runs,'decoded_known_digit_alphabet':''.join(dec),'scores':scores})

candidates=[r for r in results if r['decoded_known_digit_alphabet'].startswith('53')]
res={'status':'HOEKSTRA2001_FIG1_DIGIT_TEMPLATE_MATCH_COMPLETE','known_training_panels':known_diag,'trained_digits':sorted(avg),'panel_results':results,'panels_matching_known_prefix_53':candidates,'interpretation':'Only panel-name glyphs are classified; no profile coordinates or axes are read from raster content. A unique 53-prefix panel identifies NGC5371 among the published 24-galaxy list.','boundary':'Label identity QC only; no OCR library, no scientific raster digitization.'}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(res,indent=2)+"\n",encoding='utf-8')
print(json.dumps({'trained_digits':sorted(avg),'prefix_53_candidates':candidates,'top_row':[r for r in results if r['row']==1]},indent=2))
