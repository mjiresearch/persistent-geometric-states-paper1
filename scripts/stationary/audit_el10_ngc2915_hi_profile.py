#!/usr/bin/env python3
"""Audit Elson et al. 2010 (El10) NGC2915 public radial H I profile assets.

The paper explicitly constructs an inclination-corrected azimuthally averaged
H I surface-density profile in 17-arcsec rings (Fig. 5). This script inspects the
public arXiv source package for an exact machine-readable/native-vector route.
No raster digitization, map reconstruction, normalization, or persistence work.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV='1002.0403'
URLS=[f'https://arxiv.org/e-print/{ARXIV}',f'https://export.arxiv.org/e-print/{ARXIV}']
OUT=Path('validation/stationary/el10_ngc2915_public_profile_asset_audit_v1.json')
CTX=Path('validation/stationary/el10_ngc2915_fig5_source_context_v1.txt')

def h(b):return hashlib.sha256(b).hexdigest()
def dec(b):return b.decode('latin-1',errors='replace')
def fetch():
 err=[]
 for u in URLS:
  try:
   with urlopen(Request(u,headers={'User-Agent':'PaperI-El10-audit/1.0'}),timeout=60) as r:return r.read(),r.geturl(),r.headers.get_content_type()
  except Exception as e:err.append([u,repr(e)])
 raise RuntimeError(err)
def unpack(b):
 out={}
 with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as tf:
  for m in tf.getmembers():
   if m.isfile():
    f=tf.extractfile(m)
    if f:out[m.name]=f.read()
 return out

def eps_info(name,b):
 t=dec(b)
 def n(op):return len(re.findall(r'(?<![A-Za-z])'+re.escape(op)+r'(?![A-Za-z])',t))
 ops={x:n(x) for x in ['image','colorimage','moveto','lineto','rlineto','curveto','arc','stroke','fill','show']}
 strings=re.findall(r'\(([^()]{1,140})\)',t)
 keep=[s for s in strings if re.search(r'HI|H I|surface|density|arcsec|kpc|pc|M.?sun|Sigma|radius|R\b|10',s,re.I)]
 return {'name':name,'bytes':len(b),'sha256':h(b),'ops':ops,'native_vector_candidate':ops['image']==0 and ops['colorimage']==0 and sum(ops[x] for x in ['moveto','lineto','rlineto','curveto','arc','stroke','fill'])>0,'interesting_strings':keep[:100],'begin_document':re.findall(r'%%BeginDocument:\s*([^\r\n]+)',t)[:30]}

def main():
 payload,url,ctype=fetch(); files=unpack(payload)
 tex={n:dec(b) for n,b in files.items() if n.lower().endswith(('.tex','.ltx'))}
 contexts=[]; refs=[]
 for n,t in tex.items():
  lines=t.splitlines()
  for i,line in enumerate(lines):
   window='\n'.join(lines[max(0,i-7):min(len(lines),i+10)])
   low=window.lower()
   if ('fig' in low and '5' in low and ('surface' in low or 'density' in low or 'h i' in low or 'hi' in low)):
    ctx='\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-7),min(len(lines),i+10)))
    if ctx not in [x['context'] for x in contexts]:contexts.append({'tex_file':n,'line':i+1,'context':ctx})
    for pat in [r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',r'\\epsfig\{[^}]*file\s*=\s*([^,}\s]+)',r'\\plotone\{([^}]+)\}',r'\\plottwo\{([^}]+)\}\{([^}]+)\}']:
     for m in re.finditer(pat,window):
      refs.extend([g for g in m.groups() if g])
 refs=list(dict.fromkeys(x.strip() for x in refs))
 # Match refs to actual package names.
 fig=[]
 for r in refs:
  rr=r.strip(); rb=Path(rr).name
  for n in files:
   nb=Path(n).name
   if n==rr or nb==rb or Path(nb).stem==Path(rb).stem:fig.append(n)
 # Filename fallback around fig5/profile/density.
 for n in files:
  if re.search(r'(^|[/_.-])(?:fig|f)?0?5([/_.-]|$)|surf|dens|prof',n,re.I):fig.append(n)
 fig=list(dict.fromkeys(fig))
 inspected=[]
 for n in fig:
  b=files[n]
  if n.lower().endswith(('.eps','.ps')):inspected.append(eps_info(n,b))
  else:inspected.append({'name':n,'bytes':len(b),'sha256':h(b),'native_vector_candidate':False,'type':Path(n).suffix.lower()})
 # Data-like sidecars: preserve inventory, don't guess their semantics.
 side=[]
 for n,b in files.items():
  if n.lower().endswith(('.dat','.txt','.tab','.csv','.tbl','.table')):
   side.append({'name':n,'bytes':len(b),'sha256':h(b),'preview':dec(b)[:1500]})
 result={
  'status':'EL10_NGC2915_PUBLIC_PROFILE_ASSET_AUDIT_COMPLETE',
  'sparc_ref_id':'El10','galaxy':'NGC2915','stationary_role':'calibration',
  'source':'Elson, de Blok & Kraan-Korteweg 2010 MNRAS 404 2061; arXiv:1002.0403',
  'public_source_url':url,'content_type':ctype,'source_bytes':len(payload),'source_sha256':h(payload),'n_source_files':len(files),
  'published_profile':{
   'figure':'Figure 5','quantity':'inclination-corrected azimuthally averaged H I surface density','ring_width_arcsec':17,'position_angle_deg':285,'inclination_deg':55,
   'method':'constructed from the H I total-intensity map; rms spread within each azimuthal ring shown as error bars'
  },
  'figure5_contexts':contexts,'graphics_references':refs,'figure5_candidate_files':fig,'candidate_asset_inspection':inspected,'data_like_sidecars':side,
  'file_inventory':[{'name':n,'bytes':len(b),'sha256':h(b)} for n,b in sorted(files.items())],
  'next_action':'If Figure 5 has exact native vector data geometry or a matching numerical sidecar, recover/QC it. Otherwise disposition the exact public profile route as exhausted and move on; do not raster-digitize.',
  'boundary':'Acquisition only. No raster digitization, map/cube reconstruction, re-fitting, common normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
 }
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 lines=[]
 for c in contexts:lines += [f"--- {c['tex_file']} line {c['line']} ---",c['context'],'']
 lines += ['Figure-5 candidates:']+[json.dumps(x,ensure_ascii=False) for x in inspected]+['','Data-like sidecars:']+[json.dumps(x,ensure_ascii=False) for x in side]
 CTX.write_text('\n'.join(lines)+'\n')
 print(json.dumps({'status':result['status'],'n_files':len(files),'figure5_candidates':fig,'native_vector_candidates':[x['name'] for x in inspected if x.get('native_vector_candidate')],'sidecars':[x['name'] for x in side],'outputs':[str(OUT),str(CTX)]},indent=2))
if __name__=='__main__':main()
