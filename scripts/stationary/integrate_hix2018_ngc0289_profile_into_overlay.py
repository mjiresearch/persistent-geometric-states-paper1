#!/usr/bin/env python3
"""Promote recovered HIX2018 / NGC0289 measured native-vector H I profile."""
from __future__ import annotations
import csv,json
from pathlib import Path

QC=Path('validation/stationary/hix2018_ngc0289_native_hi_profile_recovery_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/hix2018_ngc0289_hi_profile_v1.csv')
WA97=Path('validation/stationary/wa97_ngc289_public_hi_profile_route_v1.json')
REF=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
OVERLAY=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_WA97_NGC0289_HIX2018_PROMOTION.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 q=json.loads(QC.read_text(encoding='utf-8'))
 if q.get('status')!='HIX2018_NGC0289_NATIVE_VECTOR_HI_PROFILE_RECOVERED':raise RuntimeError('Unexpected HIX NGC0289 recovery status')
 if q.get('n_points')!=52:raise RuntimeError('NGC0289 point count changed')
 if q.get('profile_semantics',{}).get('observational_status')!='measured_from_elliptical_annuli_in_non_clipped_ATCA_moment0_map':raise RuntimeError('NGC0289 source semantics changed')
 if q.get('profile_semantics',{}).get('helium_included') is not False:raise RuntimeError('NGC0289 profile no longer raw HI')
 if abs(float(q.get('source',{}).get('distance_mpc',-1))-23.06)>1e-9:raise RuntimeError('HIX source distance changed')
 if abs(float(q.get('frozen_distance_mpc',-1))-20.8)>1e-9:raise RuntimeError('Frozen NGC0289 distance changed')
 if q.get('x_axis',{}).get('max_abs_residual_kpc',1)>1e-3 or q.get('y_axis',{}).get('max_abs_residual',1)>1e-3:raise RuntimeError('Native tick calibration residual too large')
 rows_prof=read(PROFILE)
 if len(rows_prof)!=52 or any(r['galaxy']!='NGC0289' or r['stationary_role']!='calibration' or r['helium_included']!='0' for r in rows_prof):raise RuntimeError('NGC0289 profile CSV mismatch')
 if any(not r.get('radius_kpc_frozen') for r in rows_prof):raise RuntimeError('Frozen-distance radii missing')
 # Independent published R_HI QC: source Table gives 86.9 kpc; source method linearly extrapolates
 # the two points bracketing 1 Msun/pc2 before a small beam-smearing correction.
 p1,p2=rows_prof[-2],rows_prof[-1]
 r1,r2=float(p1['radius_kpc_source']),float(p2['radius_kpc_source']);s1,s2=float(p1['sigma_hi_msun_pc2']),float(p2['sigma_hi_msun_pc2'])
 if not (s1>1 and s2>1 and s2<s1):raise RuntimeError('Outer NGC0289 profile no longer supports R_HI extrapolation')
 r_cross=r2+(1.0-s2)*(r2-r1)/(s2-s1)
 published_rhi=86.9
 frac=abs(r_cross-published_rhi)/published_rhi
 if frac>0.02:raise RuntimeError(f'NGC0289 R_HI QC failed: crossing={r_cross}, published={published_rhi}')
 refs=[r for r in read(REF) if r.get('sparc_ref_id')=='Wa97' and r.get('galaxy')=='NGC0289']
 if len(refs)!=1 or refs[0].get('stationary_role')!='calibration':raise RuntimeError(f'Wa97 frozen mapping changed: {refs}')
 if not WA97.exists():raise RuntimeError('Original Wa97 route audit missing')
 wa=json.loads(WA97.read_text(encoding='utf-8'))
 if wa.get('status')!='WA97_NGC0289_PUBLIC_ROUTE_AUDIT_COMPLETE':raise RuntimeError('Wa97 audit status changed')

 rows=read(OVERLAY);fields=list(rows[0]);by={r['galaxy']:r for r in rows};old=by.get('NGC0289')
 if old is not None and old.get('preferred_public_source')=='1' and old.get('source_artifact') not in ('',str(PROFILE)):
  raise RuntimeError(f'NGC0289 already has different preferred source: {old}')
 new={
  'galaxy':'NGC0289','stationary_role':'calibration',
  'public_source_family':'Lutz et al. 2018 HIX II / later direct ATCA measured radial H I profile',
  'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'52',
  'source_quantity':'deprojected radial H I column/surface density measured in elliptical annuli from non-clipped ATCA moment-0 map',
  'helium_status':'helium not applied; source N_HI preserved','preferred_public_source':'1','source_artifact':str(PROFILE),
  'notes':(
   'SPARC Wa97 original source (Walsh et al. 1997) directly publishes Figure 6 radial H I surface density, but the public ADS copy is scan/raster-only. '
   'Public later direct ATCA observations in Lutz et al. 2018 HIX II provide NGC289 Figure A3(b) as source-native PDF vectors. '
   'HIX TeX explicitly defines panel (b) as the radial H I column-density profile measured from elliptical annuli; the profiles are measured from non-clipped moment-0 maps, using TiRiFiC inclination/PA only for annulus geometry. '
   '52 exact 3x3-pt filled native marker glyphs recovered. Native ticks calibrate 0,25,50,75 kpc and 0,2,4,6 Msun pc^-2. '
   f'Independent QC: extrapolated 1 Msun pc^-2 crossing={r_cross:.3f} kpc vs published R_HI=86.9 kpc ({100*frac:.2f}% difference before small beam correction). '
   'Source distance 23.06 Mpc retained separately from frozen SPARC distance 20.8 Mpc. Raw H I only; HIX helium correction is defined separately for atomic gas mass. '
   'No OCR, raster digitization, profile fitting, persistence fitting, or blind-outcome inspection. '
   f'Validation: {QC}; original-route audit: {WA97}.'
  )}
 if old is None:rows.append(new)
 else:old.update(new)
 rows.sort(key=lambda r:r['galaxy'])
 if len({r['galaxy'] for r in rows})!=len(rows):raise RuntimeError('Overlay duplicate after NGC0289 promotion')
 write(OVERLAY,rows,fields)

 drows=read(DISP);dfields=list(drows[0]);dby={r['sparc_ref_id']:r for r in drows}
 dnew={
  'sparc_ref_id':'Wa97','queue_status':'resolved_public_profile_recovered_later_direct_observation',
  'disposition':'NGC0289_original_Wa97_Fig6_raster_only_but_exact_public_later_direct_ATCA_HIX2018_FigA3b_native_vector_profile_recovered',
  'validation_artifact':str(QC),
  'reopen_rule':'reopen_only_for_machine_readable_Wa97_author_table_or_higher_fidelity_direct_HI_profile_or_documented_source_correction',
  'notes':f'NGC0289 calibration resolved with 52-bin Lutz et al. 2018 HIX II direct ATCA measured H I profile. Original Wa97 public Figure 6 is raster-only. HIX native-vector recovery passes published R_HI QC at {100*frac:.2f}% before beam-smearing correction. Raw H I; source/frozen distances kept separate.'
 }
 if 'Wa97' in dby:dby['Wa97'].update(dnew)
 else:drows.append(dnew)
 drows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,drows,dfields)

 rr=q['ranges']
 CHECK.write_text(
  '# Post-Wa97 / NGC0289 stationary H I checkpoint\n\n'
  'Status: **NGC0289 EXACT PUBLIC LATER-DIRECT H I PROFILE PROMOTED; RECONCILE/RERANK NEXT**\n\n'
  '- Frozen target: NGC0289 — calibration.\n'
  '- Lelli/SPARC source code: Wa97, Walsh et al. (1997). Original Figure 6 is a direct deprojected radial H I surface-density profile, but the public ADS article is raster-only.\n'
  '- Rescue source: Lutz et al. (2018), HIX survey II, new/direct ATCA H I observations.\n'
  '- Exact asset: arXiv source `Images/app-fig3.pdf`, Figure A3 panel (b), 52 native filled vector markers.\n'
  '- Semantics: radial H I column density measured from elliptical annuli in the non-clipped moment-0 map; TiRiFiC inclination/PA set annulus geometry.\n'
  f'- Source distance: 23.06 Mpc; source radius range {rr["radius_kpc_source"][0]:.3f}-{rr["radius_kpc_source"][1]:.3f} kpc.\n'
  f'- Frozen SPARC distance: 20.8 Mpc; corresponding frozen radius range {rr["radius_kpc_frozen"][0]:.3f}-{rr["radius_kpc_frozen"][1]:.3f} kpc.\n'
  f'- Sigma_HI range: {rr["sigma_hi_msun_pc2"][0]:.3f}-{rr["sigma_hi_msun_pc2"][1]:.3f} Msun pc^-2; helium not applied.\n'
  f'- Independent QC: outer-bin linear crossing at Sigma_HI=1 gives {r_cross:.3f} kpc vs published R_HI=86.9 kpc ({100*frac:.2f}% difference before small beam correction).\n'
  f'- Profile: `{PROFILE}`.\n- No OCR, raster digitization, profile fitting, persistence fitting, or blind-outcome inspection.\n- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nReconcile/rerank and continue the new highest-ranked actionable Lelli family. Do not repeat the Wa97 raster route unless its reopen rule is satisfied.\n',encoding='utf-8')
 print(json.dumps({'status':'WA97_NGC0289_HIX2018_PROFILE_PROMOTED','profile_rows':52,'rhi_crossing_kpc':r_cross,'published_rhi_kpc':published_rhi,'fractional_difference':frac,'checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
