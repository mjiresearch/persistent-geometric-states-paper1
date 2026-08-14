#!/usr/bin/env python3
"""Audit normalization readiness of certified stationary H I profiles.

No interpolation, persistence evaluation, or blind-outcome inspection is performed.
"""
from __future__ import annotations
import csv,json,re
from pathlib import Path

PROV=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
SCHEMA=Path('validation/stationary/certified_hi_profile_schema_audit_v1.json')
OUTCSV=Path('validation/stationary/certified_hi_normalization_readiness_v1.csv')
OUTJSON=Path('validation/stationary/certified_hi_normalization_readiness_v1_summary.json')
CERT={'raw_source_profile_ingested','analytic_profile_recovered'}

def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
    prov=[r for r in read_csv(PROV) if r['effective_acquisition_status'] in CERT]
    schema=json.loads(SCHEMA.read_text())
    amap={a['artifact']:a for a in schema['artifacts']}
    out=[]
    for r in prov:
        a=amap[r['effective_source_artifact']]; cols=set(a.get('columns',[]))
        frozen_radius=bool(cols & {'radius_kpc_frozen','frozen_radius_kpc'})
        source_radius=bool(cols & {'radius_kpc','radius_kpc_source','radius_kpc_source_scale','source_radius_kpc'})
        angular_radius=bool(cols & {'radius_arcsec','radius_arcsec_vector','radius_arcsec_native_grid','source_radius_arcsec','r_arcsec'})
        source_distance=bool(cols & {'source_distance_mpc','distance_mpc_source'})
        frozen_distance=bool(cols & {'frozen_distance_mpc','distance_mpc_frozen'})
        analytic=r['effective_acquisition_status']=='analytic_profile_recovered'
        helium=(r.get('effective_helium_status') or '').strip()
        helium_known=bool(helium) and not re.search(r'unknown|pending|unclear',helium,re.I)
        radius_ready=frozen_radius or (angular_radius and frozen_distance) or (source_radius and source_distance and frozen_distance)
        # Analytic parameter files carry source/frozen distances and angular scales.
        if analytic and source_distance and frozen_distance: radius_ready=True
        uncertainty_cols=[c for c in cols if any(k in c.lower() for k in ['err','uncert','sigma_minus','sigma_plus'])]
        out.append({
          'galaxy':r['galaxy'],'stationary_role':r['stationary_role'],
          'acquisition_status':r['effective_acquisition_status'],
          'artifact':r['effective_source_artifact'],
          'source_quantity':r['effective_source_quantity'],
          'helium_status':helium,
          'helium_metadata_ready':'1' if helium_known else '0',
          'radius_frozen_ready':'1' if radius_ready else '0',
          'explicit_frozen_radius_column':'1' if frozen_radius else '0',
          'has_source_radius':'1' if source_radius else '0',
          'has_angular_radius':'1' if angular_radius else '0',
          'has_source_distance':'1' if source_distance else '0',
          'has_frozen_distance':'1' if frozen_distance else '0',
          'uncertainty_columns':';'.join(uncertainty_cols),
          'normalization_ready':'1' if helium_known and radius_ready else '0'})
    fields=list(out[0])
    OUTCSV.parent.mkdir(parents=True,exist_ok=True)
    with OUTCSV.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    summary={
      'status':'CERTIFIED_HI_NORMALIZATION_READINESS_AUDITED',
      'n_certified':len(out),
      'n_calibration':sum(x['stationary_role']=='calibration' for x in out),
      'n_blind':sum(x['stationary_role']=='blind' for x in out),
      'n_normalization_ready':sum(x['normalization_ready']=='1' for x in out),
      'n_radius_ready':sum(x['radius_frozen_ready']=='1' for x in out),
      'n_helium_metadata_ready':sum(x['helium_metadata_ready']=='1' for x in out),
      'not_normalization_ready':[x['galaxy'] for x in out if x['normalization_ready']!='1'],
      'boundary':'Metadata/readiness audit only. No interpolation, persistence parameters, or blind outcomes evaluated.'}
    OUTJSON.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
