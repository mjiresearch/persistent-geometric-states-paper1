#!/usr/bin/env python3
"""Source-only QC for new FEASTS 2025 calibration H I profiles.

Targets NGC2903 and NGC4559, both frozen calibration galaxies and previously
uncertified. Uses the official machine-readable FEASTS 2025 ECSV. The source
profiles are already deprojected H I surface densities and contain no helium.
Angular radii are retained; physical radii are also recomputed at the frozen
SPARC distance without changing surface-density amplitude.

QC is acquisition/provenance only: exact one-row match, array consistency,
monotonic radii, finite/non-negative surface densities, consistency of the
published source-distance radii with the angular radii, and consistency of the
published R_1 crossing with the profile itself. No persistence or blind outcome
is read. Passing this audit does not itself promote a profile.
"""
from __future__ import annotations
import csv,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
from astropy.table import Table

FEASTS=Path('data/stationary/source_reconstruction/feasts2025_HIprof_wang25.ecsv')
MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
SPLIT=Path('validation/stationary/stationary_split_v1.csv')
OUTDIR=Path('data/stationary/source_reconstruction')
AUDIT=Path('validation/stationary/feasts2025_new_calibration_profiles_qc_v1.json')
TARGETS=('NGC2903','NGC4559')
PC_PER_ARCSEC_PER_MPC=1e6*math.pi/(180*3600)

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def crossing(r,s,level):
 # outermost downward crossing, matching an H I size convention.
 hits=[]
 for i in range(1,len(s)):
  if np.isfinite(s[i-1]) and np.isfinite(s[i]) and s[i-1]>=level and s[i]<level and s[i]!=s[i-1]:
   hits.append(float(r[i-1]+(level-s[i-1])*(r[i]-r[i-1])/(s[i]-s[i-1])))
 return hits[-1] if hits else None

