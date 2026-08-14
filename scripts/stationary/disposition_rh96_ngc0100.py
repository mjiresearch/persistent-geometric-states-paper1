#!/usr/bin/env python3
import csv,json
from pathlib import Path
A=Path('validation/stationary/rh96_ngc0100_public_profile_route_v1.json')
D=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
C=Path('validation/stationary/CHECKPOINT_RH96_NGC0100_PUBLIC_ROUTE.md')
def main():
 a=json.loads(A.read_text())
 f=a['findings']
 if a['status']!='RH96_NGC0100_PUBLIC_PROFILE_ROUTE_AUDITED' or f['n_candidate_assets']!=0: raise RuntimeError('Rh96 route state changed')
 with D.open(newline='',encoding='utf-8-sig') as h:r=list(csv.DictReader(h))
 fields=list(r[0]);by={x['sparc_ref_id']:x for x in r}
 x={'sparc_ref_id':'Rh96','queue_status':'defer_until_new_mechanism','disposition':'NGC0100_Rhee1996_publishes_radial_HI_surface_density_but_CDS_deposit_contains_only_six_summary_tables_and_no_exact_NGC100_profile_asset','validation_artifact':str(A),'reopen_rule':'reopen_for_machine_readable_radial_HI_series_source_native_vector_republication_or_public_calibrated_WSRT_map_cube_under_predeclared_reconstruction_protocol','notes':'NGC0100 blind. Rhee & van Albada 1996 states radial H I surface-density distributions are presented. CDS J/A+AS/115/407 contains only tables 1-6 (global/observational/kinematic summary quantities); bounded directory audit found no NGC100 auxiliary data, FITS, vector, or numeric radial profile. No raster digitization or blind-outcome inspection.'}
 if 'Rh96' in by:by['Rh96'].update(x)
 else:r.append(x)
 r.sort(key=lambda z:z['sparc_ref_id'])
 with D.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(r)
 C.write_text('# Rh96 / NGC0100 H I checkpoint\n\nStatus: **DEFERRED — EXACT PUBLIC PROFILE ROUTE EXHAUSTED**\n\nNGC0100 is blind. Rh96 publishes radial H I surface-density distributions, but its CDS deposit contains only six summary tables and no exact NGC100 profile asset. Reopen only for a machine-readable radial series, native-vector republication, or calibrated WSRT map/cube under a frozen reconstruction protocol. No raster digitization or blind-outcome inspection. L_A and C_A remain locked.\n')
 print(json.dumps({'status':'RH96_NGC0100_DEFERRED','profile_added':False}))
if __name__=='__main__':main()
