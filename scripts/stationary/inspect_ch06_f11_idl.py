#!/usr/bin/env python3
import io,tarfile,urllib.request,json
from pathlib import Path
b=urllib.request.urlopen(urllib.request.Request('https://arxiv.org/e-print/astro-ph/0609148',headers={'User-Agent':'PaperI'}),timeout=60).read()
with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as t:s=t.extractfile('f11.eps').read().decode('latin1','ignore')
lines=s.splitlines();prog=[x.strip() for x in lines if x.strip() and not x.lstrip().startswith(('%','/'))]
flat=' '.join(prog);sig='M -33 -16 R -33 -33 R -16 -49 R 0 -33 R';markers=[]
for left in flat.split(sig)[:-1]:
 p=left.split()
 try:
  x=float(p[-2]);y=float(p[-1]);markers.append([x+24.5,y-114.5])
 except:pass
out={'status':'CH06_F11_IDL_MARKERS_LOCATED','circle_marker_centers':markers,'n_circle_markers':len(markers),'program_tail':prog[-100:]}
Path('validation/stationary/ch06_f11_idl_structure_v1.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'n_circle_markers':len(markers),'circle_marker_centers':markers},indent=2))
