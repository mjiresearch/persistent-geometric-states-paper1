#!/usr/bin/env python3
"""Cross-match the public FEASTS 2025 H I profiles to the frozen SPARC sample.

Acquisition/provenance only. Identifies exact/canonical-name overlaps and current
certification status; it does not promote profiles or inspect persistence/blind
outcomes.
"""
from __future__ import annotations
import csv,json,re
from pathlib import Path
from collections import Counter
from astropy.table import Table

FEASTS=Path('data/stationary/source_reconstruction/feasts2025_HIprof_wang25.ecsv')
PROV=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
OUT=Path('validation/stationary/feasts2025_frozen_sparc_crossmatch_v1.json')
CERT={'raw_source_profile_ingested','analytic_profile_recovered'}

def canon(s):
 x=re.sub(r'[^A-Z0-9]','',str(s).upper())
 # Normalize common catalog prefixes with zero-padded numeric suffixes.
 for p in ('NGC','UGC','IC','DDO','ESO','UGCA'):
  if x.startswith(p):
   tail=x[len(p):]
   m=re.fullmatch(r'0*(\d+)([A-Z]*)',tail)
   if m:return p+str(int(m.group(1)))+m.group(2)
 return x

def main():
 tab=Table.read(FEASTS,format='ascii.ecsv'); fnames=[str(x) for x in tab['name']]
 with PROV.open(newline='',encoding='utf-8-sig') as f:prov=list(csv.DictReader(f))
 idx={}
 for r in prov:idx.setdefault(canon(r['galaxy']),[]).append(r)
 matches=[];unmatched=[]
 for n in fnames:
  rs=idx.get(canon(n),[])
  if len(rs)==1:
   r=rs[0];status=r.get('effective_acquisition_status','');matches.append({
    'feasts_name':n,'frozen_galaxy':r['galaxy'],'stationary_role':r['stationary_role'],'effective_status':status,
    'already_certified':status in CERT,'expected_in_169_profile_compilation':r.get('expected_in_169_profile_compilation'),
    'public_overlay_present':r.get('public_overlay_present'),'effective_public_source_family':r.get('effective_public_source_family',''),
    'candidate_new_public_profile':status not in CERT})
  elif len(rs)==0:unmatched.append({'feasts_name':n,'canonical':canon(n)})
  else:unmatched.append({'feasts_name':n,'canonical':canon(n),'error':'ambiguous frozen canonical match','frozen_candidates':[x['galaxy'] for x in rs]})
 cand=[x for x in matches if x['candidate_new_public_profile']]
 out={'status':'FEASTS2025_FROZEN_SPARC_CROSSMATCH_COMPLETE','n_feasts_profiles':len(fnames),'n_frozen_matches':len(matches),'n_unmatched':len(unmatched),'n_already_certified_matches':sum(x['already_certified'] for x in matches),'n_candidate_new_public_profiles':len(cand),'candidate_role_counts':dict(Counter(x['stationary_role'] for x in cand)),'matches':matches,'candidate_new_public_profiles':cand,'unmatched':unmatched,'boundary':'Acquisition/provenance cross-match only. No profile promotion, persistence quantities, or blind outcomes. Certified count is unchanged by this audit.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('status','n_feasts_profiles','n_frozen_matches','n_already_certified_matches','n_candidate_new_public_profiles','candidate_role_counts')},indent=2));print(json.dumps(cand,indent=2))
if __name__=='__main__':main()
