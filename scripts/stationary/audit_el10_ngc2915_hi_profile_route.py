#!/usr/bin/env python3
"""Audit Elson+2010 (El10; arXiv:1002.0403) NGC2915 radial H I profile route.

The paper explicitly constructs an azimuthally averaged, inclination-corrected
H I surface-density profile in 17-arcsec rings and shows it in Figure 5. This
script identifies the authors' Figure-5 source asset, inventories native numeric
sidecars, and statically classifies PS/EPS assets as vector/raster. PostScript
is never executed and figures are never digitized.
"""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URLS=['https://arxiv.org/e-print/1002.0403','https://export.arxiv.org/e-print/1002.0403'];UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/el10_ngc2915_hi_profile_route_v1.json')

def fetch():
 attempts=[]
 for u in URLS:
  rec={'url':u}
  try:
   req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
   with urllib.request.urlopen(req,timeout=180) as h:raw=h.read();rec.update(status='fetched',final_url=h.geturl(),content_type=h.headers.get('Content-Type',''),bytes=len(raw));attempts.append(rec);return raw,attempts
  except Exception as e:rec.update(status='error',error=f'{type(e).__name__}: {e}');attempts.append(rec)
 raise RuntimeError('El10 source fetch failed')
def psa(b):
 return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'image_ops':len(re.findall(rb'(?<![A-Za-z])image(?![A-Za-z])',b)),'colorimage_ops':b.count(b'colorimage'),'imagemask_ops':b.count(b'imagemask'),'moveto':b.count(b'moveto'),'lineto':b.count(b'lineto'),'rlineto':b.count(b'rlineto'),'curveto':b.count(b'curveto'),'stroke':b.count(b'stroke'),'fill':b.count(b'fill'),'one_letter':{x:len(re.findall(rb'(?<![A-Za-z0-9_])'+x.encode()+rb'(?![A-Za-z0-9_])',b)) for x in ['M','R','P','D','F','L','m','l','p','s']}}
def main():
 raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');files={m.name:tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
 tex={n:b.decode('latin-1','replace') for n,b in files.items() if n.lower().endswith('.tex')};contexts=[];cands=set()
 for n,t in tex.items():
  ls=t.splitlines()
  for i,line in enumerate(ls):
   low=line.lower().replace('h~i','hi')
   if ('surface density' in low and ('profile' in low or 'fig' in low)) or ('17' in low and 'arcsec' in low and 'ring' in low):
    lo=max(0,i-18);hi=min(len(ls),i+22);ctx='\n'.join(f'{j+1}: {ls[j]}' for j in range(lo,hi));contexts.append({'tex':n,'line':i+1,'context':ctx[:16000]})
    for j in range(lo,hi):
     for mm in re.finditer(r'(?:includegraphics(?:\[[^\]]*\])?\{|epsfig\{[^}]*file=|psfig\{[^}]*figure=)([^},]+)',ls[j],re.I):
      base=mm.group(1).strip()
      for c in [base,base+'.eps',base+'.ps',base+'.pdf']:
       for fn in files:
        if fn==c or Path(fn).name==Path(c).name:cands.add(fn)
 for fn in files:
  if Path(fn).suffix.lower() in {'.eps','.ps','.pdf'} and re.search(r'(fig.?5|f5|surf|dens|profile|prof)',Path(fn).name,re.I):cands.add(fn)
 assets=[]
 for fn in sorted(cands):
  b=files[fn];ext=Path(fn).suffix.lower();rec={'name':fn,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'extension':ext,'magic_hex':b[:16].hex()}
  if ext in {'.eps','.ps'}:rec['ps_audit']=psa(b)
  assets.append(rec)
 numeric=[]
 for fn,b in files.items():
  if Path(fn).suffix.lower() in {'.dat','.txt','.tbl','.csv','.tab'}:
   t=b.decode('latin-1','replace');nr=sum(bool(re.match(r'^\s*[-+]?\d+(?:\.\d+)?\s+[-+]?\d',ln)) for ln in t.splitlines())
   if nr>=5:numeric.append({'name':fn,'bytes':len(b),'numeric_rows':nr,'profile_words':[w for w in ['surface','density','radius','profile','hi'] if w in t.lower()]})
 inventory=[{'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'suffixes':Path(n).suffixes} for n,b in files.items()]
 out={'status':'EL10_NGC2915_HI_PROFILE_ROUTE_AUDIT_COMPLETE','source':'Elson, de Blok & Kraan-Korteweg 2010 MNRAS 404 2061; arXiv:1002.0403','source_fetch_attempts':attempts,'source_package_sha256':hashlib.sha256(raw).hexdigest(),'n_source_files':len(files),'file_inventory':inventory,'profile_contexts':contexts,'candidate_profile_assets':assets,'numeric_sidecar_candidates':numeric,'decision_fields':{'n_candidate_profile_assets':len(assets),'n_numeric_sidecars':len(numeric),'any_ps_vector_signal':any(a.get('ps_audit',{}).get('lineto',0)+a.get('ps_audit',{}).get('rlineto',0)+a.get('ps_audit',{}).get('curveto',0)+a.get('ps_audit',{}).get('one_letter',{}).get('R',0)+a.get('ps_audit',{}).get('one_letter',{}).get('L',0)>20 for a in assets),'any_ps_raster_signal':any(a.get('ps_audit',{}).get('image_ops',0)+a.get('ps_audit',{}).get('colorimage_ops',0)+a.get('ps_audit',{}).get('imagemask_ops',0)>0 for a in assets)},'boundary':'Source-asset audit only; no rendering, PostScript execution, OCR, raster digitization, map/cube reconstruction, helium correction, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'n_files':len(files),'assets':assets,'numeric':numeric,'decision_fields':out['decision_fields'],'contexts':contexts[:4]},indent=2))
if __name__=='__main__':main()
