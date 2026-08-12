#!/usr/bin/env python3
"""Inspect only the Ba05 Figure-3 TeX neighborhood and its referenced EPS assets.

Continuation after the committed 18-file inventory. No broad source re-audit.
"""
from __future__ import annotations
import hashlib,io,json,re,tarfile,urllib.request
from pathlib import Path
URL='https://arxiv.org/e-print/astro-ph/0504534';UA='Mozilla/5.0 PersistenceFrameworkPaperI/1.0';OUT=Path('validation/stationary/ba05_fig3_asset_classification_v1.json')
def psa(b):
 return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'creator_lines':[ln for ln in b.decode('latin-1','replace').splitlines()[:40] if 'Creator' in ln or 'BoundingBox' in ln],'image_ops':len(re.findall(rb'(?<![A-Za-z])image(?![A-Za-z])',b)),'colorimage_ops':b.count(b'colorimage'),'imagemask_ops':b.count(b'imagemask'),'moveto':b.count(b'moveto'),'lineto':b.count(b'lineto'),'rlineto':b.count(b'rlineto'),'curveto':b.count(b'curveto'),'stroke':b.count(b'stroke'),'fill':b.count(b'fill')}
def main():
 req=urllib.request.Request(URL,headers={'User-Agent':UA});
 with urllib.request.urlopen(req,timeout=180) as h:raw=h.read()
 tf=tarfile.open(fileobj=io.BytesIO(raw),mode='r:*');files={m.name:tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
 tex=files['barbieri.tex'].decode('latin-1','replace');ls=tex.splitlines();lo,hi=360,405;ctx='\n'.join(f'{i+1}: {ls[i]}' for i in range(lo-1,min(hi,len(ls))))
 refs=[]
 for i in range(lo-1,min(hi,len(ls))):
  for m in re.finditer(r'includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',ls[i],re.I):refs.append({'line':i+1,'asset':m.group(1)})
 assets=[]
 for r in refs:
  n=r['asset']
  if n in files:assets.append({'line':r['line'],'name':n,'audit':psa(files[n])})
 out={'status':'BA05_FIG3_ASSETS_CLASSIFIED','tex_lines_360_405':ctx,'graphics_references':refs,'assets':assets,'decision_fields':{'all_referenced_assets_raster_wrapped':bool(assets) and all(a['audit']['image_ops']+a['audit']['colorimage_ops']+a['audit']['imagemask_ops']>0 for a in assets),'any_substantive_native_path_signal':any(a['audit']['lineto']+a['audit']['rlineto']+a['audit']['curveto']>20 for a in assets)},'boundary':'Figure-3 asset classification only; no rendering, OCR, raster digitization, map reconstruction, persistence fitting, or blind-outcome inspection.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
