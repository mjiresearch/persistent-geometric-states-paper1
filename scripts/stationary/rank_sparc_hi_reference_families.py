#!/usr/bin/env python3
# WLM 2026 public-profile audit is persisted before queue evaluation.
from __future__ import annotations
import csv,json
from collections import defaultdict
from pathlib import Path
REFMAP=Path('data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv')
RECON=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
DISPOSITION=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv')
OUT=Path('data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv')
SUMMARY=Path('validation/stationary/sparc_hi_reference_family_priority_v1_summary.json')
WLM_AUDIT=Path('validation/stationary/lglbs2026_wlm_data_route_v1.json')
def read(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
 recon=read(RECON)
 if len(recon)!=149:raise RuntimeError(f'Expected 149 reconciled galaxies, got {len(recon)}')
 untouched={r['galaxy']:r for r in recon if r.get('public_overlay_present')=='0'};refrows=read(REFMAP)
 dr=read(DISPOSITION) if DISPOSITION.exists() else [];disp={r['sparc_ref_id']:r for r in dr}
 if len(disp)!=len(dr):raise RuntimeError('Duplicate SPARC reference ID')
 wlm_audit=json.loads(WLM_AUDIT.read_text()) if WLM_AUDIT.exists() else None
 groups=defaultdict(lambda:{'galaxies':set(),'calibration':set(),'blind':set(),'authors':set(),'bibcodes':set(),'comments':set(),'resolved':set()})
 for r in refrows:
  g=r['galaxy']
  if g not in untouched:continue
  rid=r['sparc_ref_id'] or 'UNRESOLVED_EMPTY';z=groups[rid];z['galaxies'].add(g);z[r['stationary_role']].add(g)
  if r.get('author'):z['authors'].add(r['author'])
  if r.get('bibcode'):z['bibcodes'].add(r['bibcode'])
  if r.get('comment'):z['comments'].add(r['comment'])
  z['resolved'].add(r.get('reference_resolved_in_cds_refs','0'))
 rows=[]
 for rid,z in groups.items():
  d=dict(disp.get(rid,{}))
  if rid=='Ke07' and wlm_audit and wlm_audit.get('status','').startswith('LGLBS2026_WLM'):
   d={'queue_status':'public_machine_readable_profile_identified_ingestion_pending','disposition':'WLM_2026_LGLBS_public_radial_profile_release_identified_file_level_ingestion_pending','validation_artifact':str(WLM_AUDIT),'reopen_rule':'resume_exact_WLM_table_ingestion_from_CANFAR_release; use ordinary_azimuthal_profile_not_mass_weighted_profile'}
  qs=d.get('queue_status','') or 'actionable_unreviewed';act='1' if qs=='actionable_unreviewed' else '0'
  rows.append({'sparc_ref_id':rid,'n_untouched_frozen_galaxies':len(z['galaxies']),'n_calibration':len(z['calibration']),'n_blind':len(z['blind']),'queue_actionable_now':act,'queue_status':qs,'disposition':d.get('disposition',''),'disposition_artifact':d.get('validation_artifact',''),'reopen_rule':d.get('reopen_rule',''),'reference_resolved_in_cds_refs':'1' if z['resolved']=={'1'} else '0','author':' | '.join(sorted(z['authors'])),'bibcode':' | '.join(sorted(z['bibcodes'])),'comment':' | '.join(sorted(z['comments'])),'galaxies':';'.join(sorted(z['galaxies']))})
 rows.sort(key=lambda r:(-int(r['queue_actionable_now']),-int(r['n_untouched_frozen_galaxies']),-int(r['n_calibration']),r['sparc_ref_id']))
 fields=['sparc_ref_id','n_untouched_frozen_galaxies','n_calibration','n_blind','queue_actionable_now','queue_status','disposition','disposition_artifact','reopen_rule','reference_resolved_in_cds_refs','author','bibcode','comment','galaxies']
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 actionable=[r for r in rows if r['queue_actionable_now']=='1'];deferred=[r for r in rows if r['queue_actionable_now']=='0']
 summary={'status':'SPARC_HI_REFERENCE_FAMILY_PRIORITY_COMPLETE','n_frozen_galaxies':149,'n_untouched_no_public_overlay':len(untouched),'n_reference_families_covering_untouched':len(rows),'n_actionable_reference_families':len(actionable),'n_deferred_or_redirected_reference_families':len(deferred),'top_15_actionable_reference_families':actionable[:15],'deferred_or_redirected_families':deferred,'live_family_public_route_probe':wlm_audit,'interpretation':'Coverage and actionability are separated; audited or explicitly pending source families do not block the next live acquisition family.','boundary':'Acquisition priority only; no profile normalization, persistence fitting, or blind-outcome inspection.'}
 SUMMARY.parent.mkdir(parents=True,exist_ok=True);SUMMARY.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
