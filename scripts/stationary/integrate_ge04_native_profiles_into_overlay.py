#!/usr/bin/env python3
"""Promote recovered Ge04 source-native H I profiles into the stationary overlay.

Consumes already-committed Gentile et al. 2004 Figure-2 vector profiles. This
script does not re-extract publication data. It verifies the recovery QC and
frozen Lelli/SPARC roles, updates only the public-source acquisition overlay and
Ge04 family disposition, and writes the durable resume checkpoint.

L_A and C_A remain locked. No profile normalization, persistence fitting, or
blind-outcome inspection is performed.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

VALID=Path('validation/stationary/ge04_vector_hi_profile_extraction_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/ge04_vector_hi_profiles_v1.csv')
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECKPOINT=Path('validation/stationary/CHECKPOINT_AFTER_GE04_PROMOTION.md')
TARGETS={'ESO079-G014':('calibration',12),'ESO116-G012':('blind',14)}
FAMILY='Gentile et al. 2004'
ART=str(PROFILE)


def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def main():
    if not VALID.exists() or not PROFILE.exists():
        raise RuntimeError('Ge04 recovery products missing; restore committed artifacts rather than re-running earlier audits.')
    v=json.loads(VALID.read_text(encoding='utf-8'))
    if v.get('status')!='GE04_NATIVE_VECTOR_HI_PROFILES_RECOVERED':
        raise RuntimeError(f'Unexpected Ge04 recovery status: {v.get("status")}')
    if v.get('profile_csv')!=ART:
        raise RuntimeError('Ge04 validation points to unexpected profile CSV')
    if v.get('total_profile_rows')!=sum(n for _,n in TARGETS.values()):
        raise RuntimeError('Ge04 total row count mismatch')
    for g,(role,n) in TARGETS.items():
        q=v['profiles'][g]
        if q.get('stationary_role')!=role or q.get('n_profile_points')!=n:
            raise RuntimeError(f'{g}: committed role/count mismatch: {q}')
        if not q['native_grid_qc'].get('passes') or not q['table1_rhi_qc'].get('passes'):
            raise RuntimeError(f'{g}: committed recovery QC not passing')

    prof=read_csv(PROFILE)
    counts={g:0 for g in TARGETS}
    for r in prof:
        if r['galaxy'] in counts:
            counts[r['galaxy']]+=1
            if r.get('stationary_role')!=TARGETS[r['galaxy']][0]:
                raise RuntimeError(f'{r["galaxy"]}: profile role mismatch')
    expected={g:n for g,(_,n) in TARGETS.items()}
    if counts!=expected:raise RuntimeError(f'Ge04 CSV row counts mismatch: {counts} != {expected}')

    refs=read_csv(REFMAP)
    mapped={r['galaxy']:r['stationary_role'] for r in refs if r.get('sparc_ref_id')=='Ge04' and r.get('galaxy') in TARGETS}
    if set(mapped)!=set(TARGETS):raise RuntimeError(f'Ge04 Lelli reference mapping mismatch: {mapped}')
    for g,(role,_) in TARGETS.items():
        if mapped[g]!=role:raise RuntimeError(f'{g}: frozen role changed: {mapped[g]} != {role}')

    rows=read_csv(OVERLAY);fields=list(rows[0]);by={r['galaxy']:r for r in rows}
    for g,(role,n) in TARGETS.items():
        q=v['profiles'][g]
        new={
            'galaxy':g,
            'stationary_role':role,
            'public_source_family':FAMILY,
            'acquisition_status':'raw_source_profile_ingested',
            'numeric_rows_or_model':str(n),
            'source_quantity':'source-native average radial HI surface density from Gentile et al. 2004 Figure 2 filled-circle vector markers',
            'helium_status':'helium not applied; recovered quantity is HI surface density',
            'preferred_public_source':'1',
            'source_artifact':ART,
            'notes':(
                f'Gentile et al. 2004 Figure 2 / fig2.eps native vector average profile recovered: {n} radial H I points. '
                f"Native-grid QC max |delta r|={q['native_grid_qc']['max_abs_delta_arcsec']:.4g} arcsec; "
                f"independent Table-1 R_HI QC fractional difference={q['table1_rhi_qc']['fractional_abs_delta']:.4%}. "
                'radius_kpc_source_scale uses the source-paper angular scale only; no frozen/common distance renormalization, helium correction, raster digitization, profile fitting, or common-grid resampling applied. '
                'Validation: validation/stationary/ge04_vector_hi_profile_extraction_v1.json.'
            ),
        }
        old=by.get(g)
        if old is None:
            rows.append(new);by[g]=new
        else:
            if old.get('preferred_public_source')=='1' and old.get('source_artifact') not in ('',ART):
                raise RuntimeError(f'{g}: existing different preferred public source: {old}')
            old.update(new)
    rows.sort(key=lambda r:r['galaxy'])
    if len({r['galaxy'] for r in rows})!=len(rows):raise RuntimeError('Duplicate galaxy in overlay after Ge04 promotion')
    write_csv(OVERLAY,rows,fields)

    drows=read_csv(DISP);dfields=list(drows[0]);dby={r['sparc_ref_id']:r for r in drows}
    dnew={
        'sparc_ref_id':'Ge04',
        'queue_status':'resolved_public_profile_recovered',
        'disposition':'both_frozen_ge04_profiles_recovered_from_source_native_vector_figure',
        'validation_artifact':'validation/stationary/ge04_vector_hi_profile_extraction_v1.json',
        'reopen_rule':'reopen_only_for_higher_fidelity_machine_readable_author_table_or_documented_source_correction',
        'notes':(
            'ESO079-G014 (calibration) and ESO116-G012 (blind) recovered from Gentile et al. 2004 Figure 2 native EPS filled-circle average H I markers: 12 and 14 radial rows. '
            'Independent source-grid and Table-1 R_HI checks pass. Blind acquisition metadata/profile values were ingested without inspecting any persistence/blind outcome. No raster digitization.'
        ),
    }
    if 'Ge04' in dby:dby['Ge04'].update(dnew)
    else:drows.append(dnew)
    drows.sort(key=lambda r:r['sparc_ref_id']);write_csv(DISP,drows,dfields)

    CHECKPOINT.write_text(
        '# Post-Ge04 stationary H I checkpoint\n\n'
        'Status: **GE04 PROMOTED; RECONCILE/RERANK NEXT**\n\n'
        '- Do not restart Ge04 extraction.\n'
        '- ESO079-G014 (calibration): 12 source-native radial H I points.\n'
        '- ESO116-G012 (blind): 14 source-native radial H I points.\n'
        f'- Profile artifact: `{ART}`\n'
        '- Validation: `validation/stationary/ge04_vector_hi_profile_extraction_v1.json`\n'
        '- Public overlay updated and Ge04 marked resolved.\n'
        '- Blind profile acquisition was performed without inspecting any persistence outcome.\n'
        '- `L_A` and `C_A` remain locked.\n\n'
        '## Resume point\n'
        'Run the existing public-source reconciliation and Lelli/SPARC reference-family ranking. Then continue with the new highest-ranked actionable family. Do not revisit Ge04 unless its explicit reopen rule is satisfied.\n',
        encoding='utf-8')
    print(json.dumps({'status':'GE04_PROMOTED_TO_PUBLIC_OVERLAY','targets':expected,'checkpoint':str(CHECKPOINT)},indent=2))

if __name__=='__main__':main()
