#!/usr/bin/env python3
"""Produce a compact, human-auditable geometry summary for NGC5907 in HEROES Fig. 29.

Fetches Allaert et al. 2015 source, opens Final_params_all.pdf with PyMuPDF,
prints all native words with coordinates and compact drawing statistics for the
rightmost sixth of the page. No scientific values are extracted or inferred.
"""
from __future__ import annotations
import io, json, tarfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import Request, urlopen
import pymupdf

URL='https://arxiv.org/e-print/1507.03095'
OUT=Path('validation/stationary/sa87_heroes_fig29_ngc5907_panel_summary_v1.json')

def fetch_pdf():
    with urlopen(Request(URL,headers={'User-Agent':'PaperI-SA87-panel/1.0'}),timeout=90) as r: payload=r.read()
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        for m in tf.getmembers():
            if m.isfile() and Path(m.name).name=='Final_params_all.pdf':
                f=tf.extractfile(m)
                if f:return f.read()
    raise RuntimeError('Final_params_all.pdf missing')

def rgbkey(c):
    if c is None:return None
    return tuple(round(float(x),4) for x in c)

def main():
    pdf=fetch_pdf(); doc=pymupdf.open(stream=pdf,filetype='pdf'); page=doc[0]
    W,H=page.rect.width,page.rect.height
    words=[]
    for w in page.get_text('words'):
        words.append({'x0':round(w[0],3),'y0':round(w[1],3),'x1':round(w[2],3),'y1':round(w[3],3),'cx':round((w[0]+w[2])/2,3),'cy':round((w[1]+w[3])/2,3),'text':w[4]})
    drawings=page.get_drawings()
    # Broad rightmost-column region; this is only a diagnostic summary.
    xmin=W*5/6-10; xmax=W+1
    broad=[]
    for i,d in enumerate(drawings):
        r=d['rect'];cx=(r.x0+r.x1)/2;cy=(r.y0+r.y1)/2
        if cx < xmin or cx > xmax:continue
        broad.append({'i':i,'rect':[round(r.x0,3),round(r.y0,3),round(r.x1,3),round(r.y1,3)],'cx':round(cx,3),'cy':round(cy,3),'type':d.get('type'),'color':rgbkey(d.get('color')),'fill':rgbkey(d.get('fill')),'width':round(float(d.get('width') or 0),4),'nitems':len(d.get('items',[]))})
    color_counts=Counter((str(x['color']),str(x['fill']),x['type'],x['width']) for x in broad)
    # Spatial bins by 1/10 page height and color to expose panel rows/series.
    bins=defaultdict(Counter)
    for x in broad:
        b=min(9,max(0,int(x['cy']/H*10)))
        bins[b][(str(x['color']),str(x['fill']),x['type'],x['width'])]+=1
    result={'status':'SA87_HEROES_NGC5907_PANEL_SUMMARY_COMPLETE','page_size':[round(W,3),round(H,3)],'words':words,'broad_rightmost_region':{'xmin':round(xmin,3),'xmax':round(xmax,3),'n_drawings':len(broad),'drawing_color_counts':[{'key':list(k),'count':v} for k,v in color_counts.most_common(80)],'height_bin_color_counts':{str(b):[{'key':list(k),'count':v} for k,v in c.most_common(40)] for b,c in sorted(bins.items())},'drawings':broad},'next_action':'Use native word positions to set exact NGC5907 column and Sigma_HI row bounds, then inventory only red/blue vector objects and native tick geometry in that panel.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
    print('PAGE',round(W,3),round(H,3))
    print('WORDS')
    for w in words:print(f"{w['x0']:8.3f} {w['y0']:8.3f} {w['x1']:8.3f} {w['y1']:8.3f}  {w['text']}")
    print('RIGHTMOST COLOR COUNTS')
    for k,v in color_counts.most_common(40):print(v,k)
    print('HEIGHT BINS')
    for b,c in sorted(bins.items()):
        print('BIN',b,'yrange',round(H*b/10,2),round(H*(b+1)/10,2))
        for k,v in c.most_common(15):print(' ',v,k)
    print('OUTPUT',OUT)
if __name__=='__main__':main()
