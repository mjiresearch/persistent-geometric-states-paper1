#!/usr/bin/env python3
"""Audit Barbieri+2005 (Ba05; astro-ph/0504534) Figure-3 H I radial profile route.

NGC4559 is calibration. The paper identifies Figure 3 right as the radial
neutral-hydrogen column-density profile. This script locates the source asset
from TeX and statically classifies it as vector/raster and inventories source
geometry. PostScript is never executed and no figure is digitized.
"""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URLS=['https://arxiv.org/e-print/astro-ph/0504534','https://export.arxiv.org/e-print/astro-ph/0504534'];UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/ba05_hi_profile_vector_route_v1.json')

def fetch():
 attempts=[]
 for u in URLS:
  rec={'url':u}
  try:
   req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
   with urllib.request.urlopen(req,timeout=180) as h:raw=h.read();rec.update(status='fetched',final_url=h.geturl(),content_type=h.headers.get('Content-Type',''),bytes=len(raw));attempts.append(rec);return raw,attempts
  except Exception as e:rec.update(status='error',error=f'{type(e).__name__}: {e}');attempts.append(rec)
 raise RuntimeError('Ba05 source fetch failed')
def psa(b):
 return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'image_ops':len(re.findall(rb'(?<![A-Za-z])image(?![A-Za-z])',b)),'colorimage_ops':b.count(b'colorimage'),'imagemask_ops':b.count(b'imagemask'),'moveto':b.count(b'moveto'),'lineto':b.count(b'lineto'),'rlineto':b.count(b'rlineto'),'curveto':b.count(b'curveto'),'stroke':b.count(b'stroke'),'fill':b.count(b'fill'),'one_letter':{x:len(re.findall(rb'(?<![A-Za-z0-9_])'+x.encode()+rb'(?![A-Za-z0-9_])',b)) for x in ['M','R','P','D','F','L','m','l','p','s']}}
def main():
 raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');files={m.name:tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
 tex={n:b.decode('latin-1','replace') for n,b in files.items() if n.lower().endswith('.tex')};contexts=[];cands=set()
 for n,t in tex.items():
  ls=t.splitlines()
  for i,line in enumerate(ls):
   low=line.lower()
   if ('global' in low and 'line' in low and 'column' in low and 'radial' in low) or ('figure 3' in low and 'radial' in low) or ('radial' in low and 'column density' in low):
    lo=max(0,i-16);hi=min(len(ls),i+18);ctx='\n'.join(f'{j+1}: {ls[j]}' for j in range(lo,hi));contexts.append({'tex':n,'line':i+1,'context':ctx[:12000]})
    for j in range(lo,hi):
     for mm in re.finditer(r'(?:includegraphics(?:\[[^\]]*\])?\{|epsfig\{[^}]*file=|psfig\{[^}]*figure=)([^},]+)',ls[j],re.I):
      base=mm.group(1).strip()
      for c in [base,base+'.eps',base+'.ps']:
       for fn in files:
        if fn==c or Path(fn).name==Path(c).name:cands.add(fn)
 for fn in files:
  if Path(fn).suffix.lower() in {'.eps','.ps'} and re.search(r'(fig.?3|f3|prof|dens|hi)',Path(fn).name,re.I):cands.add(fn)
 assets=[]
 for fn in sorted(cands):assets.append({'name':fn,'audit':psa(files[fn])})
 # inventory likely numeric sidecars too
 numeric=[]
 for fn,b in files.items():
  if Path(fn).suffix.lower() in {'.dat','.txt','.tbl','.csv','.tab'}:
   txt=b.decode('latin-1','replace');rows=sum(bool(re.match(r'^\s*[-+]?\d+(?:\.\d+)?\s+[-+]?\d',ln)) for ln in txt.splitlines());
   if rows>=5:numeric.append({'name':fn,'bytes':len(b),'numeric_rows':rows,'profile_words':[w for w in ['density','column','radius','profile','hi'] if w in txt.lower()]})
 out={'status':'BA05_HI_PROFILE_VECTOR_ROUTE_AUDIT_COMPLETE','source':'Barbieri et al. 2005 A&A 439 947; astro-ph/0504534','source_fetch_attempts':attempts,'source_package_sha256':hashlib.sha256(raw).hexdigest(),'n_source_files':len(files),'figure3_radial_profile_contexts':contexts,'candidate_profile_assets':assets,'numeric_sidecar_candidates':numeric,'decision_fields':{'n_candidate_profile_assets':len(assets),'any_vector_signal':any(a['audit']['lineto']+a['audit']['rlineto']+a['audit']['curveto']+a['audit']['one_letter']['R']+a['audit']['one_letter']['L']>20 for a in assets),'any_raster_signal':any(a['audit']['image_ops']+a['audit']['colorimage_ops']+a['audit']['imagemask_ops']>0 for a in assets),'n_numeric_sidecars':len(numeric)},'boundary':'Source-asset audit only; no PostScript execution, OCR, raster digitization, map/cube reconstruction, helium correction, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'assets':assets,'numeric':numeric,'decision_fields':out['decision_fields']},indent=2))
if __name__=='__main__':main()
