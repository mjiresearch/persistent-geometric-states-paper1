#!/usr/bin/env python3
"""One-pass source/asset audit for de Blok et al. 1996 (SPARC dB96).

Determines which figures/tables contain radial H I profile information and
whether the public arXiv package preserves reusable numerical/vector assets.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URL='https://export.arxiv.org/e-print/astro-ph/9605069'
UA='PersistenceFrameworkPaperI/1.0'


def fetch():
    req=Request(URL,headers={'User-Agent':UA})
    with urlopen(req,timeout=90) as r: return r.read(),r.headers.get('Content-Type','')


def sha(b): return hashlib.sha256(b).hexdigest()


def main():
    raw,ct=fetch(); tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    files=[]; texts=[]; vectors=[]
    pat=re.compile(r'figure|fig\.|surface density|surface-density|radial|H.?I|helium|1\.33|1\.4|profile|column density|UGC|F5',re.I)
    for m in tf.getmembers():
        if not m.isfile(): continue
        suf=Path(m.name).suffix.lower(); files.append({'name':m.name,'bytes':m.size,'suffix':suf})
        b=tf.extractfile(m).read()
        if suf in {'.tex','.txt','.dat','.tbl','.tab','.csv'}:
            txt=b.decode('latin-1','replace'); hits=[]
            for i,l in enumerate(txt.splitlines(),1):
                if pat.search(l): hits.append({'line':i,'text':l[:1000]})
            if hits: texts.append({'file':m.name,'hits':hits[:600]})
        if suf in {'.ps','.eps'}:
            t=b.decode('latin-1','replace'); strings=re.findall(r'\(([^()]*)\)',t)
            vectors.append({
              'name':m.name,'bytes':len(b),'sha256':sha(b),
              'bounding_box_lines':[l[:300] for l in t.splitlines() if 'BoundingBox' in l][:10],
              'moveto_count':t.count('moveto'),'lineto_count':t.count('lineto'),
              'show_count':t.count('show'),'stroke_count':t.count('stroke'),
              'literal_string_count':len(strings),
              'useful_strings':[s for s in strings if re.search(r'UGC|NGC|HI|Sigma|pc|kpc|arc|F5|[0-9]{3,}',s,re.I)][:200]
            })
    out={
      'status':'DB96_ARXIV_ASSET_AUDIT_COMPLETE',
      'source':'de Blok, McGaugh & van der Hulst 1996 MNRAS 283 18-54; arXiv astro-ph/9605069',
      'arxiv_url':URL,'content_type':ct,'archive_bytes':len(raw),'archive_sha256':sha(raw),
      'files':files,'text_hits':texts,'postscript_assets':vectors,
      'interpretation_boundary':'Asset/provenance audit only. No profile values are promoted until the source figure/table and physical axes are unambiguous.'
    }
    p=Path('validation/stationary/db96_hi_public_asset_audit_v1.json'); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'files':files,'vector_names':[v['name'] for v in vectors],'text_hit_files':[x['file'] for x in texts]},indent=2))

if __name__=='__main__': main()
