#!/usr/bin/env python3
"""Close Tr09 after the committed target-specific source audit.

The broad inventory flagged channel-map PostScript because random ASCII85/image
stream bytes happened to contain H/I-like substrings. This script verifies from
the committed audit that every such flag is inside a raster channel-map asset,
that the actual target tilted-ring vector plots carry no H I radial-density
label, that the appendix summary panels are raster image products, and that no
target radial-density table exists. It then writes the anti-loop disposition.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

AUD=Path('validation/stationary/tr09_target_figure_inventory_v1.json')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CP=Path('validation/stationary/CHECKPOINT_AFTER_TR09_DISPOSITION.md')


def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

x=json.loads(AUD.read_text())
if x.get('exact_table_candidate') is not False:
    raise RuntimeError('Tr09 target table still requires audit')
figs=x['target_figure_blocks']
# The actual radial-coordinate figures are tilted-ring kinematics, not density profiles.
tilt=[f for f in figs if f['caption'].startswith('Tilted-ring analysis of D564-8') or f['caption'].startswith('Tilted-ring analysis of D631-7')]
if len(tilt)!=2:
    raise RuntimeError(f'Expected exactly two target tilted-ring figures, got {len(tilt)}')
for f in tilt:
    a=f['assets'][0]
    if a.get('has_radial_hi_density_label') or a.get('image_ops')!=0 or a.get('colorimage_ops')!=0:
        raise RuntimeError('Unexpected density/raster state in target tilted-ring figure: '+repr(f))
# Appendix summary products are moment/PV map composites with embedded raster images.
summ=[f for f in figs if f['caption'].startswith('Summary panel for D564-8') or f['caption'].startswith('Summary panel for D631-7')]
if len(summ)!=2 or any(f['assets'][0].get('image_ops',0)<=0 for f in summ):
    raise RuntimeError('Unexpected appendix summary-panel structure')
# Any parser-flagged radial asset must be a channel map with embedded image streams;
# therefore the apparent text hits are encoded-image false positives, not labels.
flag=x.get('radial_hi_density_assets',[])
if not flag:
    raise RuntimeError('Expected committed false-positive channel-map flags for explicit resolution')
for z in flag:
    if not z['caption'].startswith('Channel maps of '):
        raise RuntimeError('Non-channel asset remains flagged: '+repr(z))
    # Resolve back to figure asset and require raster image operators.
    match=[f for f in figs if f['caption']==z['caption']]
    if len(match)!=1 or match[0]['assets'][0].get('image_ops',0)<1:
        raise RuntimeError('Flagged asset is not confirmed embedded-image channel map')

rows=read_csv(DISP); fields=list(rows[0]); by={r['sparc_ref_id']:r for r in rows}
entry={
    'sparc_ref_id':'Tr09',
    'queue_status':'defer_until_new_mechanism',
    'disposition':'original_hi_observations_public_but_no_exact_radial_hi_profile_published_in_source_products',
    'validation_artifact':str(AUD),
    'reopen_rule':'new_machine_readable_radial_hi_profile_exact_vector_republication_or_public_author_derived_profile_array',
    'notes':(
        'Trachternach et al. 2009 is the original H I synthesis observing paper for D564-8 and D631-7. '
        'Target main figures 11136fg3.ps and 11136fg5.ps are source-native vector GIPSY tilted-ring kinematic plots, not H I surface-density profiles. '
        'Appendix summary panels 11136fA4.ps and 11136fA9.ps are moment/PV map composites with embedded raster image operators; channel maps are likewise raster image streams. '
        'No target radius-by-Sigma_HI table or exact radial-density vector asset was found. Parser H/I string hits in channel-map files were verified as encoded image-stream false positives. '
        'No raster digitization or map-to-profile reconstruction performed.'
    )
}
if 'Tr09' in by: by['Tr09'].update(entry)
else: rows.append(entry)
rows.sort(key=lambda r:r['sparc_ref_id']);write_csv(DISP,rows,fields)
CP.write_text(
    '# Post-Tr09 stationary H I checkpoint\n\n'
    'Status: **TR09 CLOSED — NO EXACT PUBLIC RADIAL H I PROFILE ROUTE**\n\n'
    '- D564-8 and D631-7: original H I observations are Trachternach et al. 2009.\n'
    '- Tilted-ring figures are vector but kinematic, not radial H I surface-density profiles.\n'
    '- Appendix summary/channel products are map/image products; no radius-by-Sigma_HI table or vector profile.\n'
    '- Do not raster-digitize or reconstruct a profile from the moment map.\n'
    '- Do not restart Tr09 unless its explicit reopen rule is satisfied.\n'
    '- `L_A` and `C_A` remain locked.\n\n'
    '## Resume point\nRun the existing Lelli/SPARC family ranking and continue with the new highest-ranked actionable family.\n',encoding='utf-8')
print(json.dumps({'status':'TR09_DISPOSITION_CLOSED_NO_EXACT_PROFILE','flagged_channel_assets_resolved':len(flag),'checkpoint':str(CP)},indent=2))
