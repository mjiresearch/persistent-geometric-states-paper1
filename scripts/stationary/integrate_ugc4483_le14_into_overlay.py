#!/usr/bin/env python3
from pathlib import Path
import csv, json

VAL=Path('validation/stationary/lelli2012b_ugc4483_hi_profile_recovery_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/lelli2012b_ugc4483_hi_profile_v1.csv')
OVER=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CP=Path('validation/stationary/CHECKPOINT_AFTER_LE14_PROMOTION.md')

def rd(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def wr(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

v=json.loads(VAL.read_text())
assert v['status']=='UGC4483_NATIVE_VECTOR_HI_PROFILE_RECOVERED'
assert v['galaxy_frozen_name']=='UGC04483' and v['profile_summary']['n_rows']==10 and v['hard_qc']['passes']
assert v['profile_csv']==str(PROFILE)
assert len(rd(PROFILE))==10

rows=rd(OVER); fields=list(rows[0]); by={r['galaxy']:r for r in rows}
new={'galaxy':'UGC04483','stationary_role':'calibration','public_source_family':'Lelli et al. 2012b (Le14 upstream)',
     'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'10',
     'source_quantity':'inclination-corrected azimuthally averaged HI surface density; whole-galaxy Figure 6 dot series',
     'helium_status':'helium not applied; source profile is HI surface density','preferred_public_source':'1','source_artifact':str(PROFILE),
     'notes':'UGC4483 whole-galaxy radial HI profile recovered from source-native gnuplot CircleF calls in Lelli et al. 2012b Fig. 6. Ten monotonic data calls; one non-monotonic CircleF legend call excluded. Native kpc/arcsec/Sigma_HI axes decoded from EPS. No raster digitization, profile fitting, or helium correction.'}
old=by.get('UGC04483')
if old is None: rows.append(new)
else:
    if old.get('preferred_public_source')=='1' and old.get('source_artifact') not in ('',str(PROFILE)):
        raise RuntimeError('UGC04483 already has a different preferred source: '+repr(old))
    old.update(new)
rows.sort(key=lambda r:r['galaxy']); wr(OVER,rows,fields)

d=rd(DISP); df=list(d[0]); db={r['sparc_ref_id']:r for r in d}
entry={'sparc_ref_id':'Le14','queue_status':'partially_resolved_upstream_split_closed',
       'disposition':'ugc04483_recovered_ngc4068_redirects_to_already_deferred_sw02',
       'validation_artifact':'validation/stationary/lelli2012b_ugc4483_hi_profile_recovery_v1.json',
       'reopen_rule':'new_machine_readable_or_exact_vector_profile_for_ngc4068_or_documented_source_correction',
       'notes':'Le14 split by original H I provenance. UGC04483 recovered as 10 exact source-native Figure-6 whole-galaxy radial HI points via Lelli et al. 2012b. NGC4068 redirects to Swaters et al. 2002/WHISP, whose historical atlas target figures were already recovered and audited as raster-dominant with no exact numeric/vector profile route. Do not reopen Sw02 absent its reopen condition.'}
if 'Le14' in db: db['Le14'].update(entry)
else:d.append(entry)
d.sort(key=lambda r:r['sparc_ref_id']);wr(DISP,d,df)

CP.write_text('# Post-Le14 stationary H I checkpoint\n\nStatus: **UGC04483 PROMOTED; LE14 SPLIT CLOSED; RECONCILE/RERANK NEXT**\n\n- UGC04483: 10 source-native whole-galaxy H I points from Lelli et al. 2012b Figure 6.\n- NGC4068: redirects to Sw02/WHISP, already deferred after exact public vector/numeric route exhaustion.\n- Do not restart Ha14, Le14, UGC4483 extraction, or Sw02.\n- `L_A` and `C_A` remain locked.\n\n## Resume point\nRun existing public-source reconciliation and Lelli/SPARC family ranking. Continue with the new highest-ranked actionable family.\n')
print(json.dumps({'status':'LE14_UGC4483_PROMOTED_SPLIT_CLOSED','overlay_rows':len(rows),'checkpoint':str(CP)},indent=2))
