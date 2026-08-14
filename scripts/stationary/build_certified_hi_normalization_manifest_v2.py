#!/usr/bin/env python3
"""Build dynamic normalization manifest for the current certified H I set.

Version 2 removes the historical hard-coded 31-profile assertion and recognizes
explicit FEASTS frozen-distance radius columns. No interpolation or persistence
evaluation is performed.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

PROV=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
SCHEMA=Path('validation/stationary/certified_hi_profile_schema_audit_v1.json')
SCALE=Path('data/stationary/source_reconstruction/certified_hi_source_scale_metadata_v2.csv')
MASTER=Path('data/stationary/frozen/stationary_master_v1.csv')
OUT=Path('data/stationary/source_reconstruction/certified_hi_normalization_manifest_v2.csv')
SUMMARY=Path('validation/stationary/certified_hi_normalization_manifest_v2_summary.json')
CERT={'raw_source_profile_ingested','analytic_profile_recovered'}
LEROY='data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv'
NGC300='data/stationary/source_reconstruction/westmeier2011_ngc300_gas_profile_v1.csv'

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
 prov=[r for r in read_csv(PROV) if r['effective_acquisition_status'] in CERT]
 if not prov:raise RuntimeError('no certified profiles in reconciled provenance')
 schema=json.loads(SCHEMA.read_text());amap={a['artifact']:a for a in schema['artifacts']}
 if set(r['effective_source_artifact'] for r in prov)-set(amap):raise RuntimeError('schema audit is stale relative to current certified provenance')
 scale={r['galaxy']:r for r in read_csv(SCALE)}
 frozen={}
 for r in read_csv(MASTER):frozen.setdefault(r['galaxy'],float(r['distance_mpc']))
 rows=[];unresolved=[]
 for r in prov:
  g=r['galaxy'];art=r['effective_source_artifact'];cols=set(amap[art].get('columns',[]))
  if g in scale:
   radius_method='source_kpc_times_frozen_over_source_distance';radius_factor=float(scale[g]['radius_scale_frozen_over_source']);source_distance=scale[g]['source_distance_mpc']
  elif cols & {'radius_kpc_frozen','frozen_radius_kpc','radius_kpc_frozen_distance'}:
   radius_method='explicit_frozen_radius';radius_factor=1.0;source_distance=''
  elif cols & {'radius_arcsec','radius_arcsec_vector','radius_arcsec_native_grid','source_radius_arcsec','r_arcsec'}:
   radius_method='angular_radius_times_frozen_distance';radius_factor='';source_distance=''
  elif r['effective_acquisition_status']=='analytic_profile_recovered' and any(c.endswith('_arcsec') for c in cols):
   radius_method='analytic_angular_scale_times_frozen_distance';radius_factor='';source_distance=''
  else:
   unresolved.append((g,'radius',art,sorted(cols)));radius_method='UNRESOLVED';radius_factor='';source_distance=''
  if art==LEROY:
   helium_method='source_includes_1p36_to_common_1p33';helium_factor=1.33/1.36;source_helium_factor='1.36'
  elif art==NGC300:
   helium_method='source_includes_1p4_to_common_1p33';helium_factor=1.33/1.4;source_helium_factor='1.4'
  else:
   helium_method='raw_HI_to_common_1p33';helium_factor=1.33;source_helium_factor='1.0'
  rows.append({'galaxy':g,'stationary_role':r['stationary_role'],'acquisition_status':r['effective_acquisition_status'],'source_artifact':art,'source_quantity':r['effective_source_quantity'],'source_helium_status':r['effective_helium_status'],'frozen_distance_mpc':f'{frozen[g]:.12g}','source_distance_mpc':source_distance,'radius_mapping_method':radius_method,'radius_multiplicative_factor_if_source_kpc':'' if radius_factor=='' else f'{radius_factor:.12g}','source_helium_factor_relative_to_raw_HI':source_helium_factor,'helium_mapping_method':helium_method,'surface_density_multiplier_to_common_1p33':f'{helium_factor:.12g}','common_surface_density_convention':'Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw','inclination_amplitude_rescale':'0','normalization_ready':'1' if radius_method!='UNRESOLVED' else '0'})
 if unresolved:raise RuntimeError('unresolved normalization metadata: '+repr(unresolved))
 rows.sort(key=lambda x:x['galaxy']);OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result={'status':'CERTIFIED_HI_NORMALIZATION_MANIFEST_V2_COMPLETE','n_certified':len(rows),'n_ready':sum(x['normalization_ready']=='1' for x in rows),'role_counts':{'calibration':sum(x['stationary_role']=='calibration' for x in rows),'blind':sum(x['stationary_role']=='blind' for x in rows)},'helium_mapping_counts':{m:sum(x['helium_mapping_method']==m for x in rows) for m in sorted({x['helium_mapping_method'] for x in rows})},'radius_mapping_counts':{m:sum(x['radius_mapping_method']==m for x in rows) for m in sorted({x['radius_mapping_method'] for x in rows})},'policy':'validation/stationary/STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md','boundary':'Normalization metadata only. No profile interpolation, L_A, C_A, tau_A, persistence prediction, or blind outcome evaluated.'}
 SUMMARY.parent.mkdir(parents=True,exist_ok=True);SUMMARY.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
