#!/usr/bin/env python3
"""Inspect dashed vector paths in the Elson UGC4325 panel."""
import io,json,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
import fitz
URL='https://export.arxiv.org/e-print/1709.03288'

def dl():
 r=Request(URL,headers={'User-Agent':'PersistenceFrameworkPaperI/1.0'})
 with urlopen(r,timeout=90) as h:return h.read()
def col(c):return None if c is None else tuple(round(float(x),3) for x in c)
def main():
 raw=dl();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');pdf=tf.extractfile('profiles1_V2.pdf').read();p=fitz.open(stream=pdf,filetype='pdf')[0]
 # UGC4325 panel box from verified diagnostic
 xmin,xmax=250,445;ymin,ymax=475,710
 out=[]
 for i,d in enumerate(p.get_drawings()):
  r=d.get('rect')
  if not r or r.x1<xmin or r.x0>xmax or r.y1<ymin or r.y0>ymax:continue
  dash=str(d.get('dashes',''))
  if dash and dash not in {'[] 0','[] 0.0','None'}:
   out.append({'drawing':i,'color':col(d.get('color')),'fill':col(d.get('fill')),'width':d.get('width'),'dashes':dash,'rect':[r.x0,r.y0,r.x1,r.y1],'items':[str(x) for x in d.get('items',[])[:20]]})
 Path('validation/stationary/elson2017_ugc4325_dash_diagnostic_v1.json').write_text(json.dumps(out,indent=2)+'\n')
 print('DASHED',len(out))
 for x in out: print(json.dumps(x))
if __name__=='__main__':main()
