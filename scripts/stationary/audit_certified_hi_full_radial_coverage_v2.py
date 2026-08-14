#!/usr/bin/env python3
"""Audit radial support of the current common-normalized certified H I set."""
from __future__ import annotations
import csv,json
from collections import defaultdict
from pathlib import Path

MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
MAN=Path('data/stationary/source_reconstruction/certified_hi_normalization_manifest_v2.csv')
TAB=Path('data/stationary/source_reconstruction/certified_hi_common_tabulated_v4.csv')
ANA=Path('data/stationary/source_reconstruction/certified_hi_common_analytic_v4.csv')
OUTCSV=Path('validation/stationary/certified_hi_full_radial_coverage_v2.csv')
OUTJSON=Path('validation/stationary/certified_hi_full_radial_coverage_v2_summary.json')

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
 master=read_csv(MASTER);man={r['galaxy']:r for r in read_csv(MAN)}
 rot=defaultdict(list)
 for r in master:rot[r['galaxy']].append(float(r['radius_kpc']))
 tab=defaultdict(list)
 for r in read_csv(TAB):tab[r['galaxy']].append(float(r['radius_kpc_frozen']))
 ana={r['galaxy']:r for r in read_csv(ANA)}
 galaxies=sorted(set(tab)|set(ana))
 if set(galaxies)!=set(man):raise RuntimeError(f'normalized/manifest galaxy mismatch: normalized={len(galaxies)} manifest={len(man)}')
 rows=[]
 for g in galaxies:
  rr=sorted(rot[g]);rmin,rmax=min(rr),max(rr);role=man[g]['stationary_role']
  if g in ana:
   rows.append({'galaxy':g,'stationary_role':role,'profile_kind':'analytic','n_rotation_points':len(rr),'rotation_rmin_kpc':f'{rmin:.12g}','rotation_rmax_kpc':f'{rmax:.12g}','profile_rmin_kpc':'0','profile_rmax_kpc':'analytic','inner_gap_kpc':'0','outer_gap_kpc':'0','inner_continuation_required':'0','outer_continuation_required':'0','coverage_class':'analytic_defined_on_rotation_grid'})
  else:
   pr=sorted(tab[g]);pmin,pmax=min(pr),max(pr);inner=max(0,pmin-rmin);outer=max(0,rmax-pmax);ni=inner>1e-12;no=outer>1e-12
   cl='inner_and_outer_continuation' if ni and no else 'inner_continuation_only' if ni else 'outer_continuation_only' if no else 'full_measured_support'
   rows.append({'galaxy':g,'stationary_role':role,'profile_kind':'tabulated','n_rotation_points':len(rr),'rotation_rmin_kpc':f'{rmin:.12g}','rotation_rmax_kpc':f'{rmax:.12g}','profile_rmin_kpc':f'{pmin:.12g}','profile_rmax_kpc':f'{pmax:.12g}','inner_gap_kpc':f'{inner:.12g}','outer_gap_kpc':f'{outer:.12g}','inner_continuation_required':'1' if ni else '0','outer_continuation_required':'1' if no else '0','coverage_class':cl})
 OUTCSV.parent.mkdir(parents=True,exist_ok=True)
 with OUTCSV.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 tabrows=[r for r in rows if r['profile_kind']=='tabulated'];inner=[r for r in tabrows if r['inner_continuation_required']=='1'];outer=[r for r in tabrows if r['outer_continuation_required']=='1'];classes=sorted({r['coverage_class'] for r in rows})
 summary={'status':'CERTIFIED_HI_FULL_RADIAL_COVERAGE_V2_AUDITED','n_profiles':len(rows),'n_tabulated':len(tabrows),'n_analytic':len(ana),'role_counts':{'calibration':sum(r['stationary_role']=='calibration' for r in rows),'blind':sum(r['stationary_role']=='blind' for r in rows)},'coverage_class_counts':{c:sum(r['coverage_class']==c for r in rows) for c in classes},'n_tabulated_requiring_inner_continuation':len(inner),'n_tabulated_requiring_outer_continuation':len(outer),'inner_continuation_galaxies':[r['galaxy'] for r in inner],'outer_continuation_galaxies':[r['galaxy'] for r in outer],'new_feasts_profiles':[next(r for r in rows if r['galaxy']==g) for g in ('NGC2903','NGC4559')],'max_inner_gap_kpc':max([float(r['inner_gap_kpc']) for r in tabrows] or [0]),'max_outer_gap_kpc':max([float(r['outer_gap_kpc']) for r in tabrows] or [0]),'boundary':'Radial-support geometry only. No velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcome evaluated.'}
 OUTJSON.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
