#!/usr/bin/env python3
"""Audit Hessman & Ziebart 2011 arXiv source for exact THINGS H I profile assets.

The paper states that tabulated total H I+He surface-density profiles were
provided by the THINGS consortium. This audit searches the public source package
for numerical sidecars and native-vector figure assets. No raster digitization,
profile fitting, persistence evaluation, or blind outcomes.
"""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
ARXIV='https://export.arxiv.org/e-print/1106.5621'
UA='PersistenceFrameworkPaperI/1.0'
OUT=Path('validation/stationary/hessman2011_things_hi_profile_asset_audit_v1.json')
TARGETS=['DDO154','IC2574','NGC2403','NGC2841','NGC2976','NGC3198','NGC3521','NGC5055','NGC6946','NGC7331','NGC7793']

def ps_metrics(b):
 low=b[:20_000_000].lower()
 return {'bytes':len(b),'image_ops':len(re.findall(rb'(?<![a-z])image(?![a-z])',low)),
  'colorimage_ops':low.count(b'colorimage'),'imagemask_ops':low.count(b'imagemask'),
  'moveto_tokens':low.count(b'moveto'),'lineto_tokens':low.count(b'lineto'),'curveto_tokens':low.count(b'curveto'),
  'stroke_tokens':low.count(b'stroke'),'show_tokens':low.count(b'show'),
  'raster_signal':bool(re.search(rb'(?<![a-z])(?:image|colorimage|imagemask)(?![a-z])',low)),
  'substantial_path_signal':(low.count(b'lineto')+low.count(b'curveto')>=50)}

def main():
 with urlopen(Request(ARXIV,headers={'User-Agent':UA}),timeout=120) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*'); members={m.name:m for m in tf.getmembers() if m.isfile()}
 files=sorted(members); texts={}; assets=[]
 for name,m in members.items():
  ext=Path(name).suffix.lower()
  if ext in {'.tex','.txt','.dat','.csv','.tab','.tbl'}:
   b=tf.extractfile(m).read(); t=b.decode('latin-1','replace'); texts[name]=t
   numeric_lines=sum(bool(re.match(r'^\s*[-+]?\d+(?:\.\d+)?(?:[eEdD][-+]?\d+)?\s+[-+]?\d',line)) for line in t.splitlines())
   target_mentions={g:len(re.findall(re.escape(g),t,re.I)) for g in TARGETS}
   assets.append({'file':name,'kind':'text_or_numeric','bytes':len(b),'numeric_line_count':numeric_lines,'target_mentions':target_mentions,'head':t[:2500]})
  elif ext in {'.eps','.ps'}:
   b=tf.extractfile(m).read(); rec={'file':name,'kind':'postscript',**ps_metrics(b)}
   rec['target_mentions']={g:len(re.findall(re.escape(g).encode(),b,re.I)) for g in TARGETS}; assets.append(rec)
 # Figure environments and references to HI profile figure(s).
 figs=[]; contexts=[]
 for name,t in texts.items():
  if not name.endswith('.tex'):continue
  lines=t.splitlines(); infig=False;buf=[];start=0
  for i,line in enumerate(lines,1):
   if re.search(r'\\begin\{figure\*?\}',line):infig=True;buf=[line];start=i;continue
   if infig:
    buf.append(line)
    if re.search(r'\\end\{figure\*?\}',line):
     block='\n'.join(buf); figs.append({'file':name,'start_line':start,'assets':re.findall(r'(?:includegraphics|plotone|plottwo)(?:\[[^]]*\])?\{([^}]+)\}',block),'labels':re.findall(r'\\label\{([^}]+)\}',block),'block':block[:12000]});infig=False
  for i,line in enumerate(lines,1):
   if re.search(r'Sigma.*HI|H.?I.*surface.*dens|surface.*dens.*H.?I|tabulated total surface',line,re.I):
    contexts.append({'file':name,'line':i,'context':'\n'.join(lines[max(0,i-3):min(len(lines),i+4)])})
 result={'status':'HESSMAN2011_THINGS_HI_PROFILE_ASSET_AUDIT_COMPLETE','arxiv':ARXIV,'targets':TARGETS,'files':files,
  'candidate_assets':assets,'figure_environments':figs,'hi_profile_text_contexts':contexts,
  'n_numeric_sidecars':sum(a.get('numeric_line_count',0)>5 for a in assets if a['kind']=='text_or_numeric'),
  'n_postscript_assets':sum(a['kind']=='postscript' for a in assets),
  'n_vector_postscript_candidates':sum(a.get('substantial_path_signal',False) and not a.get('raster_signal',False) for a in assets if a['kind']=='postscript'),
  'boundary':'Public source-package inspection only; no raster digitization, profile fitting, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'files':files,'numeric_sidecars':result['n_numeric_sidecars'],'vector_candidates':result['n_vector_postscript_candidates'],'contexts':contexts[:80],'figures':figs},indent=2))
if __name__=='__main__':main()
