#!/usr/bin/env python3
"""Inspect the public arXiv source of HIX survey II for an exact NGC289 H I profile route.

This is a bounded later-direct-observation rescue audit for Wa97 / NGC0289.
No OCR, raster digitization, or source execution is performed.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

import fitz

URLS=['https://arxiv.org/e-print/1802.04043','https://export.arxiv.org/e-print/1802.04043']
OUT=Path('validation/stationary/hix2018_ngc289_native_profile_route_v1.json')
TXT=Path('validation/stationary/hix2018_ngc289_native_profile_route_v1.txt')
UA='PaperI-HIX-NGC289-profile-audit/1.0'

def sha(b): return hashlib.sha256(b).hexdigest()

def fetch():
    errs=[]
    for u in URLS:
        try:
            with urlopen(Request(u,headers={'User-Agent':UA}),timeout=60) as r:
                b=r.read(); return b,{'requested_url':u,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':r.headers.get('Content-Type',''),'bytes':len(b),'sha256':sha(b)}
        except Exception as e: errs.append({'url':u,'error':repr(e)})
    raise RuntimeError(errs)

def is_text(name):
    return name.lower().endswith(('.tex','.ltx','.txt','.dat','.csv','.tab','.tbl','.def','.par','.cfg','.ini','.lis'))

def eps_info(b):
    s=b.decode('latin-1',errors='replace')
    low=s.lower()
    return {'bytes':len(b),'sha256':sha(b),'image_ops':len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',low)),
            'colorimage_ops':low.count('colorimage'),'imagemask_ops':low.count('imagemask'),
            'moveto_ops':low.count('moveto'),'lineto_ops':low.count('lineto'),'rlineto_ops':low.count('rlineto'),
            'stroke_ops':low.count('stroke'),'show_ops':low.count(' show'),'native_vector_candidate':('image' not in low and ('moveto' in low or 'lineto' in low))}

def pdf_info(b):
    d=fitz.open(stream=b,filetype='pdf')
    return {'bytes':len(b),'sha256':sha(b),'pages':len(d),'n_images':sum(len(p.get_images(full=True)) for p in d),
            'n_drawings':sum(len(p.get_drawings()) for p in d),'text_chars':sum(len(p.get_text('text') or '') for p in d)}

def main():
    payload,meta=fetch()
    members=[]; texts=[]; blobs={}
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        for m in tf.getmembers():
            if not m.isfile(): continue
            f=tf.extractfile(m); b=f.read() if f else b''
            blobs[m.name]=b
            members.append({'name':m.name,'bytes':len(b),'sha256':sha(b)})
            if is_text(m.name): texts.append((m.name,b.decode('latin-1',errors='replace')))
    contexts=[]; referenced=[]
    for name,t in texts:
        low=t.lower()
        if 'ngc289' in low or 'ngc 289' in low or 'ngc\u2009289' in low:
            for m in re.finditer(r'ngc\s*289|ngc289',t,re.I):
                lo=max(0,m.start()-500);hi=min(len(t),m.end()+900)
                contexts.append({'file':name,'context':re.sub(r'\s+',' ',t[lo:hi]).strip()})
            # graphics references near NGC289 or any filename containing NGC289
            for g in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',t,re.I):
                if '289' in g.lower(): referenced.append(g)
    candidates=[]
    for name,b in blobs.items():
        low=name.lower()
        if '289' in low or any(Path(r).name.lower() in low or low in Path(r).name.lower() for r in referenced):
            ent={'name':name,'bytes':len(b),'sha256':sha(b)}
            try:
                if low.endswith(('.eps','.ps')): ent['structure']=eps_info(b)
                elif low.endswith('.pdf'): ent['structure']=pdf_info(b)
                elif low.endswith(('.jpg','.jpeg','.png','.gif','.tif','.tiff')): ent['structure']={'raster_asset':True}
                elif is_text(name):
                    text=b.decode('latin-1',errors='replace')
                    ent['text_excerpt']=re.sub(r'\s+',' ',text)[:2500]
            except Exception as e: ent['inspect_error']=repr(e)
            candidates.append(ent)
    # also classify all likely appendix/overview figures because filename may be opaque
    for name,b in blobs.items():
        low=name.lower()
        if any(k in low for k in ['figa3','fig_a3','appendix','overview']) and not any(c['name']==name for c in candidates):
            ent={'name':name,'bytes':len(b),'sha256':sha(b)}
            try:
                if low.endswith(('.eps','.ps')): ent['structure']=eps_info(b)
                elif low.endswith('.pdf'): ent['structure']=pdf_info(b)
                elif low.endswith(('.jpg','.jpeg','.png','.gif','.tif','.tiff')): ent['structure']={'raster_asset':True}
            except Exception as e: ent['inspect_error']=repr(e)
            candidates.append(ent)
    data_like=[m for m in members if m['name'].lower().endswith(('.dat','.csv','.tab','.tbl','.txt','.par'))]
    result={'status':'HIX2018_NGC289_SOURCE_PACKAGE_AUDIT_COMPLETE','source':meta,'n_members':len(members),
            'ngc289_contexts':contexts[:30],'graphics_references':sorted(set(referenced)),
            'candidate_assets':candidates,'data_like_members':data_like,
            'boundary':'Later direct ATCA observation rescue route only. No OCR, raster digitization, source execution, persistence fitting, or blind-outcome inspection.'}
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=[f"status={result['status']}",'SOURCE '+json.dumps(meta,sort_keys=True),f"members={len(members)}",'GRAPHICS '+json.dumps(result['graphics_references'])]
    for c in candidates: lines.append('CANDIDATE '+json.dumps(c,sort_keys=True))
    for c in contexts[:20]: lines.append('CONTEXT '+json.dumps(c,ensure_ascii=False))
    lines.append('DATA_LIKE '+json.dumps(data_like,sort_keys=True))
    TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'members':len(members),'candidates':len(candidates),'data_like':len(data_like),'outputs':[str(OUT),str(TXT)]},indent=2))

if __name__=='__main__': main()
