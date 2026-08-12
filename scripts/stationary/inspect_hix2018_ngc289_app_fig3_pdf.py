#!/usr/bin/env python3
"""Inspect the exact HIX2018 NGC289 appendix PDF (Images/app-fig3.pdf)."""
from __future__ import annotations
import collections, hashlib, io, json, tarfile
from pathlib import Path
from urllib.request import Request, urlopen
import fitz

URL='https://arxiv.org/e-print/1802.04043'
MEMBER='Images/app-fig3.pdf'
OUT=Path('validation/stationary/hix2018_ngc289_app_fig3_native_structure_v1.json')
TXT=Path('validation/stationary/hix2018_ngc289_app_fig3_native_structure_v1.txt')
UA='PaperI-HIX-NGC289-appfig3/1.0'

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=60) as r: payload=r.read(); final=r.geturl()
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        m=tf.getmember(MEMBER); f=tf.extractfile(m); b=f.read() if f else b''
    d=fitz.open(stream=b,filetype='pdf'); p=d[0]
    words=[]
    for w in p.get_text('words'):
        x0,y0,x1,y1,text,*rest=w
        words.append({'x0':round(x0,3),'y0':round(y0,3),'x1':round(x1,3),'y1':round(y1,3),
                      'cx':round((x0+x1)/2,3),'cy':round((y0+y1)/2,3),'text':text})
    drawings=p.get_drawings()
    ds=[]; color_counts=collections.Counter(); fill_counts=collections.Counter(); type_counts=collections.Counter()
    for i,x in enumerate(drawings):
        rect=x.get('rect'); color=x.get('color'); fill=x.get('fill'); typ=x.get('type');
        def ckey(v):
            if v is None:return 'None'
            return ','.join(f'{q:.4f}' for q in v)
        color_counts[ckey(color)]+=1;fill_counts[ckey(fill)]+=1;type_counts[str(typ)]+=1
        item={'i':i,'type':typ,'color':color,'fill':fill,'width':x.get('width'),'closePath':x.get('closePath'),
              'rect':[round(rect.x0,3),round(rect.y0,3),round(rect.x1,3),round(rect.y1,3)] if rect else None,
              'n_items':len(x.get('items',[]))}
        # retain compact primitive endpoints for small paths likely markers/lines
        if len(x.get('items',[]))<=8:
            prim=[]
            for z in x.get('items',[]):
                vals=[]
                for v in z:
                    if hasattr(v,'x') and hasattr(v,'y'): vals.append([round(v.x,3),round(v.y,3)])
                    elif hasattr(v,'x0') and hasattr(v,'y0'): vals.append([round(v.x0,3),round(v.y0,3),round(v.x1,3),round(v.y1,3)])
                    else: vals.append(v)
                prim.append(vals)
            item['items']=prim
        ds.append(item)
    imgs=[]
    for im in p.get_images(full=True):
        xref=im[0]
        rects=p.get_image_rects(xref)
        imgs.append({'xref':xref,'width':im[2],'height':im[3],'bpc':im[4],
                     'rects':[[round(r.x0,3),round(r.y0,3),round(r.x1,3),round(r.y1,3)] for r in rects]})
    result={'status':'HIX2018_NGC289_APP_FIG3_NATIVE_STRUCTURE_COMPLETE',
            'source_package':{'url':final,'bytes':len(payload),'sha256':sha(payload)},
            'member':MEMBER,'member_bytes':len(b),'member_sha256':sha(b),
            'page_rect':[p.rect.x0,p.rect.y0,p.rect.x1,p.rect.y1],
            'n_words':len(words),'words':words,'n_images':len(imgs),'images':imgs,
            'n_drawings':len(drawings),'drawing_type_counts':dict(type_counts),
            'stroke_color_counts':dict(color_counts),'fill_color_counts':dict(fill_counts),
            'drawings':ds,
            'boundary':'Static PDF structure only; no OCR/raster digitization or source execution.'}
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=[f"status={result['status']}",f"member={MEMBER} bytes={len(b)} sha256={sha(b)}",f"page_rect={result['page_rect']}",
           f"words={len(words)} images={len(imgs)} drawings={len(drawings)}",'IMAGES '+json.dumps(imgs),
           'STROKES '+json.dumps(dict(color_counts),sort_keys=True),'FILLS '+json.dumps(dict(fill_counts),sort_keys=True),'TYPES '+json.dumps(dict(type_counts),sort_keys=True)]
    for w in words: lines.append('WORD '+json.dumps(w,ensure_ascii=False))
    for x in ds: lines.append('DRAW '+json.dumps(x,ensure_ascii=False))
    TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'words':len(words),'images':len(imgs),'drawings':len(drawings),'member_bytes':len(b),'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
