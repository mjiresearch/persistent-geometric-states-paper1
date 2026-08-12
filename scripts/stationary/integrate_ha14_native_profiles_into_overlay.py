#!/usr/bin/env python3
"""Promote recovered Ha14 source-native H I profiles into the stationary overlay.

This consumes the already-recovered Hallenbeck et al. 2014 Figure 9 vector
profiles. It does not re-extract them. The script verifies the committed
validation artifact and frozen roles/reference mapping, then updates only the
public-source overlay and Ha14 family disposition.

L_A and C_A remain locked. No profile normalization, persistence fitting, or
blind-outcome inspection is performed.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

VALID=Path('validation/stationary/ha14_vector_hi_profile_extraction_v2.json')
PROFILE=Path('data/stationary/source_reconstruction/ha14_vector_hi_profiles_v2.csv')
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECKPOINT=Path('validation/stationary/CHECKPOINT_AFTER_HA14_PROMOTION.md')
TARGETS={'UGC09037':32,'UGC12506':39}
FAMILY='Hallenbeck et al. 2014'
ART=str(PROFILE)


def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))

def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    if not VALID.exists() or not PROFILE.exists():
        raise RuntimeError('Ha14 recovery products missing; do not rerun extraction—restore committed recovery artifacts first.')
    v=json.loads(VALID.read_text())
    if v.get('status')!='HA14_NATIVE_VECTOR_HI_PROFILES_RECOVERED_V2':
        raise RuntimeError(f'Unexpected Ha14 validation status: {v.get("status")}')
    if v.get('profile_csv')!=ART:
        raise RuntimeError('Ha14 validation points to unexpected profile CSV')
    for g,n in TARGETS.items():
        q=v['profiles'][g]['qc']
        if not q.get('passes') or q.get('n_profile_points')!=n:
            raise RuntimeError(f'{g}: committed recovery QC/row count mismatch: {q}')

    prof=read_csv(PROFILE)
    counts={g:0 for g in TARGETS}
    for r in prof:
        if r['galaxy'] in counts: counts[r['galaxy']]+=1
    if counts!=TARGETS:
        raise RuntimeError(f'Profile CSV row counts mismatch: {counts} != {TARGETS}')

    refs=read_csv(REFMAP)
    ha14=[r for r in refs if r['sparc_ref_id']=='Ha14']
    mapped={r['galaxy']:r['stationary_role'] for r in ha14 if r['galaxy'] in TARGETS}
    if set(mapped)!=set(TARGETS):
        raise RuntimeError(f'Ha14 reference mapping mismatch: {mapped}')
    if any(role!='calibration' for role in mapped.values()):
        raise RuntimeError(f'Ha14 target role changed unexpectedly: {mapped}')

    rows=read_csv(OVERLAY); fields=list(rows[0])
    by={r['galaxy']:r for r in rows}
    for g,n in TARGETS.items():
        new={
            'galaxy':g,
            'stationary_role':'calibration',
            'public_source_family':FAMILY,
            'acquisition_status':'raw_source_profile_ingested',
            'numeric_rows_or_model':str(n),
            'source_quantity':'source-native deprojected HI surface density from published Figure 9 vector primitives',
            'helium_status':'helium not applied; recovered quantity is HI surface density',
            'preferred_public_source':'1',
            'source_artifact':ART,
            'notes':(
                f'Hallenbeck et al. 2014 Figure 9 / fig-density.eps source-native IDL filled-circle profile recovered: {n} radial points. '
                'Values decoded from native vector primitives with printed-axis calibration; no raster digitization, profile fitting, distance renormalization, helium correction, or common-grid resampling applied. '
                'Validation: validation/stationary/ha14_vector_hi_profile_extraction_v2.json.'
            ),
        }
        old=by.get(g)
        if old is None:
            rows.append(new); by[g]=new
        else:
            # Idempotent upgrade only; never silently replace a different preferred source.
            if old.get('preferred_public_source')=='1' and old.get('source_artifact') not in ('',ART):
                raise RuntimeError(f'{g}: existing different preferred public source: {old}')
            old.update(new)
    rows.sort(key=lambda r:r['galaxy'])
    if len({r['galaxy'] for r in rows})!=len(rows): raise RuntimeError('Duplicate galaxy in overlay after Ha14 promotion')
    write_csv(OVERLAY,rows,fields)

    drows=read_csv(DISP); dfields=list(drows[0]); dby={r['sparc_ref_id']:r for r in drows}
    dnew={
        'sparc_ref_id':'Ha14',
        'queue_status':'resolved_public_profile_recovered',
        'disposition':'both_frozen_ha14_profiles_recovered_from_source_native_vector_figure',
        'validation_artifact':'validation/stationary/ha14_vector_hi_profile_extraction_v2.json',
        'reopen_rule':'reopen_only_for_higher_fidelity_machine_readable_author_table_or_documented_source_correction',
        'notes':(
            'UGC09037 and UGC12506 recovered from Hallenbeck et al. 2014 Figure 9 native IDL EPS as filled-circle radial H I samples with matching vector error bars. '
            '32 and 39 radial rows respectively; no raster digitization. Both are calibration galaxies. Later fit-derived R_HI values are advisory and were not substituted for the native profile.'
        ),
    }
    if 'Ha14' in dby: dby['Ha14'].update(dnew)
    else: drows.append(dnew)
    drows.sort(key=lambda r:r['sparc_ref_id'])
    write_csv(DISP,drows,dfields)

    CHECKPOINT.write_text(
        '# Post-Ha14 stationary H I checkpoint\n\n'
        'Status: **HA14 PROMOTED; RECONCILE/RERANK NEXT**\n\n'
        '- Ha14 extraction must not be restarted.\n'
        '- UGC09037: 32 source-native radial H I points.\n'
        '- UGC12506: 39 source-native radial H I points.\n'
        f'- Profile artifact: `{ART}`\n'
        '- Validation: `validation/stationary/ha14_vector_hi_profile_extraction_v2.json`\n'
        '- Public overlay updated and Ha14 marked resolved.\n'
        '- `L_A` and `C_A` remain locked.\n\n'
        '## Resume point\n'
        'Run the existing public-source reconciliation and Lelli/SPARC reference-family ranking. Then continue with the new highest-ranked actionable family. Do not revisit Ha14 unless its explicit reopen rule is satisfied.\n',
        encoding='utf-8')
    print(json.dumps({'status':'HA14_PROMOTED_TO_PUBLIC_OVERLAY','targets':TARGETS,'overlay_rows':len(rows),'checkpoint':str(CHECKPOINT)},indent=2))

if __name__=='__main__': main()
