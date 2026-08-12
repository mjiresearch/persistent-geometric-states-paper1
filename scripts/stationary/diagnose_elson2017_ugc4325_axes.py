#!/usr/bin/env python3
"""Diagnose vector axis anchors for the Elson (2017) UGC 4325 panel.

No scientific values are extracted yet.  The purpose is to identify the
horizontal zero baseline and the internal vertical R_HI marker using only PDF
vector geometry.  UGC 4325 is panel 9 (0-based index 8) of profiles1_V2.pdf.
"""
from __future__ import annotations

import io, json, math, tarfile
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen
import fitz

URL='https://export.arxiv.org/e-print/1709.03288'
PDF='profiles1_V2.pdf'
PANEL_INDEX=8


def dl():
    r=Request(URL,headers={'User-Agent':'PersistenceFrameworkPaperI/1.0'})
    with urlopen(r,timeout=90) as h: return h.read()


def color(c):
    return None if c is None else tuple(round(float(x),3) for x in c)


def line_items(d):
    out=[]
    for it in d.get('items',[]):
        if it[0]=='l':
            p,q=it[1],it[2]
            out.append((float(p.x),float(p.y),float(q.x),float(q.y)))
    return out


def main():
    raw=dl(); tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    pdf=tf.extractfile(PDF).read(); doc=fitz.open(stream=pdf,filetype='pdf'); page=doc[0]
    drawings=page.get_drawings()
    reds=[]
    for d in drawings:
        if color(d.get('color'))==(1.0,0.0,0.0):
            segs=line_items(d)
            if len(segs)>=20:
                reds.append((d,segs))
    reds.sort(key=lambda ds:(round(ds[0]['rect'].y0,1),round(ds[0]['rect'].x0,1)))
    if len(reds)!=12: raise RuntimeError(f'expected 12 red panel paths, got {len(reds)}')
    red,segs=reds[PANEL_INDEX]
    rr=red['rect']
    # Broad cell around red data rect. Neighboring panels are >80 pt away.
    xmin,xmax=rr.x0-18,rr.x1+18; ymin,ymax=rr.y0-25,rr.y1+30
    vertical=[]; horizontal=[]
    for di,d in enumerate(drawings):
        if color(d.get('color'))!=(0.0,0.0,0.0): continue
        for x1,y1,x2,y2 in line_items(d):
            if max(x1,x2)<xmin or min(x1,x2)>xmax or max(y1,y2)<ymin or min(y1,y2)>ymax:
                continue
            if abs(x1-x2)<0.15 and abs(y1-y2)>0.3:
                vertical.append({'drawing':di,'x':(x1+x2)/2,'y0':min(y1,y2),'y1':max(y1,y2),'len':abs(y2-y1),'width':d.get('width')})
            if abs(y1-y2)<0.15 and abs(x1-x2)>0.3:
                horizontal.append({'drawing':di,'y':(y1+y2)/2,'x0':min(x1,x2),'x1':max(x1,x2),'len':abs(x2-x1),'width':d.get('width')})
    # Cluster by coordinate and sum segment lengths; dashed RHI is many short verticals at same x.
    def clusters(items,key):
        groups=[]
        for v in sorted(items,key=lambda z:z[key]):
            if not groups or abs(v[key]-groups[-1]['coord'])>0.35:
                groups.append({'coord':v[key],'items':[v]})
            else:
                groups[-1]['items'].append(v)
                groups[-1]['coord']=sum(i[key] for i in groups[-1]['items'])/len(groups[-1]['items'])
        for g in groups:
            g['total_len']=sum(i['len'] for i in g['items'])
            g['max_len']=max(i['len'] for i in g['items'])
            g['n']=len(g['items'])
            if key=='x':
                g['span0']=min(i['y0'] for i in g['items']); g['span1']=max(i['y1'] for i in g['items'])
            else:
                g['span0']=min(i['x0'] for i in g['items']); g['span1']=max(i['x1'] for i in g['items'])
        return sorted(groups,key=lambda g:g['total_len'],reverse=True)
    vc=clusters(vertical,'x'); hc=clusters(horizontal,'y')
    # ordered red vertices
    verts=[(segs[0][0],segs[0][1])] + [(s[2],s[3]) for s in segs]
    result={
      'panel':'UGC04325','panel_index':PANEL_INDEX,'red_rect':[rr.x0,rr.y0,rr.x1,rr.y1],
      'n_red_vertices':len(verts),'red_vertices':verts,
      'vertical_clusters':vc[:40],'horizontal_clusters':hc[:40],
      'source_distance_mpc':10.1,'source_rhi_arcsec':142,
      'source_rhi_kpc':142*10.1*1000/206265,
    }
    Path('validation/stationary/elson2017_ugc4325_axis_diagnostic_v1.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'red_vertices','vertical_clusters','horizontal_clusters'}},indent=2))
    print('TOP VERTICAL CLUSTERS')
    for g in vc[:25]: print(g)
    print('TOP HORIZONTAL CLUSTERS')
    for g in hc[:25]: print(g)
    print('RED FIRST/LAST',verts[:5],verts[-5:])

if __name__=='__main__': main()
