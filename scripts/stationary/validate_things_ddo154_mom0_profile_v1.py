#!/usr/bin/env python3
"""Validate frozen THINGS MOM0 radial-profile reconstruction on DDO154.

Calibration/source-domain validation only. Uses the public natural-weighted,
blanked THINGS MOM0 FITS map and compares the recovered raw-HI profile to the
independent Leroy et al. 2008 radial profile over shared support, plus published
THINGS global flux and HI radius. No rotation velocities, residuals, persistence
parameters, or blind outcomes are read.
"""
from __future__ import annotations

import csv, hashlib, json, math
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

URL='https://things.www3.mpia.de/Data_files/DDO154_NA_MOM0_THINGS.FITS'
LOCAL=Path('/tmp/DDO154_NA_MOM0_THINGS.FITS')
LEROY=Path('data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv')
OUTCSV=Path('data/stationary/source_reconstruction/things_ddo154_mom0_reconstructed_raw_hi_v1.csv')
OUTJSON=Path('validation/stationary/things_ddo154_mom0_validation_v1.json')
UA='PersistenceFrameworkPaperI/1.0'

# Frozen source-domain geometry / calibration metadata.
D_MPC=4.3
INC_DEG=66.0
PA_DEG=230.0
CENTER_RA_DEG=15.0*(12.0+54.0/60.0+5.9/3600.0)
CENTER_DEC_DEG=27.0+9.0/60.0+9.9/3600.0
# Natural THINGS beam from Ianjamasimanana, de Blok & Heald 2017 Table 1,
# using the THINGS natural-weighted DDO154 cube: 14.09 x 12.62 arcsec.
BMAJ_ARCSEC=14.09
BMIN_ARCSEC=12.62
# Original THINGS global spectrum fit, Stewart et al. 2014 A&A 567 A61.
PUBLISHED_FLUX_JY_KMS=92.88
# Independent THINGS sample compilation (Oman et al. 2019 Table A2), defined
# at Sigma_HI = 1 Msun pc^-2.
PUBLISHED_RHI_KPC=4.5

AMP_MAX=0.15
MASS_MAX=0.10
FLUX_MAX=0.10
DRIFT_MAX=0.15
VALID_AREA_MIN=0.50


def download():
 req=Request(URL,headers={'User-Agent':UA})
 with urlopen(req,timeout=120) as r:
  h=hashlib.sha256();n=0
  with LOCAL.open('wb') as f:
   while True:
    b=r.read(1024*1024)
    if not b:break
    f.write(b);h.update(b);n+=len(b)
 return n,h.hexdigest()

