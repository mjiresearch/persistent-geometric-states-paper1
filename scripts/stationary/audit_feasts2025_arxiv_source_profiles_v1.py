#!/usr/bin/env python3
"""Audit Wang et al. 2025 FEASTS arXiv source for native radial-profile assets.

Acquisition/provenance audit only. Enumerates the public source tarball, scans
text-like files for NGC 3198/profile/table context, and identifies native numeric
assets. No raster/OCR extraction, persistence quantities, or blind outcomes.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen

URLS=['https://export.arxiv.org/e-print/2501.01289','https://arxiv.org/e-print/2501.01289']
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/feasts2025_arxiv_source_profile_audit_v1.json')
TEXT_EXT={'.tex','.txt','.dat','.csv','.tsv','.tbl','.table','.pro','.py','.md','.json'}
NUM_EXT={'.dat','.csv','.tsv','.txt','.tbl','.table','.fits','.fit','.npy','.npz'}
NEEDLES=('NGC3198','NGC 3198','NGC_3198','sigma_hi','Sigma_HI','surface density','radial profile','profile')

def fetch():
 errs=[]
 for u in URLS:
  try:
   with urlopen(Request(u,headers={'User-Agent':UA}),timeout=90) as h:return u,h.geturl(),h.headers.get('Content-Type',''),h.read(60_000_000)
  except Exception as e:errs.append({'url':u,'error':repr(e)})
 raise RuntimeError(errs)

def main():
 result={'status':'FEASTS2025_ARXIV_SOURCE_PROFILE_AUDITED','source_candidates':URLS}
 try:
  src,final,ct,b=fetch();result.update(source_url=src,final_url=final,content_type=ct,source_bytes=len(b))
  files=[];hits=[];numeric=[]
  with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as tf:
   for m in tf.getmembers():
    if not m.isfile():continue
    name=m.name;size=m.size;ext=Path(name).suffix.lower();files.append({'name':name,'bytes':size})
    if ext in NUM_EXT:numeric.append({'name':name,'bytes':size})
    if ext in TEXT_EXT and size<=8_000_000:
     f=tf.extractfile(m)
     if not f:continue
     t=f.read().decode('utf-8','replace')
     lines=t.splitlines()
     for i,line in enumerate(lines,1):
      if any(n.lower() in line.lower() for n in NEEDLES):
       context='\n'.join(lines[max(0,i-3):min(len(lines),i+2)])
       hits.append({'file':name,'line':i,'context':context[:5000]})
  result.update(files=files,n_files=len(files),numeric_assets=numeric,n_numeric_assets=len(numeric),profile_context_hits=hits,n_profile_context_hits=len(hits))
 except Exception as e:
  result.update(status='FEASTS2025_ARXIV_SOURCE_PROFILE_AUDIT_FAILED',error_type=type(e).__name__,error=str(e))
 result['boundary']='Public arXiv source/native-asset audit only; no raster digitization, persistence parameters, or blind outcomes.'
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'n_files':result.get('n_files'),'n_numeric_assets':result.get('n_numeric_assets'),'n_profile_context_hits':result.get('n_profile_context_hits')},indent=2))
if __name__=='__main__':main()
