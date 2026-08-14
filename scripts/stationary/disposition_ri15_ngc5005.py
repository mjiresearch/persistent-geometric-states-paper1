#!/usr/bin/env python3
import csv,json
from collections import Counter
from pathlib import Path
A=Path('validation/stationary/ri15_ngc5005_fig8_geometry_v1.json')
D=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
P=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
C=Path('validation/stationary/CHECKPOINT_RI15_NGC5005_PUBLIC_ROUTE.md')
CERT={'raw_source_profile_ingested','analytic_profile_recovered'}
def main():
 a=json.loads(A.read_text())
 f=a.get('eps_metrics',{}).get('f8.eps',{})
 if not f or not f.get('raster_signal') or f.get('substantial_path_signal'):
  raise RuntimeError('Ri15 Figure 8 geometry state changed')
 with D.open(newline='',encoding='utf-8-sig') as h:r=list(csv.DictReader(h))
 fields=list(r[0]);by={x['sparc_ref_id']:x for x in r}
 x={'sparc_ref_id':'Ri15','queue_status':'defer_until_new_mechanism','disposition':'NGC5005_Richards2015_Figure8_direct_atomic_HI_radial_surface_density_but_source_f8_EPS_is_raster_wrapped_without_recoverable_native_profile_geometry','validation_artifact':str(A),'reopen_rule':'reopen_for_machine_readable_atomic_HI_radial_series_source_native_vector_republication_or_public_calibrated_VLA_map_cube_under_predeclared_reconstruction_protocol','notes':'NGC5005 blind. Richards et al. 2015 Figure 8 is the required atomic H I radial mass-surface-density series (filled circles; about 20 arcsec sampling). Source-package audit shows f8.eps contains raster image/colorimage payloads and no substantial native path geometry; none of nine EPS assets has substantial recoverable path geometry. No raster digitization or blind-outcome inspection; no certified profile added.'}
 if 'Ri15' in by:by['Ri15'].update(x)
 else:r.append(x)
 r.sort(key=lambda z:z['sparc_ref_id'])
 with D.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(r)
 with P.open(newline='',encoding='utf-8-sig') as h:prov=list(csv.DictReader(h))
 req=[];unavail=[];cert=[]
 for q in prov:
  status=q.get('effective_acquisition_status','')
  if status in CERT:cert.append(q);continue
  if q.get('expected_in_169_profile_compilation')!='1':unavail.append(q);continue
  req.append(q)
 req.sort(key=lambda q:(q['stationary_role'],q['galaxy']))
 roles=Counter(q['stationary_role'] for q in req)
 lines=['# Ri15 / NGC5005 H I checkpoint','', 'Status: **DEFERRED — FIGURE 8 EXACT PUBLIC ROUTE EXHAUSTED**','', 'NGC5005 is blind. Richards et al. 2015 Figure 8 directly publishes the atomic H I radial mass-surface-density series as filled circles at about 20 arcsec sampling. The source asset `f8.eps` is raster-wrapped and has no substantial recoverable native path geometry. Reopen only for a machine-readable atomic H I radial series, a source-native vector republication, or a calibrated VLA map/cube under a frozen reconstruction protocol. No raster digitization or blind-outcome inspection. `L_A` and `C_A` remain locked.','', '## Public-route closure / Lelli request manifest','', f'- Frozen stationary sample: **{len(prov)} galaxies**.', f'- Already certified usable numerical H I profiles: **{len(cert)}**.', f'- Reported unavailable in the 169-profile compilation and still unresolved: **{len(unavail)}** — '+', '.join(q['galaxy'] for q in unavail)+'.', f'- Request from the private 169-profile compilation: **{len(req)} galaxies = {roles.get("calibration",0)} calibration + {roles.get("blind",0)} blind**.','- Request only acquisition-level fields: radius, radial H I surface density, units, helium convention, adopted distance, inclination, beam/radial sampling, and original source citation.','- Do not request or inspect persistence predictions, fit outcomes, or blind-sample residuals.','', '| Galaxy | Role | Current status | Public overlay | Current public source family |','|---|---|---|---:|---|']
 for q in req:
  fam=(q.get('effective_public_source_family') or '').replace('|','/');lines.append(f"| {q['galaxy']} | {q['stationary_role']} | {q.get('effective_acquisition_status','')} | {q.get('public_overlay_present','0')} | {fam} |")
 C.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'status':'RI15_NGC5005_DEFERRED_AND_LELLI_REQUEST_MANIFEST_FROZEN','profile_added':False,'n_request':len(req),'request_roles':dict(roles),'n_certified':len(cert),'n_unavailable_unresolved':len(unavail)},indent=2))
if __name__=='__main__':main()
