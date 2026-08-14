#!/usr/bin/env python3
"""Validate remaining THINGS calibration MOM0 reconstructions under frozen rules.

Targets: NGC2841 and NGC3198, both stationary calibration-role galaxies.
Runs the unchanged THINGS MOM0 reconstruction and source-domain gates. If no
product-matched independent H I size comparator exists under protocol v2,
radial-extent gate 4 fails closed as unavailable; it is never silently dropped.
No rotation residuals, persistence parameters, or blind outcomes are read.
"""
from __future__ import annotations
import csv, hashlib, json, math, re
from collections import deque
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

TARGETS={
 'NGC2841':'NGC_2841_NA_MOM0_THINGS.FITS',
 'NGC3198':'NGC_3198_NA_MOM0_THINGS.FITS',
}
BASE='https://things.www3.mpia.de/Data_files/'
META=Path('validation/stationary/things_calibration_validation_metadata_v1.json')
LEROY=Path('data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv')
OUTDIR=Path('data/stationary/source_reconstruction')
VALDIR=Path('validation/stationary')
SUMMARY=VALDIR/'things_remaining_calibration_mom0_validation_v1_summary.json'
UA='PersistenceFrameworkPaperI/1.0'
AMP_MAX=.15; MASS_MAX=.10; FLUX_MAX=.10; DRIFT_MAX=.15; VALID_AREA_MIN=.50


def num(s):
 m=re.search(r'[-+]?\d+(?:\.\d+)?',str(s))
 if not m: raise RuntimeError(f'no numeric prefix in {s!r}')
 return float(m.group(0))

def ra_deg(s):
 v=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',s)[:3]]
 return 15*(v[0]+v[1]/60+v[2]/3600)

def dec_deg(s):
 sign=-1 if str(s).strip().startswith('-') else 1
 v=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',s)[:3]]
 return sign*(v[0]+v[1]/60+v[2]/3600)

