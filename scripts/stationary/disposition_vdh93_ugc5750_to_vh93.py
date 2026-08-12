#!/usr/bin/env python3
"""Resolve VdH93 / UGC05750 as the already-audited van der Hulst et al. 1993 H I source.

SPARC/Lelli carries an unresolved `VdH93` code for UGC05750. The repository's
frozen dB01 original-source decomposition independently maps UGC05750 to van der
Hulst et al. (1993), and the existing VH93 audit explicitly includes UGC05750
among the Figure-2 radial H I profiles. This script records that alias/provenance
link and prevents a duplicate public-source search under a second spelling/code.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DB01=Path('data/stationary/source_reconstruction/db01_original_hi_source_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
VH93=Path('validation/stationary/VH93_PUBLIC_PROFILE_ROUTE_AUDIT_V1.md')
OUT=Path('validation/stationary/vdh93_ugc5750_provenance_redirect_v1.json')
CHECK=Path('validation/stationary/CHECKPOINT_VDH93_UGC5750_REDIRECT_TO_VH93.md')

def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    refs=read_csv(REF)
    vd=[r for r in refs if r.get('galaxy')=='UGC05750' and r.get('sparc_ref_id')=='VdH93']
    db=[r for r in refs if r.get('galaxy')=='UGC05750' and r.get('sparc_ref_id')=='dB01']
    if len(vd)!=1 or len(db)!=1 or vd[0].get('stationary_role')!='calibration' or db[0].get('stationary_role')!='calibration':
        raise RuntimeError(f'UGC05750 frozen mapping changed: VdH93={vd}, dB01={db}')

    src=[r for r in read_csv(DB01) if r.get('galaxy')=='UGC05750']
    if len(src)!=1:
        raise RuntimeError(f'UGC05750 dB01 original-source row changed: {src}')
    s=src[0]
    if s.get('original_hi_source')!='van_der_Hulst_et_al_1993_VH93':
        raise RuntimeError(f'UGC05750 upstream H I source changed: {s}')

    if not VH93.exists():
        raise RuntimeError('Existing VH93 audit missing')
    txt=VH93.read_text(encoding='utf-8').lower()
    required=['ugc05750','figure 2','radial h i surface-density','scanned journal reproduction','no curve digitization']
    missing=[x for x in required if x not in txt]
    if missing:
        raise RuntimeError(f'VH93 audit no longer contains expected UGC05750 evidence: {missing}')

    audit={
        'status':'VDH93_UGC05750_REDIRECT_TO_VH93_CONFIRMED',
        'galaxy':'UGC05750','stationary_role':'calibration','sparc_ref_id':'VdH93',
        'sparc_mapping':{'VdH93':vd[0],'dB01':db[0]},
        'upstream_source_trace':s,
        'existing_vh93_state':{
            'artifact':str(VH93),
            'source':'van der Hulst et al. 1993, AJ 106, 548-559',
            'product':'Figure 2 radial H I surface-density profile for UGC5750',
            'current_public_recoverability':'scan-only figure values; no exact numeric/native-vector series established'
        },
        'decision':'Treat unresolved VdH93 as the already-audited VH93 source lineage for UGC05750; do not repeat the exhausted public scan/table search.',
        'reopen_rule':'reopen_only_for_a_genuinely_new_machine_readable_radial_table_exact_native_vector_republication_public_calibrated_map_cube_with_predeclared_reconstruction_protocol_or_documented_source_correction',
        'boundary':'No raster digitization, map/cube reconstruction, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked.'
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')

    rows=read_csv(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
    new={
        'sparc_ref_id':'VdH93','queue_status':'redirect_existing_source_family',
        'disposition':'unresolved_VdH93_code_for_UGC05750_maps_via_dB01_source_trace_to_already_audited_van_der_Hulst1993_VH93_HI_source',
        'validation_artifact':str(OUT),
        'reopen_rule':audit['reopen_rule'],
        'notes':(
            'UGC05750/UGC5750 (calibration). SPARC/Lelli unresolved code VdH93 is paired with dB01. '
            'The frozen dB01 original-source map independently identifies van der Hulst et al. 1993 (VH93) as the resolved H I source for UGC05750. '
            'The existing VH93 audit explicitly includes UGC05750 in Figure 2 and establishes direct radial H I surface-density points, but the current public copy is scan-only with no exact numerical/native-vector route. '
            'Do not repeat the exhausted VH93 search under the VdH93 code.'
        )
    }
    if 'VdH93' in by: by['VdH93'].update(new)
    else: rows.append(new)
    rows.sort(key=lambda r:r['sparc_ref_id'])
    write_csv(DISP,rows,fields)

    CHECK.write_text(
        '# VdH93 / UGC05750 stationary H I checkpoint\n\n'
        'Status: **UNRESOLVED LELLI CODE REDIRECTED TO EXISTING VH93 SOURCE STATE**\n\n'
        '- Frozen target: UGC05750 / UGC5750 — calibration.\n'
        '- SPARC/Lelli lists `dB01` plus unresolved `VdH93` for this target.\n'
        '- Frozen dB01 original-source decomposition maps UGC05750 to van der Hulst et al. (1993), `VH93`.\n'
        '- Existing `VH93` audit explicitly includes UGC05750 in Figure 2 radial H I surface-density profiles.\n'
        '- Current public VH93 product remains scan-only; no exact numeric/native-vector series was established, and no raster digitization is allowed.\n'
        f'- Durable provenance redirect: `{OUT}`.\n'
        f'- Existing source-route authority: `{VH93}`.\n'
        '- `L_A` and `C_A` remain locked.\n\n'
        '## Resume point\nRerank and continue the next actionable Lelli family. Do not reopen VH93 merely because `VdH93` appears as a separate unresolved code.\n',
        encoding='utf-8')
    print(json.dumps({'status':audit['status'],'checkpoint':str(CHECK)},indent=2))

if __name__=='__main__':
    main()
