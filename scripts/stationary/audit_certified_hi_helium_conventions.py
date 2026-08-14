#!/usr/bin/env python3
"""Group certified stationary H I profiles by documented helium convention.

Metadata audit only; no surface-density conversion or persistence evaluation.
"""
from __future__ import annotations
import csv,json
from collections import defaultdict
from pathlib import Path
P=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
OUT=Path('validation/stationary/certified_hi_helium_conventions_v1.json')
CERT={'raw_source_profile_ingested','analytic_profile_recovered'}
def main():
 with P.open(newline='',encoding='utf-8-sig') as f:rows=[r for r in csv.DictReader(f) if r['effective_acquisition_status'] in CERT]
 groups=defaultdict(list)
 for r in rows:groups[(r['effective_source_artifact'],r['effective_helium_status'],r['effective_source_quantity'])].append(r['galaxy'])
 result={'status':'CERTIFIED_HI_HELIUM_CONVENTIONS_AUDITED','n_certified':len(rows),'groups':[
  {'artifact':a,'helium_status':h,'source_quantity':q,'galaxies':gs,'n_galaxies':len(gs)} for (a,h,q),gs in sorted(groups.items())],
  'boundary':'Metadata audit only; no surface-density conversion, persistence parameters, or blind outcomes evaluated.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
