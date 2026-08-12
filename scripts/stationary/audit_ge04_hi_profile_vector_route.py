#!/usr/bin/env python3
"""Audit Gentile+2004 (Ge04; astro-ph/0403154) radial HI profile figure.

The paper explicitly identifies Figure 2 as the radial neutral-hydrogen surface
density distribution for its five galaxies. Frozen targets are ESO079-G014
(calibration) and ESO116-G012 (blind). This script finds the Figure-2 source
asset from the authors' TeX and statically inventories its vector/raster
operators and source geometry. PostScript is never executed.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

URLS=['https://arxiv.org/e-print/astro-ph/0403154','https://export.arxiv.org/e-print/astro-ph/0403154']
UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/ge04_hi_profile_vector_route_v1.json')
TARGETS=['ESO 116-G12','ESO 79-G14']

def fetch():
 attempts=[]
 for u in URLS:
  rec={'url':u}
  try:
   req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
   with urllib.request.urlopen(req,timeout=180) as h:
    raw=h.read();rec.update(status='fetched',final_url=h.geturl(),content_type=h.headers.get('Content-Type',''),bytes=len(raw));attempts.append(rec);return raw,attempts
  except Exception as e:rec.update(status='error',error=f'{type(e).__name__}: {e}');attempts.append(rec)
 raise RuntimeError('Ge04 source fetch failed')

def compact(s):return re.sub(r'[^A-Z0-9]','',s.upper())
def ps_audit(b):
 text=b.decode('latin-1','replace')
 return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),
  'image_ops':len(re.findall(rb'(?<![A-Za-z])image(?![A-Za-z])',b)),
  'colorimage_ops':b.count(b'colorimage'),'imagemask_ops':b.count(b'imagemask'),
  'moveto_literal':b.count(b'moveto'),'lineto_literal':b.count(b'lineto'),'rlineto_literal':b.count(b'rlineto'),'curveto_literal':b.count(b'curveto'),
  'stroke_literal':b.count(b'stroke'),'fill_literal':b.count(b'fill'),'show_literal':b.count(b'show'),
  'one_letter_counts':{x:len(re.findall(rb'(?<![A-Za-z0-9_])'+x.encode()+rb'(?![A-Za-z0-9_])',b)) for x in ['M','R','P','D','F','L','m','l','p','s']},
  'bounding_box_lines':[ln for ln in text.splitlines() if 'BoundingBox' in ln][:20]}

def main():
 raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*'); members=[m for m in tf.getmembers() if m.isfile()]
 files={m.name:tf.extractfile(m).read() for m in members}
 tex={n:b.decode('latin-1','replace') for n,b in files.items() if n.lower().endswith('.tex')}
 figure2_contexts=[];candidate_assets=set()
 for n,t in tex.items():
  lines=t.splitlines()
  for i,line in enumerate(lines):
   low=line.lower()
   # capture explicit Fig 2 caption / HI radial-distribution neighborhood
   if ('radial distribution' in low and ('h i' in low or 'hi' in low or 'neutral hydrogen' in low)) or ('surface density' in low and 'figure' in low):
    lo=max(0,i-20);hi=min(len(lines),i+20);ctx='\n'.join(f'{j+1}: {lines[j]}' for j in range(lo,hi))
    figure2_contexts.append({'tex':n,'line':i+1,'context':ctx[:12000]})
    for j in range(lo,hi):
     for mm in re.finditer(r'(?:includegraphics(?:\[[^\]]*\])?\{|epsfig\{[^}]*file=|psfig\{[^}]*figure=)([^},]+)',lines[j],re.I):
      base=mm.group(1).strip()
      for c in [base,base+'.eps',base+'.ps']:
       for fn in files:
        if fn==c or Path(fn).name==Path(c).name:candidate_assets.add(fn)
 # also include any graphic named fig2/f2/profile/sigma-ish
 for fn in files:
  if Path(fn).suffix.lower() in {'.eps','.ps'} and re.search(r'(fig.?2|f2|surf|dens|sigma|hi)',Path(fn).name,re.I):candidate_assets.add(fn)
 assets=[]
 for fn in sorted(candidate_assets):
  b=files[fn];assets.append({'name':fn,'audit':ps_audit(b)})
 target_text={}
 for target in TARGETS:
  target_text[target]=[]
  for n,t in tex.items():
   lines=t.splitlines()
   for i,line in enumerate(lines):
    if compact(target) in compact(line):
     target_text[target].append({'tex':n,'line':i+1,'context':'\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-4),min(len(lines),i+6)))[:5000]})
 out={'status':'GE04_HI_PROFILE_VECTOR_ROUTE_AUDIT_COMPLETE','source':'Gentile et al. 2004 MNRAS 351 903; astro-ph/0403154',
  'source_fetch_attempts':attempts,'source_package_sha256':hashlib.sha256(raw).hexdigest(),'n_source_files':len(files),
  'figure2_contexts':figure2_contexts,'candidate_profile_assets':assets,'target_text_contexts':target_text,
  'decision_fields':{'n_candidate_profile_assets':len(assets),'any_raster_operator':any(a['audit']['image_ops']+a['audit']['colorimage_ops']+a['audit']['imagemask_ops']>0 for a in assets),'any_vector_path_signal':any(a['audit']['lineto_literal']+a['audit']['rlineto_literal']+a['audit']['curveto_literal']+a['audit']['one_letter_counts']['R']+a['audit']['one_letter_counts']['P']>20 for a in assets)},
  'boundary':'Source-native asset audit only. No PostScript execution, OCR, raster digitization, gas normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'n_files':len(files),'candidate_assets':assets,'decision_fields':out['decision_fields']},indent=2))
if __name__=='__main__':main()
