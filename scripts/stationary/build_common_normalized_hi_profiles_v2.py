#!/usr/bin/env python3
"""Build common-normalized H I source products for the 31 certified galaxies.

V2 preserves source blanks as missing and excludes edge-only missing Leroy rows
from measured support under STATIONARY_HI_MISSING_VALUE_POLICY_V1.

No interpolation, source-current evaluation, persistence parameters, or blind
outcomes are evaluated here.
"""
from __future__ import annotations
import csv,json,math
from collections import defaultdict
from pathlib import Path

MAN=Path('data/stationary/source_reconstruction/certified_hi_normalization_manifest_v1.csv')
OUT_TAB=Path('data/stationary/source_reconstruction/certified_hi_common_tabulated_v2.csv')
OUT_ANA=Path('data/stationary/source_reconstruction/certified_hi_common_analytic_v2.csv')
SUMMARY=Path('validation/stationary/certified_hi_common_normalized_v2_summary.json')

ART={
 'ch06':'data/stationary/source_reconstruction/ch06_ngc0024_hi_profile_v1.csv',
 'ge04':'data/stationary/source_reconstruction/ge04_vector_hi_profiles_v1.csv',
 'ha14':'data/stationary/source_reconstruction/ha14_vector_hi_profiles_v2.csv',
 'hix':'data/stationary/source_reconstruction/hix2018_ngc0289_hi_profile_v1.csv',
 'i168':'data/stationary/source_reconstruction/iorio2017_ddo168_hi_profile_v1.csv',
 'i2':'data/stationary/source_reconstruction/iorio2017_ddo87_ddo126_hi_profiles_v1.csv',
 'u4483':'data/stationary/source_reconstruction/lelli2012b_ugc4483_hi_profile_v1.csv',
 'leroy':'data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv',
 'n5907':'data/stationary/source_reconstruction/sa87_ngc5907_heroes2015_hi_m0_mean_v1.csv',
 'vm97':'data/stationary/source_reconstruction/vm97_ngc6015_hi_profile_v1.csv',
 'n300':'data/stationary/source_reconstruction/westmeier2011_ngc300_gas_profile_v1.csv',
 'begum':'data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv',
 'jadhav':'data/stationary/source_reconstruction/jadhav_banerjee2019_lsb_hi_analytic_profiles_v1.csv'}

def read_csv(p):
 with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def fval(x):return None if x is None or str(x).strip()=='' else float(x)
def arcsec_to_kpc(a,d_mpc):return float(a)*float(d_mpc)*1000.0*math.pi/(180.0*3600.0)
def fmt(x):return '' if x is None else f'{float(x):.12g}'

