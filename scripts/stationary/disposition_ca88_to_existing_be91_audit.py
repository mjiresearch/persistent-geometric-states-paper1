#!/usr/bin/env python3
"""Close the standalone Ca88/UGC02259 queue entry using the existing Be91 source audit.

Carignan, Sancisi & van Albada (1988) was already audited directly while
Be91 was decomposed to its original 21-cm sources.  This step prevents that
same exhausted source route from reappearing merely because SPARC also lists
Ca88 separately for UGC02259.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
AUDIT=Path('validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_QC_V1.md')
DETAIL=Path('validation/stationary/be91_remaining_original_hi_papers_audit_v1.json')
CHECK=Path('validation/stationary/CHECKPOINT_CA88_REDIRECT.md')


def read(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def write(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def main():
    if not AUDIT.exists() or not DETAIL.exists():
        raise RuntimeError('Existing UGC02259/Carignan 1988 audit products missing; do not recreate the source audit.')
    txt=AUDIT.read_text(encoding='utf-8')
    required=['Carignan, Sancisi & van Albada (1988) — UGC02259','radial H I distribution is **Fig. 5**','no native vector drawings','No raster digitization was performed']
    if any(x not in txt for x in required):
        raise RuntimeError('Existing Be91 UGC02259 audit no longer contains expected locked findings')

    refs=read(REFMAP)
    ca=[r for r in refs if r.get('sparc_ref_id')=='Ca88' and r.get('galaxy')=='UGC02259']
    if len(ca)!=1 or ca[0].get('stationary_role')!='calibration':
        raise RuntimeError(f'Unexpected Ca88 frozen mapping: {ca}')

    rows=read(DISP); fields=list(rows[0]); by={r['sparc_ref_id']:r for r in rows}
    new={
        'sparc_ref_id':'Ca88',
        'queue_status':'defer_until_new_mechanism',
        'disposition':'same_Carignan1988_UGC02259_original_HI_source_already_exhaustively_audited_under_Be91_decomposition',
        'validation_artifact':'validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_QC_V1.md',
        'reopen_rule':'new_machine_readable_radial_table_public_calibrated_map_cube_exact_native_vector_or_analytic_republication',
        'notes':(
            'UGC02259 (calibration). Carignan, Sancisi & van Albada 1988 directly publishes the radial H I distribution in Fig. 5, '
            'derived by averaging H I surface densities in rings. This exact original-source branch was already audited under the Be91 decomposition: '
            'public tables are rotation/observing/mass-model products rather than radius-versus-Sigma_HI; the public PDF has image content and no native vector drawings; '
            'bounded CDS/VizieR search found no machine-readable radial H I table. Do not repeat the Ca88 search absent a genuinely new mechanism. No raster digitization.'
        )
    }
    if 'Ca88' in by: by['Ca88'].update(new)
    else: rows.append(new)
    rows.sort(key=lambda r:r['sparc_ref_id'])
    write(DISP,rows,fields)

    CHECK.write_text(
        '# Ca88 / UGC02259 stationary H I checkpoint\n\n'
        'Status: **REDIRECTED TO EXISTING COMPLETED ORIGINAL-SOURCE AUDIT; DO NOT RESTART**\n\n'
        '- Frozen target: UGC02259 — calibration.\n'
        '- Ca88 is Carignan, Sancisi & van Albada (1988), the same original H I branch already audited during Be91 decomposition.\n'
        '- Direct radial H I distribution: Fig. 5.\n'
        '- Public paper: figure-only radial profile; no numerical Sigma_HI table and no native vector drawings in the audited public copy.\n'
        '- Existing authority: `validation/stationary/BE91_ORIGINAL_SOURCE_PROFILE_QC_V1.md`.\n'
        '- No raster digitization or map reconstruction.\n'
        '- `L_A` and `C_A` remain locked.\n\n'
        '## Resume point\nRun the existing reference-family ranking and continue the new highest-ranked actionable family.\n',
        encoding='utf-8')
    print(json.dumps({'status':'CA88_REDIRECTED_TO_EXISTING_BE91_AUDIT','galaxy':'UGC02259','role':'calibration','checkpoint':str(CHECK)},indent=2))

if __name__=='__main__': main()