def read_leroy_raw():
 rows=[]
 with LEROY.open(newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if r['galaxy']!='DDO154':continue
   s=r['source_sigmaHI_including_helium_msun_pc2'].strip()
   if not s:continue
   rows.append((float(r['source_radius_kpc']),float(s)/1.36))
 if len(rows)<3:raise RuntimeError('DDO154 Leroy profile missing')
 rows.sort()
 return np.array([x[0] for x in rows]),np.array([x[1] for x in rows])

def linear_integral(r,s,a,b,n=5000):
 x=np.linspace(a,b,n);y=np.interp(x,r,s)
 return float(np.trapezoid(2*math.pi*x*y,x))*1e6  # Msun; kpc^2 -> pc^2

def main():
 nbytes,sha=download()
 with fits.open(LOCAL,memmap=False) as hdul:
  hdr=hdul[0].header.copy();data=np.asarray(hdul[0].data,dtype=float).squeeze()
 if data.ndim!=2:raise RuntimeError(f'expected 2D squeezed MOM0, got {data.shape}')
 if str(hdr.get('BUNIT','')).strip().upper()!='JY/B*M/S':raise RuntimeError(f'unexpected BUNIT {hdr.get("BUNIT")}')
 ny,nx=data.shape
 finite=np.isfinite(data)
 nfinite=int(finite.sum());nnonfinite=int((~finite).sum());nzero=int(np.count_nonzero(finite & (data==0)));nneg=int(np.count_nonzero(finite & (data<0)))
 if nnonfinite==0:raise RuntimeError('no FITS blank/nonfinite pixels found; source blanking semantics ambiguous')

 w=WCS(hdr).celestial
 yy,xx=np.indices(data.shape,dtype=float)
 ra,dec=w.all_pix2world(xx,yy,0)
 dra=((ra-CENTER_RA_DEG+180.0)%360.0)-180.0
 east=dra*np.cos(np.deg2rad(CENTER_DEC_DEG))*3600.0
 north=(dec-CENTER_DEC_DEG)*3600.0
 pa=np.deg2rad(PA_DEG);ci=math.cos(math.radians(INC_DEG))
 major=east*math.sin(pa)+north*math.cos(pa)
 minor=east*math.cos(pa)-north*math.sin(pa)
 rell_arcsec=np.sqrt(major**2+(minor/ci)**2)

 beam_fwhm=math.sqrt(BMAJ_ARCSEC*BMIN_ARCSEC)
 pix_arcsec=math.sqrt(abs(float(hdr['CDELT1'])*float(hdr['CDELT2'])))*3600.0
 pix_area=pix_arcsec**2
 beam_area=math.pi/(4.0*math.log(2.0))*BMAJ_ARCSEC*BMIN_ARCSEC
 nu_ghz=float(hdr.get('RESTFREQ',hdr.get('RESTFRQ',1420405750.0)))/1e9
 # MOM0 is Jy/beam*m/s. Convert to K km/s, then optically-thin raw HI.
 jybeam_ms_to_k_kms=(1.222e6/(nu_ghz**2*BMAJ_ARCSEC*BMIN_ARCSEC))/1000.0
 nhi_per_kkms=1.823e18
 atoms_per_msun_pc2=1.2488e20
 sigma_factor=jybeam_ms_to_k_kms*nhi_per_kkms/atoms_per_msun_pc2*ci
 sigma=np.where(finite,data*sigma_factor,np.nan)

 kpc_per_arcsec=D_MPC*1000.0*math.pi/(180.0*3600.0)
 maxr=float(np.nanmax(rell_arcsec))*kpc_per_arcsec
 nann=int(math.floor(float(np.nanmax(rell_arcsec))/beam_fwhm))
 rows=[];seen_missing=False;interior_missing=False
 for j in range(nann):
  ain=j*beam_fwhm;aout=(j+1)*beam_fwhm;acen=(j+0.5)*beam_fwhm
  geom_area_arcsec2=math.pi*(aout*aout-ain*ain)*ci
  expected_pix=geom_area_arcsec2/pix_area
  inann=(rell_arcsec>=ain)&(rell_arcsec<aout)
  valid=inann&finite
  nv=int(valid.sum());frac=(nv/expected_pix) if expected_pix>0 else 0.0
  usable=frac>=VALID_AREA_MIN and nv>0
  if not usable:seen_missing=True
  elif seen_missing:interior_missing=True
  vals=sigma[valid]
  mean=float(np.mean(vals)) if nv else math.nan
  std=float(np.std(vals,ddof=1)) if nv>1 else math.nan
  neff=max(nv*pix_area/beam_area,1.0)
  sem=std/math.sqrt(neff) if nv>1 else math.nan
  rows.append({'annulus_index':j,'r_in_kpc':ain*kpc_per_arcsec,'r_center_kpc':acen*kpc_per_arcsec,'r_out_kpc':aout*kpc_per_arcsec,
               'valid_pixel_count':nv,'expected_pixel_count':expected_pix,'valid_area_fraction':frac,'usable':int(usable),
               'sigma_hi_raw_msun_pc2':mean,'sigma_hi_raw_std_msun_pc2':std,'sigma_hi_raw_sem_beam_msun_pc2':sem,'n_eff_beams':neff})
 if interior_missing:raise RuntimeError('DDO154 has usable annulus after a <50% valid-area annulus; frozen protocol fails closed')
 usable=[r for r in rows if r['usable']]
 if len(usable)<3:raise RuntimeError('too few usable annuli')

 # Gate 1 and Gate 5: independent beam-spaced samples against Leroy raw HI.
 lr,ls=read_leroy_raw();rlo=float(lr.min());rhi=float(lr.max())
 overlap=[r for r in usable if rlo<=r['r_center_kpc']<=rhi]
 if len(overlap)<3:raise RuntimeError(f'too few independent Leroy-overlap annuli: {len(overlap)}')
 ratios=[];fracs=[];cmp=[]
 for r in overlap:
  pub=float(np.interp(r['r_center_kpc'],lr,ls));rec=float(r['sigma_hi_raw_msun_pc2']);ratio=rec/pub
  ratios.append(ratio);fracs.append(abs(rec-pub)/pub);cmp.append({'r_kpc':r['r_center_kpc'],'reconstructed_raw_hi':rec,'leroy_raw_hi_interp':pub,'ratio':ratio,'abs_fractional_difference':abs(rec-pub)/pub})
 med_abs=float(np.median(fracs));amp_pass=med_abs<=AMP_MAX
 half=len(ratios)//2
 inner=float(np.median(ratios[:half]));outer=float(np.median(ratios[-half:]));drift=abs(inner-outer);drift_pass=drift<=DRIFT_MAX

 # Gate 2: same physical overlap interval. Reconstructed annuli are treated as
 # their measured annular means and clipped only geometrically at overlap ends.
 rec_mass=0.0
 for r in usable:
  a=max(rlo,float(r['r_in_kpc']));b=min(rhi,float(r['r_out_kpc']))
  if b>a:rec_mass+=math.pi*(b*b-a*a)*float(r['sigma_hi_raw_msun_pc2'])*1e6
 pub_mass=linear_integral(lr,ls,rlo,rhi)
 mass_frac=abs(rec_mass-pub_mass)/pub_mass;mass_pass=mass_frac<=MASS_MAX

 # Gate 3: integrate finite MOM0 map without clipping negative finite pixels.
 total_flux=float(np.nansum(data))*pix_area/beam_area/1000.0
 flux_frac=abs(total_flux-PUBLISHED_FLUX_JY_KMS)/PUBLISHED_FLUX_JY_KMS;flux_pass=flux_frac<=FLUX_MAX

 # Gate 4: first outward crossing of 1 Msun/pc^2 in contiguous usable profile.
 ur=np.array([r['r_center_kpc'] for r in usable]);us=np.array([r['sigma_hi_raw_msun_pc2'] for r in usable])
 crossings=[]
 for i in range(1,len(us)):
  if us[i-1]>=1.0 and us[i]<1.0:
   x0,x1=ur[i-1],ur[i];y0,y1=us[i-1],us[i]
   crossings.append(float(x0+(1.0-y0)*(x1-x0)/(y1-y0)))
 if not crossings:reconstructed_rhi=None;rhi_pass=False;rhi_diff=None
 else:
  reconstructed_rhi=crossings[-1]
  rhi_diff=abs(reconstructed_rhi-PUBLISHED_RHI_KPC)
  beam_kpc=beam_fwhm*kpc_per_arcsec
  rhi_pass=rhi_diff<=max(beam_kpc,0.10*PUBLISHED_RHI_KPC)

 OUTCSV.parent.mkdir(parents=True,exist_ok=True)
 with OUTCSV.open('w',newline='',encoding='utf-8') as f:
  wri=csv.DictWriter(f,fieldnames=list(rows[0]));wri.writeheader();wri.writerows(rows)
 all_pass=amp_pass and mass_pass and flux_pass and rhi_pass and drift_pass and not interior_missing
 result={
  'status':'THINGS_DDO154_MOM0_VALIDATION_PASS' if all_pass else 'THINGS_DDO154_MOM0_VALIDATION_FAIL',
  'galaxy':'DDO154','stationary_role':'calibration','protocol':'validation/stationary/THINGS_MOM0_PROFILE_RECONSTRUCTION_PROTOCOL_V1.md',
  'source':{'url':URL,'bytes':nbytes,'sha256':sha,'bunit':hdr.get('BUNIT'),'map_shape':[ny,nx],'restfreq_hz':float(hdr.get('RESTFREQ',hdr.get('RESTFRQ',1420405750.0))),
            'n_finite_pixels':nfinite,'n_blank_nonfinite_pixels':nnonfinite,'n_exact_zero_finite_pixels':nzero,'n_negative_finite_pixels':nneg},
  'geometry':{'distance_mpc':D_MPC,'inclination_deg':INC_DEG,'pa_deg':PA_DEG,'center_ra_deg':CENTER_RA_DEG,'center_dec_deg':CENTER_DEC_DEG},
  'beam':{'major_arcsec':BMAJ_ARCSEC,'minor_arcsec':BMIN_ARCSEC,'geometric_mean_arcsec':beam_fwhm,'beam_area_arcsec2':beam_area,'pixel_arcsec':pix_arcsec,
          'source':'Ianjamasimanana, de Blok & Heald 2017 AJ 153:213 Table 1; THINGS natural-weighted cube'},
  'conversion':{'jybeam_ms_to_k_kms':jybeam_ms_to_k_kms,'sigma_hi_raw_per_mom0':sigma_factor,'helium_factor_applied':0},
  'profile':{'n_annuli_total':len(rows),'n_annuli_usable_contiguous':len(usable),'max_usable_radius_kpc':float(usable[-1]['r_out_kpc']),'interior_missing':interior_missing,'valid_area_threshold':VALID_AREA_MIN,'csv':str(OUTCSV)},
  'gates':{
   'overlap_profile_amplitude':{'threshold_median_abs_fractional_difference':AMP_MAX,'n_independent_samples':len(overlap),'median_abs_fractional_difference':med_abs,'pass':amp_pass,'samples':cmp},
   'overlap_annular_hi_mass':{'threshold_fractional_difference':MASS_MAX,'range_kpc':[rlo,rhi],'reconstructed_msun':rec_mass,'published_leroy_msun':pub_mass,'fractional_difference':mass_frac,'pass':mass_pass},
   'global_hi_flux':{'threshold_fractional_difference':FLUX_MAX,'reconstructed_jy_kms':total_flux,'published_jy_kms':PUBLISHED_FLUX_JY_KMS,'fractional_difference':flux_frac,'pass':flux_pass,'published_source':'Stewart et al. 2014 A&A 567 A61, fit to original THINGS global spectrum'},
   'hi_radial_extent':{'published_rhi_kpc':PUBLISHED_RHI_KPC,'published_definition':'Sigma_HI=1 Msun pc^-2','reconstructed_rhi_kpc':reconstructed_rhi,'absolute_difference_kpc':rhi_diff,'tolerance_kpc':max(beam_fwhm*kpc_per_arcsec,0.10*PUBLISHED_RHI_KPC),'pass':rhi_pass,'published_source':'Oman et al. 2019 MNRAS 482 821 Table A2, THINGS row'},
   'no_systematic_radial_drift':{'threshold_ratio_difference':DRIFT_MAX,'inner_median_ratio':inner,'outer_median_ratio':outer,'absolute_ratio_difference':drift,'pass':drift_pass}
  },
  'all_five_gates_pass':all_pass,
  'boundary':'Calibration/source-profile validation only. No rotation velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcomes evaluated.'}
 OUTJSON.parent.mkdir(parents=True,exist_ok=True);OUTJSON.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not all_pass:raise SystemExit(2)

if __name__=='__main__':main()
