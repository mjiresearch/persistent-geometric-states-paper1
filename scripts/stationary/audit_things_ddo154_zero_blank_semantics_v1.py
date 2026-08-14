#!/usr/bin/env python3
"""Audit the finite blank sentinel in the public THINGS DDO154 MOM0 FITS map.

This source-product semantics audit tests whether exact floating-point zero is
used as the blanked-mask value. It does not convert intensities to HI surface
density and does not read any rotation or persistence quantity.
"""
from __future__ import annotations
import hashlib,json
from collections import deque
from pathlib import Path
from urllib.request import Request,urlopen

import numpy as np
from astropy.io import fits

URL='https://things.www3.mpia.de/Data_files/DDO154_NA_MOM0_THINGS.FITS'
TMP=Path('/tmp/DDO154_NA_MOM0_THINGS.FITS')
OUT=Path('validation/stationary/things_ddo154_zero_blank_semantics_v1.json')
UA='PersistenceFrameworkPaperI/1.0'

def download():
 h=hashlib.sha256();n=0
 with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=120) as r,TMP.open('wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b:break
   f.write(b);h.update(b);n+=len(b)
 return n,h.hexdigest()

def main():
 nbytes,sha=download()
 with fits.open(TMP,memmap=False) as hdul:
  h=hdul[0].header.copy();a=np.asarray(hdul[0].data,dtype=float).squeeze()
 if a.ndim!=2:raise RuntimeError(a.shape)
 finite=np.isfinite(a);zero=finite&(a==0.0);nonzero=finite&(a!=0.0);neg=finite&(a<0.0);pos=finite&(a>0.0)
 ny,nx=a.shape
 border=np.zeros_like(zero);border[0,:]=border[-1,:]=True;border[:,0]=border[:,-1]=True
 # Flood-fill exact-zero pixels connected to the image boundary.
 seen=np.zeros_like(zero,dtype=bool);q=deque()
 ys,xs=np.nonzero(zero&border)
 for y,x in zip(ys.tolist(),xs.tolist()):seen[y,x]=True;q.append((y,x))
 while q:
  y,x=q.popleft()
  for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
   yy,xx=y+dy,x+dx
   if 0<=yy<ny and 0<=xx<nx and zero[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((yy,xx))
 interior_zero=zero&~seen
 # Bounding box of nonzero pixels and exact-zero fraction in that rectangle.
 yy,xx=np.nonzero(nonzero)
 bbox=None
 if len(yy):
  y0,y1=int(yy.min()),int(yy.max());x0,x1=int(xx.min()),int(xx.max())
  box=np.zeros_like(zero);box[y0:y1+1,x0:x1+1]=True
  bbox={'x_min':x0,'x_max':x1,'y_min':y0,'y_max':y1,'area_pixels':int(box.sum()),'zero_pixels_inside_bbox':int((zero&box).sum()),'zero_fraction_inside_bbox':float((zero&box).sum()/box.sum())}
 vals=a[nonzero]
 qtiles={str(p):float(np.quantile(vals,p)) for p in (0.0,0.001,0.01,0.05,0.5,0.95,0.99,0.999,1.0)} if vals.size else {}
 all_border_zero=bool(np.all(zero[border]))
 result={'status':'THINGS_DDO154_ZERO_BLANK_SEMANTICS_AUDITED','source_url':URL,'bytes':nbytes,'sha256':sha,'shape':[ny,nx],'bunit':h.get('BUNIT'),
  'counts':{'total_pixels':int(a.size),'finite':int(finite.sum()),'nonfinite':int((~finite).sum()),'exact_zero':int(zero.sum()),'nonzero_finite':int(nonzero.sum()),'negative_finite_nonzero':int(neg.sum()),'positive_finite_nonzero':int(pos.sum()),'border_pixels':int(border.sum()),'border_exact_zero':int((zero&border).sum()),'boundary_connected_zero':int(seen.sum()),'interior_zero_not_boundary_connected':int(interior_zero.sum())},
  'fractions':{'exact_zero_of_all':float(zero.sum()/a.size),'boundary_connected_of_all_zero':float(seen.sum()/zero.sum()) if zero.sum() else None},
  'all_image_border_pixels_exact_zero':all_border_zero,'nonzero_bbox':bbox,'nonzero_value_quantiles_jybeam_ms':qtiles,
  'interpretation_gate':{'zero_as_source_blank_supported':bool(all_border_zero and zero.sum()>0 and seen.sum()/zero.sum()>0.95 and neg.sum()>0),
   'rule_if_supported':'Treat exact floating-point zero in this THINGS MOM0 product as source blank/mask, not as measured zero emission; retain all nonzero finite pixels including negative values.'},
  'documentary_context':'Walter et al. 2008 states noise areas are blanked in residual-rescaled cubes with the master emission mask, moments are calculated from all pixels in those blanked cubes, and MOM0 is primary-beam corrected. The public floating MOM0 has no NaN/BLANK representation, so the pixel topology is audited here to identify its finite sentinel.',
  'boundary':'Source-product blanking semantics only; no HI conversion, radial profile, velocity, residual, persistence parameter, or blind outcome.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not result['interpretation_gate']['zero_as_source_blank_supported']:raise SystemExit(2)
if __name__=='__main__':main()
