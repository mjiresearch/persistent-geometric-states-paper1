#!/usr/bin/env python3
"""Compact structural summary of VM97 NGC6015 Figure-3 PGPLOT EPS.

Statically extracts embedded 07540003.eps from the legacy A&A PostScript and
summarizes panel frames, PGPLOT marker calls, primitive data-point calls, and
coordinate clusters. No PostScript execution and no raster operations.
"""
from __future__ import annotations
import gzip,json,re
from collections import Counter,defaultdict
from pathlib import Path
from urllib.request import Request,urlopen

URL='https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz'
TARGET='07540003.eps'
OUT=Path('validation/stationary/vm97_ngc6015_fig3_pgplot_geometry_summary_v1.json')
TXT=Path('validation/stationary/vm97_ngc6015_fig3_pgplot_geometry_summary_v1.txt')

def fetch():
 with urlopen(Request(URL,headers={'User-Agent':'PaperI-VM97-geometry/1.0'}),timeout=90) as r:return gzip.decompress(r.read()).decode('latin-1',errors='replace')
def extract(t):
 m=re.search(r'^%%BeginDocument:\s*'+re.escape(TARGET)+r'\s*$',t,re.M)
 if not m:raise RuntimeError('BeginDocument missing')
 e=re.search(r'^%%EndDocument\s*$',t[m.end():],re.M)
 if not e:raise RuntimeError('EndDocument missing')
 return t[m.start():m.end()+e.end()]

def main():
 b=extract(fetch())
 # Canonical PGPLOT frame pattern seen in source EPS.
 frames=[]
 pat=re.compile(r'(?P<w>\d+)\s+0\s+(?P<x>\d+)\s+(?P<y>\d+)\s+L\s+0\s+(?P<h>\d+)\s+C\s+-(?P=w)\s+0\s+C\s+0\s+-(?P=h)\s+C')
 for m in pat.finditer(b):frames.append({k:int(m.group(k)) for k in ['x','y','w','h']}|{'char':m.start()})
 # Explicit marker invocations (definitions excluded because no leading numeric pair).
 markers=[]
 for m in re.finditer(r'(?<![\w/.-])(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+M(\d+)\b',b):
  markers.append({'x':float(m.group(1)),'y':float(m.group(2)),'marker':int(m.group(3)),'char':m.start()})
 # PGPLOT point primitive D: x y D (zero-length stroke point).
 dots=[]
 for m in re.finditer(r'(?<![\w/.-])(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+D\b',b):
  dots.append({'x':float(m.group(1)),'y':float(m.group(2)),'char':m.start()})
 # Circle primitives: x y radius CC/FC when present.
 circles=[]
 for m in re.finditer(r'(?<![\w/.-])(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(CC|FC)\b',b):
  circles.append({'x':float(m.group(1)),'y':float(m.group(2)),'r':float(m.group(3)),'kind':m.group(4),'char':m.start()})
 # Collect source lines containing marker/dot calls or long L/C sequences, excluding proc definitions.
 lines=[]
 for no,line in enumerate(b.splitlines(),1):
  if line.startswith('/') or line.startswith('%'):continue
  if re.search(r'\bM\d+\b|\sD\b|\s(?:CC|FC)\b',line):lines.append({'line':no,'text':line[:1200]})
 # Associate primitives with detected frames geometrically.
 def assoc(items):
  out=[]
  for i,f in enumerate(frames):
   inside=[q for q in items if f['x']-5<=q['x']<=f['x']+f['w']+5 and f['y']-5<=q['y']<=f['y']+f['h']+5]
   out.append({'frame_index':i,'frame':f,'n':len(inside),'items':inside})
  return out
 # Cluster all marker y coordinates into coarse 250-unit bands, useful if frame regex misses subpanels.
 bands=defaultdict(list)
 for q in markers:d=int(q['y']//250)*250;bands[d].append(q)
 result={
  'status':'VM97_NGC6015_FIG3_PGPLOT_GEOMETRY_SUMMARY_COMPLETE',
  'source':'Verdes-Montenegro et al. 1997 Figure 3 / embedded 07540003.eps',
  'n_chars':len(b),'frames':frames,'n_frames':len(frames),
  'marker_counts':dict(Counter(q['marker'] for q in markers)),'n_markers':len(markers),'markers_by_frame':assoc(markers),
  'n_dots':len(dots),'dots_by_frame':assoc(dots),'n_circles':len(circles),'circles_by_frame':assoc(circles),
  'marker_y_bands':{str(k):{'n':len(v),'markers':v} for k,v in sorted(bands.items()) if v},
  'source_lines_with_point_calls':lines,
  'next_action':'Identify Figure 3d frame from panel order/axis context; classify its repeated marker primitive as radial HI samples, recover native x/y positions, then calibrate from major tick geometry and source caption/axis units.',
  'boundary':'Static source geometry only; no PostScript execution, raster digitization, OCR, profile fitting, or persistence analysis. L_A and C_A remain locked.'
 }
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 TXT.write_text('\n'.join([f"frames={json.dumps(frames)}",f"marker_counts={json.dumps(result['marker_counts'])}",f"n_markers={len(markers)} n_dots={len(dots)} n_circles={len(circles)}",'','MARKERS_BY_FRAME']+[json.dumps(x) for x in result['markers_by_frame']]+['','DOTS_BY_FRAME']+[json.dumps(x) for x in result['dots_by_frame']]+['','POINT_CALL_LINES']+[json.dumps(x) for x in lines])+'\n')
 print(json.dumps({'status':result['status'],'frames':frames,'marker_counts':result['marker_counts'],'n_markers':len(markers),'n_dots':len(dots),'n_circles':len(circles),'per_frame':[{'frame':x['frame_index'],'bounds':x['frame'],'markers':x['n']} for x in result['markers_by_frame']],'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