def main():
 tab=Table.read(FEASTS,format='ascii.ecsv')
 split={r['galaxy']:r['stationary_role'] for r in read_csv(SPLIT)}
 master=defaultdict(list)
 for r in read_csv(MASTER):master[r['galaxy']].append(r)
 results=[]
 for g in TARGETS:
  if split.get(g)!='calibration':raise RuntimeError(f'{g} is not calibration')
  rows=tab[np.asarray(tab['name']).astype(str)==g]
  if len(rows)!=1:raise RuntimeError(f'{g}: expected one FEASTS row, found {len(rows)}')
  row=rows[0]; source_dist=float(row['Dist'])
  aa=np.asarray(row['radi_arcsec'],dtype=float); rk=np.asarray(row['radi_kpc'],dtype=float); ss=np.asarray(row['SigmaHI_Msunpc2'],dtype=float)
  same_lengths=(len(aa)==len(rk)==len(ss))
  finite=np.isfinite(aa)&np.isfinite(rk)&np.isfinite(ss)
  a=aa[finite]; k=rk[finite]; s=ss[finite]
  frozen_dist=sorted({float(x['distance_mpc']) for x in master[g]})
  if len(frozen_dist)!=1:raise RuntimeError(f'{g}: frozen distance ambiguity {frozen_dist}')
  fd=frozen_dist[0]
  rr=sorted(float(x['radius_kpc']) for x in master[g]); rotmin=min(rr);rotmax=max(rr)
  source_kpc_from_arc=a*source_dist*PC_PER_ARCSEC_PER_MPC/1000
  frozen_kpc=a*fd*PC_PER_ARCSEC_PER_MPC/1000
  source_radius_relerr=float(np.nanmax(np.abs(k-source_kpc_from_arc)/np.maximum(np.abs(k),1e-12))) if len(k) else math.inf
  r1_arc_calc=crossing(a,s,1.0); r1_kpc_calc=crossing(k,s,1.0)
  r1a=float(row['r1_arcsec']);r1k=float(row['r1_kpc'])
  step_arc=float(np.nanmedian(np.diff(a))) if len(a)>1 else math.inf
  step_kpc=float(np.nanmedian(np.diff(k))) if len(k)>1 else math.inf
  r1_arc_err=None if r1_arc_calc is None else abs(r1_arc_calc-r1a)
  r1_kpc_err=None if r1_kpc_calc is None else abs(r1_kpc_calc-r1k)
  checks={
   'exactly_one_source_row':len(rows)==1,
   'same_array_lengths':same_lengths,
   'at_least_three_finite_profile_points':len(a)>=3,
   'finite_radii_positive':bool(len(a)>=3 and np.all(a>0) and np.all(k>0)),
   'strictly_monotonic_angular_radius':bool(len(a)>=3 and np.all(np.diff(a)>0)),
   'strictly_monotonic_source_kpc_radius':bool(len(k)>=3 and np.all(np.diff(k)>0)),
   'surface_density_nonnegative':bool(len(s)>=3 and np.all(s>=0)),
   'source_kpc_matches_angular_radius_at_source_distance':source_radius_relerr<=5e-4,
   'r1_crossing_present':r1_arc_calc is not None and r1_kpc_calc is not None,
   'r1_crossing_consistent_with_tabulated_r1_within_one_profile_step':bool(r1_arc_err is not None and r1_arc_err<=step_arc and r1_kpc_err is not None and r1_kpc_err<=step_kpc),
  }
  passes=all(checks.values())
  outcsv=OUTDIR/f'feasts2025_{g.lower()}_hi_profile_raw_v1.csv'
  OUTDIR.mkdir(parents=True,exist_ok=True)
  with outcsv.open('w',newline='',encoding='utf-8') as f:
   fields=['galaxy','stationary_role','source','radius_arcsec','radius_kpc_source_distance','radius_kpc_frozen_distance','sigma_hi_raw_msun_pc2','source_distance_mpc','frozen_distance_mpc','helium_included']
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
   for av,kv,fkv,sv in zip(a,k,frozen_kpc,s):
    w.writerow({'galaxy':g,'stationary_role':'calibration','source':'Wang et al. 2025 FEASTS HIprof_wang25.ecsv','radius_arcsec':f'{av:.15g}','radius_kpc_source_distance':f'{kv:.15g}','radius_kpc_frozen_distance':f'{fkv:.15g}','sigma_hi_raw_msun_pc2':f'{sv:.15g}','source_distance_mpc':f'{source_dist:.15g}','frozen_distance_mpc':f'{fd:.15g}','helium_included':'0'})
  results.append({
   'galaxy':g,'stationary_role':'calibration','status':'FEASTS2025_SOURCE_PROFILE_QC_PASS' if passes else 'FEASTS2025_SOURCE_PROFILE_QC_FAIL_CLOSED',
   'source_profile_file':str(FEASTS),'normalized_profile_csv':str(outcsv),'source_distance_mpc':source_dist,'frozen_distance_mpc':fd,
   'n_array_slots':len(aa),'n_finite_profile_points':len(a),'radius_arcsec_min':float(a.min()) if len(a) else None,'radius_arcsec_max':float(a.max()) if len(a) else None,
   'radius_kpc_source_min':float(k.min()) if len(k) else None,'radius_kpc_source_max':float(k.max()) if len(k) else None,
   'radius_kpc_frozen_min':float(frozen_kpc.min()) if len(frozen_kpc) else None,'radius_kpc_frozen_max':float(frozen_kpc.max()) if len(frozen_kpc) else None,
   'sigma_hi_min':float(s.min()) if len(s) else None,'sigma_hi_max':float(s.max()) if len(s) else None,
   'frozen_rotation_rmin_kpc':rotmin,'frozen_rotation_rmax_kpc':rotmax,
   'inner_gap_kpc':max(0.0,float(frozen_kpc.min())-rotmin) if len(frozen_kpc) else None,
   'outer_gap_kpc':max(0.0,rotmax-float(frozen_kpc.max())) if len(frozen_kpc) else None,
   'source_radius_max_relative_error_from_angular_conversion':source_radius_relerr,
   'published_r1_arcsec':r1a,'profile_r1_arcsec':r1_arc_calc,'r1_arcsec_abs_error':r1_arc_err,'median_profile_step_arcsec':step_arc,
   'published_r1_kpc':r1k,'profile_r1_kpc':r1_kpc_calc,'r1_kpc_abs_error':r1_kpc_err,'median_profile_step_kpc':step_kpc,
   'published_r001_arcsec':float(row['r001_arcsec']),'published_r001_kpc':float(row['r001_kpc']),
   'helium_included':False,
   'source_geometry_note':'Wang et al. 2025 FEASTS total-power radial profile; elliptical-annulus geometry from the H I disk and surface density deprojected in the source analysis. Preserve source amplitude; only angular radius is converted to the frozen SPARC distance.',
   'checks':checks,'passes_all_source_qc':passes,
  })
 payload={'status':'FEASTS2025_NEW_CALIBRATION_PROFILE_QC_COMPLETE','source_release':'Wang et al. 2025 FEASTS / HIprof_wang25.ecsv','source_doi':'10.3847/1538-4357/ada95a','source_arxiv':'2501.01289','helium_convention':'raw atomic H I; no helium included','targets':list(TARGETS),'n_pass':sum(x['passes_all_source_qc'] for x in results),'results':results,'promotion_boundary':'This audit does not promote profiles. Promotion requires a separate overlay update after reviewing these source-only QC results.','science_boundary':'No rotation velocities, residuals, persistence parameters, L_A, C_A, tau_A, or blind outcomes read.'}
 AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload,indent=2))
 if payload['n_pass']!=len(TARGETS):raise SystemExit(2)
if __name__=='__main__':main()
