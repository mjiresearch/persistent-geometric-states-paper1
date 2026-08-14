#!/usr/bin/env python3
"""Second calibration-only validation of the frozen THINGS MOM0 reconstruction.

Target: NGC2976 (stationary calibration role).  Geometry, natural beam, and
integrated H I flux are read from the Walter+2008 source-table audit; the
product-matched H I diameter is read from the Wang+2016 THINGS catalogue row.
The independent Leroy+2008 radial profile is used only for source-domain
validation. No rotation residual, persistence parameter, or blind outcome is
read or evaluated.
"""
from __future__ import annotations
import csv,hashlib,json,math,re
from collections import deque
from pathlib import Path
from urllib.request import Request,urlopen

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

G='NGC2976'
URL='https://things.www3.mpia.de/Data_files/NGC_2976_NA_MOM0_THINGS.FITS'
TMP=Path('/tmp/NGC_2976_NA_MOM0_THINGS.FITS')
META=Path('validation/stationary/things_calibration_validation_metadata_v1.json')
LEROY=Path('data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv')
OUTCSV=Path('data/stationary/source_reconstruction/things_ngc2976_mom0_reconstructed_raw_hi_v1.csv')
OUTJSON=Path('validation/stationary/things_ngc2976_mom0_validation_v1.json')
UA='PersistenceFrameworkPaperI/1.0'
AMP_MAX=0.15;MASS_MAX=0.10;FLUX_MAX=0.10;DRIFT_MAX=0.15;VALID_AREA_MIN=0.50

def num(s):
 m=re.search(r'[-+]?\d+(?:\.\d+)?',str(s));
 if not m:raise RuntimeError(f'no numeric prefix in {s!r}')
 return float(m.group(0))
def ra_deg(s):
 v=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',s)[:3]]
 return 15.0*(v[0]+v[1]/60+v[2]/3600)
def dec_deg(s):
 sign=-1 if str(s).strip().startswith('-') else 1
 v=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',s)[:3]]
 return sign*(v[0]+v[1]/60+v[2]/3600)
