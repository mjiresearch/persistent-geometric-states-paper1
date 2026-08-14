#!/usr/bin/env python3
"""Promote the exact FEASTS 2025 NGC4559 H I profile into the public overlay."""
from __future__ import annotations
import csv,json
from pathlib import Path

QC=Path('validation/stationary/feasts2025_new_calibration_profiles_qc_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/feasts2025_ngc4559_hi_profile_raw_v1.csv')
OVER=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_FEASTS2025_NGC4559_PROMOTION_V1.md')
FIELDS=['galaxy','stationary_role','public_source_family','acquisition_status','numeric_rows_or_model','source_quantity','helium_status','preferred_public_source','source_artifact','notes']

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
 q=json.loads(QC.read_text());qr=[x for x in q['results'] if x['galaxy']=='NGC4559']
 if len(qr)!=1 or not qr[0]['passes_all_source_qc']:raise RuntimeError('NGC4559 FEASTS source QC is not passing')
 pr=read_csv(PROFILE)
 if len(pr)!=26 or any(r['galaxy']!='NGC4559' or r['stationary_role']!='calibration' for r in pr):raise RuntimeError('unexpected NGC4559 profile payload')
 rows=read_csv(OVER);by={r['galaxy']:r for r in rows}
 if len(by)!=len(rows):raise RuntimeError('duplicate overlay galaxy')
 old=by.get('NGC4559')
 if old and old['acquisition_status'] in {'raw_source_profile_ingested','analytic_profile_recovered'}:raise RuntimeError('NGC4559 already certified; refusing duplicate promotion')
 prior=''
 if old:
  if old['stationary_role']!='calibration':raise RuntimeError('NGC4559 role mismatch')
  prior=f" Prior overlay provenance retained: {old['public_source_family']} ({old['acquisition_status']}) — {old['notes']}"
 by['NGC4559']={
  'galaxy':'NGC4559','stationary_role':'calibration','public_source_family':'Wang et al. 2025 / FEASTS machine-readable radial H I profiles',
  'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'26',
  'source_quantity':'deprojected radial atomic HI surface density from FEASTS total-power profile; angular radius retained and converted to frozen distance',
  'helium_status':'raw atomic HI; helium not included','preferred_public_source':'1','source_artifact':str(PROFILE),
  'notes':'Official password-free FEASTS release HIprof_wang25.ecsv (Wang et al. 2025, ApJ 980:25, DOI 10.3847/1538-4357/ada95a). Exact machine-readable NGC4559 row: 26 finite monotonic non-negative Sigma_HI points. Source displayed D=8.9 Mpc; radii imply D=8.895488079 Mpc, consistent with 0.1-Mpc display precision. Frozen D=9.0 Mpc; angular radii mapped to frozen physical radius with no surface-density amplitude rescale. Raw HI, no helium. Source R1 consistency passes. Measured profile has an inner support gap relative to the first frozen rotation point; continuation policy is a separate stage and is not altered here. This exact machine-readable release supersedes the earlier Ba05 raster-only public-route disposition for numerical acquisition.'+prior
 }
 out=[by[g] for g in sorted(by)]
 with OVER.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 CHECK.write_text('# FEASTS 2025 NGC4559 promotion checkpoint v1\n\n- Galaxy: **NGC4559** (calibration).\n- Source: Wang et al. 2025 FEASTS official machine-readable `HIprof_wang25.ecsv`.\n- Exact usable profile: 26 finite radial raw-H I points.\n- Source QC: PASS.\n- Helium: not included; common 1.33 normalization remains a later deterministic step.\n- Radius: source angular radius preserved and converted using frozen SPARC distance; no inclination/amplitude rescale.\n- Inner measured-support gap is recorded, not filled during acquisition.\n- This exact release reopens/resolves the formerly raster-only Ba05 public route without raster digitization.\n- No persistence quantities or blind outcomes inspected.\n- `L_A` and `C_A` remain locked.\n\nNext: reconcile public provenance and regenerate the private-request manifest.\n')
 print(json.dumps({'status':'FEASTS2025_NGC4559_PROMOTED_TO_OVERLAY','profile_rows':len(pr),'overlay_rows':len(out)},indent=2))
if __name__=='__main__':main()
