#!/usr/bin/env python3
"""Audit Zakharova+2023 arXiv source for exact THINGS gas-profile assets.

No raster digitization, profile fitting, persistence evaluation, or blind outcomes.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/2309.01710';UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/zakharova2023_things_profile_asset_audit_v1.json')
TARGETS=['NGC2841','NGC3521','NGC5055','NGC7331']
def ps_metrics(b):
 low=b[:20_000_000].lower();return {'bytes':len(b),'image_ops':len(re.findall(rb'(?<![a-z])image(?![a-z])',low)),'colorimage_ops':low.count(b'colorimage'),'imagemask_ops':low.count(b'imagemask'),'moveto_tokens':low.count(b'moveto'),'lineto_tokens':low.count(b'lineto'),'curveto_tokens':low.count(b'curveto'),'stroke_tokens':low.count(b'stroke'),'raster_signal':bool(re.search(rb'(?<![a-z])(?:image|colorimage|imagemask)(?![a-z])',low)),'substantial_path_signal':(low.count(b'lineto')+low.count(b'curveto')>=50)}
def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');members={m.name:m for m in tf.getmembers() if m.isfile()};assets=[];contexts=[]
 for name,m in members.items():
  ext=Path(name).suffix.lower();b=tf.extractfile(m).read()
  if ext in {'.tex','.txt','.dat','.csv','.tab','.tbl'}:
   t=b.decode('latin-1','replace');num=sum(bool(re.match(r'^\s*[-+]?\d+(?:\.\d+)?(?:[eEdD][-+]?\d+)?\s+[-+]?\d',line)) for line in t.splitlines());assets.append({'file':name,'kind':'text_or_numeric','bytes':len(b),'numeric_line_count':num,'target_mentions':{g:len(re.findall(re.escape(g),t,re.I)) for g in TARGETS},'head':t[:2500]})
   lines=t.splitlines()
   for i,line in enumerate(lines):
    if re.search(r'surface density|3D.?barolo|Sigma.*H|HI distribution|neutral gas',line,re.I):contexts.append({'file':name,'line':i+1,'context':'\n'.join(lines[max(0,i-3):min(len(lines),i+4)])})
  elif ext in {'.eps','.ps','.pdf'}:
   rec={'file':name,'kind':'postscript_or_pdf',**ps_metrics(b)};rec['target_mentions']={g:len(re.findall(re.escape(g).encode(),b,re.I)) for g in TARGETS};assets.append(rec)
 result={'status':'ZAKHAROVA2023_THINGS_PROFILE_ASSET_AUDIT_COMPLETE','arxiv':ARXIV,'targets':TARGETS,'files':sorted(members),'candidate_assets':assets,'contexts':contexts,
  'n_numeric_sidecars':sum(a.get('numeric_line_count',0)>5 for a in assets if a['kind']=='text_or_numeric'),'n_vector_candidates':sum(a.get('substantial_path_signal',False) and not a.get('raster_signal',False) for a in assets if a['kind']=='postscript_or_pdf'),
  'boundary':'Public source-package inspection only; no raster digitization, profile fitting, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'files':sorted(members),'numeric_sidecars':result['n_numeric_sidecars'],'vector_candidates':result['n_vector_candidates'],'contexts':contexts[:100]},indent=2))
if __name__=='__main__':main()
