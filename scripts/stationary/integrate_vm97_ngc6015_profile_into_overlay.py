#!/usr/bin/env python3
"""Promote recovered VM97 / NGC6015 native-vector H I profile into overlay."""
from __future__ import annotations
import csv,json
from pathlib import Path

QC=Path('validation/stationary/vm97_ngc6015_native_hi_profile_recovery_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/vm97_ngc6015_hi_profile_v1.csv')
REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_VM97_NGC6015_PROMOTION.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 q=json.loads(QC.read_text(encoding='utf-8'))
 if q.get('status')!='VM97_NGC6015_NATIVE_VECTOR_HI_PROFILE_RECOVERED':raise RuntimeError('Unexpected VM97 recovery status')
 if q.get('figure3_native_structure',{}).get('n_profile_points')!=31:raise RuntimeError('VM97 point count changed')
 if q.get('figure3_native_structure',{}).get('raster_operator_count')!=0:raise RuntimeError('VM97 source no longer vector-only')
 if not q.get('native_grid_qc',{}).get('passes'):raise RuntimeError('VM97 native grid QC failed')
 sq=q.get('source_statement_qc',{})
 if not sq.get('passes') or sq.get('mass_fractional_abs_delta',1)>0.12:raise RuntimeError('VM97 independent source-statement QC failed')
 rows_prof=read(PROFILE)
 if len(rows_prof)!=31 or any(r['galaxy']!='NGC6015' or r['stationary_role']!='calibration' for r in rows_prof):raise RuntimeError('VM97 profile CSV mismatch')
 refs=[r for r in read(REF) if r.get('sparc_ref_id')=='VM97' and r.get('galaxy')=='NGC6015']
 if len(refs)!=1 or refs[0].get('stationary_role')!='calibration':raise RuntimeError(f'VM97 frozen mapping changed: {refs}')

 rows=read(OVERLAY);fields=list(rows[0]);by={r['galaxy']:r for r in rows};old=by.get('NGC6015')
 if old is not None and old.get('preferred_public_source')=='1' and old.get('source_artifact') not in ('',str(PROFILE)):
  raise RuntimeError(f'NGC6015 already has different preferred public source: {old}')
 new={
  'galaxy':'NGC6015','stationary_role':'calibration','public_source_family':'Verdes-Montenegro et al. 1997 / source-native A&A PGPLOT Figure 3d',
  'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'31',
  'source_quantity':'source-native radial H I surface density from pure-vector Figure 3d M3 markers',
  'helium_status':'helium not applied; source H I surface density preserved','preferred_public_source':'1','source_artifact':str(PROFILE),
  'notes':(
   'VM97 direct public H I profile recovered from the legacy A&A electronic PostScript. Figure 3 embedded 07540003.eps is pure PGPLOT vector with zero raster operators. '
   'Panel 3d contains 31 exact M3 source markers; native PGPLOT stroke-glyph major labels calibrate radius and Sigma_HI. '
   'Recovered vector radii match the 15,25,...315 arcsec native annular grid to <0.085 arcsec. '
   'Independent QC: first-bin/peak=57.54%, matching the paper ~57% central H I depression; simple annular integral=3.673e9 Msun versus paper total M_HI=3.9e9 Msun (5.81% low over represented radial coverage), confirming source scale/raw-HI convention. '
   'No PostScript execution, raster digitization, OCR, profile fitting, helium scaling, common-distance renormalization, persistence fitting, or blind-outcome inspection. '
   f'Validation: {QC}.'
  )}
 if old is None:rows.append(new)
 else:old.update(new)
 rows.sort(key=lambda r:r['galaxy'])
 if len({r['galaxy'] for r in rows})!=len(rows):raise RuntimeError('Overlay duplicate after VM97 promotion')
 write(OVERLAY,rows,fields)

 drows=read(DISP);dfields=list(drows[0]);dby={r['sparc_ref_id']:r for r in drows}
 dnew={
  'sparc_ref_id':'VM97','queue_status':'resolved_public_profile_recovered',
  'disposition':'NGC6015_resolved_from_source_native_AA_legacy_PGPLOT_Figure3d_HI_profile',
  'validation_artifact':str(QC),
  'reopen_rule':'reopen_only_for_higher_fidelity_machine_readable_author_table_or_documented_source_correction',
  'notes':'NGC6015 calibration resolved: 31 exact source-native Figure-3d H I surface-density samples recovered from pure PGPLOT vectors, with independent grid/central-depression/integrated-HI-mass QC. No raster digitization or helium scaling.'
 }
 if 'VM97' in dby:dby['VM97'].update(dnew)
 else:drows.append(dnew)
 drows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,drows,dfields)

 r=q['profile_ranges']
 CHECK.write_text(
  '# Post-VM97 / NGC6015 stationary H I checkpoint\n\n'
  'Status: **NGC6015 SOURCE-NATIVE PGPLOT H I PROFILE PROMOTED; RECONCILE/RERANK NEXT**\n\n'
  '- Frozen target: NGC6015 — calibration.\n'
  '- Source: Verdes-Montenegro, Bosma & Athanassoula (1997), A&A 321, 754-764.\n'
  '- Exact source asset: legacy A&A Figure 3 embedded `07540003.eps`, pure PGPLOT vector, zero raster operators.\n'
  '- Figure 3d: 31 exact H I surface-density samples.\n'
  f'- Source-scale radial range: {r["radius_arcsec"][0]:.3f}-{r["radius_arcsec"][1]:.3f} arcsec = {r["radius_kpc_source_scale"][0]:.3f}-{r["radius_kpc_source_scale"][1]:.3f} kpc at D=13.9 Mpc.\n'
  f'- Sigma_HI range: {r["sigma_hi_msun_pc2"][0]:.3f}-{r["sigma_hi_msun_pc2"][1]:.3f} Msun pc^-2.\n'
  '- Independent QC: recovered central/peak = 57.54% vs source ~57%; annular mass scale within 5.81% of paper total H I mass over represented profile coverage.\n'
  f'- Profile: `{PROFILE}`.\n'
  f'- Validation: `{QC}`.\n'
  '- No PostScript execution, raster digitization, OCR, helium scaling, profile fitting, persistence fitting, or blind-outcome inspection.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nReconcile/rerank and continue the new highest-ranked actionable Lelli family. Do not restart VM97 unless its explicit reopen rule is satisfied.\n',encoding='utf-8')
 print(json.dumps({'status':'VM97_NGC6015_PROMOTED','profile_rows':31,'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