def download(url,tmp):
 h=hashlib.sha256(); n=0
 with urlopen(Request(url,headers={'User-Agent':UA}),timeout=180) as r,tmp.open('wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b: break
   f.write(b); h.update(b); n+=len(b)
 return n,h.hexdigest()

def metadata(m,g):
 if m['roles'].get(g)!='calibration': raise RuntimeError(f'{g} is not calibration')
 tr=m['targets_raw'][g]
 gs=tr.get('candidate_geometry_rows',[]); bs=tr.get('candidate_natural_beam_rows',[])
 if len(gs)!=1 or len(bs)!=1: raise RuntimeError(f'{g} geometry/beam ambiguity')
 geom=gs[0]; beam=bs[0]
 flux=[x for x in tr['all_walter_rows'] if x['line']>1400 and len(x['fields'])==10 and x['fields'][1].upper()!='NA']
 if len(flux)!=1: raise RuntimeError(f'{g} flux-row ambiguity: {[(x["line"],x["fields"]) for x in flux]}')
 flux=flux[0]
 wrows=[x['raw_line'] for x in m.get('wang_target_rows',[]) if x['galaxy']==g and ' THINGS ' in x['raw_line']]
 wang=None
 if len(wrows)==1:
  wf=wrows[0].split(); wang={'dhi_kpc':float(wf[1]),'distance_mpc':float(wf[3]),'raw_line':wrows[0]}
 elif len(wrows)>1: raise RuntimeError(f'{g} multiple Wang THINGS rows')
 return {
  'ra_deg':ra_deg(geom['fields'][2]),'dec_deg':dec_deg(geom['fields'][3]),'distance_mpc':num(geom['fields'][4]),
  'inclination_deg':num(geom['fields'][8]),'pa_deg':num(geom['fields'][9]),
  'beam_major_arcsec':float(beam['fields'][2]),'beam_minor_arcsec':float(beam['fields'][3]),'beam_pa_deg':float(beam['fields'][4]),
  'published_flux_jy_kms':float(flux['fields'][1]),'published_mhi_1e8_msun':float(flux['fields'][2]),
  'wang_things':wang,'walter_geometry_line':geom['line'],'walter_beam_line':beam['line'],'walter_flux_line':flux['line']}

def leroy_raw(g):
 z=[]
 with LEROY.open(newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if r['galaxy']==g and r['source_sigmaHI_including_helium_msun_pc2'].strip():
    z.append((float(r['source_radius_kpc']),float(r['source_sigmaHI_including_helium_msun_pc2'])/1.36))
 z.sort()
 if len(z)<3: raise RuntimeError(f'{g}: too few Leroy bins')
 return np.array([x[0] for x in z]),np.array([x[1] for x in z])

def integral(r,s,a,b,n=5000):
 x=np.linspace(a,b,n); return float(np.trapezoid(2*math.pi*x*np.interp(x,r,s),x))*1e6

def zero_topology(a):
 finite=np.isfinite(a); zero=finite&(a==0); neg=finite&(a<0); ny,nx=a.shape
 border=np.zeros_like(zero); border[0,:]=border[-1,:]=True; border[:,0]=border[:,-1]=True
 seen=np.zeros_like(zero); q=deque(); ys,xs=np.nonzero(zero&border)
 for y,x in zip(ys.tolist(),xs.tolist()): seen[y,x]=True; q.append((y,x))
 while q:
  y,x=q.popleft()
  for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
   yy,xx=y+dy,x+dx
   if 0<=yy<ny and 0<=xx<nx and zero[yy,xx] and not seen[yy,xx]: seen[yy,xx]=True; q.append((yy,xx))
 frac=float(seen.sum()/zero.sum()) if zero.sum() else 0
 ok=bool(zero.sum()>0 and np.all(zero[border]) and frac>.95 and neg.sum()>0)
 return {'exact_zero':int(zero.sum()),'boundary_connected_zero':int(seen.sum()),'boundary_connected_fraction':frac,
         'all_border_zero':bool(np.all(zero[border])),'negative_nonzero':int(np.count_nonzero(neg&(a!=0))),'zero_as_blank_supported':ok}

def validate(g,filename,m):
 md=metadata(m,g); url=BASE+filename; tmp=Path('/tmp')/filename
 nbytes,sha=download(url,tmp)
 with fits.open(tmp,memmap=False) as hdu: hdr=hdu[0].header.copy(); data=np.asarray(hdu[0].data,dtype=float).squeeze()
 if data.ndim!=2: raise RuntimeError(f'{g} shape {data.shape}')
 if str(hdr.get('BUNIT','')).strip().upper()!='JY/B*M/S': raise RuntimeError(f'{g} BUNIT {hdr.get("BUNIT")}')
 topo=zero_topology(data)
 if not topo['zero_as_blank_supported']: raise RuntimeError(f'{g} zero-mask topology failed: {topo}')
 valid=np.isfinite(data)&(data!=0)
 yy,xx=np.indices(data.shape,dtype=float); w=WCS(hdr).celestial; ra,dec=w.all_pix2world(xx,yy,0)
 dra=((ra-md['ra_deg']+180)%360)-180; east=dra*np.cos(np.deg2rad(md['dec_deg']))*3600; north=(dec-md['dec_deg'])*3600
 pa=math.radians(md['pa_deg']); ci=math.cos(math.radians(md['inclination_deg']))
 major=east*math.sin(pa)+north*math.cos(pa); minor=east*math.cos(pa)-north*math.sin(pa); rell=np.sqrt(major**2+(minor/ci)**2)
 bmaj=md['beam_major_arcsec']; bmin=md['beam_minor_arcsec']; bf=math.sqrt(bmaj*bmin); barea=math.pi/(4*math.log(2))*bmaj*bmin
 pix=math.sqrt(abs(float(hdr['CDELT1'])*float(hdr['CDELT2'])))*3600; parea=pix*pix
 nu=float(hdr.get('RESTFREQ',hdr.get('RESTFRQ',1420405750.0)))/1e9
 jy_to_k_kms=1.222e6/(nu*nu*bmaj*bmin)/1000
 sf=jy_to_k_kms*1.823e18/1.2488e20*ci
 sigma=np.where(valid,data*sf,np.nan); kpa=md['distance_mpc']*1000*math.pi/(180*3600)
 nann=int(math.floor(float(np.nanmax(rell))/bf)); rows=[]; seen_miss=False; interior=False
 for j in range(nann):
  ai=j*bf; ao=(j+1)*bf; ac=(j+.5)*bf; expect=math.pi*(ao*ao-ai*ai)*ci/parea
  sel=(rell>=ai)&(rell<ao)&valid; nv=int(sel.sum()); frac=nv/expect if expect>0 else 0; usable=frac>=VALID_AREA_MIN and nv>0
  if not usable: seen_miss=True
  elif seen_miss: interior=True
  vals=sigma[sel]; mean=float(np.mean(vals)) if nv else math.nan; std=float(np.std(vals,ddof=1)) if nv>1 else math.nan
  neff=max(nv*parea/barea,1.0); sem=std/math.sqrt(neff) if nv>1 else math.nan
  rows.append({'annulus_index':j,'r_in_kpc':ai*kpa,'r_center_kpc':ac*kpa,'r_out_kpc':ao*kpa,'valid_pixel_count':nv,
               'expected_pixel_count':expect,'valid_area_fraction':frac,'usable':int(usable),'sigma_hi_raw_msun_pc2':mean,
               'sigma_hi_raw_std_msun_pc2':std,'sigma_hi_raw_sem_beam_msun_pc2':sem,'n_eff_beams':neff})
 if interior: raise RuntimeError(f'{g}: usable annulus occurs after <50% valid-area annulus')
 use=[r for r in rows if r['usable']]; lr,ls=leroy_raw(g); lo,hi=float(lr.min()),float(lr.max()); ov=[r for r in use if lo<=r['r_center_kpc']<=hi]
 if len(ov)<3: raise RuntimeError(f'{g}: too few overlap annuli')
 ratios=[]; fracs=[]; samples=[]
 for r in ov:
  pub=float(np.interp(r['r_center_kpc'],lr,ls)); rec=float(r['sigma_hi_raw_msun_pc2']); rat=rec/pub
  ratios.append(rat); fracs.append(abs(rec-pub)/pub); samples.append({'r_kpc':r['r_center_kpc'],'reconstructed_raw_hi':rec,'leroy_raw_hi_interp':pub,'ratio':rat,'abs_fractional_difference':abs(rec-pub)/pub})
 amp=float(np.median(fracs)); half=len(ratios)//2; inner=float(np.median(ratios[:half])); outer=float(np.median(ratios[-half:])); drift=abs(inner-outer)
 recm=0.0
 for r in use:
  a=max(lo,float(r['r_in_kpc'])); b=min(hi,float(r['r_out_kpc']))
  if b>a: recm+=math.pi*(b*b-a*a)*float(r['sigma_hi_raw_msun_pc2'])*1e6
 pubm=integral(lr,ls,lo,hi); mfrac=abs(recm-pubm)/pubm
 flux=float(np.sum(data[valid]))*parea/barea/1000; ffrac=abs(flux-md['published_flux_jy_kms'])/md['published_flux_jy_kms']
 ur=np.array([r['r_center_kpc'] for r in use]); us=np.array([r['sigma_hi_raw_msun_pc2'] for r in use]); cross=[]
 for i in range(1,len(us)):
  if us[i-1]>=1 and us[i]<1: cross.append(float(ur[i-1]+(1-us[i-1])*(ur[i]-ur[i-1])/(us[i]-us[i-1])))
 rr=cross[-1] if cross else None; wang=md['wang_things']
 if wang is not None:
  if abs(wang['distance_mpc']-md['distance_mpc'])>1e-9: raise RuntimeError(f'{g}: Walter/Wang distance mismatch')
  pubr=wang['dhi_kpc']/2; beamk=bf*kpa; tol=max(beamk,.10*pubr); rdiff=None if rr is None else abs(rr-pubr); rpass=rr is not None and rdiff<=tol
  rg={'status':'evaluated_wang_things','published_rhi_kpc':pubr,'reconstructed_rhi_kpc':rr,'absolute_difference_kpc':rdiff,'fractional_difference':None if rr is None else rdiff/pubr,'beam_kpc':beamk,'tolerance_kpc':tol,'pass':bool(rpass),'source':wang}
 else:
  rg={'status':'not_evaluated_fail_closed','reason':'No Wang Sample=THINGS row in frozen calibration metadata; protocol v2 requires a documented priority-2 product-matched comparator before gate 4 can pass.','reconstructed_rhi_kpc':rr,'pass':False}
 gates={
  'overlap_profile_amplitude':{'threshold':AMP_MAX,'n_independent_samples':len(ov),'median_abs_fractional_difference':amp,'pass':amp<=AMP_MAX,'samples':samples},
  'overlap_annular_hi_mass':{'threshold':MASS_MAX,'range_kpc':[lo,hi],'reconstructed_msun':recm,'published_leroy_msun':pubm,'fractional_difference':mfrac,'pass':mfrac<=MASS_MAX},
  'global_hi_flux':{'threshold':FLUX_MAX,'reconstructed_jy_kms':flux,'published_walter_jy_kms':md['published_flux_jy_kms'],'fractional_difference':ffrac,'pass':ffrac<=FLUX_MAX},
  'hi_radial_extent':rg,
  'no_systematic_radial_drift':{'threshold':DRIFT_MAX,'inner_median_ratio':inner,'outer_median_ratio':outer,'absolute_ratio_difference':drift,'pass':drift<=DRIFT_MAX}}
 n=sum(bool(x['pass']) for x in gates.values()); allpass=n==5
 outcsv=OUTDIR/f'things_{g.lower()}_mom0_reconstructed_raw_hi_v1.csv'; outjson=VALDIR/f'things_{g.lower()}_mom0_validation_v1.json'
 OUTDIR.mkdir(parents=True,exist_ok=True); VALDIR.mkdir(parents=True,exist_ok=True)
 with outcsv.open('w',newline='',encoding='utf-8') as f: wr=csv.DictWriter(f,fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
 result={'status':f'THINGS_{g}_MOM0_VALIDATION_PASS' if allpass else f'THINGS_{g}_MOM0_VALIDATION_FAIL_CLOSED','galaxy':g,'stationary_role':'calibration','protocol':'validation/stationary/THINGS_MOM0_PROFILE_RECONSTRUCTION_PROTOCOL_V2.md','source':{'url':url,'bytes':nbytes,'sha256':sha,'bunit':hdr.get('BUNIT'),'shape':list(data.shape)},'source_metadata':md,'blank_semantics':topo,'conversion':{'sigma_hi_raw_per_mom0':sf,'helium_factor_applied':0},'profile':{'n_annuli_total':len(rows),'n_annuli_usable_contiguous':len(use),'max_usable_radius_kpc':float(use[-1]['r_out_kpc']) if use else None,'interior_missing':interior,'csv':str(outcsv)},'gates':gates,'n_gates_pass':n,'n_gates_fail_or_unavailable':5-n,'all_five_gates_pass':allpass,'boundary':'Calibration/source-profile validation only. No rotation velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcomes evaluated.'}
 outjson.write_text(json.dumps(result,indent=2)+'\n'); return result

def main():
 m=json.loads(META.read_text()); results=[]
 for g,f in TARGETS.items():
  try: results.append(validate(g,f,m))
  except Exception as e: results.append({'galaxy':g,'status':'VALIDATION_RUNTIME_FAIL_CLOSED','error':repr(e),'all_five_gates_pass':False})
 summary={'status':'THINGS_REMAINING_CALIBRATION_VALIDATION_COMPLETE','targets':list(TARGETS),'results':[{'galaxy':r['galaxy'],'status':r['status'],'n_gates_pass':r.get('n_gates_pass'),'all_five_gates_pass':r.get('all_five_gates_pass')} for r in results],'n_full_pass':sum(bool(r.get('all_five_gates_pass')) for r in results),'boundary':'Calibration/source-profile validation only; blind outcomes and persistence quantities remain sealed.'}
 VALDIR.mkdir(parents=True,exist_ok=True); SUMMARY.write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
 if any(r['status']=='VALIDATION_RUNTIME_FAIL_CLOSED' for r in results): raise SystemExit(3)
if __name__=='__main__': main()
