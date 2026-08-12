#!/usr/bin/env python3
"""Close Bl99 -> Co91 provenance chain for NGC5585 without raster digitization.

Bl99 is a downstream Halpha/mass-model paper reusing the Co91 Westerbork H I
profile. Co91 directly publishes the raw radial H I surface-density profile in
Figure 6, but the bounded public exact-value route currently resolves only to a
scan/raster article. The frozen target is blind; no outcome information is read.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
BL=Path('validation/stationary/bl99_ngc5585_hi_provenance_profile_audit_v1.json')
CO=Path('validation/stationary/co91_ngc5585_public_hi_profile_route_v1.json')
OUT=Path('validation/stationary/bl99_co91_ngc5585_source_disposition_v1.json')
CHECK=Path('validation/stationary/CHECKPOINT_BL99_CO91_NGC5585_SOURCE_DISPOSITION.md')

def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    refs=read_csv(REF)
    blref=[r for r in refs if r.get('galaxy')=='NGC5585' and r.get('sparc_ref_id')=='Bl99']
    coref=[r for r in refs if r.get('galaxy')=='NGC5585' and r.get('sparc_ref_id')=='Co91']
    if len(blref)!=1 or len(coref)!=1 or blref[0].get('stationary_role')!='blind' or coref[0].get('stationary_role')!='blind':
        raise RuntimeError(f'Frozen NGC5585 mapping changed: Bl99={blref}, Co91={coref}')
    bl=json.loads(BL.read_text(encoding='utf-8'));co=json.loads(CO.read_text(encoding='utf-8'))
    if bl.get('status')!='BL99_NGC5585_HI_PROVENANCE_PROFILE_AUDIT_COMPLETE':raise RuntimeError('Bl99 audit status changed')
    if co.get('status')!='CO91_NGC5585_PUBLIC_ROUTE_AUDIT_COMPLETE':raise RuntimeError('Co91 audit status changed')
    # Bl99 source package must remain TeX + figures only, with no machine-readable radial-profile sidecar.
    inv=bl.get('member_inventory',[])
    names=[x.get('name','') for x in inv]
    data_ext=('.dat','.csv','.tab','.tbl')
    if any(n.lower().endswith(data_ext) for n in names):raise RuntimeError(f'New Bl99 data sidecar appeared: {names}')
    joined=json.dumps(bl.get('text_contexts',[]))
    required=['C\\\\^ot\\\\\'e, Carignan, \\\\& Sancisi 1991','radial profile scaled by 1.33','kinematics are from C\\\\^ot\\\\\'e, Carignan, \\\\& Sancisi 1991']
    # Escaping in JSON may vary; use simpler semantic substrings too.
    semantic=['radial profile scaled by 1.33','kinematics are from','Carignan','Sancisi 1991']
    if any(x not in joined for x in semantic):raise RuntimeError('Bl99 provenance/profile evidence changed')
    # Co91 public PDF must remain structurally raster/scan-only in bounded audit.
    pdfs=co.get('pdf_structural_audits',[])
    good=[p for p in pdfs if 'page_count' in p]
    if len(good)!=1:raise RuntimeError(f'Unexpected Co91 PDF audits: {pdfs}')
    if any(pg.get('n_drawings')!=0 for pg in good[0].get('pages',[])):raise RuntimeError('Co91 public PDF now has native vector drawings; reopen exact route')
    ctx=json.dumps(good[0].get('contexts',[]))
    for phrase in ['Radial distribution of HI surface density for NGC 5585','multiplied by 4/3 to include a correction for the primordial helium content']:
        if phrase not in ctx:raise RuntimeError(f'Co91 expected source evidence missing: {phrase}')
    decision={
      'status':'BL99_CO91_NGC5585_CHAIN_DISPOSITIONED',
      'galaxy':'NGC5585','stationary_role':'blind',
      'bl99':{
        'decision':'redirect_to_Co91_original_direct_HI_source',
        'reason':'Bl99 is new CFHT Halpha analysis using pre-existing 20-arcsec Westerbork H I; its text says H I kinematics are from Cote, Carignan & Sancisi 1991 and the gas contribution uses that H I radial profile scaled by 1.33 for helium. Public source package has TeX plus figures but no numerical H I profile sidecar.',
        'audit':str(BL)},
      'co91':{
        'decision':'defer_exact_numeric_profile_pending_new_public_mechanism',
        'reason':'Co91 directly publishes Figure 6 raw radial H I surface density, derived from average H I brightness in concentric ellipses with cos(i) correction; helium x4/3 is applied only later in mass modeling. Current bounded public ADS copy is scan/raster-only with zero native drawings and no exact machine-readable series established.',
        'audit':str(CO)},
      'reopen_rule':'reopen_for_machine_readable_Co91_or_author_table_exact_native_vector_republication_or_public_calibrated_HI_map_cube_under_a_predeclared_reconstruction_protocol_or_documented_source_correction',
      'boundary':'No OCR, raster digitization, ad-hoc map/cube reconstruction, blind rotation-outcome inspection, profile fitting, or persistence fitting. L_A and C_A remain locked.'}
    OUT.write_text(json.dumps(decision,indent=2)+'\n',encoding='utf-8')
    rows=read_csv(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
    updates={
      'Bl99':{
        'sparc_ref_id':'Bl99','queue_status':'redirect_original_hi_source_family',
        'disposition':'NGC5585_Bl99_downstream_Halpha_mass_model_reuses_Co91_Westerbork_HI_radial_profile',
        'validation_artifact':str(OUT),'reopen_rule':decision['reopen_rule'],
        'notes':'NGC5585 blind. Bl99 explicitly states its H I kinematics are from Cote, Carignan & Sancisi 1991 and uses the H I radial profile scaled by 1.33 for He. No numerical H I sidecar in the Bl99 arXiv source package. Redirect to Co91; do not treat Bl99 as independent 21-cm observations.'},
      'Co91':{
        'sparc_ref_id':'Co91','queue_status':'deferred_exact_profile_route_exhausted',
        'disposition':'NGC5585_Co91_direct_Fig6_raw_HI_surface_density_but_current_public_exact_route_scan_only',
        'validation_artifact':str(OUT),'reopen_rule':decision['reopen_rule'],
        'notes':'NGC5585 blind. Co91 directly publishes Figure 6 radial H I surface density from concentric ellipses with inclination correction; 4/3 helium is applied separately later. ADS public article is scan/raster-only with zero native drawings; no machine-readable/native-vector exact series established in bounded public search. No raster digitization.'}}
    for code,new in updates.items():
        if code in by:by[code].update(new)
        else:rows.append(new)
    rows.sort(key=lambda r:r['sparc_ref_id']);write_csv(DISP,rows,fields)
    CHECK.write_text(
      '# Bl99 / Co91 / NGC5585 stationary H I checkpoint\n\n'
      'Status: **BL99 REDIRECTED TO CO91; CO91 EXACT PUBLIC PROFILE ROUTE DEFERRED**\n\n'
      '- Frozen target: NGC5585 — blind. No blind rotation/persistence outcome was inspected.\n'
      '- Bl99 is a downstream CFHT Halpha/mass-model paper using the pre-existing Westerbork H I data from Cote, Carignan & Sancisi (1991).\n'
      '- Bl99 explicitly says the gaseous contribution uses the H I radial profile scaled by 1.33 for He; no numerical radial-H I sidecar is present in its public arXiv source package.\n'
      '- Co91 is the direct 21-cm source. Figure 6 is the radial H I surface-density distribution, derived from concentric ellipses and corrected by cos(i).\n'
      '- Co91 applies 4/3 helium only later in the mass model; Figure 6 therefore represents the raw H I profile.\n'
      '- The bounded public Co91 article route is scan/raster-only with zero native PDF drawings; no exact numerical/native-vector series was established.\n'
      f'- Durable disposition: `{OUT}`.\n'
      '- Reopen only for a genuinely new exact public mechanism listed in the disposition; do not raster-digitize or rebuild a cube ad hoc.\n'
      '- `L_A` and `C_A` remain locked.\n\n'
      '## Resume point\nRerank and continue the next actionable Lelli family.\n',encoding='utf-8')
    print(json.dumps({'status':decision['status'],'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
