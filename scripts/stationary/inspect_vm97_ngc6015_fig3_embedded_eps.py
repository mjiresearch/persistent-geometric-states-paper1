#!/usr/bin/env python3
"""Statically inspect VM97 Figure-3 embedded EPS in legacy A&A PostScript.

The parent legacy article audit identifies page 757 / embedded `07540003.eps` as
Figure 3. This script isolates that exact embedded document and records raster
operator contexts, DSC geometry, literal strings and vector primitives. It never
executes PostScript.
"""
from __future__ import annotations
import gzip,hashlib,json,re
from pathlib import Path
from urllib.request import Request,urlopen

URLS=['https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz','https://cdsarc.u-strasbg.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz']
TARGET='07540003.eps'
OUT=Path('validation/stationary/vm97_ngc6015_fig3_embedded_eps_structure_v1.json')
CTX=Path('validation/stationary/vm97_ngc6015_fig3_embedded_eps_context_v1.txt')

def h(b):return hashlib.sha256(b).hexdigest()
def fetch():
 errs=[]
 for u in URLS:
  try:
   with urlopen(Request(u,headers={'User-Agent':'PaperI-VM97-fig3/1.0'}),timeout=90) as r:return r.read(),r.geturl()
  except Exception as e:errs.append([u,repr(e)])
 raise RuntimeError(errs)
def n(t,op):return len(re.findall(r'(?<![A-Za-z])'+re.escape(op)+r'(?![A-Za-z])',t))
def extract_doc(t,name):
 m=re.search(r'^%%BeginDocument:\s*'+re.escape(name)+r'\s*$',t,re.M)
 if not m:raise RuntimeError(f'{name} BeginDocument not found')
 # Embedded document may contain nested DSC but not another EndDocument for this old asset.
 e=re.search(r'^%%EndDocument\s*$',t[m.end():],re.M)
 if not e:raise RuntimeError(f'{name} EndDocument not found')
 end=m.end()+e.end()
 return t[m.start():end]
def main():
 gz,url=fetch();ps=gzip.decompress(gz);t=ps.decode('latin-1',errors='replace');b=extract_doc(t,TARGET)
 ops={x:n(b,x) for x in ['image','colorimage','imagemask','moveto','lineto','rlineto','curveto','arc','stroke','fill','show']}
 imgctx=[]
 for op in ['colorimage','imagemask','image']:
  for m in re.finditer(r'(?<![A-Za-z])'+op+r'(?![A-Za-z])',b):
   lo=max(0,m.start()-1200);hi=min(len(b),m.end()+500)
   imgctx.append({'op':op,'char':m.start(),'context':b[lo:hi]})
 literals=re.findall(r'\(([^()]{1,240})\)',b)
 strings=[s for s in literals if re.search(r'HI|H I|density|surface|radius|arcsec|kpc|B-I|B-V|B-R|position|angle|ellipt',s,re.I)]
 # DSC/comment lines are useful for deciding if this is a composite raster import.
 dsc=[ln for ln in b.splitlines() if ln.startswith('%%') or re.search(r'BoundingBox|Image|image|raster|bitmap',ln,re.I)]
 # Show all short vector operator lines outside large hex/image payloads.
 vector_lines=[]
 for ln in b.splitlines():
  if len(ln)>500:continue
  if re.search(r'\b(?:moveto|lineto|rlineto|stroke|fill|arc|newpath|closepath)\b',ln):vector_lines.append(ln)
 result={
  'status':'VM97_NGC6015_FIG3_EMBEDDED_EPS_STATIC_INSPECTION_COMPLETE','source_url':url,'embedded_document':TARGET,
  'embedded_chars':len(b),'embedded_sha256':h(b.encode('latin-1',errors='replace')),'header':b[:2500],
  'ops':ops,'interesting_strings':strings[:300],'dsc_and_image_lines':dsc[:500],'image_operator_contexts':imgctx,'vector_operator_lines':vector_lines[:1000],
  'decision_fields':{
   'raster_operator_count':ops['image']+ops['colorimage']+ops['imagemask'],
   'vector_path_operator_count':sum(ops[x] for x in ['lineto','rlineto','curveto','arc','stroke','fill']),
   'has_literal_axis_labels':bool(strings),
  },
  'next_action':'Classify whether the five raster image operators correspond to the Figure-3 panels/data layers. If panel 3d data are raster-encoded and no separate vector/data path exists, disposition VM97 exact public route and advance. Do not raster-digitize.',
  'boundary':'Static parsing only; no PostScript execution, raster digitization, OCR, map reconstruction, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
 }
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 lines=[f'URL={url}',f'embedded={TARGET}',f'ops={json.dumps(ops)}','', 'HEADER',b[:6000],'','IMAGE_CONTEXTS']
 for x in imgctx:lines += [f"--- {x['op']} @{x['char']} ---",x['context']]
 lines += ['','INTERESTING_STRINGS']+strings[:300]+['','VECTOR_LINES']+vector_lines[:1000]
 CTX.write_text('\n'.join(lines)+'\n',encoding='latin-1',errors='replace')
 print(json.dumps({'status':result['status'],'ops':ops,'raster_count':result['decision_fields']['raster_operator_count'],'vector_path_count':result['decision_fields']['vector_path_operator_count'],'strings':strings[:100],'image_context_count':len(imgctx),'outputs':[str(OUT),str(CTX)]},indent=2))
if __name__=='__main__':main()
