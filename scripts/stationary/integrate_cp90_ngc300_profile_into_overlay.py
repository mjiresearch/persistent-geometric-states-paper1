#!/usr/bin/env python3
"""Promote the Westmeier+2011 NGC300 profile into the stationary public overlay.

Continuation of the Lelli/SPARC CP90 branch. The source profile is the already
committed 20-row native LaTeX Table-2 extraction from deeper ATCA observations.
It is a later higher-fidelity public replacement, not a numerical recovery of
Puche+1990. Any other frozen CP90 members must already have preferred public
profiles and are verified but never modified here.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

VALID=Path('validation/stationary/cp90_westmeier2011_ngc300_profile_extraction_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/westmeier2011_ngc300_gas_profile_v1.csv')
REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_CP90_PROMOTION.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 v=json.loads(VALID.read_text())
 if v.get('status')!='CP90_WESTMEIER2011_NGC300_PROFILE_EXTRACTED' or v.get('n_rows')!=20:
  raise RuntimeError(f'Unexpected CP90 extraction state: {v}')
 if not all(v.get('qc',{}).values()):raise RuntimeError(f'CP90 extraction QC not fully passing: {v.get("qc")}')
 prof=read(PROFILE)
 if len(prof)!=20 or any(r['galaxy']!='NGC0300' or r['stationary_role']!='calibration' for r in prof):
  raise RuntimeError('NGC0300 profile CSV role/count mismatch')
 if [float(r['radius_arcsec']) for r in prof] != [float(x) for x in range(100,2001,100)]:
  raise RuntimeError('NGC0300 profile radius grid changed')
 if any(r['sigma_gas_msun_pc2']=='' for r in prof):raise RuntimeError('Missing NGC0300 Sigma_gas')

 refs=read(REFMAP);cp=[r for r in refs if r.get('sparc_ref_id')=='CP90']
 ng=[r for r in cp if r['galaxy']=='NGC0300']
 if len(ng)!=1 or ng[0]['stationary_role']!='calibration':raise RuntimeError(f'CP90 NGC0300 mapping changed: {ng}')

 rows=read(OVERLAY);fields=list(rows[0]);by={r['galaxy']:r for r in rows}
 # Protect every other CP90 frozen mapping: it must already be resolved if it is
 # absent from the current untouched queue; never overwrite it in this branch.
 other=[]
 for r in cp:
  if r['galaxy']=='NGC0300':continue
  old=by.get(r['galaxy'])
  if old is None or old.get('preferred_public_source')!='1':
   raise RuntimeError(f'Other CP90 member not safely resolved in overlay: {r} -> {old}')
  other.append({'galaxy':r['galaxy'],'role':r['stationary_role'],'existing_source':old['public_source_family'],'existing_rows':old['numeric_rows_or_model']})
 old=by.get('NGC0300')
 if old is not None and old.get('preferred_public_source')=='1' and old.get('source_artifact') not in ('',str(PROFILE)):
  raise RuntimeError(f'NGC0300 already has different preferred public source: {old}')
 new={
  'galaxy':'NGC0300','stationary_role':'calibration',
  'public_source_family':'Westmeier et al. 2011 / NGC300 ATCA',
  'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'20',
  'source_quantity':'source-published face-on gas mass surface density derived from HI column density',
  'helium_status':'already includes helium x1.4','preferred_public_source':'1',
  'source_artifact':str(PROFILE),
  'notes':(
   'Later deeper ATCA public replacement for the Lelli/CP90 NGC0300 branch; not a numerical extraction of Puche et al. 1990. '
   'Exact native LaTeX Westmeier et al. 2011 Table 2 values: 20 rows, 100-2000 arcsec (0.92-18.42 kpc source-paper scale). '
   'Sigma_gas is derived from the HI column-density profile and already includes the paper factor f=1.4 for helium. '
   'No raster digitization, map/cube reconstruction, re-fitting, common-distance renormalization, or persistence fitting. '
   'Validation: validation/stationary/cp90_westmeier2011_ngc300_profile_extraction_v1.json.'
  )}
 if old is None:rows.append(new)
 else:old.update(new)
 rows.sort(key=lambda r:r['galaxy'])
 if len({r['galaxy'] for r in rows})!=len(rows):raise RuntimeError('Overlay duplicate after CP90 promotion')
 write(OVERLAY,rows,fields)

 drows=read(DISP);dfields=list(drows[0]);dby={r['sparc_ref_id']:r for r in drows}
 dnew={
  'sparc_ref_id':'CP90','queue_status':'resolved_public_profile_recovered',
  'disposition':'NGC0300_resolved_by_later_deeper_Westmeier2011_ATCA_native_Table2_profile_other_CP90_members_preserved',
  'validation_artifact':'validation/stationary/cp90_westmeier2011_ngc300_profile_extraction_v1.json',
  'reopen_rule':'reopen_NGC0300_only_for_higher_fidelity_machine_readable_profile_or_documented_source_correction',
  'notes':(
   f'NGC0300 (calibration) resolved with 20 exact native Westmeier et al. 2011 Table-2 Sigma_gas rows, already helium x1.4; later deeper ATCA public replacement rather than CP90 VLA numeric recovery. '
   f'Other frozen CP90 members verified as already preferred/resolved and not modified: {json.dumps(other,sort_keys=True)}.'
  )}
 if 'CP90' in dby:dby['CP90'].update(dnew)
 else:drows.append(dnew)
 drows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,drows,dfields)
 CHECK.write_text(
  '# Post-CP90 stationary H I checkpoint\n\n'
  'Status: **CP90 NGC0300 PROMOTED; RECONCILE/RERANK NEXT**\n\n'
  '- NGC0300 — calibration — 20 exact native Westmeier et al. 2011 Table-2 rows.\n'
  '- Radius: 100-2000 arcsec; 0.92-18.42 kpc on source-paper scale.\n'
  '- Quantity: face-on gas mass surface density derived from H I column density; helium x1.4 already included.\n'
  '- This is a later deeper ATCA public replacement for the CP90/Lelli branch, not a numeric recovery of Puche et al. 1990.\n'
  f'- Profile artifact: `{PROFILE}`\n'
  f'- Other CP90 frozen members were verified as already resolved and left unchanged: `{json.dumps(other,sort_keys=True)}`\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nRun reconciliation/ranking and continue the new highest-ranked actionable Lelli family. Do not restart CP90 unless its reopen rule is satisfied.\n',encoding='utf-8')
 print(json.dumps({'status':'CP90_NGC0300_PROMOTED','other_cp90_members_preserved':other,'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
