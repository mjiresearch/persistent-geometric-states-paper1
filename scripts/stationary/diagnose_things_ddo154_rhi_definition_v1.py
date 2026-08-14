#!/usr/bin/env python3
"""Diagnose DDO154 R_HI definition from the public THINGS MOM0 map.

Calibration/source-domain diagnostic only. Compares annular-profile crossing to
map-isodensity area-equivalent radii; no rotation velocities, persistence
parameters, or blind outcomes are read.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
from urllib.request import Request,urlopen
import numpy as np
from astropy.io import fits
from scipy import ndimage

URL='https://things.www3.mpia.de/Data_files/DDO154_NA_MOM0_THINGS.FITS';UA='PersistenceFrameworkPaperI/1.0'
LOCAL=Path('/tmp/DDO154_NA_MOM0_THINGS.FITS')
PROFILE=Path('data/stationary/source_reconstruction/things_ddo154_mom0_reconstructed_raw_hi_v2.csv')
OUT=Path('validation/stationary/things_ddo154_rhi_definition_diagnostic_v1.json')
D_MPC=4.3; INC_DEG=66.0; BMAJ=14.09; BMIN=12.62; THRESH=1.0; OMAN_RHI=4.5

def download():
 h=hashlib.sha256();n=0
 with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=120) as r,LOCAL.open('wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b:break
   f.write(b);h.update(b);n+=len(b)
 return n,h.hexdigest()
def parse_csv():
 import csv
 with PROFILE.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def crossing(rows):
 r=np.array([float(x['r_center_kpc']) for x in rows if x['usable']=='1']);s=np.array([float(x['sigma_hi_raw_msun_pc2']) for x in rows if x['usable']=='1'])
 cc=[]
 for i in range(1,len(r)):
  if (s[i-1]-THRESH)*(s[i]-THRESH)<=0 and s[i-1]!=s[i]:
   t=(THRESH-s[i-1])/(s[i]-s[i-1]);cc.append(float(r[i-1]+t*(r[i]-r[i-1])))
 return cc

def main():
 n,sha=download()
 with fits.open(LOCAL,memmap=False) as hdul:
  hdr=hdul[0].header; a=np.asarray(hdul[0].data,dtype=float).squeeze()
 if a.ndim!=2:raise RuntimeError(a.shape)
 pix_arcsec=abs(float(hdr['CDELT1']))*3600.0
 ci=math.cos(math.radians(INC_DEG))
 beam_area=math.pi/(4*math.log(2))*BMAJ*BMIN
 rest=float(hdr.get('RESTFREQ',hdr.get('RESTFRQ',1420405750.0)));nu_ghz=rest/1e9
 jybeam_ms_to_k_kms=(1.222e6/(nu_ghz**2*BMAJ*BMIN))/1000.0
 sigma_factor=jybeam_ms_to_k_kms*1.823e18/1.2488e20*ci
 valid=np.isfinite(a)&(a!=0.0); sigma=np.full(a.shape,np.nan);sigma[valid]=a[valid]*sigma_factor
 above=valid&(sigma>=THRESH)
 # Face-on area equals projected area divided by cos(i).
 kpc_per_arcsec=D_MPC*1000.0*math.pi/(180*3600)
 pix_proj_kpc2=(pix_arcsec*kpc_per_arcsec)**2
 total_faceon_area=float(above.sum())*pix_proj_kpc2/ci
 req_all=math.sqrt(total_faceon_area/math.pi)
 # Largest 8-connected above-threshold island; holes below threshold are excluded by definition.
 lab,nlab=ndimage.label(above,structure=np.ones((3,3),dtype=int))
 sizes=np.bincount(lab.ravel());sizes[0]=0
 largest=int(np.argmax(sizes)) if nlab else 0
 nlargest=int(sizes[largest]) if largest else 0
 req_largest=math.sqrt((nlargest*pix_proj_kpc2/ci)/math.pi) if nlargest else None
 # Convex hull-equivalent area is not used; report extent of all/connected area only.
 cc=crossing(parse_csv())
 result={'status':'THINGS_DDO154_RHI_DEFINITION_DIAGNOSTIC_COMPLETE','galaxy':'DDO154','stationary_role':'calibration','source':{'url':URL,'bytes':n,'sha256':sha},
  'threshold_raw_hi_msun_pc2':THRESH,'conversion':{'sigma_hi_raw_per_mom0':sigma_factor,'inclination_deg':INC_DEG,'pixel_arcsec':pix_arcsec,'pixel_projected_kpc2':pix_proj_kpc2},
  'annular_profile_crossings_kpc':cc,'n_annular_crossings':len(cc),
  'isodensity_area':{'n_above_threshold_pixels_all':int(above.sum()),'faceon_area_kpc2_all':total_faceon_area,'equivalent_radius_kpc_all':req_all,
    'n_connected_components':int(nlab),'n_pixels_largest_component':nlargest,'equivalent_radius_kpc_largest_component':req_largest},
  'oman2019_things_rhi_kpc':OMAN_RHI,
  'fractional_differences_to_oman':{'annular':None if not cc else abs(cc[0]-OMAN_RHI)/OMAN_RHI,'area_all':abs(req_all-OMAN_RHI)/OMAN_RHI,'area_largest':None if req_largest is None else abs(req_largest-OMAN_RHI)/OMAN_RHI},
  'boundary':'Calibration/source-domain R_HI-definition diagnostic only; no velocities, residuals, persistence parameters, or blind outcomes.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
