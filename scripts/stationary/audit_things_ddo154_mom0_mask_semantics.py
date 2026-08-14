#!/usr/bin/env python3
"""Audit how the public THINGS DDO154 MOM0 FITS encodes source blanking.

Pixel-domain mask audit only; no radial profile, velocity, persistence parameter,
or blind outcome is evaluated.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from urllib.request import Request,urlopen
import numpy as np
from astropy.io import fits
URL='https://things.www3.mpia.de/Data_files/DDO154_NA_MOM0_THINGS.FITS';UA='PersistenceFrameworkPaperI/1.0'
LOCAL=Path('/tmp/DDO154_NA_MOM0_THINGS.FITS');OUT=Path('validation/stationary/things_ddo154_mom0_mask_semantics_v1.json')
def download():
 h=hashlib.sha256();n=0
 with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=120) as r,LOCAL.open('wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b:break
   f.write(b);h.update(b);n+=len(b)
 return n,h.hexdigest()
def main():
 n,sha=download()
 with fits.open(LOCAL,memmap=False) as hdul:
  hdr=hdul[0].header.copy();a=np.asarray(hdul[0].data,dtype=float).squeeze()
 if a.ndim!=2:raise RuntimeError(a.shape)
 finite=np.isfinite(a);zero=finite&(a==0);pos=finite&(a>0);neg=finite&(a<0);nonzero=finite&(a!=0)
 ny,nx=a.shape
 border=np.zeros(a.shape,dtype=bool);border[0,:]=border[-1,:]=True;border[:,0]=border[:,-1]=True
 # Thin border and central box statistics help distinguish zero-padded blanking from valid zero measurements.
 bwidth=max(1,min(nx,ny)//20);outer=np.zeros(a.shape,dtype=bool);outer[:bwidth,:]=outer[-bwidth:,:]=True;outer[:,:bwidth]=True;outer[:,-bwidth:]=True
 cy,cx=ny//2,nx//2;hy,hx=max(1,ny//10),max(1,nx//10);center=np.zeros(a.shape,dtype=bool);center[cy-hy:cy+hy+1,cx-hx:cx+hx+1]=True
 vals=a[nonzero]
 q={str(p):float(np.quantile(vals,p)) for p in [0,0.001,0.01,0.05,0.5,0.95,0.99,0.999,1]} if vals.size else {}
 result={'status':'THINGS_DDO154_MOM0_MASK_SEMANTICS_AUDITED','url':URL,'bytes':n,'sha256':sha,'shape':[ny,nx],'bunit':hdr.get('BUNIT'),
  'header_blank_keyword':hdr.get('BLANK'),'datamin_header':hdr.get('DATAMIN'),'datamax_header':hdr.get('DATAMAX'),
  'counts':{'total':int(a.size),'finite':int(finite.sum()),'nonfinite':int((~finite).sum()),'exact_zero':int(zero.sum()),'positive':int(pos.sum()),'negative':int(neg.sum()),'nonzero':int(nonzero.sum())},
  'fractions':{'exact_zero':float(zero.mean()),'negative':float(neg.mean()),'nonzero':float(nonzero.mean()),
    'border_exact_zero':float(zero[border].mean()),'outer_5pct_exact_zero':float(zero[outer].mean()),'center_exact_zero':float(zero[center].mean()),
    'border_nonzero':float(nonzero[border].mean()),'outer_5pct_nonzero':float(nonzero[outer].mean()),'center_nonzero':float(nonzero[center].mean())},
  'nonzero_value_quantiles':q,
  'candidate_mask_rule_for_followup':'Treat exact-zero MOM0 pixels as source-blanked and all finite nonzero pixels, including negative values, as valid only if this encoding is supported by source/product semantics and reproduces independent profile/flux QC. This audit itself does not promote that rule.',
  'boundary':'Pixel-mask encoding audit only; no radial profile, persistence parameter, or blind outcome evaluated.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
