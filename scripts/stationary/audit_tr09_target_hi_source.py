#!/usr/bin/env python3
"""Audit Trachternach+2009 arXiv source for D564-8 and D631-7 H I profiles."""
from pathlib import Path
import io, tarfile, urllib.request, hashlib, json, re

ARXIV='0907.5533'; URL=f'https://arxiv.org/e-print/{ARXIV}'
OUT=Path('validation/stationary/tr09_d5648_d6317_source_audit_v1.json')
CTX=Path('validation/stationary/tr09_d5648_d6317_source_context_v1.txt')
req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 PersistenceFrameworkPaperI/1.0'})
with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
members=[m for m in tf.getmembers() if m.isfile()]
names=[m.name for m in members]
contexts=[]; refs=[]; graphics=[]
for m in members:
    b=tf.extractfile(m).read(); low=m.name.lower()
    if low.endswith(('.tex','.txt','.bbl','.bib')):
        t=b.decode('latin-1','replace'); lines=t.splitlines()
        for i,line in enumerate(lines):
            hood='\n'.join(lines[max(0,i-10):min(len(lines),i+11)])
            if any(k.lower() in hood.lower() for k in ['D564-8','D631-7','surface density','column density','radial profile','H I distribution','HI distribution']):
                contexts.append({'file':m.name,'line':i+1,'context':'\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-10),min(len(lines),i+11)))})
                for r in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',hood):
                    refs.append({'tex_file':m.name,'near_line':i+1,'graphic_ref':r})
    if low.endswith(('.eps','.ps','.pdf','.png','.jpg','.jpeg','.gif','.tif','.tiff')):
        graphics.append({'name':m.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
# dedupe refs
u=[];seen=set()
for r in refs:
    k=(r['tex_file'],r['graphic_ref'])
    if k not in seen:seen.add(k);u.append(r)
refs=u

def resolve(ref):
    stem=Path(ref).stem
    for n in names:
        if n==ref or Path(n).stem==stem:return n
    return None
assets=[]
for r in refs:
    n=resolve(r['graphic_ref'])
    if not n:continue
    b=tf.extractfile(tf.getmember(n)).read(); low=n.lower(); z={'ref':r,'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    if low.endswith(('.eps','.ps')):
        t=b.decode('latin-1','replace')
        z.update({'type':'postscript','image_ops':len(re.findall(r'(?<![A-Za-z])image(?![A-Za-z])',t)),
                  'colorimage_ops':len(re.findall(r'(?<![A-Za-z])colorimage(?![A-Za-z])',t)),
                  'fill_tokens':len(re.findall(r'\b(?:fill|CircleF|TriUF|TriDF)\b',t)),
                  'path_tokens':len(re.findall(r'\b(?:moveto|lineto|rlineto|M|L|V|R)\b',t))})
        z['native_vector_candidate']=z['image_ops']==0 and z['colorimage_ops']==0 and z['path_tokens']>20
    elif low.endswith('.pdf'):
        t=b.decode('latin-1','replace'); imgs=len(re.findall(r'/Subtype\s*/Image',t))
        z.update({'type':'pdf','image_xobjects':imgs,'native_vector_candidate':imgs==0})
    else:z.update({'type':'raster','native_vector_candidate':False})
    assets.append(z)

CTX.parent.mkdir(parents=True,exist_ok=True)
CTX.write_text('\n\n'.join(f"===== {c['file']}:{c['line']} =====\n{c['context']}" for c in contexts)+'\n')
out={'status':'TR09_D5648_D6317_SOURCE_AUDIT_COMPLETE','arxiv':ARXIV,
     'source_package_sha256':hashlib.sha256(raw).hexdigest(),'n_members':len(members),'members':names,
     'target_contexts':contexts,'target_graphics_refs':refs,'resolved_assets':assets,'all_graphics':graphics,
     'next_gate':'inspect_target_asset_or_upstream_provenance_from_committed_audit',
     'boundary':'Source acquisition/provenance only; no rendering, OCR, raster digitization, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
OUT.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'refs':refs,'assets':assets,'n_contexts':len(contexts)},indent=2))
