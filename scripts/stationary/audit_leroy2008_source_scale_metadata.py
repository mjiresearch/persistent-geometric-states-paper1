#!/usr/bin/env python3
"""Audit Leroy+2008 VizieR catalog for source distance/inclination metadata.

Public-source metadata only; no profile rescaling or persistence evaluation.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.request import Request,urlopen

BASE='https://cdsarc.cds.unistra.fr/ftp/J/AJ/136/2782/'
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/leroy2008_source_scale_metadata_audit_v1.json')
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']

def get(url):
 with urlopen(Request(url,headers={'User-Agent':UA}),timeout=60) as h:return h.read().decode('utf-8','replace')

def main():
 idx=get(BASE); readme=get(BASE+'ReadMe')
 files=re.findall(r'href=["\']([^"\']+)["\']',idx,re.I)
 candidates=[]
 for f in files:
  if f.startswith('.') or f.startswith('/') or f.lower() in {'readme'}:continue
  if re.search(r'table|gal|sample|global',f,re.I):
   try:
    t=get(BASE+f)
   except Exception as e:
    candidates.append({'file':f,'error':repr(e)});continue
   candidates.append({'file':f,'bytes':len(t),'target_mentions':{g:len(re.findall(re.escape(g.replace('NGC','NGC ')),t,re.I))+len(re.findall(re.escape(g),t,re.I)) for g in TARGETS},'head':t[:3000]})
 # Capture ReadMe definitions around distance/inclination terms and file summary.
 lines=readme.splitlines(); hits=[]
 for i,line in enumerate(lines):
  if re.search(r'distance|inclination|File Summary|table[0-9]',line,re.I):
   hits.append({'line':i+1,'text':line})
 result={'status':'LEROY2008_SOURCE_SCALE_METADATA_ROUTE_AUDITED','catalog_base':BASE,'targets':TARGETS,
  'directory_files':files,'readme_hits':hits[:300],'candidate_files':candidates,
  'boundary':'Public metadata audit only; no profile rescaling, interpolation, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'files':files,'readme_hits':hits[:80]},indent=2))
if __name__=='__main__':main()
