#!/usr/bin/env python3
"""Disposition Bl04 (NGC5985) as downstream to WHISP H I observations.

Blais-Ouellette et al. 2004 is a Fabry-Perot H-alpha paper. Its NGC5985 H I
rotation curve is derived from WHISP observations; the paper states that the
general WHISP procedures are in Swaters et al. 2000 and that details for this
particular galaxy would be published in a future paper. The CDS catalogue for
Bl04 contains rotation-curve tables, not a radial H I surface-density profile.

No prior WHISP route is restarted and no map/cube is converted into a profile.
"""
from __future__ import annotations
import csv,json
from pathlib import Path
REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
DISP=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_AFTER_BL04_DISPOSITION.md')

def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,rows,fields):
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 refs=read(REFMAP);hits=[r for r in refs if r.get('sparc_ref_id')=='Bl04']
 if len(hits)!=1 or hits[0]['galaxy']!='NGC5985' or hits[0]['stationary_role']!='calibration':
  raise RuntimeError(f'Bl04 frozen mapping changed: {hits}')
 rows=read(DISP);fields=list(rows[0]);by={r['sparc_ref_id']:r for r in rows}
 new={
  'sparc_ref_id':'Bl04',
  'queue_status':'redirected_to_original_sources',
  'disposition':'downstream_Halpha_kinematic_paper_redirects_NGC5985_HI_to_WHISP_observations_without_published_radial_profile',
  'validation_artifact':'validation/stationary/CHECKPOINT_AFTER_BL04_DISPOSITION.md',
  'reopen_rule':'reopen_only_for_later_public_NGC5985_WHISP_machine_readable_radial_HI_profile_source_native_vector_profile_or_exact_analytic_republication',
  'notes':(
   'NGC5985 (calibration). Blais-Ouellette et al. 2004 is primarily Fabry-Perot H-alpha work. '
   'The paper explicitly states that the NGC5985 H I rotation curve was derived from WHISP data; general WHISP procedures are cited to Swaters et al. 2000, while details for NGC5985 were said to be forthcoming. '
   'The public CDS product J/A+A/420/147 supplies optical and H I rotation curves, not radius-by-radius H I surface density. '
   'No published exact NGC5985 radial Sigma_HI table/vector product was identified in this provenance gate. No map/cube reconstruction or raster digitization performed.'
  )}
 if 'Bl04' in by:by['Bl04'].update(new)
 else:rows.append(new)
 rows.sort(key=lambda r:r['sparc_ref_id']);write(DISP,rows,fields)
 CHECK.write_text(
  '# Post-Bl04 stationary H I checkpoint\n\n'
  'Status: **BL04 REDIRECTED TO WHISP OBSERVATIONS; RERANK NEXT**\n\n'
  '- NGC5985 — calibration.\n'
  '- Bl04 is Blais-Ouellette et al. 2004, a Fabry-Perot H-alpha/kinematic paper.\n'
  '- Its NGC5985 H I curve is explicitly derived from WHISP data.\n'
  '- Paper says general WHISP procedures are in Swaters et al. 2000 and NGC5985-specific details would be published later.\n'
  '- CDS J/A+A/420/147 contains rotation curves only, not radial H I surface density.\n'
  '- No raster digitization or map/cube-to-profile reconstruction performed.\n'
  '- `L_A` and `C_A` remain locked.\n\n'
  '## Resume point\nRerank and continue the new highest-ranked actionable Lelli family. Reopen Bl04 only if an exact later NGC5985 WHISP radial-profile product is identified.\n',encoding='utf-8')
 print(json.dumps({'status':'BL04_WHISP_REDIRECT_RECORDED','target':'NGC5985','checkpoint':str(CHECK)},indent=2))
if __name__=='__main__':main()