def main():
 man=read_csv(MAN); mm={r['galaxy']:r for r in man}
 if len(mm)!=31:raise RuntimeError('normalization manifest must contain exactly 31 galaxies')
 tab=[]; missing_excluded=defaultdict(int)
 def emit(g,idx,source_radius,source_unit,r_frozen,sigma,e_minus=None,e_plus=None,source_note=''):
  m=mm[g]; mult=float(m['surface_density_multiplier_to_common_1p33'])
  if sigma is None or not math.isfinite(sigma) or sigma<0 or r_frozen<0:raise RuntimeError(f'invalid included row {g} {idx}')
  tab.append({'galaxy':g,'stationary_role':m['stationary_role'],'sample_index':idx,
   'source_artifact':m['source_artifact'],'source_radius_value':fmt(source_radius),'source_radius_unit':source_unit,
   'radius_kpc_frozen':fmt(r_frozen),'sigma_source_msun_pc2':fmt(sigma),
   'sigma_source_err_minus_msun_pc2':fmt(e_minus),'sigma_source_err_plus_msun_pc2':fmt(e_plus),
   'surface_density_multiplier_to_common_1p33':m['surface_density_multiplier_to_common_1p33'],
   'sigma_neutral_1p33_msun_pc2':fmt(sigma*mult),
   'sigma_neutral_1p33_err_minus_msun_pc2':fmt(None if e_minus is None else e_minus*mult),
   'sigma_neutral_1p33_err_plus_msun_pc2':fmt(None if e_plus is None else e_plus*mult),
   'radius_mapping_method':m['radius_mapping_method'],'helium_mapping_method':m['helium_mapping_method'],
   'inclination_amplitude_rescale':'0','source_note':source_note})

 for key in ('ch06','hix'):
  for i,r in enumerate(read_csv(ART[key])):
   emit(r['galaxy'],i,fval(r.get('radius_kpc_source') or r.get('radius_kpc_frozen')),'kpc_source',
        fval(r['radius_kpc_frozen']),fval(r['sigma_hi_msun_pc2']))

 specs=[
  ('ge04','radius_arcsec_vector','sigma_hi_msun_pc2',None,None),
  ('i168','source_radius_arcsec','source_sigmaHI_msun_pc2','source_sigmaHI_err_msun_pc2','source_sigmaHI_err_msun_pc2'),
  ('i2','source_radius_arcsec','source_sigmaHI_msun_pc2','source_sigmaHI_err_msun_pc2','source_sigmaHI_err_msun_pc2'),
  ('u4483','radius_arcsec','sigma_hi_msun_pc2',None,None),
  ('vm97','radius_arcsec_vector','sigma_hi_msun_pc2',None,None),
  ('n300','radius_arcsec','sigma_gas_msun_pc2','sigma_gas_err_msun_pc2','sigma_gas_err_msun_pc2')]
 for key,rc,sc,em,ep in specs:
  counters=defaultdict(int)
  for r in read_csv(ART[key]):
   g=r['galaxy']; a=fval(r[rc]); rf=arcsec_to_kpc(a,float(mm[g]['frozen_distance_mpc']))
   idx=counters[g];counters[g]+=1
   emit(g,idx,a,'arcsec',rf,fval(r[sc]),fval(r.get(em)) if em else None,fval(r.get(ep)) if ep else None)

 counters=defaultdict(int)
 for r in read_csv(ART['ha14']):
  g=r['galaxy']; scale=float(mm[g]['radius_multiplicative_factor_if_source_kpc']); idx=counters[g];counters[g]+=1
  emit(g,idx,fval(r['radius_kpc']),'kpc_source',fval(r['radius_kpc'])*scale,fval(r['sigma_hi_msun_pc2']),fval(r.get('sigma_hi_err_minus_msun_pc2')),fval(r.get('sigma_hi_err_plus_msun_pc2')))

 # Leroy: preserve source blanks as missing; accept only one contiguous finite block
 # per galaxy, as frozen by STATIONARY_HI_MISSING_VALUE_POLICY_V1.
 by_leroy=defaultdict(list)
 for r in read_csv(ART['leroy']):by_leroy[r['galaxy']].append(r)
 for g,rr in sorted(by_leroy.items()):
  sig=[fval(r['source_sigmaHI_including_helium_msun_pc2']) for r in rr]
  finite=[i for i,x in enumerate(sig) if x is not None and math.isfinite(x)]
  if not finite:raise RuntimeError(f'Leroy {g}: no finite H I values')
  lo,hi=min(finite),max(finite)
  if any(sig[i] is None or not math.isfinite(sig[i]) for i in range(lo,hi+1)):
   raise RuntimeError(f'Leroy {g}: interior missing H I value violates frozen policy')
  scale=float(mm[g]['radius_multiplicative_factor_if_source_kpc'])
  out_idx=0
  for i,r in enumerate(rr):
   sigma=sig[i]
   if sigma is None or not math.isfinite(sigma):
    missing_excluded[g]+=1
    continue
   e=fval(r['source_sigmaHI_rms_msun_pc2'])
   emit(g,out_idx,fval(r['source_radius_kpc']),'kpc_source',fval(r['source_radius_kpc'])*scale,sigma,e,e,
        source_note='finite Leroy table7 measured row; source blank edge rows excluded under frozen missing-value policy')
   out_idx+=1

 if dict(missing_excluded) not in ({}, {'NGC2841':5,'NGC2976':8}):
  raise RuntimeError(f'unexpected missing-row pattern: {dict(missing_excluded)}')

 # NGC5907: consume the already-certified Paper-I m=0 artifact directly.
 # The recovery script verified identical approaching/receding source radius grids
 # before constructing the arithmetic mean, so no side re-pairing occurs here.
 n5907=read_csv(ART['n5907'])
 if len(n5907)!=54:raise RuntimeError(f'NGC5907 m0 row count changed: {len(n5907)}')
 scale=float(mm['NGC5907']['radius_multiplicative_factor_if_source_kpc'])
 for i,r in enumerate(n5907):
  idx=int(r['sample_index'])
  if idx!=i:raise RuntimeError(f'NGC5907 m0 sample index changed at row {i}: {idx}')
  rs=fval(r['radius_kpc_source']); sigma=fval(r['sigma_hi_m0_mean_msun_pc2'])
  emit('NGC5907',idx,rs,'kpc_source',rs*scale,sigma,
       source_note='certified Paper-I deterministic arithmetic mean of source-published approaching/receding Figure 29 Sigma_HI on identical native radii; side half-difference retained in source artifact, not treated as measurement uncertainty')

 tab_gals=sorted({r['galaxy'] for r in tab})
 expected_tab=sorted(g for g,m in mm.items() if m['acquisition_status']=='raw_source_profile_ingested')
 if tab_gals!=expected_tab:raise RuntimeError(f'tabulated galaxy mismatch: got {tab_gals}, expected {expected_tab}')
 for g in tab_gals:
  rr=[float(x['radius_kpc_frozen']) for x in tab if x['galaxy']==g]
  if any(b<=a for a,b in zip(rr,rr[1:])):raise RuntimeError(f'non-increasing radius after normalization: {g}')

 ana=[]
 for r in read_csv(ART['begum']):
  g=r['galaxy']; m=mm[g]; d=float(m['frozen_distance_mpc']); mult=float(m['surface_density_multiplier_to_common_1p33'])
  r0=arcsec_to_kpc(fval(r['r0_arcsec']),d); r0e=arcsec_to_kpc(fval(r['r0_err_arcsec']),d)
  c=arcsec_to_kpc(fval(r['c_arcsec']) or 0,d); ce=arcsec_to_kpc(fval(r['c_err_arcsec']),d) if fval(r['c_err_arcsec']) is not None else None
  ana.append({'galaxy':g,'stationary_role':m['stationary_role'],'source_artifact':m['source_artifact'],'profile_family':'offcentered_gaussian_sum',
   'n_components':'1','sigma01_neutral_1p33_msun_pc2':fmt(fval(r['sigma0_msun_pc2'])*mult),'sigma01_err_neutral_1p33_msun_pc2':fmt(fval(r['sigma0_err_msun_pc2'])*mult),
   'a1_kpc_frozen':fmt(c),'a1_err_kpc_frozen':fmt(ce),'r01_kpc_frozen':fmt(r0),'r01_err_kpc_frozen':fmt(r0e),
   'sigma02_neutral_1p33_msun_pc2':'','sigma02_err_neutral_1p33_msun_pc2':'','a2_kpc_frozen':'','a2_err_kpc_frozen':'','r02_kpc_frozen':'','r02_err_kpc_frozen':'',
   'surface_density_multiplier_to_common_1p33':m['surface_density_multiplier_to_common_1p33'],'radius_mapping_method':m['radius_mapping_method'],'inclination_amplitude_rescale':'0'})
 for r in read_csv(ART['jadhav']):
  g=r['galaxy'];m=mm[g]; mult=float(m['surface_density_multiplier_to_common_1p33']); scale=float(m['radius_multiplicative_factor_if_source_kpc'])
  has2=fval(r['sigma02_msun_pc2']) is not None
  def rs(k):return None if fval(r[k]) is None else fval(r[k])*scale
  ana.append({'galaxy':g,'stationary_role':m['stationary_role'],'source_artifact':m['source_artifact'],'profile_family':'offcentered_gaussian_sum',
   'n_components':'2' if has2 else '1','sigma01_neutral_1p33_msun_pc2':fmt(fval(r['sigma01_msun_pc2'])*mult),'sigma01_err_neutral_1p33_msun_pc2':fmt(fval(r['sigma01_err_msun_pc2'])*mult),
   'a1_kpc_frozen':fmt(rs('a1_kpc')),'a1_err_kpc_frozen':fmt(rs('a1_err_kpc')),'r01_kpc_frozen':fmt(rs('r01_kpc')),'r01_err_kpc_frozen':fmt(rs('r01_err_kpc')),
   'sigma02_neutral_1p33_msun_pc2':fmt(None if not has2 else fval(r['sigma02_msun_pc2'])*mult),'sigma02_err_neutral_1p33_msun_pc2':fmt(None if not has2 else fval(r['sigma02_err_msun_pc2'])*mult),
   'a2_kpc_frozen':fmt(rs('a2_kpc')),'a2_err_kpc_frozen':fmt(rs('a2_err_kpc')),'r02_kpc_frozen':fmt(rs('r02_kpc')),'r02_err_kpc_frozen':fmt(rs('r02_err_kpc')),
   'surface_density_multiplier_to_common_1p33':m['surface_density_multiplier_to_common_1p33'],'radius_mapping_method':m['radius_mapping_method'],'inclination_amplitude_rescale':'0'})
 ana.sort(key=lambda x:x['galaxy'])
 expected_ana=sorted(g for g,m in mm.items() if m['acquisition_status']=='analytic_profile_recovered')
 if [x['galaxy'] for x in ana]!=expected_ana:raise RuntimeError('analytic galaxy mismatch')

 OUT_TAB.parent.mkdir(parents=True,exist_ok=True)
 with OUT_TAB.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(tab[0]));w.writeheader();w.writerows(tab)
 with OUT_ANA.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(ana[0]));w.writeheader();w.writerows(ana)
 result={'status':'CERTIFIED_HI_COMMON_NORMALIZED_V2_BUILT','n_certified_galaxies':len(tab_gals)+len(ana),'n_tabulated_galaxies':len(tab_gals),'n_analytic_galaxies':len(ana),
  'n_tabulated_rows':len(tab),'n_source_missing_rows_excluded':sum(missing_excluded.values()),'missing_rows_excluded_by_galaxy':dict(sorted(missing_excluded.items())),
  'tabulated_role_counts':{'calibration':sum(mm[g]['stationary_role']=='calibration' for g in tab_gals),'blind':sum(mm[g]['stationary_role']=='blind' for g in tab_gals)},
  'analytic_role_counts':{'calibration':sum(x['stationary_role']=='calibration' for x in ana),'blind':sum(x['stationary_role']=='blind' for x in ana)},
  'outputs':[str(OUT_TAB),str(OUT_ANA)],'normalization_policy':'validation/stationary/STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md',
  'missing_value_policy':'validation/stationary/STATIONARY_HI_MISSING_VALUE_POLICY_V1.md',
  'boundary':'Normalization only; no interpolation, source-current evaluation, L_A, C_A, tau_A, persistence prediction, or blind outcome evaluated.'}
 SUMMARY.parent.mkdir(parents=True,exist_ok=True);SUMMARY.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
