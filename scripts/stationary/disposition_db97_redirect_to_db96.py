#!/usr/bin/env python3
"""Close dB97 as a downstream redirect to the existing dB96 acquisition state.

No source data are re-fetched or re-audited. The canonical Lelli/SPARC map is
used only to verify the two frozen dB97 targets and their roles. Existing dB96
recovery checkpoint must already document both as unresolved numerical profiles.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
DB96=Path('validation/stationary/DB96_JADHAV2019_PROFILE_RECOVERY_V1.md')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_DB97_REDIRECT.md')
EXPECTED={'F565-V2':'blind','F571-V1':'calibration'}

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 refs=read(REFMAP);got={r['galaxy']:r['stationary_role'] for r in refs if r.get('sparc_ref_id')=='dB97'}
 if got!=EXPECTED:raise RuntimeError(f'dB97 frozen mapping changed: {got} != {EXPECTED}')
 if not DB96.exists():raise RuntimeError('Existing dB96 checkpoint missing; do not recreate prior work')
 t=DB96.read_text(encoding='utf-8')
 for g in EXPECTED:
  if g not in t:raise RuntimeError(f'{g} absent from existing dB96 unresolved checkpoint')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={
  'sparc_ref_id':'dB97',
  'queue_status':'redirect_existing_source_family',
  'disposition':'downstream_mass_model_redirect_to_existing_db96_original_HI_source_state',
  'validation_artifact':'validation/stationary/CHECKPOINT_DB97_REDIRECT.md',
  'reopen_rule':'reopen_only_for_genuinely_new_public_numeric_vector_or_analytic_profile_route_for_F565-V2_or_F571-V1',
  'notes':(
   'de Blok & McGaugh 1997 is a mass-model analysis. F565-V2 (blind) and F571-V1 (calibration) '
   'trace to the original de Blok, McGaugh & van der Hulst 1996 H I observations (dB96). '
   'The existing dB96 checkpoint already records both as unresolved public numerical profiles. '
   'Do not restart exhausted dB96 routes merely because dB97 appears as a separate SPARC reference.'
  )}
 if 'dB97' in by:by['dB97'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
 CHECK.write_text(
  '# Post-dB97 stationary H I checkpoint\n\n'
  'Status: **DB97 REDIRECTED TO EXISTING DB96 STATE; RERANK NEXT**\n\n'
  '- F565-V2 — blind; dB97 -> original dB96 H I source; existing dB96 numerical profile remains unresolved.\n'
  '- F571-V1 — calibration; dB97 -> original dB96 H I source; existing dB96 numerical profile remains unresolved.\n'
  '- No dB96 route was restarted.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nRun the existing reconciliation/ranking and continue the new highest-ranked actionable Lelli family.\n',encoding='utf-8')
 print(json.dumps({'status':'DB97_REDIRECT_DISPOSITION_RECORDED','targets':EXPECTED,'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
