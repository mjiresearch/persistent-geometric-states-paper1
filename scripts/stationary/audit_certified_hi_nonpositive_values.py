#!/usr/bin/env python3
"""Audit non-positive/nonfinite surface-density values in all certified tabulated H I products.

Preserves source values exactly. No clipping, interpolation, normalization, persistence
parameters, or blind outcomes are evaluated.
"""
from __future__ import annotations
import csv,json,math
from collections import defaultdict
from pathlib import Path

MAN=Path('data/stationary/source_reconstruction/certified_hi_normalization_manifest_v1.csv')
OUT=Path('validation/stationary/certified_hi_nonpositive_value_audit_v1.json')

def read_csv(p):
 with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def val(s):
 try:return float(s)
 except:return float('nan')

def main():
 man=read_csv(MAN)
 rows=[]
 for m in man:
  if m['acquisition_status']!='raw_source_profile_ingested':continue
  g=m['galaxy']; art=Path(m['source_artifact']); rr=read_csv(art); cols=set(rr[0]) if rr else set()
  # Explicit source-sigma column map by schema, never heuristic value inference.
  if 'source_sigmaHI_including_helium_msun_pc2' in cols: sc='source_sigmaHI_including_helium_msun_pc2'; ec='source_sigmaHI_rms_msun_pc2'
  elif 'source_sigmaHI_msun_pc2' in cols: sc='source_sigmaHI_msun_pc2'; ec='source_sigmaHI_err_msun_pc2'
  elif 'sigma_gas_msun_pc2' in cols: sc='sigma_gas_msun_pc2'; ec='sigma_gas_err_msun_pc2'
  elif 'sigma_hi_msun_pc2' in cols: sc='sigma_hi_msun_pc2'; ec=None
  else: raise RuntimeError(f'{g}: no explicit source surface-density column')
  # Some shared artifacts contain multiple galaxies.
  if 'galaxy' in cols: rr=[r for r in rr if r['galaxy']==g]
  vals=[]
  for i,r in enumerate(rr):
   x=val(r.get(sc,'')); e=val(r.get(ec,'')) if ec else float('nan')
   vals.append(x)
   if not math.isfinite(x) or x<=0:
    rows.append({'galaxy':g,'stationary_role':m['stationary_role'],'source_artifact':str(art),'row_index':i,
     'source_sigma_column':sc,'source_sigma_value':None if not math.isfinite(x) else x,
     'source_uncertainty_column':ec or '','source_uncertainty_value':None if not math.isfinite(e) else e,
     'classification':'nonfinite' if not math.isfinite(x) else ('zero' if x==0 else 'negative'),
     'abs_sigma_over_uncertainty':None if (not math.isfinite(x) or not math.isfinite(e) or e<=0) else abs(x)/e})
 by=defaultdict(lambda:{'negative':0,'zero':0,'nonfinite':0})
 for r in rows:by[r['galaxy']][r['classification']]+=1
 result={'status':'CERTIFIED_HI_NONPOSITIVE_VALUE_AUDIT_COMPLETE','n_tabulated_certified':sum(m['acquisition_status']=='raw_source_profile_ingested' for m in man),
  'n_flagged_rows':len(rows),'n_galaxies_with_flags':len(by),'galaxy_counts':dict(sorted(by.items())),'flagged_rows':rows,
  'boundary':'Source-value audit only. No clipping, normalization, interpolation, persistence parameters, or blind outcomes evaluated.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
