#!/usr/bin/env python3
"""Audit Jadhav & Banerjee 2019 source package for the kpc scale of Table 7.

Text/source provenance only. No profile transformation or persistence evaluation.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/1906.10039'
OUT=Path('validation/stationary/jadhav2019_scale_provenance_audit_v1.json')
UA='PersistenceFrameworkPaperI/1.0'
TERMS=['Table 3','Table 7','surface density','de Blok','F574','F583','F568','distance','HI']
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=90) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
 texts=[]; files=[]
 for m in tf.getmembers():
  if not m.isfile():continue
  files.append(m.name)
  if m.name.lower().endswith(('.tex','.txt','.dat','.csv')):
   b=tf.extractfile(m).read(); texts.append((m.name,b.decode('latin-1','replace')))
 contexts=[]
 for name,t in texts:
  lines=t.splitlines()
  for i,line in enumerate(lines):
   if any(term.lower() in line.lower() for term in TERMS):
    lo=max(0,i-3);hi=min(len(lines),i+4)
    contexts.append({'file':name,'line':i+1,'context':'\n'.join(lines[lo:hi])})
 result={'status':'JADHAV2019_SCALE_PROVENANCE_AUDITED','arxiv':ARXIV,'files':files,'contexts':contexts,
  'boundary':'Source-text provenance audit only; no profile transformation, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'files':files,'contexts':contexts[:120]},indent=2))
if __name__=='__main__':main()
