#!/usr/bin/env python3
"""Inspect the HEROES-II Figure 29 PDF with PyMuPDF for exact vector recovery.

Requires PyMuPDF (fitz). Fetches the arXiv source, opens Final_params_all.pdf and
Final_params_all_flare.pdf, inventories text coordinates, raster images, and
vector drawing objects. This does not infer data values yet; it establishes
whether the NGC5907 Sigma_HI panel can be extracted source-natively.
"""
from __future__ import annotations
import hashlib, io, json, tarfile
from pathlib import Path
from urllib.request import Request, urlopen
import fitz

ARXIV='1507.03095'
URL=f'https://arxiv.org/e-print/{ARXIV}'
OUT=Path('validation/stationary/sa87_heroes_fig29_pdf_vector_inventory_v1.json')
CTX=Path('validation/stationary/sa87_heroes_fig29_pdf_vector_context_v1.txt')
TARGETS=['Final_params_all.pdf','Final_params_all_flare.pdf']

def h(b):return hashlib.sha256(b).hexdigest()
def fetch():
    with urlopen(Request(URL,headers={'User-Agent':'PaperI-SA87-vector/1.0'}),timeout=90) as r:return r.read(),r.geturl()
def unpack(payload):
    out={}
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        for m in tf.getmembers():
            if m.isfile() and Path(m.name).name in TARGETS:
                f=tf.extractfile(m)
                if f:out[Path(m.name).name]=f.read()
    return out

def compact_drawing(d):
    items=[]
    for it in d.get('items',[]):
        typ=it[0]
        vals=[]
        for v in it[1:]:
            if isinstance(v,fitz.Point):vals.append([round(v.x,4),round(v.y,4)])
            elif isinstance(v,fitz.Rect):vals.append([round(v.x0,4),round(v.y0,4),round(v.x1,4),round(v.y1,4)])
            elif isinstance(v,(int,float)):vals.append(round(float(v),4))
            else:vals.append(str(v))
        items.append([typ,*vals])
    c={
      'rect':[round(x,4) for x in d['rect']],
      'type':d.get('type'),'fill':d.get('fill'),'color':d.get('color'),
      'width':d.get('width'),'closePath':d.get('closePath'),'even_odd':d.get('even_odd'),
      'items':items[:80],
    }
    return c

def inspect(name,b):
    doc=fitz.open(stream=b,filetype='pdf')
    pages=[]
    for pi,page in enumerate(doc):
        words=page.get_text('words')
        text_words=[{'x0':round(w[0],3),'y0':round(w[1],3),'x1':round(w[2],3),'y1':round(w[3],3),'text':w[4],'block':w[5],'line':w[6],'word':w[7]} for w in words]
        images=page.get_images(full=True)
        drawings=page.get_drawings()
        # Preserve all drawing bounding boxes and item content; Figure 29 is compact.
        pages.append({
          'page_index':pi,'rect':[round(x,3) for x in page.rect],
          'n_words':len(words),'words':text_words,
          'n_images':len(images),'images':[list(x) for x in images],
          'n_drawings':len(drawings),'drawings':[compact_drawing(d) for d in drawings],
        })
    return {'name':name,'bytes':len(b),'sha256':h(b),'page_count':len(doc),'pages':pages}

def main():
    payload,url=fetch();files=unpack(payload)
    missing=[x for x in TARGETS if x not in files]
    if missing:raise RuntimeError(f'Missing target PDFs: {missing}')
    inv=[inspect(n,files[n]) for n in TARGETS]
    result={
      'status':'SA87_HEROES_FIG29_PDF_VECTOR_INVENTORY_COMPLETE',
      'source':'Allaert et al. 2015 A&A 582 A18; arXiv:1507.03095',
      'arxiv_source_url':url,'source_sha256':h(payload),
      'files':inv,
      'decision':{
        'final_params_has_zero_raster_images':all(p['n_images']==0 for f in inv if f['name']=='Final_params_all.pdf' for p in f['pages']),
        'final_params_has_vector_drawings':any(p['n_drawings']>0 for f in inv if f['name']=='Final_params_all.pdf' for p in f['pages']),
        'next_action':'Use native text coordinates to locate NGC5907 column and Sigma_HI top panel; classify vector path/marker geometry inside that panel, then calibrate axes and recover source series if unambiguous.'
      },
      'boundary':'Static PDF parsing only. No raster digitization, OCR, PDF execution, map/cube reconstruction, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,default=str)+'\n')
    lines=[]
    for f in inv:
        lines += [f"=== {f['name']} bytes={f['bytes']} sha={f['sha256']} ==="]
        for p in f['pages']:
            lines += [f"page {p['page_index']} rect={p['rect']} images={p['n_images']} drawings={p['n_drawings']} words={p['n_words']}", 'TEXT WORDS:']
            lines += [f"{w['x0']:.3f} {w['y0']:.3f} {w['x1']:.3f} {w['y1']:.3f}  {w['text']}" for w in p['words']]
            lines += ['DRAWING RECTS:']+[f"{i}: rect={d['rect']} type={d['type']} fill={d['fill']} color={d['color']} width={d['width']} nitems={len(d['items'])}" for i,d in enumerate(p['drawings'])]
    CTX.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':result['status'],'summary':[{'name':f['name'],'pages':[{'images':p['n_images'],'drawings':p['n_drawings'],'words':p['n_words']} for p in f['pages']]} for f in inv],'decision':result['decision'],'outputs':[str(OUT),str(CTX)]},indent=2))
if __name__=='__main__':main()
