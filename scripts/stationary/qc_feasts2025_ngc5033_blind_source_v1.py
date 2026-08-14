#!/usr/bin/env python3
"""Locked source-only FEASTS 2025 QC for blind galaxy NGC5033.

Implements FEASTS2025_BLIND_HI_SOURCE_ACQUISITION_PROTOCOL_V1 exactly. It does
not read Vobs, residuals, persistence outputs, or any blind-model result.
"""
from __future__ import annotations
import csv,json,math
from pathlib import Path
import numpy as np
from astropy.table import Table

FEASTS=Path('data/stationary/source_reconstruction/feasts2025_HIprof_wang25.ecsv')
MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
SPLIT=Path('validation/stationary/stationary_split_v1.csv')
OUT=Path('data/stationary/source_reconstruction/feasts2025_ngc5033_hi_profile_raw_v1.csv')
AUDIT=Path('validation/stationary/feasts2025_ngc5033_blind_source_qc_v1.json')
PC_PER_ARCSEC_PER_MPC=1e6*math.pi/(180*3600)
G='NGC5033'

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def crossing(r,s,level=1.0):
 hits=[]
 for i in range(1,len(s)):
  if np.isfinite(s[i-1]) and np.isfinite(s[i]) and s[i-1]>=level and s[i]<level and s[i]!=s[i-1]:
   hits.append(float(r[i-1]+(level-s[i-1])*(r[i]-r[i-1])/(s[i]-s[i-1])))
 return hits[-1] if hits else None

def main():
 roles={r['galaxy']:r['stationary_role'] for r in read_csv(SPLIT)}
 if roles.get(G)!='blind':raise RuntimeError('NGC5033 is not frozen blind')
 tab=Table.read(FEASTS,format='ascii.ecsv');rows=tab[np.asarray(tab['name']).astype(str)==G]
 if len(rows)!=1:raise RuntimeError(f'expected one source row, found {len(rows)}')
 row=rows[0];d=float(row['Dist'])
 aa=np.asarray(row['radi_arcsec'],dtype=float);kk=np.asarray(row['radi_kpc'],dtype=float);ss=np.asarray(row['SigmaHI_Msunpc2'],dtype=float)
 same=(len(aa)==len(kk)==len(ss));m=np.isfinite(aa)&np.isfinite(kk)&np.isfinite(ss);a=aa[m];k=kk[m];s=ss[m]
 master=[r for r in read_csv(MASTER) if r['galaxy']==G]
 fd=sorted({float(r['distance_mpc']) for r in master})
 if len(fd)!=1:raise RuntimeError(f'frozen distance ambiguity {fd}')
 fd=fd[0];rot=sorted(float(r['radius_kpc']) for r in master)
 implied=k*1000/(a*PC_PER_ARCSEC_PER_MPC);dim=float(np.nanmedian(implied));span=float(np.nanmax(implied)-np.nanmin(implied))
 frozen=a*fd*PC_PER_ARCSEC_PER_MPC/1000
 r1a_calc=crossing(a,s);r1k_calc=crossing(k,s);r1a=float(row['r1_arcsec']);r1k=float(row['r1_kpc'])
 stepa=float(np.nanmedian(np.diff(a))) if len(a)>1 else math.inf;stepk=float(np.nanmedian(np.diff(k))) if len(k)>1 else math.inf
 checks={
  'exactly_one_source_row':len(rows)==1,'same_array_lengths':same,'at_least_three_finite_profile_points':len(a)>=3,
  'finite_radii_positive':bool(len(a)>=3 and np.all(a>0) and np.all(k>0)),
  'strictly_monotonic_angular_radius':bool(len(a)>=3 and np.all(np.diff(a)>0)),
  'strictly_monotonic_source_kpc_radius':bool(len(k)>=3 and np.all(np.diff(k)>0)),
  'surface_density_nonnegative':bool(len(s)>=3 and np.all(s>=0)),
  'source_distance_implied_by_radii_consistent_with_displayed_distance_precision':bool(abs(dim-d)<=0.05),
  'implied_distance_constant_across_profile':bool(span<=1e-8),
  'r1_crossing_present':r1a_calc is not None and r1k_calc is not None,
  'r1_crossing_consistent_with_tabulated_r1_within_one_profile_step':bool(r1a_calc is not None and abs(r1a_calc-r1a)<=stepa and r1k_calc is not None and abs(r1k_calc-r1k)<=stepk),
 }
 passed=all(checks.values())
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:
  fields=['galaxy','stationary_role','source','radius_arcsec','radius_kpc_source_distance','radius_kpc_frozen_distance','sigma_hi_raw_msun_pc2','source_distance_mpc','source_distance_implied_by_radii_mpc','frozen_distance_mpc','helium_included']
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for av,kv,fv,sv in zip(a,k,frozen,s):w.writerow({'galaxy':G,'stationary_role':'blind','source':'Wang et al. 2025 FEASTS HIprof_wang25.ecsv','radius_arcsec':f'{av:.15g}','radius_kpc_source_distance':f'{kv:.15g}','radius_kpc_frozen_distance':f'{fv:.15g}','sigma_hi_raw_msun_pc2':f'{sv:.15g}','source_distance_mpc':f'{d:.15g}','source_distance_implied_by_radii_mpc':f'{dim:.15g}','frozen_distance_mpc':f'{fd:.15g}','helium_included':'0'})
 result={'status':'FEASTS2025_NGC5033_BLIND_SOURCE_QC_PASS' if passed else 'FEASTS2025_NGC5033_BLIND_SOURCE_QC_FAIL_CLOSED','galaxy':G,'stationary_role':'blind','protocol':'validation/stationary/FEASTS2025_BLIND_HI_SOURCE_ACQUISITION_PROTOCOL_V1.md','source_profile_file':str(FEASTS),'normalized_profile_csv':str(OUT),'source_distance_mpc_displayed':d,'source_distance_mpc_implied_by_radii':dim,'source_distance_abs_difference_mpc':abs(dim-d),'frozen_distance_mpc':fd,'n_array_slots':len(aa),'n_finite_profile_points':len(a),'radius_arcsec_min':float(a.min()) if len(a) else None,'radius_arcsec_max':float(a.max()) if len(a) else None,'radius_kpc_source_min':float(k.min()) if len(k) else None,'radius_kpc_source_max':float(k.max()) if len(k) else None,'radius_kpc_frozen_min':float(frozen.min()) if len(frozen) else None,'radius_kpc_frozen_max':float(frozen.max()) if len(frozen) else None,'sigma_hi_min':float(s.min()) if len(s) else None,'sigma_hi_max':float(s.max()) if len(s) else None,'frozen_rotation_rmin_kpc':min(rot),'frozen_rotation_rmax_kpc':max(rot),'inner_gap_kpc':max(0.0,float(frozen.min())-min(rot)) if len(frozen) else None,'outer_gap_kpc':max(0.0,max(rot)-float(frozen.max())) if len(frozen) else None,'published_r1_arcsec':r1a,'profile_r1_arcsec':r1a_calc,'published_r1_kpc':r1k,'profile_r1_kpc':r1k_calc,'median_profile_step_arcsec':stepa,'median_profile_step_kpc':stepk,'published_r001_arcsec':float(row['r001_arcsec']),'published_r001_kpc':float(row['r001_kpc']),'helium_included':False,'checks':checks,'passes_all_locked_source_qc':passed,'blind_firewall':'No Vobs, residual acceleration, persistence prediction, model preference, L_A, C_A, or tau_A read.'}
 AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not passed:raise SystemExit(2)
if __name__=='__main__':main()
