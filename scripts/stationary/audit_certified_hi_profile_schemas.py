#!/usr/bin/env python3
"""Inventory schemas for the certified stationary H I profile artifacts.

Acquisition/QC only. Does not evaluate persistence parameters or blind outcomes.
"""
from __future__ import annotations
import csv, json
from collections import defaultdict
from pathlib import Path

PROV=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
OUT=Path('validation/stationary/certified_hi_profile_schema_audit_v1.json')
CERT={'raw_source_profile_ingested','analytic_profile_recovered'}

def rows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
    prov=rows(PROV)
    cert=[r for r in prov if r['effective_acquisition_status'] in CERT]
    by_art=defaultdict(list)
    for r in cert:by_art[r['effective_source_artifact']].append(r)
    arts=[]
    for name,prs in sorted(by_art.items()):
        p=Path(name)
        rec={'artifact':name,'exists':p.exists(),'galaxies':[x['galaxy'] for x in prs],
             'roles':[x['stationary_role'] for x in prs],
             'statuses':[x['effective_acquisition_status'] for x in prs]}
        if p.exists() and p.suffix.lower()=='.csv':
            rr=rows(p); rec['n_rows']=len(rr); rec['columns']=list(rr[0]) if rr else []
            rec['sample_rows']=rr[:2]
            gcols=[c for c in rec['columns'] if c.lower() in {'galaxy','name','object','target','gal'}]
            if gcols:
                c=gcols[0]; rec['galaxy_column']=c; rec['unique_galaxy_values']=sorted({x.get(c,'') for x in rr})[:250]
        arts.append(rec)
    result={'status':'CERTIFIED_HI_PROFILE_SCHEMA_AUDIT_COMPLETE','n_certified_galaxies':len(cert),
            'role_counts':{'calibration':sum(r['stationary_role']=='calibration' for r in cert),
                           'blind':sum(r['stationary_role']=='blind' for r in cert)},
            'n_unique_artifacts':len(by_art),'artifacts':arts,
            'boundary':'Profile acquisition/schema QC only; no persistence parameters or blind outcomes evaluated.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
