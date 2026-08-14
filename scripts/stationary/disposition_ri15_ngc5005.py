#!/usr/bin/env python3
import csv,json
from pathlib import Path
A=Path('validation/stationary/ri15_ngc5005_fig8_geometry_v1.json')
D=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
C=Path('validation/stationary/CHECKPOINT_RI15_NGC5005_PUBLIC_ROUTE.md')
def main():
 a=json.loads(A.read_text())
 e=a.get('eps_metrics',{})
 f=e.get('f8.eps',{})
 if not f or not f.get('raster_signal') or f.get('substantial_path_signal'):
  raise RuntimeError('Ri15 Figure 8 geometry state changed')
 with D.open(newline='',encoding='utf-8-sig') as h:r=list(csv.DictReader(h))
 fields=list(r[0]);by={x['sparc_ref_id']:x for x in r}
 x={'sparc_ref_id':'Ri15','queue_status':'defer_until_new_mechanism','disposition':'NGC5005_Richards2015_Figure8_direct_atomic_HI_radial_surface_density_but_source_f8_EPS_is_raster_wrapped_without_recoverable_native_profile_geometry','validation_artifact':str(A),'reopen_rule':'reopen_for_machine_readable_atomic_HI_radial_series_source_native_vector_republication_or_public_calibrated_VLA_map_cube_under_predeclared_reconstruction_protocol','notes':'NGC5005 blind. Richards et al. 2015 Figure 8 is the required atomic H I radial mass-surface-density series (filled circles; about 20 arcsec sampling). Source-package audit shows f8.eps contains raster image/colorimage payloads and no substantial native path geometry; none of nine EPS assets has substantial recoverable path geometry. No raster digitization or blind-outcome inspection; no certified profile added.'}
 if 'Ri15' in by:by['Ri15'].update(x)
 else:r.append(x)
 r.sort(key=lambda z:z['sparc_ref_id'])
 with D.open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(r)
 C.write_text('# Ri15 / NGC5005 H I checkpoint\n\nStatus: **DEFERRED — FIGURE 8 EXACT PUBLIC ROUTE EXHAUSTED**\n\nNGC5005 is blind. Richards et al. 2015 Figure 8 directly publishes the atomic H I radial mass-surface-density series as filled circles at about 20 arcsec sampling. The source asset f8.eps is raster-wrapped and has no substantial recoverable native path geometry. Reopen only for a machine-readable atomic H I radial series, a source-native vector republication, or a calibrated VLA map/cube under a frozen reconstruction protocol. No raster digitization or blind-outcome inspection. L_A and C_A remain locked.\n')
 print(json.dumps({'status':'RI15_NGC5005_DEFERRED','profile_added':False}))
if __name__=='__main__':main()
