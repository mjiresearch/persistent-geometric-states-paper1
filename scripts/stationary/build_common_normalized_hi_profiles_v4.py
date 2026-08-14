#!/usr/bin/env python3
"""Extend the validated v3 common-normalized profiles with FEASTS 2025 additions.

The existing v3 products remain the immutable 31-galaxy baseline. Version 4
verifies that the only newly certified raw profiles absent from v3 are NGC2903
and NGC4559, then appends their exact FEASTS source rows using the same common
normalization: frozen-distance radius already recorded in the acquisition file,
and Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw. No interpolation/continuation,
persistence quantities, or blind outcomes are evaluated.
"""
from __future__ import annotations
import csv,json,shutil
from pathlib import Path
from collections import Counter

MAN=Path('data/stationary/source_reconstruction/certified_hi_normalization_manifest_v2.csv')
BASE_TAB=Path('data/stationary/source_reconstruction/certified_hi_common_tabulated_v3.csv')
BASE_ANA=Path('data/stationary/source_reconstruction/certified_hi_common_analytic_v3.csv')
OUT_TAB=Path('data/stationary/source_reconstruction/certified_hi_common_tabulated_v4.csv')
OUT_ANA=Path('data/stationary/source_reconstruction/certified_hi_common_analytic_v4.csv')
SUMMARY=Path('validation/stationary/certified_hi_common_normalized_v4_summary.json')
NEW={'NGC2903','NGC4559'}

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def fmt(x):return f'{float(x):.12g}'

def main():
 man=read_csv(MAN);mm={r['galaxy']:r for r in man}
 if len(mm)!=len(man):raise RuntimeError('duplicate normalization-manifest galaxy')
 base_tab=read_csv(BASE_TAB);base_ana=read_csv(BASE_ANA)
 base_gals={r['galaxy'] for r in base_tab}|{r['galaxy'] for r in base_ana}
 current=set(mm)
 additions=current-base_gals;removed=base_gals-current
 if additions!=NEW or removed:raise RuntimeError(f'unexpected delta from v3 baseline: additions={sorted(additions)} removed={sorted(removed)}')
 if len(base_gals)!=31:raise RuntimeError(f'v3 baseline changed: expected 31 galaxies, got {len(base_gals)}')
 fields=list(base_tab[0]);out=list(base_tab)
 added_rows={}
 for g in sorted(NEW):
  m=mm[g]
  if m['stationary_role']!='calibration' or m['acquisition_status']!='raw_source_profile_ingested':raise RuntimeError(f'{g}: unexpected manifest state')
  art=Path(m['source_artifact']);rr=read_csv(art)
  if not rr or any(x['galaxy']!=g for x in rr):raise RuntimeError(f'{g}: source artifact content mismatch')
  prev=None
  for i,r in enumerate(rr):
   radius=float(r['radius_kpc_frozen_distance']);sigma=float(r['sigma_hi_raw_msun_pc2']);arc=float(r['radius_arcsec'])
   if radius<=0 or sigma<0:raise RuntimeError(f'{g}: invalid radius/sigma row {i}')
   if prev is not None and radius<=prev:raise RuntimeError(f'{g}: non-increasing radius')
   prev=radius;mult=float(m['surface_density_multiplier_to_common_1p33'])
   row={'galaxy':g,'stationary_role':'calibration','sample_index':str(i),'source_artifact':str(art),'source_radius_value':fmt(arc),'source_radius_unit':'arcsec','radius_kpc_frozen':fmt(radius),'sigma_source_msun_pc2':fmt(sigma),'sigma_source_err_minus_msun_pc2':'','sigma_source_err_plus_msun_pc2':'','surface_density_multiplier_to_common_1p33':m['surface_density_multiplier_to_common_1p33'],'sigma_neutral_1p33_msun_pc2':fmt(sigma*mult),'sigma_neutral_1p33_err_minus_msun_pc2':'','sigma_neutral_1p33_err_plus_msun_pc2':'','radius_mapping_method':m['radius_mapping_method'],'helium_mapping_method':m['helium_mapping_method'],'inclination_amplitude_rescale':'0','source_note':'Official FEASTS 2025 machine-readable raw-HI profile; angular radius mapped to frozen distance during acquisition; no interpolation or continuation.'}
   if set(row)!=set(fields):raise RuntimeError('v4 row schema mismatch')
   out.append(row)
  added_rows[g]=len(rr)
 out.sort(key=lambda r:(r['galaxy'],int(r['sample_index'])))
 OUT_TAB.parent.mkdir(parents=True,exist_ok=True)
 with OUT_TAB.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 shutil.copyfile(BASE_ANA,OUT_ANA)
 all_gals={r['galaxy'] for r in out}|{r['galaxy'] for r in base_ana}
 roles=Counter(mm[g]['stationary_role'] for g in all_gals)
 result={'status':'CERTIFIED_HI_COMMON_NORMALIZED_V4_BUILT','v3_baseline_galaxies':len(base_gals),'new_galaxies':sorted(NEW),'new_rows':added_rows,'n_certified_galaxies':len(all_gals),'n_tabulated_galaxies':len({r['galaxy'] for r in out}),'n_analytic_galaxies':len({r['galaxy'] for r in base_ana}),'role_counts':dict(roles),'n_tabulated_rows':len(out),'outputs':[str(OUT_TAB),str(OUT_ANA)],'normalization_policy':'validation/stationary/STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md','boundary':'Common source normalization only. No interpolation, continuation, source-current evaluation, persistence parameters, or blind outcomes.'}
 if len(all_gals)!=len(mm):raise RuntimeError(f'normalized galaxy count {len(all_gals)} != manifest {len(mm)}')
 SUMMARY.parent.mkdir(parents=True,exist_ok=True);SUMMARY.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
