#!/usr/bin/env python3
"""Recover small native tick-line geometry in the NGC5907 Sigma_HI panel."""
from __future__ import annotations
import io,json,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
import pymupdf
URL='https://arxiv.org/e-print/1507.03095'
OUT=Path('validation/stationary/sa87_ngc5907_fig29_tick_geometry_v1.json')

def pdf():
 with urlopen(Request(URL,headers={'User-Agent':'PaperI-SA87-ticks/1.0'}),timeout=90) as r:b=r.read()
 with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as tf:
  for m in tf.getmembers():
   if m.isfile() and Path(m.name).name=='Final_params_all.pdf':
    f=tf.extractfile(m)
    if f:return f.read()
 raise RuntimeError('missing pdf')
def blk(c):return c is not None and all(abs(float(x))<1e-8 for x in c)
def cv(v):
 if isinstance(v,pymupdf.Point):return [round(v.x,6),round(v.y,6)]
 if isinstance(v,pymupdf.Rect):return [round(v.x0,6),round(v.y0,6),round(v.x1,6),round(v.y1,6)]
 if isinstance(v,(int,float)):return round(float(v),6)
 return str(v)
def main():
 p=pymupdf.open(stream=pdf(),filetype='pdf')[0];ticks=[]
 for i,d in enumerate(p.get_drawings()):
  r=d['rect'];col=d.get('color');fill=d.get('fill')
  if not (blk(col) or blk(fill)):continue
  # near top-right panel axes, only small degenerate line objects (ticks), not 3x3 marker outlines
  if not (1538<= (r.x0+r.x1)/2 <=1795 and 68<= (r.y0+r.y1)/2 <=253):continue
  if not ((r.width<=5 and r.height<0.2) or (r.height<=5 and r.width<0.2)):continue
  ticks.append({'index':i,'rect':[round(r.x0,6),round(r.y0,6),round(r.x1,6),round(r.y1,6)],'size':[round(r.width,6),round(r.height,6)],'type':d.get('type'),'width':round(float(d.get('width') or 0),6),'items':[[it[0],*[cv(v) for v in it[1:]]] for it in d.get('items',[])]})
 words=[]
 for w in p.get_text('words'):
  cx=(w[0]+w[2])/2;cy=(w[1]+w[3])/2
  if 1500<=cx<=1800 and 20<=cy<=975:words.append({'text':w[4],'center':[round(cx,6),round(cy,6)],'rect':[round(w[0],6),round(w[1],6),round(w[2],6),round(w[3],6)]})
 result={'status':'SA87_NGC5907_FIG29_TICK_GEOMETRY_COMPLETE','ticks':ticks,'words':words,'next_action':'Match y ticks to labels 0,2,4,6 and x ticks to bottom-column Radius labels 0,10,20,30,40,50; solve linear transforms.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'ticks':ticks},indent=2))
if __name__=='__main__':main()
