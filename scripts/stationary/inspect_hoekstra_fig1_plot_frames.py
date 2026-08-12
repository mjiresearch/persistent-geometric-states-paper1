#!/usr/bin/env python3
"""Identify Hoekstra 2001 Fig.1 panel frames/tick geometry in compiled PDF.

This uses vector drawing metadata only. It does not read scientific curve values.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import json
import pymupdf
URL="https://arxiv.org/pdf/astro-ph/0010569"
OUT=Path("validation/stationary/hoekstra2001_fig1_plot_frames_v1.json")
raw=urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"}),timeout=120).read()
doc=pymupdf.open(stream=raw,filetype='pdf');p=doc[3]
recs=[]
for i,d in enumerate(p.get_drawings()):
    r=d.get('rect'); col=d.get('color'); fill=d.get('fill'); items=d.get('items',[])
    rec={
      'index':i,'rect':[r.x0,r.y0,r.x1,r.y1],'width_rect':r.x1-r.x0,'height_rect':r.y1-r.y0,
      'color':col,'fill':fill,'line_width':d.get('width'),'dashes':d.get('dashes'),'n_items':len(items),
      'item_types':[x[0] for x in items[:100]],
      'items_preview':[str(x)[:600] for x in items[:30]],
    }
    # Keep drawing groups intersecting the Figure-1 panel region and relevant to top-left frame.
    if r.x1>=85 and r.x0<=215 and r.y1>=120 and r.y0<=235:
        recs.append(rec)
res={'status':'HOEKSTRA2001_FIG1_PLOT_FRAME_AUDIT_COMPLETE','page_rect':[p.rect.x0,p.rect.y0,p.rect.x1,p.rect.y1],'top_left_region_drawings':recs,'boundary':'Vector frame/tick metadata only; no profile-coordinate extraction.'}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8');print(json.dumps(recs,indent=2))
