#!/usr/bin/env python3
"""Coverage audit for certified H I profiles with explicit frozen-radius readiness.

No persistence parameters or blind rotation residuals are evaluated.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
READY=Path('validation/stationary/certified_hi_normalization_readiness_v1.csv')
OUT=Path('validation/stationary/normalization_ready_profile_coverage_v1.json')

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
 master=read_csv(MASTER); ready=[r for r in read_csv(READY) if r['normalization_ready']=='1']
 bym={}
 for r in master:bym.setdefault(r['galaxy'],[]).append(r)
 recs=[]
 for meta in ready:
  g=meta['galaxy']; p=Path(meta['artifact']); rr=read_csv(p)
  rr=[x for x in rr if x.get('galaxy',g)==g]
  mr=sorted(float(x['radius_kpc']) for x in bym[g])
  if meta['acquisition_status']=='analytic_profile_recovered':
   recs.append({'galaxy':g,'stationary_role':meta['stationary_role'],'profile_kind':'analytic',
     'rotation_rmin_kpc':min(mr),'rotation_rmax_kpc':max(mr),'coverage_status':'analytic_defined_on_rotation_grid'})
   continue
  cols=set(rr[0]) if rr else set()
  if 'radius_kpc_frozen' not in cols:raise RuntimeError(f'{g}: readiness asserted but no radius_kpc_frozen')
  pr=sorted(float(x['radius_kpc_frozen']) for x in rr)
  recs.append({'galaxy':g,'stationary_role':meta['stationary_role'],'profile_kind':'tabulated',
    'n_profile_rows':len(pr),'profile_rmin_kpc':min(pr),'profile_rmax_kpc':max(pr),
    'rotation_rmin_kpc':min(mr),'rotation_rmax_kpc':max(mr),
    'inner_rotation_covered':min(mr)>=min(pr),'outer_rotation_covered':max(mr)<=max(pr),
    'full_rotation_grid_covered':min(mr)>=min(pr) and max(mr)<=max(pr)})
 result={'status':'NORMALIZATION_READY_PROFILE_COVERAGE_AUDITED','n_galaxies':len(recs),'galaxies':recs,
  'boundary':'Geometry/coverage only. No interpolation applied, no persistence parameters or blind outcomes evaluated.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
