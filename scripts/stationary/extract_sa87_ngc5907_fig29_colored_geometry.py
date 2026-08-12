#!/usr/bin/env python3
"""Extract colored native-vector geometry from NGC5907 Sigma_HI panel in HEROES Fig. 29.

This is a geometry/QC stage only: it records all red/blue vector objects in the
rightmost top panel, their bounding boxes, drawing primitives, and native black
axis/tick geometry. It does not yet choose which objects are scientific samples.
"""
from __future__ import annotations
import io, json, math, tarfile
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen
import pymupdf

URL='https://arxiv.org/e-print/1507.03095'
OUT=Path('validation/stationary/sa87_ngc5907_fig29_colored_geometry_v1.json')
TXT=Path('validation/stationary/sa87_ngc5907_fig29_colored_geometry_v1.txt')
# Native PDF geometry established from text labels/ticks.
REGION={'x0':1538.0,'x1':1794.0,'y0':58.0,'y1':252.0}

def fetch_pdf():
    with urlopen(Request(URL,headers={'User-Agent':'PaperI-SA87-colored-geometry/1.0'}),timeout=90) as r:payload=r.read()
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        for m in tf.getmembers():
            if m.isfile() and Path(m.name).name=='Final_params_all.pdf':
                f=tf.extractfile(m)
                if f:return f.read()
    raise RuntimeError('Final_params_all.pdf missing')

def rgb(c):
    if c is None:return None
    return tuple(round(float(x),6) for x in c)
def conv(v):
    if isinstance(v,pymupdf.Point):return [round(v.x,6),round(v.y,6)]
    if isinstance(v,pymupdf.Rect):return [round(v.x0,6),round(v.y0,6),round(v.x1,6),round(v.y1,6)]
    if isinstance(v,(float,int)):return round(float(v),6)
    return str(v)
def item_dump(items):return [[it[0],*[conv(v) for v in it[1:]]] for it in items]

def inside(cx,cy):return REGION['x0']<=cx<=REGION['x1'] and REGION['y0']<=cy<=REGION['y1']
def is_red(c):return c is not None and c[0]>0.9 and c[1]<0.1 and c[2]<0.1
def is_blue(c):return c is not None and c[2]>0.9 and c[0]<0.1 and c[1]<0.1

def main():
    b=fetch_pdf();doc=pymupdf.open(stream=b,filetype='pdf');p=doc[0]
    selected=[];black=[]
    for i,d in enumerate(p.get_drawings()):
        r=d['rect'];cx=(r.x0+r.x1)/2;cy=(r.y0+r.y1)/2
        if not inside(cx,cy):continue
        c=rgb(d.get('color'));f=rgb(d.get('fill'));typ=d.get('type');w=float(d.get('width') or 0)
        rec={'index':i,'rect':[round(r.x0,6),round(r.y0,6),round(r.x1,6),round(r.y1,6)],'center':[round(cx,6),round(cy,6)],'size':[round(r.width,6),round(r.height,6)],'type':typ,'color':c,'fill':f,'width':round(w,6),'closePath':d.get('closePath'),'items':item_dump(d.get('items',[]))}
        if is_red(c) or is_red(f):rec['series_color']='red';selected.append(rec)
        elif is_blue(c) or is_blue(f):rec['series_color']='blue';selected.append(rec)
        elif (c==(0.0,0.0,0.0) or f==(0.0,0.0,0.0)):
            # keep black panel/tick/marker objects for axis calibration; cap to region only
            black.append(rec)
    # Exact native text words within / adjacent to the panel.
    words=[]
    for w in p.get_text('words'):
        cx=(w[0]+w[2])/2;cy=(w[1]+w[3])/2
        if 1500<=cx<=1800 and 20<=cy<=270:
            words.append({'rect':[round(w[0],6),round(w[1],6),round(w[2],6),round(w[3],6)],'center':[round(cx,6),round(cy,6)],'text':w[4]})
    shape_counts=Counter((x['series_color'],x['type'],tuple(x['size']),x['width'],str(x['color']),str(x['fill'])) for x in selected)
    result={'status':'SA87_NGC5907_FIG29_COLORED_GEOMETRY_EXTRACTED','source':'Allaert et al. 2015 Figure 29 / Final_params_all.pdf','region':REGION,'native_words':words,'n_colored_objects':len(selected),'colored_shape_counts':[{'key':list(k),'count':v} for k,v in shape_counts.most_common()],'colored_objects':selected,'n_black_objects':len(black),'black_objects':black,'next_action':'Identify repeated red/blue marker primitive(s) by shape and size, exclude legend/connecting paths, recover marker centers, calibrate x/y from native ticks, and preserve approaching/receding series separately.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
    lines=['WORDS']+[json.dumps(x) for x in words]+['','SHAPE_COUNTS']+[f'{v} {k}' for k,v in shape_counts.most_common()]+['','COLORED_OBJECTS']+[json.dumps(x) for x in selected]+['','BLACK_OBJECTS']+[json.dumps(x) for x in black]
    TXT.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':result['status'],'region':REGION,'words':words,'shape_counts':result['colored_shape_counts'],'n_colored':len(selected),'n_black':len(black),'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
