#!/usr/bin/env python3
"""Disposition the remaining Bl04 gap (NGC5985) as downstream to WHISP H I.

Blais-Ouellette et al. 2004 is a Fabry-Perot H-alpha paper. Its frozen SPARC
Bl04 mappings are NGC5055 (blind) and NGC5985 (calibration). NGC5055 is already
covered by a preferred machine-readable Leroy et al. 2008 / THINGS profile in
the public-source overlay and is not modified here. The sole untouched Bl04
target, NGC5985, has an H I rotation curve derived from WHISP observations; the
paper states that general WHISP procedures are in Swaters et al. 2000 and that
details for NGC5985 would be published in a future paper. The CDS catalogue for
Bl04 contains rotation-curve tables, not a radial H I surface-density profile.

No completed NGC5055 source is altered, no prior WHISP route is restarted, and
no map/cube is converted into a profile.
"""
from __future__ import annotations
import csv,json
from pathlib import Path
REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_BL04_DISPOSITION.md')
EXPECTED={'NGC5055':'blind','NGC5985':'calibration'}

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 refs=read(REFMAP);got={r['galaxy']:r['stationary_role'] for r in refs if r.get('sparc_ref_id')=='Bl04'}
 if got!=EXPECTED:
  raise RuntimeError(f'Bl04 frozen mapping changed: {got} != {EXPECTED}')
 overlay=read(OVERLAY);ngc5055=[r for r in overlay if r['galaxy']=='NGC5055']
 if len(ngc5055)!=1:
  raise RuntimeError(f'Expected one existing NGC5055 overlay row, got {ngc5055}')
 old=ngc5055[0]
 if old.get('preferred_public_source')!='1' or old.get('acquisition_status')!='raw_source_profile_ingested' or old.get('numeric_rows_or_model')!='43' or 'THINGS' not in old.get('public_source_family',''):
  raise RuntimeError(f'NGC5055 completed overlay state changed: {old}')
 if any(r['galaxy']=='NGC5985' and r.get('preferred_public_source')=='1' for r in overlay):
  raise RuntimeError('NGC5985 unexpectedly already has a preferred public profile; do not overwrite it')

 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={
  'sparc_ref_id':'Bl04',
  'queue_status':'redirected_to_original_sources',
  'disposition':'NGC5055_already_resolved_via_THINGS_remaining_NGC5985_HI_redirects_to_WHISP_without_published_radial_profile',
  'validation_artifact':'validation/stationary/CHECKPOINT_AFTER_BL04_DISPOSITION.md',
  'reopen_rule':'reopen_only_for_later_public_NGC5985_WHISP_machine_readable_radial_HI_profile_source_native_vector_profile_or_exact_analytic_republication',
  'notes':(
   'Bl04 has two frozen mappings. NGC5055 (blind) is already independently resolved in the public overlay by Leroy et al. 2008 / THINGS with 43 machine-readable rows and is not modified. '
   'The remaining untouched target NGC5985 (calibration) is in a Fabry-Perot H-alpha paper whose H I rotation curve is explicitly derived from WHISP data; general WHISP procedures are cited to Swaters et al. 2000 and NGC5985-specific details were said to be forthcoming. '
   'CDS J/A+A/420/147 supplies optical and H I rotation curves, not radius-by-radius H I surface density. No exact public NGC5985 radial Sigma_HI table/vector product was identified in this provenance gate. No map/cube reconstruction or raster digitization performed.'
  )}
 if 'Bl04' in by:by['Bl04'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
 CHECK.write_text(
  '# Post-Bl04 stationary H I checkpoint\n\n'
  'Status: **BL04 REMAINING GAP REDIRECTED TO WHISP; RERANK NEXT**\n\n'
  '- NGC5055 — blind — already complete via Leroy et al. 2008 / THINGS: 43 machine-readable rows; unchanged.\n'
  '- NGC5985 — calibration — sole untouched Bl04 target.\n'
  '- Bl04 is Blais-Ouellette et al. 2004, a Fabry-Perot H-alpha/kinematic paper.\n'
  '- Its NGC5985 H I curve is explicitly derived from WHISP data.\n'
  '- Paper says general WHISP procedures are in Swaters et al. 2000 and NGC5985-specific details would be published later.\n'
  '- CDS J/A+A/420/147 contains rotation curves only, not radial H I surface density.\n'
  '- No raster digitization or map/cube-to-profile reconstruction performed.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nRerank and continue the new highest-ranked actionable Lelli family. Reopen Bl04 only if an exact later NGC5985 WHISP radial-profile product is identified.\n',encoding='utf-8')
 print(json.dumps({'status':'BL04_WHISP_REDIRECT_RECORDED','completed_existing':'NGC5055','remaining_target':'NGC5985','checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
