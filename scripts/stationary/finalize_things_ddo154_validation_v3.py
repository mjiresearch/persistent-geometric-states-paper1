#!/usr/bin/env python3
"""Finalize DDO154 THINGS MOM0 validation with matched Wang+2016 H I size.

This step changes no reconstruction, threshold, or source-profile value.  It
only evaluates the previously pending radial-extent gate in the v2 validation
against the product-matched DDO154 THINGS row from Wang et al. (2016).
No rotation residuals, persistence parameters, or blind outcomes are evaluated.
"""
from __future__ import annotations
import copy,json,math
from pathlib import Path

V2=Path('validation/stationary/things_ddo154_mom0_validation_v2.json')
WANG=Path('validation/stationary/wang2016_ddo154_things_hi_diameter_v1.json')
OUT=Path('validation/stationary/things_ddo154_mom0_validation_v3.json')


def main():
 v=json.loads(V2.read_text());w=json.loads(WANG.read_text())
 if w.get('status')!='WANG2016_DDO154_THINGS_HI_DIAMETER_AUDITED':raise RuntimeError('Wang audit not certified')
 row=w['row']
 if row.get('Sample')!='THINGS' or abs(float(row['Dist_Mpc'])-4.3)>1e-9:raise RuntimeError(f'not product-matched THINGS row: {row}')
 if v.get('galaxy')!='DDO154' or v.get('stationary_role')!='calibration':raise RuntimeError('unexpected v2 validation target')
 # Preserve all already-evaluated gates exactly as recorded in v2.
 prior=v['gates']
 for name in ('overlap_profile_amplitude','overlap_annular_hi_mass','global_hi_flux','no_systematic_radial_drift'):
  if not prior[name].get('pass'):raise RuntimeError(f'prior gate not PASS: {name}')
 reconstructed=float(prior['hi_radial_extent']['reconstructed_rhi_kpc'])
 published=float(w['r_hi_kpc'])
 d_mpc=float(v['geometry']['distance_mpc'])
 beam_arcsec=float(v['beam']['geometric_mean_arcsec'])
 beam_kpc=beam_arcsec*d_mpc*1000.0*math.pi/(180.0*3600.0)
 tolerance=max(beam_kpc,0.10*published)
 diff=abs(reconstructed-published)
 extent_pass=diff<=tolerance
 out=copy.deepcopy(v)
 out['status']='THINGS_DDO154_MOM0_VALIDATION_PASS' if extent_pass else 'THINGS_DDO154_MOM0_VALIDATION_FAIL'
 out['validation_version']='v3_product_matched_wang2016_extent'
 out['gates']['hi_radial_extent']={
  'published_rhi_kpc':published,
  'published_dhi_kpc':float(row['DHI_kpc']),
  'published_distance_mpc':float(row['Dist_Mpc']),
  'published_sample':row['Sample'],
  'published_definition':'Wang et al. 2016 D_HI/2 at azimuthally averaged raw Sigma_HI=1 Msun pc^-2; natural-weighted H I image where possible; beam-smearing-corrected D_HI',
  'reconstructed_rhi_kpc':reconstructed,
  'absolute_difference_kpc':diff,
  'fractional_difference':diff/published,
  'beam_kpc':beam_kpc,
  'ten_percent_reference_kpc':0.10*published,
  'tolerance_rule':'max(one geometric-mean beam in kpc, 10% of published R_HI)',
  'tolerance_kpc':tolerance,
  'pass':extent_pass,
  'published_source':'Wang et al. 2016 MNRAS 460, 2143; VizieR J/MNRAS/460/2143/table2; product-matched Sample=THINGS DDO154 row',
  'source_audit':str(WANG)
 }
 gate_names=('overlap_profile_amplitude','overlap_annular_hi_mass','global_hi_flux','hi_radial_extent','no_systematic_radial_drift')
 out['n_gates_pass']=sum(bool(out['gates'][g].get('pass')) for g in gate_names)
 out['n_gates_fail']=len(gate_names)-out['n_gates_pass']
 out['n_gates_not_evaluated']=0
 out['all_five_gates_pass']=out['n_gates_pass']==5
 out['anchor_correction_note']='The earlier 4.5 kpc/Oman anchor was not product-matched to the Walter+2008 THINGS map. V3 uses Wang+2016 Sample=THINGS at D=4.3 Mpc. No threshold or reconstruction value was changed.'
 out['boundary']='Calibration/source-profile validation only. No rotation velocities, residuals, L_A, C_A, tau_A, persistence prediction, or blind outcomes evaluated.'
 OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
 if not out['all_five_gates_pass']:raise SystemExit(2)

if __name__=='__main__':main()
