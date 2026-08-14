#!/usr/bin/env python3
"""Promote the exact FEASTS 2025 NGC2903 H I profile into the public overlay."""
from __future__ import annotations
import csv,json
from pathlib import Path

QC=Path('validation/stationary/feasts2025_new_calibration_profiles_qc_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/feasts2025_ngc2903_hi_profile_raw_v1.csv')
OVER=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_FEASTS2025_NGC2903_PROMOTION_V1.md')
FIELDS=['galaxy','stationary_role','public_source_family','acquisition_status','numeric_rows_or_model','source_quantity','helium_status','preferred_public_source','source_artifact','notes']

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
 q=json.loads(QC.read_text());qr=[x for x in q['results'] if x['galaxy']=='NGC2903']
 if len(qr)!=1 or not qr[0]['passes_all_source_qc']:raise RuntimeError('NGC2903 FEASTS source QC is not passing')
 pr=read_csv(PROFILE)
 if len(pr)!=35 or any(r['galaxy']!='NGC2903' or r['stationary_role']!='calibration' for r in pr):raise RuntimeError('unexpected NGC2903 profile payload')
 rows=read_csv(OVER);by={r['galaxy']:r for r in rows}
 if len(by)!=len(rows):raise RuntimeError('duplicate overlay galaxy')
 old=by.get('NGC2903')
 if old is None:raise RuntimeError('expected existing NGC2903 vector-candidate overlay row')
 if old['stationary_role']!='calibration':raise RuntimeError('NGC2903 role mismatch')
 if old['acquisition_status'] in {'raw_source_profile_ingested','analytic_profile_recovered'}:raise RuntimeError('NGC2903 already certified; refusing duplicate promotion')
 prior=f"Prior public candidate retained for provenance: {old['public_source_family']} ({old['acquisition_status']}) — {old['notes']}"
 by['NGC2903']={
  'galaxy':'NGC2903','stationary_role':'calibration','public_source_family':'Wang et al. 2025 / FEASTS machine-readable radial H I profiles',
  'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'35',
  'source_quantity':'deprojected radial atomic HI surface density from FEASTS total-power profile; angular radius retained and converted to frozen distance',
  'helium_status':'raw atomic HI; helium not included','preferred_public_source':'1','source_artifact':str(PROFILE),
  'notes':'Official password-free FEASTS release HIprof_wang25.ecsv (Wang et al. 2025, ApJ 980:25, DOI 10.3847/1538-4357/ada95a). Exact machine-readable NGC2903 row: 35 finite monotonic non-negative Sigma_HI points. Source displayed D=8.5 Mpc; radii imply D=8.495690862 Mpc, consistent with 0.1-Mpc display precision. Frozen D=6.6 Mpc; angular radii mapped to frozen physical radius with no surface-density amplitude rescale. Raw HI, no helium. Source R1 consistency passes. Measured profile has an inner support gap relative to the first frozen rotation point; continuation policy is a separate stage and is not altered here. '+prior
 }
 out=[by[g] for g in sorted(by)]
 with OVER.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 CHECK.write_text('# FEASTS 2025 NGC2903 promotion checkpoint v1\n\n- Galaxy: **NGC2903** (calibration).\n- Source: Wang et al. 2025 FEASTS official machine-readable `HIprof_wang25.ecsv`.\n- Exact usable profile: 35 finite radial raw-H I points.\n- Source QC: PASS.\n- Helium: not included; common 1.33 normalization remains a later deterministic step.\n- Radius: source angular radius preserved and converted using frozen SPARC distance; no inclination/amplitude rescale.\n- Inner measured-support gap is recorded, not filled during acquisition.\n- No persistence quantities or blind outcomes inspected.\n- `L_A` and `C_A` remain locked.\n\nNext: reconcile public provenance and regenerate the private-request manifest.\n')
 print(json.dumps({'status':'FEASTS2025_NGC2903_PROMOTED_TO_OVERLAY','profile_rows':len(pr),'overlay_rows':len(out)},indent=2))
if __name__=='__main__':main()
