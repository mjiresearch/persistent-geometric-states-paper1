#!/usr/bin/env python3
"""Audit Leroy+2008 source text for H I surface-density inclination handling.

Source-text convention audit only; no science pixels or persistence quantities.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/0810.2556';UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/leroy2008_hi_inclination_convention_v1.json')
PAT=[r'cos\s*\(?i',r'inclination',r'face.?on',r'surface density',r'Sigma_\{?HI',r'HI.*map',r'deproject']
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');contexts=[];files=[]
 for m in tf.getmembers():
  if not m.isfile():continue
  files.append(m.name)
  if not m.name.lower().endswith(('.tex','.txt')):continue
  t=tf.extractfile(m).read().decode('latin-1','replace');lines=t.splitlines()
  for i,line in enumerate(lines):
   if any(re.search(p,line,re.I) for p in PAT):
    contexts.append({'file':m.name,'line':i+1,'context':'\n'.join(lines[max(0,i-4):min(len(lines),i+5)])})
 result={'status':'LEROY2008_HI_INCLINATION_CONVENTION_AUDITED','arxiv':ARXIV,'files':files,'contexts':contexts,
  'boundary':'Source-text convention audit only; no science pixels, profile extraction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'contexts':contexts},indent=2))
if __name__=='__main__':main()
