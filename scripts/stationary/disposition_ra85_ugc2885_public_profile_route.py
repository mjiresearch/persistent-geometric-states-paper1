#!/usr/bin/env python3
"""Disposition RA85 / UGC02885 after bounded exact public-profile recovery.

Lelli/SPARC points to Roelfsema & Allen (1985).  A later independent WSRT
observation (Hunter et al. 2013) directly derives the UGC 2885 radial H I
surface-density profile and is therefore a high-value public replacement route.
Two independent committed source-package audits show that the arXiv package
contains the relevant profile only as JPEG figures and no numeric sidecar or
PostScript/vector profile asset.  Do not raster-digitize; defer until a new exact
public mechanism appears.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
AUD1=Path('validation/stationary/ra85_hunter2013_ugc2885_profile_route_v1.json')
AUD2=Path('validation/stationary/ra85_ugc2885_hunter2013_public_profile_audit_v1.json')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_RA85_DISPOSITION.md')

def read(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    hits=[r for r in read(REF) if r.get('sparc_ref_id')=='RA85']
    if len(hits)!=1 or hits[0].get('galaxy')!='UGC02885' or hits[0].get('stationary_role')!='calibration':
        raise RuntimeError(f'RA85 frozen mapping changed: {hits}')
    if not AUD1.exists() or not AUD2.exists():
        raise RuntimeError('RA85 Hunter 2013 audits missing; restore committed audits rather than restarting.')
    a=json.loads(AUD1.read_text(encoding='utf-8'))
    b=json.loads(AUD2.read_text(encoding='utf-8'))
    if a.get('status')!='RA85_HUNTER2013_UGC2885_PROFILE_ROUTE_AUDIT_COMPLETE':
        raise RuntimeError('Unexpected primary RA85 audit status')
    if b.get('status')!='RA85_UGC2885_HUNTER2013_PUBLIC_PROFILE_AUDIT_COMPLETE':
        raise RuntimeError('Unexpected independent RA85 audit status')
    if a.get('decision_fields',{}).get('n_numeric_sidecars')!=0:
        raise RuntimeError('RA85 audit now reports a numeric sidecar; do not defer.')
    if a.get('decision_fields',{}).get('any_ps_vector_signal'):
        raise RuntimeError('RA85 audit now reports vector signal; do not defer.')
    names={x.get('name') for x in a.get('candidate_profile_assets',[])}
    if 'fig14.jpg' not in names:
        raise RuntimeError(f'Expected UGC2885 Figure 14 asset absent: {names}')

    rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
    new={
        'sparc_ref_id':'RA85',
        'queue_status':'defer_until_new_mechanism',
        'disposition':'original_RA85_target_confirmed_but_later_direct_WSRT_profile_public_only_as_JPEG_no_numeric_or_vector_asset',
        'validation_artifact':'validation/stationary/ra85_hunter2013_ugc2885_profile_route_v1.json',
        'reopen_rule':'new_machine_readable_author_table_exact_native_vector_public_profile_array_or_calibrated_HI_map_cube_with_predeclared_reconstruction_protocol',
        'notes':(
            'UGC02885/UGC 2885 (calibration). Lelli/SPARC RA85 is Roelfsema & Allen 1985. '
            'A later independent direct WSRT observation, Hunter et al. 2013 (AJ 146,92; arXiv:1307.7116), derives radial H I surface densities from the integrated H I map with GIPSY using the optical ellipse geometry and 14.8-arcsec radial step. '
            'Its Figure 14 publishes the face-on H I+He surface-density profile for UGC 2885. Two committed source-package audits find 17 source files, profile figures as JPEG only (including fig14.jpg), zero numerical sidecars, and no PostScript/vector profile asset. '
            'A separate 2007 WSRT tilted-ring analysis confirms an H I surface-density profile/terminal edge but no public exact numeric profile asset was identified in the bounded search. '
            'Do not raster-digitize or reconstruct from maps under the current frozen protocol.'
        )
    }
    if 'RA85' in by:by['RA85'].update(new)
    else:rows.append(new)
    rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
    CHECK.write_text(
        '# RA85 / UGC02885 stationary H I checkpoint\n\n'
        'Status: **DIRECT H I PROFILE CONFIRMED; CURRENT EXACT PUBLIC NUMERIC/VECTOR ROUTE EXHAUSTED**\n\n'
        '- Frozen target: UGC02885 / UGC 2885 — calibration.\n'
        '- Lelli/SPARC source family: RA85 = Roelfsema & Allen (1985).\n'
        '- High-value later direct route: Hunter et al. (2013), new WSRT H I observations.\n'
        '- Hunter et al. derive radial H I surface densities directly from the integrated H I map with GIPSY, at the same 14.8-arcsec annular step as the optical photometry.\n'
        '- UGC2885 Figure 14 is the face-on H I+He radial profile.\n'
        '- arXiv source package: figures are JPEG; no numerical sidecar or native-vector profile asset.\n'
        '- Independent audit agrees; no raster digitization or map reconstruction.\n'
        '- Reopen only for a genuinely new exact public profile/table/vector/array, or a separately frozen calibrated-map reconstruction protocol.\n'
        '- `L_A` and `C_A` remain locked.\n\n'
        '## Resume point\nReconcile/rerank and continue the new highest-ranked actionable Lelli family.\n',encoding='utf-8')
    print(json.dumps({'status':'RA85_DEFERRED_EXACT_PUBLIC_ROUTE_EXHAUSTED','galaxy':'UGC02885','role':'calibration','checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
