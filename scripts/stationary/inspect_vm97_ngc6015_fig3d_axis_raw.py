#!/usr/bin/env python3
"""Compact static dump of VM97 Figure-3d axis/vector source around the bottom frame."""
from __future__ import annotations
import gzip,json,re
from pathlib import Path
from urllib.request import Request,urlopen
URL='https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz'
TARGET='07540003.eps'
OUT=Path('validation/stationary/vm97_ngc6015_fig3d_axis_raw_v1.json')
TXT=Path('validation/stationary/vm97_ngc6015_fig3d_axis_raw_v1.txt')
def fetch():
 with urlopen(Request(URL,headers={'User-Agent':'PaperI-VM97-fig3d-axis/1.0'}),timeout=90) as r:return gzip.decompress(r.read()).decode('latin-1',errors='replace')
def extract(t):
 m=re.search(r'^%%BeginDocument:\s*'+re.escape(TARGET)+r'\s*$',t,re.M); e=re.search(r'^%%EndDocument\s*$',t[m.end():],re.M)
 return t[m.start():m.end()+e.end()]
def main():
 b=extract(fetch())
 # Bottom frame begins at the exact frame command and ends after M3 data/polyline before next unrelated source section.
 start=b.find('2825 0 435 326 L')
 if start<0:raise RuntimeError('bottom frame start not found')
 m3def=b.find('/M3 {',start)
 if m3def<0:raise RuntimeError('M3 definition not found')
 # include 7k before M3 definition (axes and labels) plus 7k after (markers/polyline)
 lo=start;hi=min(len(b),m3def+9000);chunk=b[lo:hi]
 markers=[{'x':int(x),'y':int(y)} for x,y in re.findall(r'(?<!\d)(\d+)\s+(\d+)\s+M3\b',chunk)]
 # All short horizontal/vertical L tick candidates in frame bounds.
 ticks=[]
 for dx,dy,x,y in re.findall(r'(?<!\d)(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+L\b',chunk):
  dx,dy,x,y=map(int,(dx,dy,x,y));
  if 400<=x<=3300 and 250<=y<=1600 and ((abs(dx)<=70 and dy==0) or (abs(dy)<=70 and dx==0)):
   ticks.append({'dx':dx,'dy':dy,'x':x,'y':y})
 # Keep every non-comment source line before M3 definition; label strokes are compact.
 pre=b[start:m3def]
 lines=[ln for ln in pre.splitlines() if ln.strip() and not ln.startswith('%')]
 result={'status':'VM97_NGC6015_FIG3D_AXIS_RAW_COMPLETE','frame':{'x0':435,'y0':326,'x1':3260,'y1':1521},'m3_markers':markers,'n_m3':len(markers),'tick_candidates':ticks,'pre_m3_source_lines':lines,'raw_chunk':chunk,'next_action':'Use exact major/minor tick pattern and stroke-glyph label geometry to lock lower arcsec x scale and Sigma_HI y scale; then transform the 31 M3 positions.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 TXT.write_text('\n'.join(['MARKERS '+json.dumps(markers),'TICKS '+json.dumps(ticks),'','PRE_M3']+lines+['','RAW_CHUNK',chunk])+'\n',encoding='latin-1',errors='replace')
 print('MARKERS',json.dumps(markers));print('TICKS',json.dumps(ticks));print('PRE_M3_BEGIN');print('\n'.join(lines));print('PRE_M3_END');print('OUTPUT',OUT)
if __name__=='__main__':main()
