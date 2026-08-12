#!/usr/bin/env python3
"""Close Ca88 by linking it to the existing UGC02259 original-source audit.

Ca88 is Carignan, Sancisi & van Albada 1988, the same original H I paper already
audited through the Be91 decomposition. Do not refetch or re-audit it.
"""
from __future__ import annotations
import csv,json
from pathlib import Path
REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
AUDIT=Path('validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_DISPOSITION_V1.md')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_CA88_REDIRECT.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 hits=[r for r in read(REF) if r.get('sparc_ref_id')=='Ca88']
 if len(hits)!=1 or hits[0]['galaxy']!='UGC02259' or hits[0]['stationary_role']!='calibration':
  raise RuntimeError(f'Ca88 frozen mapping changed: {hits}')
 t=AUDIT.read_text()
 required=['`UGC02259` -> Carignan, Sancisi & van Albada (1988)','Figure 5','Table IV is the rotation curve','not raster-digitized']
 for s in required:
  if s not in t:raise RuntimeError(f'Existing UGC02259 audit no longer contains expected evidence: {s}')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={
  'sparc_ref_id':'Ca88','queue_status':'redirect_existing_source_family',
  'disposition':'same_original_UGC02259_HI_source_already_exhaustively_audited_through_Be91_branch',
  'validation_artifact':'validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_DISPOSITION_V1.md',
  'reopen_rule':'reopen_only_for_genuinely_new_machine_readable_vector_or_fully_specified_analytic_UGC02259_HI_profile_route',
  'notes':(
   'Ca88 is Carignan, Sancisi & van Albada 1988, already reached as the original UGC02259 21-cm source through Be91. '
   'Existing audit: radial H I distribution is Figure 5; Table IV is the rotation curve; no native radial Sigma_HI table/vector profile or independently normalized analytic profile recovered; no raster digitization. '
   'Do not repeat the same public paper/figure route merely because Ca88 appears as a direct SPARC reference.'
  )}
 if 'Ca88' in by:by['Ca88'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
 CHECK.write_text(
  '# Post-Ca88 stationary H I checkpoint\n\n'
  'Status: **CA88 REDIRECTED TO EXISTING UGC02259 AUDIT; RERANK NEXT**\n\n'
  '- UGC02259 — calibration.\n'
  '- Ca88 is the same Carignan, Sancisi & van Albada 1988 original H I source already audited through Be91.\n'
  '- Radial H I distribution is Figure 5; Table IV is rotation curve; no exact native numerical/vector radial profile recovered.\n'
  '- No source paper was re-fetched or re-audited.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nRerank and continue the new highest-ranked actionable Lelli family.\n',encoding='utf-8')
 print(json.dumps({'status':'CA88_REDIRECT_EXISTING_AUDIT_RECORDED','checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
