#!/usr/bin/env python3
"""One-pass public source-asset audit for Noordermeer et al. (2005), SPARC Ref No05.

No05 is a direct WHISP observing survey of 68 early-type disk galaxies and its
paper states that the appendix atlas contains radial H I surface-density
profiles for every galaxy. This audit checks whether the public arXiv source
package contains numerically reusable profile assets.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URL='https://export.arxiv.org/e-print/astro-ph/0508319'
UA='PersistenceFrameworkPaperI/1.0'


def fetch():
    req=Request(URL,headers={'User-Agent':UA})
    with urlopen(req,timeout=90) as r:
        return r.read(),r.headers.get('Content-Type','')


def sha(b): return hashlib.sha256(b).hexdigest()


def scan_text(name,text):
    pat=re.compile(r'radial|surface density|surface-density|H.?I|helium|1\.33|1\.4|profile|atlas|UGC|face.on|inclination',re.I)
    hits=[]
    for i,l in enumerate(text.splitlines(),1):
        if pat.search(l): hits.append({'line':i,'text':l[:900]})
        if len(hits)>=400: break
    return {'file':name,'hits':hits} if hits else None


def scan_vector(name,b):
    t=b.decode('latin-1',errors='replace')
    strings=re.findall(r'\(([^()]*)\)',t)
    useful=[s for s in strings if re.search(r'UGC|NGC|HI|Sigma|pc|kpc|arcsec|M.?sun|[0-9]{3,}',s,re.I)]
    return {
      'name':name,'bytes':len(b),'sha256':sha(b),
      'bounding_box_lines':[l[:300] for l in t.splitlines() if 'BoundingBox' in l][:8],
      'moveto_count':t.count('moveto'),'lineto_count':t.count('lineto'),
      'show_count':t.count('show'),'stroke_count':t.count('stroke'),
      'setrgbcolor_count':t.count('setrgbcolor'),
      'literal_string_count':len(strings),'useful_strings':useful[:200],
    }


def main():
    raw,ct=fetch(); tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
    files=[]; text_hits=[]; vectors=[]; tables=[]
    for m in tf.getmembers():
        if not m.isfile(): continue
        suf=Path(m.name).suffix.lower(); rec={'name':m.name,'bytes':m.size,'suffix':suf}; files.append(rec)
        b=tf.extractfile(m).read()
        if suf in {'.tex','.txt','.dat','.tbl','.tab','.csv'}:
            h=scan_text(m.name,b.decode('latin-1',errors='replace'))
            if h: text_hits.append(h)
            if suf in {'.dat','.tbl','.tab','.csv'}: tables.append(rec)
        if suf in {'.ps','.eps'}:
            vectors.append(scan_vector(m.name,b))
    out={
      'status':'NO05_ARXIV_ASSET_AUDIT_COMPLETE',
      'source':'Noordermeer et al. 2005 A&A 442 137-157; arXiv astro-ph/0508319',
      'arxiv_url':URL,'content_type':ct,'archive_bytes':len(raw),'archive_sha256':sha(raw),
      'n_files':len(files),'files':files,'machine_readable_table_assets':tables,
      'text_hits':text_hits,'postscript_assets':vectors,'n_postscript_assets':len(vectors),
      'interpretation_boundary':'Source-asset audit only. No radial values are promoted until galaxy identity, radius axis, surface-density quantity and geometry are unambiguous.'
    }
    p=Path('validation/stationary/no05_whisp_public_asset_audit_v1.json'); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({
      'status':out['status'],'n_files':out['n_files'],'tables':tables,
      'n_postscript_assets':out['n_postscript_assets'],
      'vector_names':[x['name'] for x in vectors],
      'text_hit_files':[x['file'] for x in text_hits]
    },indent=2))

if __name__=='__main__': main()
