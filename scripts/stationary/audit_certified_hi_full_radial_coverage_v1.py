#!/usr/bin/env python3
"""Audit radial support of all 31 common-normalized certified H I profiles.

Uses only radial coordinates and frozen stationary roles. Does not read or compare
rotation velocities, residuals, persistence predictions, or blind outcomes.
"""
from __future__ import annotations
import csv,json
from collections import defaultdict
from pathlib import Path

MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
SPLIT=Path('validation/stationary/stationary_split_v1.csv')
TAB=Path('data/stationary/source_reconstruction/certified_hi_common_tabulated_v3.csv')
ANA=Path('data/stationary/source_reconstruction/certified_hi_common_analytic_v3.csv')
OUTCSV=Path('validation/stationary/certified_hi_full_radial_coverage_v1.csv')
OUTJSON=Path('validation/stationary/certified_hi_full_radial_coverage_v1_summary.json')

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
 master=read_csv(MASTER); split={r['galaxy']:r['stationary_role'] for r in read_csv(SPLIT)}
 rot=defaultdict(list)
 for r in master:rot[r['galaxy']].append(float(r['radius_kpc']))
 tab=defaultdict(list)
 for r in read_csv(TAB):tab[r['galaxy']].append(float(r['radius_kpc_frozen']))
 ana={r['galaxy']:r for r in read_csv(ANA)}
 galaxies=sorted(set(tab)|set(ana))
 if len(galaxies)!=31:raise RuntimeError(f'expected 31 common profiles, found {len(galaxies)}')
 rows=[]
 for g in galaxies:
  rr=sorted(rot[g]); rmin,rmax=min(rr),max(rr)
  if g in ana:
   rows.append({'galaxy':g,'stationary_role':split[g],'profile_kind':'analytic','n_rotation_points':len(rr),
    'rotation_rmin_kpc':f'{rmin:.12g}','rotation_rmax_kpc':f'{rmax:.12g}',
    'profile_rmin_kpc':'0','profile_rmax_kpc':'analytic','inner_gap_kpc':'0','outer_gap_kpc':'0',
    'inner_continuation_required':'0','outer_continuation_required':'0','coverage_class':'analytic_defined_on_rotation_grid'})
  else:
   pr=sorted(tab[g]); pmin,pmax=min(pr),max(pr)
   inner=max(0.0,pmin-rmin); outer=max(0.0,rmax-pmax)
   need_in=inner>1e-12; need_out=outer>1e-12
   if need_in and need_out:cl='inner_and_outer_continuation'
   elif need_in:cl='inner_continuation_only'
   elif need_out:cl='outer_continuation_only'
   else:cl='full_measured_support'
   rows.append({'galaxy':g,'stationary_role':split[g],'profile_kind':'tabulated','n_rotation_points':len(rr),
    'rotation_rmin_kpc':f'{rmin:.12g}','rotation_rmax_kpc':f'{rmax:.12g}',
    'profile_rmin_kpc':f'{pmin:.12g}','profile_rmax_kpc':f'{pmax:.12g}',
    'inner_gap_kpc':f'{inner:.12g}','outer_gap_kpc':f'{outer:.12g}',
    'inner_continuation_required':'1' if need_in else '0','outer_continuation_required':'1' if need_out else '0','coverage_class':cl})
 fields=list(rows[0]);OUTCSV.parent.mkdir(parents=True,exist_ok=True)
 with OUTCSV.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 classes=sorted({r['coverage_class'] for r in rows})
 tabrows=[r for r in rows if r['profile_kind']=='tabulated']
 inner=[r for r in tabrows if r['inner_continuation_required']=='1']; outer=[r for r in tabrows if r['outer_continuation_required']=='1']
 summary={'status':'CERTIFIED_HI_FULL_RADIAL_COVERAGE_V1_AUDITED','n_profiles':len(rows),'n_tabulated':len(tabrows),'n_analytic':len(ana),
  'role_counts':{'calibration':sum(r['stationary_role']=='calibration' for r in rows),'blind':sum(r['stationary_role']=='blind' for r in rows)},
  'coverage_class_counts':{c:sum(r['coverage_class']==c for r in rows) for c in classes},
  'n_tabulated_requiring_inner_continuation':len(inner),'n_tabulated_requiring_outer_continuation':len(outer),
  'inner_continuation_galaxies':[r['galaxy'] for r in inner],'outer_continuation_galaxies':[r['galaxy'] for r in outer],
  'max_inner_gap_kpc':max([float(r['inner_gap_kpc']) for r in tabrows] or [0]),
  'max_outer_gap_kpc':max([float(r['outer_gap_kpc']) for r in tabrows] or [0]),
  'largest_inner_gaps':sorted([{'galaxy':r['galaxy'],'role':r['stationary_role'],'gap_kpc':float(r['inner_gap_kpc']),'rotation_rmin_kpc':float(r['rotation_rmin_kpc']),'profile_rmin_kpc':float(r['profile_rmin_kpc'])} for r in inner],key=lambda x:x['gap_kpc'],reverse=True)[:10],
  'largest_outer_gaps':sorted([{'galaxy':r['galaxy'],'role':r['stationary_role'],'gap_kpc':float(r['outer_gap_kpc']),'rotation_rmax_kpc':float(r['rotation_rmax_kpc']),'profile_rmax_kpc':float(r['profile_rmax_kpc'])} for r in outer],key=lambda x:x['gap_kpc'],reverse=True)[:10],
  'boundary':'Radial-support geometry only. No velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcome evaluated.'}
 OUTJSON.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
