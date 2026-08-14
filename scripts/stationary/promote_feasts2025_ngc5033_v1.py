#!/usr/bin/env python3
"""Promote blind NGC5033 FEASTS 2025 H I source after locked source-only QC."""
from __future__ import annotations
import csv,json
from pathlib import Path

QC=Path('validation/stationary/feasts2025_ngc5033_blind_source_qc_v1.json')
PROFILE=Path('data/stationary/source_reconstruction/feasts2025_ngc5033_hi_profile_raw_v1.csv')
OVER=Path('data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv')
CHECK=Path('validation/stationary/CHECKPOINT_FEASTS2025_NGC5033_BLIND_PROMOTION_V1.md')
FIELDS=['galaxy','stationary_role','public_source_family','acquisition_status','numeric_rows_or_model','source_quantity','helium_status','preferred_public_source','source_artifact','notes']

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
 q=json.loads(QC.read_text())
 if q.get('galaxy')!='NGC5033' or q.get('stationary_role')!='blind' or not q.get('passes_all_locked_source_qc'):raise RuntimeError('locked NGC5033 blind source QC not passing')
 pr=read_csv(PROFILE)
 if len(pr)!=50 or any(r['galaxy']!='NGC5033' or r['stationary_role']!='blind' for r in pr):raise RuntimeError('unexpected NGC5033 profile payload')
 rows=read_csv(OVER);by={r['galaxy']:r for r in rows}
 if len(by)!=len(rows):raise RuntimeError('duplicate overlay galaxy')
 old=by.get('NGC5033')
 if old is None:raise RuntimeError('expected existing NGC5033 vector-candidate overlay row')
 if old['stationary_role']!='blind':raise RuntimeError('NGC5033 role mismatch')
 if old['acquisition_status'] in {'raw_source_profile_ingested','analytic_profile_recovered'}:raise RuntimeError('NGC5033 already certified')
 prior=f"Prior public candidate retained for provenance: {old['public_source_family']} ({old['acquisition_status']}) — {old['notes']}"
 by['NGC5033']={
  'galaxy':'NGC5033','stationary_role':'blind','public_source_family':'Wang et al. 2025 / FEASTS machine-readable radial H I profiles',
  'acquisition_status':'raw_source_profile_ingested','numeric_rows_or_model':'50',
  'source_quantity':'deprojected radial atomic HI surface density from FEASTS total-power profile; angular radius retained and converted to frozen distance',
  'helium_status':'raw atomic HI; helium not included','preferred_public_source':'1','source_artifact':str(PROFILE),
  'notes':'Promoted strictly under FEASTS2025_BLIND_HI_SOURCE_ACQUISITION_PROTOCOL_V1 before any blind outcome inspection. Official password-free FEASTS HIprof_wang25.ecsv (Wang et al. 2025, ApJ 980:25, DOI 10.3847/1538-4357/ada95a): 50 finite monotonic non-negative raw-HI points. Source displayed D=18.5 Mpc; radii imply D=18.490621288 Mpc, within source display precision. Frozen D=15.7 Mpc; angular radii mapped to frozen physical radius with no surface-density amplitude rescale. Source R1 consistency passes. Measured profile has an inner support gap but no outer gap; continuation remains separate. No Vobs, residual, persistence prediction, model preference, L_A, C_A, or tau_A read. '+prior
 }
 out=[by[g] for g in sorted(by)]
 with OVER.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 CHECK.write_text('# FEASTS 2025 NGC5033 blind promotion checkpoint v1\n\n- Galaxy: **NGC5033** (blind).\n- Source: official Wang et al. 2025 FEASTS machine-readable `HIprof_wang25.ecsv`.\n- Locked blind source-acquisition protocol was frozen before numerical profile inspection.\n- Source-only QC: PASS on all locked checks.\n- Exact usable profile: 50 finite raw-H I radial points.\n- No helium in source; common 1.33 normalization remains deterministic.\n- Angular radii mapped to frozen distance; no inclination/amplitude rescale.\n- Inner support gap recorded; no acquisition-stage filling.\n- **Blind firewall preserved:** no Vobs, residual, persistence prediction, or model preference inspected.\n- `L_A` and `C_A` remain locked.\n\nNext: reconcile certified count and regenerate request manifest.\n')
 print(json.dumps({'status':'FEASTS2025_NGC5033_PROMOTED_TO_OVERLAY','profile_rows':len(pr),'overlay_rows':len(out),'blind_firewall':'preserved'},indent=2))
if __name__=='__main__':main()
