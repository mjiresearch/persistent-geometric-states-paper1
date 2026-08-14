#!/usr/bin/env python3
"""Audit Stevens+2019 source package for machine-readable observed H I profiles.

The paper uses 110 well-resolved inclination-corrected H I radial profiles from
THINGS, LITTLE THINGS, LVHIS, and Bluedisk. This audit inventories numerical
sidecars and source references for the Paper-I THINGS targets. No raster
extraction, profile fitting, persistence evaluation, or blind outcomes.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/1908.11149';UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/stevens2019_observed_hi_profile_asset_audit_v1.json')
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*'); members={m.name:m for m in tf.getmembers() if m.isfile()}
 assets=[];contexts=[]
 for name,m in members.items():
  ext=Path(name).suffix.lower(); b=tf.extractfile(m).read()
  if ext in {'.tex','.txt','.dat','.csv','.tab','.tbl','.ascii','.out'}:
   t=b.decode('latin-1','replace'); lines=t.splitlines(); numeric=sum(bool(re.match(r'^\s*[-+]?\d+(?:\.\d+)?(?:[eEdD][-+]?\d+)?(?:\s+|,)[-+]?\d',line)) for line in lines)
   mentions={g:len(re.findall(re.escape(g),t,re.I)) for g in TARGETS}
   assets.append({'file':name,'kind':'text_or_numeric','bytes':len(b),'numeric_line_count':numeric,'target_mentions':mentions,'head':t[:3000]})
   for i,line in enumerate(lines):
    if re.search(r'THINGS|LITTLE THINGS|surface density profile|Sigma.*HI|Wang et al|Obreschkow|Butler',line,re.I):
     contexts.append({'file':name,'line':i+1,'context':'\n'.join(lines[max(0,i-4):min(len(lines),i+5)])})
  elif ext in {'.eps','.ps','.pdf'}:
   low=b[:20_000_000].lower();assets.append({'file':name,'kind':'figure','bytes':len(b),'raster_signal':bool(re.search(rb'(?<![a-z])(?:image|colorimage|imagemask)(?![a-z])',low)),'path_tokens':low.count(b'lineto')+low.count(b'curveto'),'target_mentions':{g:len(re.findall(re.escape(g).encode(),b,re.I)) for g in TARGETS}})
 result={'status':'STEVENS2019_OBSERVED_HI_PROFILE_ASSET_AUDIT_COMPLETE','arxiv':ARXIV,'files':sorted(members),'assets':assets,'contexts':contexts,
  'n_numeric_sidecars':sum(a.get('numeric_line_count',0)>10 for a in assets if a['kind']=='text_or_numeric'),
  'numeric_sidecar_files':[a['file'] for a in assets if a.get('numeric_line_count',0)>10],
  'target_mention_files':{g:[a['file'] for a in assets if a.get('target_mentions',{}).get(g,0)>0] for g in TARGETS},
  'boundary':'Public source-package asset audit only; no raster extraction, profile fitting, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'files':sorted(members),'numeric_sidecars':result['numeric_sidecar_files'],'target_mention_files':result['target_mention_files'],'contexts':contexts[:120]},indent=2))
if __name__=='__main__':main()
