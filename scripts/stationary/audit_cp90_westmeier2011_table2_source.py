#!/usr/bin/env python3
"""Audit Westmeier+2011 arXiv source for the exact NGC300 Table-2 gas profile.

Continuation of the CP90 branch. This does not revisit the 1990 scan. It inspects
the later higher-fidelity public ATCA replacement route (arXiv:1009.0317) and
records the native LaTeX/source rows around Table 2, especially radius and
Sigma_gas. No map reconstruction or figure digitization.
"""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URLS=['https://arxiv.org/e-print/1009.0317','https://export.arxiv.org/e-print/1009.0317'];UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/cp90_westmeier2011_table2_source_audit_v1.json')
def fetch():
 attempts=[]
 for u in URLS:
  rec={'url':u}
  try:
   req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/gzip,application/octet-stream,*/*;q=0.5'})
   with urllib.request.urlopen(req,timeout=180) as h:raw=h.read();rec.update(status='fetched',final_url=h.geturl(),content_type=h.headers.get('Content-Type',''),bytes=len(raw));attempts.append(rec);return raw,attempts
  except Exception as e:rec.update(status='error',error=f'{type(e).__name__}: {e}');attempts.append(rec)
 raise RuntimeError('Westmeier 2011 source fetch failed')
def main():
 raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');files={m.name:tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()};hits=[];numeric=[]
 for n,b in files.items():
  if Path(n).suffix.lower() not in {'.tex','.txt','.dat','.tbl','.csv','.tab'}:continue
  t=b.decode('latin-1','replace');ls=t.splitlines();low=t.lower()
  if any(k in low for k in ['sigma_{\\rm gas}','sigma_{gas}','sigma_gas','surface density','modelling parameters of ngc 300','modeling parameters of ngc 300']):
   for i,line in enumerate(ls):
    l=line.lower()
    if ('table' in l and ('model' in l or 'ngc 300' in l)) or 'sigma_{\\rm gas}' in l or 'sigma_{gas}' in l or 'surface density' in l:
     lo=max(0,i-18);hi=min(len(ls),i+70);hits.append({'asset':n,'line':i+1,'context':'\n'.join(f'{j+1}: {ls[j]}' for j in range(lo,hi))[:25000]})
  nr=[]
  for i,line in enumerate(ls,1):
   # Table rows with at least six ampersands and a numeric leading radius.
   if line.count('&')>=6 and re.match(r'^\s*[-+]?\d+(?:\.\d+)?\s*&',line):nr.append({'line':i,'text':line[:3000]})
  if nr:numeric.append({'asset':n,'rows':nr[:500]})
 out={'status':'CP90_WESTMEIER2011_TABLE2_SOURCE_AUDIT_COMPLETE','source':'Westmeier, Braun & Koribalski 2011 MNRAS 410 2217; arXiv:1009.0317','source_fetch_attempts':attempts,'source_package_sha256':hashlib.sha256(raw).hexdigest(),'n_files':len(files),'file_inventory':[{'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in files.items()],'table2_context_candidates':hits[:100],'multi_column_numeric_row_assets':numeric,'decision_fields':{'has_table_context':bool(hits),'has_native_multi_column_numeric_rows':bool(numeric)},'boundary':'Source-table audit only; no figure digitization, map/cube reconstruction, profile fitting, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'n_files':len(files),'decision_fields':out['decision_fields'],'numeric_assets':[(x['asset'],len(x['rows'])) for x in numeric],'contexts':[{'asset':x['asset'],'line':x['line'],'context':x['context'][:5000]} for x in hits[:8]]},indent=2))
if __name__=='__main__':main()
