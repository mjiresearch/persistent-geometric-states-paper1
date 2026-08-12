#!/usr/bin/env python3
"""One-pass public source-asset audit for Swaters et al. (2002), SPARC Ref Sw02.

Acquisition/provenance only. No profile normalization or persistence fitting.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URL='https://export.arxiv.org/e-print/astro-ph/0204525'
UA='PersistenceFrameworkPaperI/1.0'


def fetch():
    req=Request(URL,headers={'User-Agent':UA})
    with urlopen(req,timeout=90) as r:
        return r.read(), r.headers.get('Content-Type','')


def sha(b): return hashlib.sha256(b).hexdigest()


def scan_text(name,text):
    pat=re.compile(r'radial|surface density|surface-density|H.?I|helium|1\.33|1\.4|profile|UGC|DDO',re.I)
    hits=[]
    for i,l in enumerate(text.splitlines(),1):
        if pat.search(l): hits.append({'line':i,'text':l[:700]})
        if len(hits)>=250: break
    return {'file':name,'hits':hits} if hits else None


def scan_ps(name,b):
    t=b.decode('latin-1',errors='replace')
    # Structural signals only; no coordinates promoted in this audit.
    ugc=sorted(set(re.findall(r'UGC\s*0*([0-9]{2,5})',t,re.I)))
    ddo=sorted(set(re.findall(r'DDO\s*0*([0-9]{1,3})',t,re.I)))
    return {
        'name':name,'bytes':len(b),'sha256':sha(b),
        'bounding_box_lines':[l[:250] for l in t.splitlines() if 'BoundingBox' in l][:8],
        'has_setrgbcolor':'setrgbcolor' in t,
        'has_moveto_lineto':('moveto' in t and 'lineto' in t),
        'ugc_labels':ugc[:100],'ddo_labels':ddo[:100],
        'surface_density_text':bool(re.search(r'surface\s*density|Sigma',t,re.I)),
    }


def main():
    raw,ct=fetch(); tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    files=[]; text=[]; vectors=[]
    for m in tf.getmembers():
        if not m.isfile(): continue
        suf=Path(m.name).suffix.lower(); rec={'name':m.name,'bytes':m.size,'suffix':suf}; files.append(rec)
        b=tf.extractfile(m).read()
        if suf in {'.tex','.txt','.dat','.tbl'}:
            h=scan_text(m.name,b.decode('latin-1',errors='replace'))
            if h: text.append(h)
        if suf in {'.ps','.eps'}:
            vectors.append(scan_ps(m.name,b))
    out={
      'status':'SW02_ARXIV_ASSET_AUDIT_COMPLETE',
      'source':'Swaters et al. 2002 A&A 390 829-861; arXiv astro-ph/0204525',
      'arxiv_url':URL,'content_type':ct,'archive_bytes':len(raw),'archive_sha256':sha(raw),
      'n_files':len(files),'files':files,'text_hits':text,'postscript_assets':vectors,
      'n_postscript_assets':len(vectors),
      'interpretation_boundary':'Asset audit only. No numerical HI profile is promoted until its galaxy identity, axes, source quantity and curve geometry are unambiguous.'
    }
    p=Path('validation/stationary/sw02_whisp_public_asset_audit_v1.json'); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({
      'status':out['status'],'n_files':out['n_files'],'n_postscript_assets':out['n_postscript_assets'],
      'vector_names':[x['name'] for x in vectors],
      'text_hit_files':[x['file'] for x in text]
    },indent=2))

if __name__=='__main__': main()
