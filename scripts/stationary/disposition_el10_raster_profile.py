#!/usr/bin/env python3
"""Close El10 after the source-native NGC2915 radial H I route was audited.

Consumes the committed El10 route audit only. Figure 5 is explicitly the
azimuthally averaged, inclination-corrected H I surface-density profile, but its
source asset HI_surface_density_profileV2.eps is raster-wrapped and the arXiv
source package contains no machine-readable radial-profile sidecar.
"""
from __future__ import annotations
import csv,json
from pathlib import Path
REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
AUD=Path('validation/stationary/el10_ngc2915_hi_profile_route_v1.json')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_EL10_DISPOSITION.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 hits=[r for r in read(REF) if r.get('sparc_ref_id')=='El10']
 if len(hits)!=1 or hits[0]['galaxy']!='NGC2915' or hits[0]['stationary_role']!='calibration':
  raise RuntimeError(f'El10 frozen mapping changed: {hits}')
 a=json.loads(AUD.read_text())
 if a.get('status')!='EL10_NGC2915_HI_PROFILE_ROUTE_AUDIT_COMPLETE':raise RuntimeError('Unexpected El10 audit status')
 assets=[x for x in a['candidate_profile_assets'] if x['name']=='HI_surface_density_profileV2.eps']
 if len(assets)!=1:raise RuntimeError(f'El10 profile asset mismatch: {assets}')
 p=assets[0]['ps_audit']
 if p['image_ops']<1 or p['colorimage_ops']<1 or (p['lineto']+p['rlineto']+p['curveto'])>20:
  raise RuntimeError(f'El10 profile asset no longer supports raster-wrapped classification: {p}')
 if a.get('numeric_sidecar_candidates'):raise RuntimeError(f'Unexpected El10 numeric sidecar appeared: {a["numeric_sidecar_candidates"]}')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={
  'sparc_ref_id':'El10','queue_status':'deferred_public_route_exhausted',
  'disposition':'original_ATCA_HI_profile_published_but_Figure5_source_asset_is_raster_wrapped_and_no_numeric_sidecar_exists',
  'validation_artifact':'validation/stationary/el10_ngc2915_hi_profile_route_v1.json',
  'reopen_rule':'reopen_only_for_machine_readable_author_table_source_native_vector_profile_or_documented_exact_numeric_republication',
  'notes':(
   'NGC2915 (calibration). Elson et al. 2010 is itself the new deep ATCA H I observing source. '
   'The paper constructs an azimuthally averaged inclination-corrected H I surface-density profile in 17-arcsec rings and identifies Figure 5 as that profile. '
   'The arXiv source asset HI_surface_density_profileV2.eps is raster-wrapped (PostScript image/colorimage operators with only trivial framing path operations), and the complete 18-file source package exposes no machine-readable radial-profile sidecar. '
   'No raster digitization and no total-intensity-map/cube-to-profile reconstruction performed.'
  )}
 if 'El10' in by:by['El10'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
 CHECK.write_text(
  '# Post-El10 stationary H I checkpoint\n\n'
  'Status: **EL10 CLOSED — FIGURE-5 PROFILE RASTER-WRAPPED; RERANK NEXT**\n\n'
  '- NGC2915 — calibration.\n'
  '- El10 is the original deep ATCA H I observing paper.\n'
  '- Figure 5 is explicitly the inclination-corrected radial H I surface-density profile in 17-arcsec rings.\n'
  '- Source asset `HI_surface_density_profileV2.eps` is raster-wrapped; no machine-readable profile sidecar is present.\n'
  '- No raster digitization or map/cube-to-profile reconstruction performed.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nRerank and continue the new highest-ranked actionable Lelli family.\n',encoding='utf-8')
 print(json.dumps({'status':'EL10_RASTER_ONLY_DISPOSITION_RECORDED','target':'NGC2915','checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
