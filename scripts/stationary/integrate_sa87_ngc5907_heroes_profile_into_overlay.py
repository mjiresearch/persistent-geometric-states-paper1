#!/usr/bin/env python3
"""Promote the recovered HEROES-II NGC5907 H I profiles into the public overlay.

The authoritative recovered source product is the 108-row side-specific
(approaching/receding) Sigma_HI table extracted from source-native Figure-29 PDF
vectors. A 54-bin arithmetic m=0 mean is retained as a deterministic Paper-I
derivative for the axisymmetric stationary source build, but is not described as
an author-published average.
"""
from __future__ import annotations
import csv,json
from pathlib import Path

QC=Path('validation/stationary/sa87_ngc5907_heroes2015_native_hi_recovery_v1.json')
SIDES=Path('data/stationary/source_reconstruction/sa87_ngc5907_heroes2015_hi_side_profiles_v1.csv')
M0=Path('data/stationary/source_reconstruction/sa87_ngc5907_heroes2015_hi_m0_mean_v1.csv')
REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_SA87_NGC5907_PROMOTION.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 q=json.loads(QC.read_text(encoding='utf-8'))
 if q.get('status')!='SA87_NGC5907_HEROES_NATIVE_HI_PROFILES_RECOVERED':raise RuntimeError('Unexpected SA87 recovery status')
 sp=q.get('source_profiles',{})
 if sp.get('approaching',{}).get('n_points')!=54 or sp.get('receding',{}).get('n_points')!=54:raise RuntimeError('SA87 side counts changed')
 if sp.get('identical_radius_grid_max_delta_kpc',1)>1e-5:raise RuntimeError('SA87 side radius grids not aligned')
 ax=q.get('axis_calibration',{})
 if ax.get('max_tick_residual_kpc',1)>1e-3 or ax.get('max_tick_residual_msun_pc2',1)>1e-4:raise RuntimeError('SA87 axis calibration QC failed')
 for side in ('approaching','receding'):
  if sp[side]['marker_polyline_qc']['max_pdf_points']>0.01:raise RuntimeError(f'SA87 {side} marker QC failed')
 if q.get('source_convention',{}).get('quantity')!='Sigma_HI (M_sun pc^-2), source axis label':raise RuntimeError('SA87 source quantity convention changed')

 sides=read(SIDES);m0=read(M0)
 if len(sides)!=108 or len(m0)!=54:raise RuntimeError(f'SA87 CSV counts changed: sides={len(sides)} m0={len(m0)}')
 if {r['side'] for r in sides}!={'approaching','receding'}:raise RuntimeError('SA87 source-side labels changed')
 if any(r['galaxy']!='NGC5907' or r['stationary_role']!='calibration' for r in sides+m0):raise RuntimeError('SA87 role/galaxy mismatch')
 # The m=0 derivative must be exactly the pointwise arithmetic mean of retained source sides.
 app=sorted((r for r in sides if r['side']=='approaching'),key=lambda r:int(r['sample_index']))
 rec=sorted((r for r in sides if r['side']=='receding'),key=lambda r:int(r['sample_index']))
 mm=sorted(m0,key=lambda r:int(r['sample_index']))
 for a,r,m in zip(app,rec,mm):
  if abs(float(a['radius_kpc_source'])-float(r['radius_kpc_source']))>1e-5:raise RuntimeError('Side grid mismatch in CSV')
  expect=0.5*(float(a['sigma_hi_msun_pc2'])+float(r['sigma_hi_msun_pc2']))
  if abs(expect-float(m['sigma_hi_m0_mean_msun_pc2']))>2e-8:raise RuntimeError('m0 mean no longer deterministic arithmetic mean')

 refs=[r for r in read(REF) if r.get('sparc_ref_id')=='SA87' and r.get('galaxy')=='NGC5907']
 if len(refs)!=1 or refs[0].get('stationary_role')!='calibration':raise RuntimeError(f'SA87 frozen mapping changed: {refs}')

 rows=read(OVERLAY);fields=list(rows[0]);by={r['galaxy']:r for r in rows};old=by.get('NGC5907')
 if old is not None and old.get('preferred_public_source')=='1' and old.get('source_artifact') not in ('',str(SIDES)):
  raise RuntimeError(f'NGC5907 already has different preferred source: {old}')
 new={
  'galaxy':'NGC5907','stationary_role':'calibration','public_source_family':'Allaert et al. 2015 HEROES II / later direct NGC5907 HI reanalysis',
  'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'108',
  'source_quantity':'source-native side-specific Sigma_HI: 54 approaching + 54 receding; separate 54-bin deterministic Paper-I m=0 mean retained',
  'helium_status':'no recovery scaling; values preserved as source-labeled Sigma_HI','preferred_public_source':'1','source_artifact':str(SIDES),
  'notes':(
   'Lelli/SPARC SA87 is Sancisi & van Albada 1987 (review; original NGC5907 H I lineage Sancisi 1976). '
   'Higher-information later direct public route: Allaert et al. 2015 HEROES II re-analysis of interferometric 21-cm data with full-cube tilted-ring modelling. '
   'Figure 29 Final_params_all.pdf is fully native vector: exact source recovery yields 54 blue approaching and 54 red receding Sigma_HI samples on an identical 0-55.83 kpc source grid. '
   'Native marker/polyline and tick-geometry QC pass. Source-side values remain authoritative. '
   f'A separate deterministic axisymmetric mean is stored at {M0} and is explicitly not an author-published average. '
   'No helium multiplication/division, raster digitization, OCR, profile fitting, map reconstruction, common-distance renormalization, persistence fitting, or blind-outcome inspection. '
   f'Validation: {QC}.'
  )}
 if old is None:rows.append(new)
 else:old.update(new)
 rows.sort(key=lambda r:r['galaxy'])
 if len({r['galaxy'] for r in rows})!=len(rows):raise RuntimeError('Overlay duplicate after SA87 promotion')
 write(OVERLAY,rows,fields)

 drows=read(DISP);dfields=list(drows[0]);dby={r['sparc_ref_id']:r for r in drows}
 dnew={
  'sparc_ref_id':'SA87','queue_status':'resolved_public_profile_recovered',
  'disposition':'NGC5907_resolved_via_later_direct_HEROES2015_source_native_vector_SigmaHI_profiles',
  'validation_artifact':str(QC),
  'reopen_rule':'reopen_only_for_higher_fidelity_machine_readable_author_table_or_documented_source_correction',
  'notes':(
   'NGC5907 (calibration) resolved through Allaert et al. 2015 HEROES II, a later direct interferometric H I re-analysis. '
   'Source Figure 29 native PDF vectors yield 108 exact side-specific Sigma_HI samples (54 approaching, 54 receding), with native axis/marker QC. '
   'The separate 54-bin Paper-I arithmetic m=0 mean is deterministic and not represented as source-published. '
   'No raster digitization, helium scaling, or persistence/blind analysis.'
  )}
 if 'SA87' in dby:dby['SA87'].update(dnew)
 else:drows.append(dnew)
 drows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,drows,dfields)

 CHECK.write_text(
  '# Post-SA87 / NGC5907 stationary H I checkpoint\n\n'
  'Status: **NGC5907 HEROES NATIVE-VECTOR H I PROFILE PROMOTED; RECONCILE/RERANK NEXT**\n\n'
  '- Frozen target: NGC5907 — calibration.\n'
  '- Lelli/SPARC trail: SA87 review -> original Sancisi 1976 H I lineage -> higher-information later direct HEROES-II H I re-analysis.\n'
  '- Source recovery: 108 native Figure-29 Sigma_HI values = 54 approaching + 54 receding, identical source radius grid.\n'
  '- Radius range: approximately 0-55.83 kpc on source-native Figure-29 coordinates.\n'
  f'- Authoritative source-side artifact: `{SIDES}`.\n'
  f'- Deterministic Paper-I m=0 derivative: `{M0}` (54 bins; arithmetic side mean; not source-published).\n'
  f'- QC: `{QC}`.\n'
  '- No helium scaling, raster digitization, OCR, map reconstruction, common normalization, persistence fitting, or blind-outcome inspection.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nReconcile/rerank and continue the new highest-ranked actionable Lelli family. Do not restart SA87 unless its reopen rule is satisfied.\n',encoding='utf-8')
 print(json.dumps({'status':'SA87_NGC5907_PROMOTED','source_rows':108,'derived_m0_rows':54,'checkpoint':str(CHECK)},indent=2))

if __name__=='__main__':main()
