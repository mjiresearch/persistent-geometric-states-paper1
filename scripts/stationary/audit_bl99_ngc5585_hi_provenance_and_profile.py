#!/usr/bin/env python3
"""Audit Bl99 / NGC5585 H I provenance and any exact republished profile asset.

The frozen target is blind, but this script inspects source provenance/assets only.
No rotation-fit outcome, persistence fit, OCR, raster digitization, or source execution.
"""
from __future__ import annotations
import csv, hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URLS=['https://arxiv.org/e-print/astro-ph/9911223','https://export.arxiv.org/e-print/astro-ph/9911223']
REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OUT=Path('validation/stationary/bl99_ngc5585_hi_provenance_profile_audit_v1.json')
TXT=Path('validation/stationary/bl99_ngc5585_hi_provenance_profile_audit_v1.txt')
UA='PaperI-Bl99-NGC5585-audit/1.0'

def sha(b):return hashlib.sha256(b).hexdigest()
def fetch():
    errs=[]
    for u in URLS:
        try:
            with urlopen(Request(u,headers={'User-Agent':UA}),timeout=60) as r:
                b=r.read();return b,{'requested_url':u,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':r.headers.get('Content-Type',''),'bytes':len(b),'sha256':sha(b)}
        except Exception as e:errs.append({'url':u,'error':repr(e)})
    raise RuntimeError(errs)
def is_text(n):return n.lower().endswith(('.tex','.ltx','.txt','.dat','.csv','.tab','.tbl','.bib','.bbl','.sty'))
def eps_info(b):
    s=b.decode('latin-1',errors='replace');low=s.lower()
    return {'bytes':len(b),'sha256':sha(b),'image_ops':len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',low)),'colorimage_ops':low.count('colorimage'),'imagemask_ops':low.count('imagemask'),'moveto_ops':low.count('moveto'),'lineto_ops':low.count('lineto'),'rlineto_ops':low.count('rlineto'),'stroke_ops':low.count('stroke'),'show_ops':low.count(' show'),'native_vector_candidate':('image' not in low and ('moveto' in low or 'lineto' in low))}
def contexts(text,patterns,window=650):
    out=[];seen=set()
    for p in patterns:
        for m in re.finditer(p,text,re.I|re.S):
            s=re.sub(r'\s+',' ',text[max(0,m.start()-window):min(len(text),m.end()+window)]).strip()
            if s not in seen:seen.add(s);out.append({'pattern':p,'context':s})
    return out[:100]

def main():
    with REF.open(newline='',encoding='utf-8-sig') as f:refs=list(csv.DictReader(f))
    target=[r for r in refs if r.get('galaxy')=='NGC5585' and r.get('sparc_ref_id')=='Bl99']
    if len(target)!=1 or target[0].get('stationary_role')!='blind':raise RuntimeError(f'Frozen Bl99 mapping changed: {target}')
    payload,meta=fetch();members=[];texts=[];blobs={}
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as tf:
        for m in tf.getmembers():
            if not m.isfile():continue
            f=tf.extractfile(m);b=f.read() if f else b'';blobs[m.name]=b
            members.append({'name':m.name,'bytes':len(b),'sha256':sha(b)})
            if is_text(m.name):texts.append((m.name,b.decode('latin-1',errors='replace')))
    pats=[r'C[oô]t[eé].{0,80}1991',r'Carignan.{0,80}Sancisi',r'Westerbork',r'21\s*cm',r'H\s*I\s+surface',r'HI\s+surface',r'gas\s+surface',r'surface\s+density',r'radial\s+profile',r'neutral\s+hydrogen',r'atomic\s+gas',r'helium',r'1\.33',r'1\.4']
    text_hits=[];graphics=[]
    for name,t in texts:
        hs=contexts(t,pats)
        for h in hs:h['file']=name
        text_hits.extend(hs)
        for g in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}|\\epsfbox\{([^}]+)\}',t,re.I):
            q=g[0] or g[1]
            if q:graphics.append(q)
    assets=[]
    for name,b in blobs.items():
        low=name.lower()
        if low.endswith(('.eps','.ps')):
            assets.append({'name':name,'structure':eps_info(b)})
        elif low.endswith(('.dat','.csv','.tab','.tbl','.txt')):
            txt=b.decode('latin-1',errors='replace')
            numeric_lines=sum(1 for line in txt.splitlines() if len(re.findall(r'[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?',line))>=2)
            assets.append({'name':name,'bytes':len(b),'sha256':sha(b),'numeric_like_lines':numeric_lines,'excerpt':re.sub(r'\s+',' ',txt)[:1200]})
        elif low.endswith(('.jpg','.jpeg','.png','.gif','.tif','.tiff')):
            assets.append({'name':name,'bytes':len(b),'sha256':sha(b),'raster_asset':True})
    # Find explicit bibliography entries containing likely upstream source authors/year.
    bib_hits=[]
    for name,t in texts:
        for line in t.splitlines():
            if ('1991' in line and ('Cote' in line or 'Cot' in line or 'Carignan' in line or 'Sancisi' in line)) or ('Westerbork' in line):
                bib_hits.append({'file':name,'line':line.strip()})
    result={'status':'BL99_NGC5585_HI_PROVENANCE_PROFILE_AUDIT_COMPLETE','galaxy':'NGC5585','stationary_role':'blind','sparc_ref_id':'Bl99','frozen_mapping':target[0],'source':meta,'n_members':len(members),'member_inventory':members,'graphics_references':sorted(set(graphics)),'text_contexts':text_hits,'bibliography_hits':bib_hits,'asset_structures':assets,'boundary':'Source acquisition/provenance only for frozen blind target. No blind rotation outcomes, persistence fits, OCR, raster digitization, profile fitting, or source execution. L_A and C_A remain locked.'}
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=[f"status={result['status']}",'SOURCE '+json.dumps(meta,sort_keys=True),f"members={len(members)}",'GRAPHICS '+json.dumps(result['graphics_references'])]
    for h in bib_hits:lines.append('BIB '+json.dumps(h,ensure_ascii=False))
    for h in text_hits:lines.append('CONTEXT '+json.dumps(h,ensure_ascii=False))
    for a in assets:lines.append('ASSET '+json.dumps(a,ensure_ascii=False,sort_keys=True))
    TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'members':len(members),'contexts':len(text_hits),'bib_hits':len(bib_hits),'assets':len(assets),'outputs':[str(OUT),str(TXT)]},indent=2))
if __name__=='__main__':main()
