#!/usr/bin/env python3
"""Audit the legacy A&A PostScript route for VM97 / NGC6015 Figure 3d.

Verdes-Montenegro, Bosma & Athanassoula (1997), A&A 321, 754-764,
directly publishes the radial H I surface-density profile in Figure 3d. The
legacy A&A electronic archive provides a gzipped PostScript article. This script
fetches that source-native publication asset and statically inventories page,
embedded-document, raster-image, vector, and text structure without executing
PostScript.

Acquisition/provenance only. No raster digitization, OCR, PostScript execution,
map reconstruction, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import gzip,hashlib,json,re
from pathlib import Path
from urllib.request import Request,urlopen

PS_URLS=[
 'https://cdsarc.u-strasbg.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz',
 'https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.ps.gz',
]
PDF_URLS=[
 'https://cdsarc.u-strasbg.fr/ftp/vizier/aa/papers/7321003/2300754.pdf',
 'https://cdsarc.cds.unistra.fr/ftp/vizier/aa/papers/7321003/2300754.pdf',
]
OUT=Path('validation/stationary/vm97_ngc6015_legacy_postscript_profile_audit_v1.json')
CTX=Path('validation/stationary/vm97_ngc6015_legacy_postscript_context_v1.txt')

def h(b):return hashlib.sha256(b).hexdigest()
def fetch(urls):
 errs=[]
 for u in urls:
  try:
   with urlopen(Request(u,headers={'User-Agent':'PaperI-VM97-audit/1.0'}),timeout=90) as r:return r.read(),r.geturl(),r.headers.get_content_type()
  except Exception as e:errs.append([u,repr(e)])
 return None,None,errs

def nops(t,op):return len(re.findall(r'(?<![A-Za-z])'+re.escape(op)+r'(?![A-Za-z])',t))
def strings(t):
 # Simple PS literal strings; audit only.
 vals=re.findall(r'\(([^()]{1,220})\)',t)
 return [s for s in vals if re.search(r'Fig\.?\s*3|H.?I|surface|density|arcsec|kpc|M.?sun|NGC|6015|radius',s,re.I)]

def page_blocks(t):
 starts=[(m.start(),m.group(1),m.group(2)) for m in re.finditer(r'^%%Page:\s*(\S+)\s+(\d+)',t,re.M)]
 out=[]
 for i,(pos,label,num) in enumerate(starts):
  end=starts[i+1][0] if i+1<len(starts) else len(t)
  b=t[pos:end]
  out.append({'label':label,'ordinal':int(num),'chars':len(b),'image_ops':nops(b,'image'),'colorimage_ops':nops(b,'colorimage'),'imagemask_ops':nops(b,'imagemask'),'moveto_ops':nops(b,'moveto'),'lineto_ops':nops(b,'lineto'),'stroke_ops':nops(b,'stroke'),'fill_ops':nops(b,'fill'),'arc_ops':nops(b,'arc'),'interesting_strings':strings(b)[:120],'begin_documents':re.findall(r'%%BeginDocument:\s*([^\r\n]+)',b)[:60]})
 return out

def main():
 psgz,psurl,pserr=fetch(PS_URLS)
 pdf,pdfurl,pdferr=fetch(PDF_URLS)
 if psgz is None:raise RuntimeError(f'Legacy A&A PostScript unavailable: {pserr}')
 try:ps=gzip.decompress(psgz)
 except Exception as e:raise RuntimeError(f'Legacy asset not valid gzip: {e!r}')
 t=ps.decode('latin-1',errors='replace')
 ops={x:nops(t,x) for x in ['image','colorimage','imagemask','moveto','lineto','rlineto','curveto','arc','stroke','fill','show']}
 begins=re.findall(r'%%BeginDocument:\s*([^\r\n]+)',t)
 pages=page_blocks(t)
 # Context around literal Fig. 3 and likely HI-density words.
 contexts=[]
 for pat in [r'Fig\.?\s*3',r'HI surface',r'H I surface',r'surface density',r'NGC\s*6015']:
  for m in re.finditer(pat,t,re.I):
   lo=max(0,m.start()-1200);hi=min(len(t),m.end()+2400)
   c=t[lo:hi]
   contexts.append({'pattern':pat,'char':m.start(),'context':c})
 # Dedup contexts by first 200 chars.
 ded=[];seen=set()
 for c in contexts:
  k=c['context'][:300]
  if k not in seen:seen.add(k);ded.append(c)
 result={
  'status':'VM97_NGC6015_LEGACY_POSTSCRIPT_AUDIT_COMPLETE','sparc_ref_id':'VM97','galaxy':'NGC6015','stationary_role':'calibration',
  'source':'Verdes-Montenegro, Bosma & Athanassoula 1997 A&A 321, 754-764, The ringed, warped and isolated galaxy NGC 6015',
  'published_profile':{'figure':'Figure 3d','quantity':'radial H I surface density / column-density distribution','method':'integrating the two-dimensional H I distribution using geometrical parameters from the H I velocity field','source_distance_mpc':13.9,'source_axes':'lower radius scale arcsec; upper radius scale kpc'},
  'legacy_postscript':{'url':psurl,'compressed_bytes':len(psgz),'compressed_sha256':h(psgz),'uncompressed_bytes':len(ps),'uncompressed_sha256':h(ps),'header':t[:1200],'ops':ops,'begin_documents':begins,'n_pages':len(pages),'pages':pages},
  'legacy_pdf':None if pdf is None else {'url':pdfurl,'bytes':len(pdf),'sha256':h(pdf),'content_type':'application/pdf'},
  'pdf_fetch_errors':pdferr if pdf is None else [],'postscript_contexts':ded[:80],
  'decision_fields':{'article_has_raster_ops':(ops['image']+ops['colorimage']+ops['imagemask'])>0,'article_has_vector_ops':sum(ops[x] for x in ['lineto','rlineto','curveto','arc','stroke','fill'])>0,'embedded_document_count':len(begins)},
  'next_action':'Locate the page/embedded object containing Figure 3 and determine whether panel 3d H I profile is native vector. If vector, extract axis/curve geometry exactly; if raster-only and no numeric sidecar exists, disposition and advance without digitization.',
  'boundary':'Static PostScript parsing only; do not execute PostScript. No raster digitization, OCR, map reconstruction, profile fitting, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
 }
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 lines=[f'PS_URL={psurl}',f'compressed_sha={h(psgz)}',f'uncompressed_sha={h(ps)}',f'ops={json.dumps(ops)}','BEGIN_DOCUMENTS']+begins+['','PAGES']
 for p in pages:lines.append(json.dumps(p,ensure_ascii=False))
 lines += ['','CONTEXTS']
 for c in ded[:80]:lines += [f"--- {c['pattern']} @{c['char']} ---",c['context']]
 CTX.write_text('\n'.join(lines)+'\n',encoding='latin-1',errors='replace')
 print(json.dumps({'status':result['status'],'ps_url':psurl,'compressed_bytes':len(psgz),'uncompressed_bytes':len(ps),'ops':ops,'n_pages':len(pages),'begin_documents':begins,'page_summaries':[{k:p[k] for k in ['label','ordinal','image_ops','colorimage_ops','imagemask_ops','moveto_ops','lineto_ops','stroke_ops','fill_ops','arc_ops','begin_documents']} for p in pages],'outputs':[str(OUT),str(CTX)]},indent=2))
if __name__=='__main__':main()
