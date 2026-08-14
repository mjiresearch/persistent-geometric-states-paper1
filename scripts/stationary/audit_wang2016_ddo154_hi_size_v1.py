#!/usr/bin/env python3
"""Extract DDO154 H I size information from Wang+2016 arXiv source tables.

Published-source metadata audit only; no profile reconstruction, persistence
parameters, or blind outcomes.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/1605.01489';UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/wang2016_ddo154_hi_size_audit_v1.json')
TARGETS=['DDO154','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793','IC2574']
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*'); contexts=[];files=[]
 for m in tf.getmembers():
  if not m.isfile():continue
  files.append(m.name)
  if not m.name.lower().endswith(('.tex','.txt','.dat','.csv','.tab','.tbl')):continue
  t=tf.extractfile(m).read().decode('latin-1','replace');lines=t.splitlines()
  for i,line in enumerate(lines):
   matched=[g for g in TARGETS if re.search(re.escape(g.replace('NGC','NGC ')),line,re.I) or re.search(re.escape(g),line,re.I)]
   if matched:
    contexts.append({'file':m.name,'line':i+1,'targets':matched,'context':'\n'.join(lines[max(0,i-8):min(len(lines),i+9)])})
   elif re.search(r'D_\{?HI|DHI|H.?I.*diameter|surface density.*1|1.*M.*pc',line,re.I):
    contexts.append({'file':m.name,'line':i+1,'targets':[],'context':'\n'.join(lines[max(0,i-5):min(len(lines),i+6)])})
 result={'status':'WANG2016_DDO154_HI_SIZE_AUDITED','arxiv':ARXIV,'files':files,'contexts':contexts,
  'boundary':'Published source-table/definition audit only; no profile reconstruction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
