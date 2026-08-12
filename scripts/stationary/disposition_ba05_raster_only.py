#!/usr/bin/env python3
"""Close Ba05 after the exact public radial-profile route was exhausted.

Consumes committed Ba05 audit artifacts only; does not refetch/reinspect source.
NGC4559's published Figure-3 right radial H I column-density profile is embedded
in a GIMP raster-wrapped EPS (`global_rev_r.eps`) with one PostScript image
operator and zero native vector path commands. No machine-readable numeric
sidecar exists in the 18-file arXiv source package.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CLASS=Path('validation/stationary/ba05_fig3_asset_classification_v1.json')
INV=Path('validation/stationary/ba05_source_inventory_v1.json')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_BA05_DISPOSITION.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 refs=read(REFMAP);hits=[r for r in refs if r.get('sparc_ref_id')=='Ba05']
 if len(hits)!=1 or hits[0]['galaxy']!='NGC4559' or hits[0]['stationary_role']!='calibration':
  raise RuntimeError(f'Ba05 frozen mapping changed: {hits}')
 c=json.loads(CLASS.read_text());inv=json.loads(INV.read_text())
 if c.get('status')!='BA05_FIG3_ASSETS_CLASSIFIED':raise RuntimeError('Unexpected Ba05 classification status')
 if not c['decision_fields'].get('all_referenced_assets_raster_wrapped') or c['decision_fields'].get('any_substantive_native_path_signal'):
  raise RuntimeError('Ba05 Figure-3 classification no longer supports raster-only disposition')
 prof=[a for a in c['assets'] if a['name']=='global_rev_r.eps']
 if len(prof)!=1:raise RuntimeError('Ba05 global_rev_r.eps missing from classification')
 a=prof[0]['audit']
 if a['image_ops']!=1 or any(a[x] for x in ['moveto','lineto','rlineto','curveto','stroke','fill']):
  raise RuntimeError(f'Ba05 profile asset geometry changed: {a}')
 if inv.get('n_files')!=18:raise RuntimeError('Ba05 source inventory changed')

 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={
  'sparc_ref_id':'Ba05',
  'queue_status':'deferred_public_route_exhausted',
  'disposition':'original_HI_profile_published_but_public_source_asset_is_raster_wrapped_and_no_numeric_sidecar_exists',
  'validation_artifact':'validation/stationary/ba05_fig3_asset_classification_v1.json',
  'reopen_rule':'reopen_only_for_machine_readable_author_table_source_native_vector_profile_or_other_documented_exact_numeric_republication',
  'notes':(
   'NGC4559 (calibration). Barbieri et al. 2005 is the original WSRT H I source. '
   'TeX explicitly identifies global_rev_r.eps as Figure 3: global H I line profile (left) and column-density radial profile (right). '
   'The GIMP-generated EPS contains exactly one PostScript image operator and zero native moveto/lineto/rlineto/curveto/stroke/fill plot geometry. '
   'The complete 18-file arXiv package contains no machine-readable radial-profile sidecar. No raster digitization performed.'
  )}
 if 'Ba05' in by:by['Ba05'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
 CHECK.write_text(
  '# Post-Ba05 stationary H I checkpoint\n\n'
  'Status: **BA05 CLOSED — PUBLIC EXACT ROUTE EXHAUSTED; RERANK NEXT**\n\n'
  '- NGC4559 — calibration.\n'
  '- Ba05 is the original WSRT H I source.\n'
  '- Figure 3 right is the published radial H I column-density profile.\n'
  '- Source asset `global_rev_r.eps` is GIMP raster-wrapped: 1 `image`, 0 native vector path commands.\n'
  '- Complete 18-file arXiv source has no machine-readable radial-profile sidecar.\n'
  '- No raster digitization or map/cube reconstruction was performed.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nRun reconciliation/ranking and continue the new highest-ranked actionable Lelli family. Do not revisit Ba05 unless its reopen rule is satisfied.\n',encoding='utf-8')
 print(json.dumps({'status':'BA05_RASTER_ONLY_DISPOSITION_RECORDED','target':'NGC4559','checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
