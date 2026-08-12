#!/usr/bin/env python3
"""Close JC90 by linking it to the existing NGC3109 original-source audit.

JC90 is Jobin & Carignan 1990, already audited as the original NGC3109 H I
source through the Be91 provenance decomposition. This script consumes only the
saved audit; it does not refetch or re-read the source paper.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
AUDIT=Path('validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_DISPOSITION_V1.md')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_JC90_REDIRECT.md')

def read(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    hits=[r for r in read(REF) if r.get('sparc_ref_id')=='JC90']
    if len(hits)!=1 or hits[0]['galaxy']!='NGC3109' or hits[0]['stationary_role']!='calibration':
        raise RuntimeError(f'JC90 frozen mapping changed: {hits}')
    t=AUDIT.read_text(encoding='utf-8')
    required=[
        '`NGC3109` -> Jobin & Carignan (1990)',
        'radial H I profile shown in Figure 6',
        'no source-native radial H I surface-density table is exposed',
        'Figure coordinates are raster/image content and are not digitized',
    ]
    for s in required:
        if s not in t:raise RuntimeError(f'Existing NGC3109 audit no longer contains expected evidence: {s}')
    rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
    new={
        'sparc_ref_id':'JC90',
        'queue_status':'redirect_existing_source_family',
        'disposition':'same_original_NGC3109_HI_source_already_exhaustively_audited_through_Be91_branch',
        'validation_artifact':'validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_DISPOSITION_V1.md',
        'reopen_rule':'reopen_only_for_genuinely_new_machine_readable_vector_or_fully_specified_analytic_NGC3109_HI_profile_route',
        'notes':(
            'JC90 is Jobin & Carignan 1990, already reached as the original NGC3109 21-cm source through Be91. '
            'Existing audit: elliptical averaging produced the inclination-corrected radial H I profile in Figure 6; native tables cover observing/global H I, optical photometry, rotation curve and mass models rather than radial Sigma_HI; figure coordinates are raster/image content and were not digitized. '
            'Do not repeat the same public paper/figure route merely because JC90 appears as a direct SPARC reference.'
        ),
    }
    if 'JC90' in by:by['JC90'].update(new)
    else:rows.append(new)
    rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
    CHECK.write_text(
        '# Post-JC90 stationary H I checkpoint\n\n'
        'Status: **JC90 REDIRECTED TO EXISTING NGC3109 AUDIT; RERANK NEXT**\n\n'
        '- NGC3109 — calibration.\n'
        '- JC90 is Jobin & Carignan 1990, the same original H I source already audited through Be91.\n'
        '- Radial H I profile is Figure 6; no native radial Sigma_HI table/vector profile was recovered; no raster digitization.\n'
        '- No source paper was re-fetched or re-audited.\n'
        '- `L_A` and `C_A` remain locked.\n\n'
        '## Resume point\nRerank and continue the new highest-ranked actionable Lelli family.\n',
        encoding='utf-8')
    print(json.dumps({'status':'JC90_REDIRECT_EXISTING_AUDIT_RECORDED','checkpoint':str(CHECK)},indent=2))

if __name__=='__main__':main()