def download():
 h=hashlib.sha256();n=0
 with urlopen(Request(URL,headers={'User-Agent':UA}),timeout=120) as r,TMP.open('wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b:break
   f.write(b);h.update(b);n+=len(b)
 return n,h.hexdigest()
def read_meta():
 m=json.loads(META.read_text())
 if m['roles'].get(G)!='calibration':raise RuntimeError('NGC2976 role not calibration')
 rr=m['targets_raw'][G]['all_walter_rows']
 geom=next(x for x in rr if x['line']==935)
 beam=next(x for x in rr if len(x['fields'])==10 and x['fields'][1].upper()=='NA')
 flux=next(x for x in rr if len(x['fields'])==10 and x['fields'][1].upper()!='NA' and x['line']>1400)
 wrows=[x['raw_line'] for x in m['wang_target_rows'] if x['galaxy']==G and ' THINGS ' in x['raw_line']]
 if len(wrows)!=1:raise RuntimeError(f'expected one NGC2976 THINGS Wang row, got {wrows}')
 wf=wrows[0].split()
 return {
  'ra_deg':ra_deg(geom['fields'][2]),'dec_deg':dec_deg(geom['fields'][3]),'distance_mpc':num(geom['fields'][4]),
  'inclination_deg':num(geom['fields'][8]),'pa_deg':num(geom['fields'][9]),
  'beam_major_arcsec':float(beam['fields'][2]),'beam_minor_arcsec':float(beam['fields'][3]),'beam_pa_deg':float(beam['fields'][4]),
  'published_flux_jy_kms':float(flux['fields'][1]),'published_mhi_1e8_msun':float(flux['fields'][2]),
  'wang_dhi_kpc':float(wf[1]),'wang_distance_mpc':float(wf[3]),'wang_raw_line':wrows[0],
  'walter_geometry_line':geom['line'],'walter_beam_line':beam['line'],'walter_flux_line':flux['line']}
def read_leroy_raw():
 z=[]
 with LEROY.open(newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if r['galaxy']!=G:continue
   s=r['source_sigmaHI_including_helium_msun_pc2'].strip()
   if s:z.append((float(r['source_radius_kpc']),float(s)/1.36))
 z.sort()
 if len(z)<3:raise RuntimeError('too few finite Leroy NGC2976 bins')
 return np.array([x[0] for x in z]),np.array([x[1] for x in z])
def integral(r,s,a,b,n=5000):
 x=np.linspace(a,b,n);return float(np.trapezoid(2*math.pi*x*np.interp(x,r,s),x))*1e6
def zero_topology(a):
 finite=np.isfinite(a);zero=finite&(a==0);neg=finite&(a<0);ny,nx=a.shape
 border=np.zeros_like(zero);border[0,:]=border[-1,:]=True;border[:,0]=border[:,-1]=True
 seen=np.zeros_like(zero);q=deque();ys,xs=np.nonzero(zero&border)
 for y,x in zip(ys.tolist(),xs.tolist()):seen[y,x]=True;q.append((y,x))
 while q:
  y,x=q.popleft()
  for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
   yy,xx=y+dy,x+dx
   if 0<=yy<ny and 0<=xx<nx and zero[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((yy,xx))
 frac=float(seen.sum()/zero.sum()) if zero.sum() else 0.0
 ok=bool(zero.sum()>0 and np.all(zero[border]) and frac>0.95 and neg.sum()>0)
 return {'exact_zero':int(zero.sum()),'boundary_connected_zero':int(seen.sum()),'boundary_connected_fraction':frac,'all_border_zero':bool(np.all(zero[border])),'negative_nonzero':int(np.count_nonzero(neg&(a!=0))),'zero_as_blank_supported':ok}
def main():
 md=read_meta()
 if abs(md['wang_distance_mpc']-md['distance_mpc'])>1e-9:raise RuntimeError('Walter/Wang distance mismatch')
 nbytes,sha=download()
 with fits.open(TMP,memmap=False) as hdu:hdr=hdu[0].header.copy();data=np.asarray(hdu[0].data,dtype=float).squeeze()
 if data.ndim!=2:raise RuntimeError(data.shape)
 if str(hdr.get('BUNIT','')).strip().upper()!='JY/B*M/S':raise RuntimeError(hdr.get('BUNIT'))
 topo=zero_topology(data)
 if not topo['zero_as_blank_supported']:raise RuntimeError(f'NGC2976 zero-mask topology failed: {topo}')
 valid=np.isfinite(data)&(data!=0)
 yy,xx=np.indices(data.shape,dtype=float);w=WCS(hdr).celestial;ra,dec=w.all_pix2world(xx,yy,0)
 dra=((ra-md['ra_deg']+180)%360)-180;east=dra*np.cos(np.deg2rad(md['dec_deg']))*3600;north=(dec-md['dec_deg'])*3600
 pa=math.radians(md['pa_deg']);ci=math.cos(math.radians(md['inclination_deg']))
 major=east*math.sin(pa)+north*math.cos(pa);minor=east*math.cos(pa)-north*math.sin(pa);rell=np.sqrt(major**2+(minor/ci)**2)
 bmaj=md['beam_major_arcsec'];bmin=md['beam_minor_arcsec'];bf=math.sqrt(bmaj*bmin);barea=math.pi/(4*math.log(2))*bmaj*bmin
 pix=math.sqrt(abs(float(hdr['CDELT1'])*float(hdr['CDELT2'])))*3600;parea=pix*pix
 nu=float(hdr.get('RESTFREQ',hdr.get('RESTFRQ',1420405750.0)))/1e9
 jy_to_k_kms=1.222e6/(nu*nu*bmaj*bmin)/1000
 sf=jy_to_k_kms*1.823e18/1.2488e20*ci
 sigma=np.where(valid,data*sf,np.nan)
 kpa=md['distance_mpc']*1000*math.pi/(180*3600);nann=int(math.floor(float(np.nanmax(rell))/bf));rows=[];seen_miss=False;interior=False
 for j in range(nann):
  ai=j*bf;ao=(j+1)*bf;ac=(j+.5)*bf;expect=math.pi*(ao*ao-ai*ai)*ci/parea;sel=(rell>=ai)&(rell<ao)&valid;nv=int(sel.sum());frac=nv/expect if expect>0 else 0;usable=frac>=VALID_AREA_MIN and nv>0
  if not usable:seen_miss=True
  elif seen_miss:interior=True
  vals=sigma[sel];mean=float(np.mean(vals)) if nv else math.nan;std=float(np.std(vals,ddof=1)) if nv>1 else math.nan;neff=max(nv*parea/barea,1.0);sem=std/math.sqrt(neff) if nv>1 else math.nan
  rows.append({'annulus_index':j,'r_in_kpc':ai*kpa,'r_center_kpc':ac*kpa,'r_out_kpc':ao*kpa,'valid_pixel_count':nv,'expected_pixel_count':expect,'valid_area_fraction':frac,'usable':int(usable),'sigma_hi_raw_msun_pc2':mean,'sigma_hi_raw_std_msun_pc2':std,'sigma_hi_raw_sem_beam_msun_pc2':sem,'n_eff_beams':neff})
 if interior:raise RuntimeError('usable annulus occurs after <50% valid-area annulus')
 use=[r for r in rows if r['usable']]
 lr,ls=read_leroy_raw();lo,hi=float(lr.min()),float(lr.max());ov=[r for r in use if lo<=r['r_center_kpc']<=hi]
 if len(ov)<3:raise RuntimeError('too few independent overlap annuli')
 ratios=[];fracs=[];samples=[]
 for r in ov:
  pub=float(np.interp(r['r_center_kpc'],lr,ls));rec=float(r['sigma_hi_raw_msun_pc2']);rat=rec/pub;ratios.append(rat);fracs.append(abs(rec-pub)/pub);samples.append({'r_kpc':r['r_center_kpc'],'reconstructed_raw_hi':rec,'leroy_raw_hi_interp':pub,'ratio':rat,'abs_fractional_difference':abs(rec-pub)/pub})
 amp=float(np.median(fracs));amp_pass=amp<=AMP_MAX;half=len(ratios)//2;inner=float(np.median(ratios[:half]));outer=float(np.median(ratios[-half:]));drift=abs(inner-outer);drift_pass=drift<=DRIFT_MAX
 recm=0.0
 for r in use:
  a=max(lo,float(r['r_in_kpc']));b=min(hi,float(r['r_out_kpc']))
  if b>a:recm+=math.pi*(b*b-a*a)*float(r['sigma_hi_raw_msun_pc2'])*1e6
 pubm=integral(lr,ls,lo,hi);mfrac=abs(recm-pubm)/pubm;mass_pass=mfrac<=MASS_MAX
 flux=float(np.sum(data[valid]))*parea/barea/1000;ffrac=abs(flux-md['published_flux_jy_kms'])/md['published_flux_jy_kms'];flux_pass=ffrac<=FLUX_MAX
 ur=np.array([r['r_center_kpc'] for r in use]);us=np.array([r['sigma_hi_raw_msun_pc2'] for r in use]);cross=[]
 for i in range(1,len(us)):
  if us[i-1]>=1 and us[i]<1:
   cross.append(float(ur[i-1]+(1-us[i-1])*(ur[i]-ur[i-1])/(us[i]-us[i-1])))
 rr=cross[-1] if cross else None;pubr=md['wang_dhi_kpc']/2;beamk=bf*kpa;tol=max(beamk,.10*pubr);rdiff=None if rr is None else abs(rr-pubr);rpass=rr is not None and rdiff<=tol
 OUTCSV.parent.mkdir(parents=True,exist_ok=True)
 with OUTCSV.open('w',newline='',encoding='utf-8') as f:wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
 gates={'overlap_profile_amplitude':{'threshold':AMP_MAX,'n_independent_samples':len(ov),'median_abs_fractional_difference':amp,'pass':amp_pass,'samples':samples},'overlap_annular_hi_mass':{'threshold':MASS_MAX,'range_kpc':[lo,hi],'reconstructed_msun':recm,'published_leroy_msun':pubm,'fractional_difference':mfrac,'pass':mass_pass},'global_hi_flux':{'threshold':FLUX_MAX,'reconstructed_jy_kms':flux,'published_walter_jy_kms':md['published_flux_jy_kms'],'fractional_difference':ffrac,'pass':flux_pass},'hi_radial_extent':{'published_wang_rhi_kpc':pubr,'reconstructed_rhi_kpc':rr,'absolute_difference_kpc':rdiff,'fractional_difference':None if rr is None else rdiff/pubr,'beam_kpc':beamk,'tolerance_kpc':tol,'pass':rpass},'no_systematic_radial_drift':{'threshold':DRIFT_MAX,'inner_median_ratio':inner,'outer_median_ratio':outer,'absolute_ratio_difference':drift,'pass':drift_pass}}
 n=sum(bool(x['pass']) for x in gates.values());allpass=n==5
 result={'status':'THINGS_NGC2976_MOM0_VALIDATION_PASS' if allpass else 'THINGS_NGC2976_MOM0_VALIDATION_FAIL','galaxy':G,'stationary_role':'calibration','protocol':'validation/stationary/THINGS_MOM0_PROFILE_RECONSTRUCTION_PROTOCOL_V1.md','source':{'url':URL,'bytes':nbytes,'sha256':sha,'bunit':hdr.get('BUNIT'),'shape':list(data.shape)},'source_metadata':md,'blank_semantics':topo,'conversion':{'sigma_hi_raw_per_mom0':sf,'helium_factor_applied':0},'profile':{'n_annuli_total':len(rows),'n_annuli_usable_contiguous':len(use),'max_usable_radius_kpc':float(use[-1]['r_out_kpc']) if use else None,'interior_missing':interior,'csv':str(OUTCSV)},'gates':gates,'n_gates_pass':n,'n_gates_fail':5-n,'all_five_gates_pass':allpass,'boundary':'Calibration/source-profile validation only. No rotation velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcomes evaluated.'}
 OUTJSON.parent.mkdir(parents=True,exist_ok=True);OUTJSON.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not allpass:raise SystemExit(2)
if __name__=='__main__':main()
