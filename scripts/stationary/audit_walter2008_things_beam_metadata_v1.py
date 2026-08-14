#!/usr/bin/env python3
"""Recover natural-weighted THINGS beam metadata from Walter et al. (2008) source.

Source/provenance audit only. No FITS science pixels, radial profiles, velocities,
residuals, persistence parameters, or blind outcomes are evaluated.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen

URL='https://export.arxiv.org/e-print/0810.2125'
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/walter2008_things_beam_metadata_v1.json')
TARGETS=['DDO 154','IC 2574','NGC 2403','NGC 2841','NGC 2976','NGC 3198','NGC 3521','NGC 5055','NGC 6946','NGC 7331','NGC 7793']

def main():
 with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=90) as h:
  blob=h.read(30_000_000); final=h.geturl();ctype=h.headers.get('Content-Type','')
 files=[];hits=[]
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:*') as tf:
  for m in tf.getmembers():
   if not m.isfile() or m.size>5_000_000:continue
   f=tf.extractfile(m)
   if f is None:continue
   b=f.read(); files.append({'name':m.name,'bytes':len(b)})
   if not m.name.lower().endswith(('.tex','.txt','.dat','.tab')):continue
   t=b.decode('latin-1','replace'); lines=t.splitlines()
   for i,line in enumerate(lines):
    compact=re.sub(r'[^a-z0-9]','',line.lower())
    matched=[]
    for g in TARGETS:
     if re.sub(r'[^a-z0-9]','',g.lower()) in compact:matched.append(g)
    if matched:
     lo=max(0,i-2);hi=min(len(lines),i+3)
     hits.append({'file':m.name,'line':i+1,'targets':matched,'context':'\n'.join(lines[lo:hi])})
 # Prefer contexts that mention beam/table/robust/natural nearby.
 beam_hits=[x for x in hits if any(k in x['context'].lower() for k in ['beam','natural','robust','arcsec','rms','table'])]
 result={'status':'WALTER2008_THINGS_BEAM_METADATA_SOURCE_AUDITED','source_url':URL,'final_url':final,'content_type':ctype,'source_bytes':len(blob),
         'files':files,'n_target_hits':len(hits),'n_beam_context_hits':len(beam_hits),'beam_context_hits':beam_hits,
         'boundary':'Survey-source metadata audit only; no science-pixel interpretation, profile reconstruction, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not beam_hits:raise SystemExit('no target beam metadata contexts found')
if __name__=='__main__':main()
