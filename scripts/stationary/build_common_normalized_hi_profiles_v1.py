#!/usr/bin/env python3
"""Build common-normalized H I source products for the 31 certified galaxies.

Outputs:
- 24 tabulated profiles on the frozen radial scale and common 1.33 neutral-gas convention;
- 7 published analytic profiles with their length parameters on the frozen scale.

No interpolation, source-current evaluation, persistence parameters, or blind
outcomes are evaluated here.
"""
from __future__ import annotations
import csv,json,math
from collections import defaultdict
from pathlib import Path

MAN=Path('data/stationary/source_reconstruction/certified_hi_normalization_manifest_v1.csv')
OUT_TAB=Path('data/stationary/source_reconstruction/certified_hi_common_tabulated_v1.csv')
OUT_ANA=Path('data/stationary/source_reconstruction/certified_hi_common_analytic_v1.csv')
SUMMARY=Path('validation/stationary/certified_hi_common_normalized_v1_summary.json')

ART={
 'ch06':'data/stationary/source_reconstruction/ch06_ngc0024_hi_profile_v1.csv',
 'ge04':'data/stationary/source_reconstruction/ge04_vector_hi_profiles_v1.csv',
 'ha14':'data/stationary/source_reconstruction/ha14_vector_hi_profiles_v2.csv',
 'hix':'data/stationary/source_reconstruction/hix2018_ngc0289_hi_profile_v1.csv',
 'i168':'data/stationary/source_reconstruction/iorio2017_ddo168_hi_profile_v1.csv',
 'i2':'data/stationary/source_reconstruction/iorio2017_ddo87_ddo126_hi_profiles_v1.csv',
 'u4483':'data/stationary/source_reconstruction/lelli2012b_ugc4483_hi_profile_v1.csv',
 'leroy':'data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv',
 'n5907':'data/stationary/source_reconstruction/sa87_ngc5907_heroes2015_hi_side_profiles_v1.csv',
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
 tab=[]
 def emit(g,idx,source_radius,source_unit,r_frozen,sigma,e_minus=None,e_plus=None,source_note=''):
  m=mm[g]; mult=float(m['surface_density_multiplier_to_common_1p33'])
  if sigma is None or sigma<0 or r_frozen<0:raise RuntimeError(f'invalid row {g} {idx}')
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

 # Explicit frozen-radius products.
 for key in ('ch06','hix'):
  for i,r in enumerate(read_csv(ART[key])):
   emit(r['galaxy'],i,fval(r.get('radius_kpc_source') or r.get('radius_kpc_frozen')), 'kpc_source',
        fval(r['radius_kpc_frozen']),fval(r['sigma_hi_msun_pc2']))
 # Angular-radius raw-HI products.
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
 # Source-kpc profiles with explicit frozen/source distance factors.
 counters=defaultdict(int)
 for r in read_csv(ART['ha14']):
  g=r['galaxy']; scale=float(mm[g]['radius_multiplicative_factor_if_source_kpc']); idx=counters[g];counters[g]+=1
  emit(g,idx,fval(r['radius_kpc']),'kpc_source',fval(r['radius_kpc'])*scale,fval(r['sigma_hi_msun_pc2']),fval(r.get('sigma_hi_err_minus_msun_pc2')),fval(r.get('sigma_hi_err_plus_msun_pc2')))
 counters=defaultdict(int)
 for r in read_csv(ART['leroy']):
  g=r['galaxy']; scale=float(mm[g]['radius_multiplicative_factor_if_source_kpc']); idx=counters[g];counters[g]+=1
  e=fval(r['source_sigmaHI_rms_msun_pc2'])
  emit(g,idx,fval(r['source_radius_kpc']),'kpc_source',fval(r['source_radius_kpc'])*scale,fval(r['source_sigmaHI_including_helium_msun_pc2']),e,e)
 # NGC5907: deterministic m=0 mean of paired approaching/receding side bins.
 sides=defaultdict(list)
 for r in read_csv(ART['n5907']):sides[int(r['sample_index'])].append(r)
 scale=float(mm['NGC5907']['radius_multiplicative_factor_if_source_kpc'])
 if len(sides)!=54 or any(len(v)!=2 for v in sides.values()):raise RuntimeError('NGC5907 side pairing changed')
 for idx in sorted(sides):
  pair=sides[idx]; rs=[fval(x['radius_kpc_source']) for x in pair]; ss=[fval(x['sigma_hi_msun_pc2']) for x in pair]
  rmean=sum(rs)/2; smean=sum(ss)/2
  emit('NGC5907',idx,rmean,'kpc_source',rmean*scale,smean,source_note='deterministic mean of paired approaching/receding Figure 29 side values')

 tab_gals=sorted({r['galaxy'] for r in tab})
 expected_tab=sorted(g for g,m in mm.items() if m['acquisition_status']=='raw_source_profile_ingested')
 if tab_gals!=expected_tab:raise RuntimeError(f'tabulated galaxy mismatch: got {tab_gals}, expected {expected_tab}')
 # Enforce strictly increasing common radii within each tabulated profile.
 for g in tab_gals:
  rr=[float(x['radius_kpc_frozen']) for x in tab if x['galaxy']==g]
  if any(b<=a for a,b in zip(rr,rr[1:])):raise RuntimeError(f'non-increasing radius after normalization: {g}')

 # Analytic normalized representations: unified off-centred Gaussian component columns.
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
 result={'status':'CERTIFIED_HI_COMMON_NORMALIZED_V1_BUILT','n_certified_galaxies':len(tab_gals)+len(ana),'n_tabulated_galaxies':len(tab_gals),'n_analytic_galaxies':len(ana),
  'n_tabulated_rows':len(tab),'tabulated_role_counts':{'calibration':sum(mm[g]['stationary_role']=='calibration' for g in tab_gals),'blind':sum(mm[g]['stationary_role']=='blind' for g in tab_gals)},
  'analytic_role_counts':{'calibration':sum(x['stationary_role']=='calibration' for x in ana),'blind':sum(x['stationary_role']=='blind' for x in ana)},
  'outputs':[str(OUT_TAB),str(OUT_ANA)],'policy':'validation/stationary/STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md',
  'boundary':'Normalization only; no interpolation, source-current evaluation, L_A, C_A, tau_A, persistence prediction, or blind outcome evaluated.'}
 SUMMARY.parent.mkdir(parents=True,exist_ok=True);SUMMARY.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
