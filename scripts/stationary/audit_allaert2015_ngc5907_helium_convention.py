#!/usr/bin/env python3
"""Audit Allaert+2015 source text for the H I surface-density helium convention.

Text provenance only; no profile conversion or persistence evaluation.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/1507.03095'; UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/allaert2015_ngc5907_helium_convention_v1.json')
PATTERNS=[r'helium',r'1\.33',r'1\.36',r'1\.4',r'H.?I surface density',r'surface density',r'column density',r'H.?I mass',r'atomic gas',r'M_\{?H']
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=90) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*'); contexts=[]; files=[]
 for m in tf.getmembers():
  if not m.isfile():continue
  files.append(m.name)
  if not m.name.lower().endswith(('.tex','.txt')):continue
  t=tf.extractfile(m).read().decode('latin-1','replace'); lines=t.splitlines()
  for i,line in enumerate(lines):
   if any(re.search(p,line,re.I) for p in PATTERNS):
    contexts.append({'file':m.name,'line':i+1,'context':'\n'.join(lines[max(0,i-3):min(len(lines),i+4)])})
 result={'status':'ALLAERT2015_NGC5907_HELIUM_CONVENTION_AUDITED','arxiv':ARXIV,'files':files,'contexts':contexts,
  'boundary':'Source-text convention audit only; no profile conversion, interpolation, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'contexts':contexts},indent=2))
if __name__=='__main__':main()
