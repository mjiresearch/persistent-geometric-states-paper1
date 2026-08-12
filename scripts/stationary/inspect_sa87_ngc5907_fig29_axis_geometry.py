#!/usr/bin/env python3
"""Inspect only black axis/tick geometry for NGC5907 Sigma_HI panel in HEROES Fig.29."""
from __future__ import annotations
import io,json,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
import pymupdf
URL='https://arxiv.org/e-print/1507.03095'
OUT=Path('validation/stationary/sa87_ngc5907_fig29_axis_geometry_v1.json')
REG=(1525.0,55.0,1795.0,252.0)

def fetch_pdf():
    with urlopen(Request(URL,headers={'User-Agent':'PaperI-SA87-axis/1.0'}),timeout=90) as r:b=r.read()
    with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as tf:
        for m in tf.getmembers():
            if m.isfile() and Path(m.name).name=='Final_params_all.pdf':
                f=tf.extractfile(m)
                if f:return f.read()
    raise RuntimeError('pdf missing')
def cv(v):
    if isinstance(v,pymupdf.Point):return [round(v.x,6),round(v.y,6)]
    if isinstance(v,pymupdf.Rect):return [round(v.x0,6),round(v.y0,6),round(v.x1,6),round(v.y1,6)]
    if isinstance(v,(int,float)):return round(float(v),6)
    return str(v)
def black(c):return c is not None and all(abs(float(x))<1e-6 for x in c)
def main():
    d=pymupdf.open(stream=fetch_pdf(),filetype='pdf')[0]
    x0,y0,x1,y1=REG; objs=[]
    for i,o in enumerate(d.get_drawings()):
        r=o['rect'];cx=(r.x0+r.x1)/2;cy=(r.y0+r.y1)/2
        if not (x0<=cx<=x1 and y0<=cy<=y1):continue
        col=o.get('color');fill=o.get('fill');typ=o.get('type');w=float(o.get('width') or 0)
        if not (black(col) or black(fill)):continue
        # exclude the 3x3 black outlines around colored markers
        if r.width<=4 and r.height<=4:continue
        objs.append({'index':i,'rect':[round(r.x0,6),round(r.y0,6),round(r.x1,6),round(r.y1,6)],'type':typ,'width':round(w,6),'color':None if col is None else [round(float(x),6) for x in col],'fill':None if fill is None else [round(float(x),6) for x in fill],'items':[[it[0],*[cv(v) for v in it[1:]]] for it in o.get('items',[])]})
    words=[]
    for w in d.get_text('words'):
        cx=(w[0]+w[2])/2;cy=(w[1]+w[3])/2
        if 1500<=cx<=1800 and 20<=cy<=275:words.append({'text':w[4],'rect':[round(w[0],6),round(w[1],6),round(w[2],6),round(w[3],6)],'center':[round(cx,6),round(cy,6)]})
    result={'status':'SA87_NGC5907_FIG29_AXIS_GEOMETRY_COMPLETE','region':REG,'words':words,'n_nonmarker_black_objects':len(objs),'objects':objs,'next_action':'Identify frame/tick coordinates, fit exact linear transforms radius(x) and Sigma_HI(y), and apply only to red/blue source-native polyline vertices.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
