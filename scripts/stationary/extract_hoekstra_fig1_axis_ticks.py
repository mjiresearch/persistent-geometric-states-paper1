#!/usr/bin/env python3
"""Extract native vector axis tick coordinates from one Hoekstra Fig.1 panel.

No text/image interpretation and no profile coordinates. This isolates the frame
and tick marks to establish exact axis grids before H I path promotion.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import json,math
import pymupdf
URL='https://arxiv.org/pdf/astro-ph/0010569'
OUT=Path('validation/stationary/hoekstra2001_fig1_axis_ticks_v1.json')
raw=urlopen(Request(URL,headers={'User-Agent':'Mozilla/5.0 PersistenceFrameworkPaperI/1.0'}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype='pdf');p=doc[3]
frames=[]
for i,d in enumerate(p.get_drawings()):
    r=d.get('rect');
    # Panel frame groups have ~95 data width plus labels extending ~15 px left, and ~63 px height.
    if d.get('color') and max(d.get('color'))<0.05 and 60 < (r.y1-r.y0) < 66 and 100 < (r.x1-r.x0) < 115 and len(d.get('items',[]))>100:
        frames.append((i,d))
# Use first such group; tick grid is shared across panels. Determine actual data frame from longest horizontal/vertical lines.
i,d=frames[0]; items=d.get('items',[])
lines=[]
for it in items:
    if it[0]!='l':continue
    a,b=it[1],it[2];lines.append((a.x,a.y,b.x,b.y))
# Find dominant horizontal frame lines by maximum span and dominant vertical frame lines by maximum span.
h=[z for z in lines if abs(z[1]-z[3])<1e-4];v=[z for z in lines if abs(z[0]-z[2])<1e-4]
longh=sorted(h,key=lambda z:abs(z[2]-z[0]),reverse=True)[:10]
longv=sorted(v,key=lambda z:abs(z[3]-z[1]),reverse=True)[:10]
xleft=min(min(z[0],z[2]) for z in longh[:2]);xright=max(max(z[0],z[2]) for z in longh[:2])
ytop=min(min(z[1],z[3]) for z in longv[:2]);ybottom=max(max(z[1],z[3]) for z in longv[:2])
def near(a,b,t=0.02):return abs(a-b)<t
left_ticks=[];right_ticks=[];bottom_ticks=[];top_ticks=[]
for x0,y0,x1,y1 in lines:
    if abs(y0-y1)<1e-4:
        L=abs(x1-x0)
        if L<=8:
            if near(x0,xleft) or near(x1,xleft):left_ticks.append({'y':y0,'length':L,'line':[x0,y0,x1,y1]})
            if near(x0,xright) or near(x1,xright):right_ticks.append({'y':y0,'length':L,'line':[x0,y0,x1,y1]})
    if abs(x0-x1)<1e-4:
        L=abs(y1-y0)
        if L<=8:
            if near(y0,ybottom) or near(y1,ybottom):bottom_ticks.append({'x':x0,'length':L,'line':[x0,y0,x1,y1]})
            if near(y0,ytop) or near(y1,ytop):top_ticks.append({'x':x0,'length':L,'line':[x0,y0,x1,y1]})
def dedup(rows,key):
    out=[]
    for r in sorted(rows,key=lambda q:q[key]):
        if not out or abs(r[key]-out[-1][key])>0.05:out.append(r)
        elif r['length']>out[-1]['length']:out[-1]=r
    return out
res={'status':'HOEKSTRA2001_FIG1_AXIS_TICKS_COMPLETE','drawing_index':i,'frame':[xleft,ytop,xright,ybottom],'left_ticks':dedup(left_ticks,'y'),'right_ticks':dedup(right_ticks,'y'),'bottom_ticks':dedup(bottom_ticks,'x'),'top_ticks':dedup(top_ticks,'x'),'long_horizontal':longh,'long_vertical':longv,'boundary':'Native vector frame/tick geometry only; no scientific profile extraction.'}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8');print(json.dumps(res,indent=2))
