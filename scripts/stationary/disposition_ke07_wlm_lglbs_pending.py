#!/usr/bin/env python3
from __future__ import annotations
import csv,json
from pathlib import Path
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
AUD=Path('validation/stationary/lglbs2026_wlm_data_route_v1.json')

def read(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    if not AUD.exists():raise RuntimeError('WLM 2026 public-data route audit missing')
    q=json.loads(AUD.read_text(encoding='utf-8'))
    if q.get('status') not in {'LGLBS2026_WLM_DATA_ROUTE_AUDITED','LGLBS2026_WLM_CANFAR_LISTING_INSPECTED','LGLBS2026_WLM_TABLE_DIRECTORY_AUDITED'}:
        raise RuntimeError(f'Unexpected WLM audit status: {q.get("status")}')
    rows=read(OVERLAY);fields=list(rows[0]);by={r['galaxy']:r for r in rows}
    new={
      'galaxy':'UGCA444','stationary_role':'blind',
      'public_source_family':'Eibensteiner et al. 2026 LGLBS / public radial-profile release',
      'acquisition_status':'direct_profile_identified_numeric_pending','numeric_rows_or_model':'0',
      'source_quantity':'azimuthally averaged atomic-gas surface-density radial profile; 120 pc radial bins',
      'helium_status':'published Sigma_atom includes x1.35 helium/heavy-elements factor; raw HI requires deterministic division by 1.35',
      'preferred_public_source':'0','source_artifact':str(AUD),
      'notes':'UGCA444=WLM. 2026 LGLBS paper explicitly states processed profiles are publicly released under DOI 10.11570/26.0020. CANFAR DOI and data directory resolve and contain a dedicated tables directory, but file-level table enumeration is still pending in the current acquisition tooling. Adopted LGLBS geometry D=0.984 Mpc, i=74 deg, PA=174 deg. Do not substitute the mass-weighted 120-pc profile for the ordinary azimuthal profile. No numerical profile is certified yet.'}
    if 'UGCA444' in by:by['UGCA444'].update(new)
    else:rows.append(new)
    rows.sort(key=lambda r:r['galaxy']);write(OVERLAY,rows,fields)
    dr=read(DISP);df=list(dr[0]);db={r['sparc_ref_id']:r for r in dr}
    dnew={
      'sparc_ref_id':'Ke07','queue_status':'public_machine_readable_profile_identified_ingestion_pending',
      'disposition':'WLM_exact_public_2026_LGLBS_radial_profile_release_identified_CANFAR_table_file_enumeration_pending',
      'validation_artifact':str(AUD),
      'reopen_rule':'resume_when_CANFAR_tables_directory_file_level_listing_or_equivalent_exact_release_table_is_accessible; ingest ordinary azimuthal Sigma_atom and derive raw_HI by division_by_1.35',
      'notes':'Ke07 original WLM VLA source is superseded for acquisition by the 2026 LGLBS VLA+GBT public radial-profile release. Public numerical route exists, but no exact row set has yet been ingested; therefore this is coverage only, not a certified usable profile.'}
    if 'Ke07' in db:db['Ke07'].update(dnew)
    else:dr.append(dnew)
    dr.sort(key=lambda r:r['sparc_ref_id']);write(DISP,dr,df)
    print(json.dumps({'status':'KE07_WLM_PUBLIC_NUMERIC_ROUTE_IDENTIFIED_INGESTION_PENDING','galaxy':'UGCA444','certified_profile_added':False},indent=2))
if __name__=='__main__':main()
