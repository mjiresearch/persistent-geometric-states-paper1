#!/usr/bin/env python3
"""Build a provenance-only request manifest for unresolved frozen SPARC H I profiles."""
import csv,json,hashlib
from collections import Counter
from pathlib import Path
SRC=Path('data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv')
OUT=Path('data/stationary/source_reconstruction/lelli_hi_profile_request_manifest_v1.csv')
SUM=Path('validation/stationary/lelli_hi_profile_request_manifest_v1_summary.json')
CERT={'raw_source_profile_ingested','analytic_profile_recovered'}
FIELDS=['galaxy','stationary_role','request_from_lelli','expected_in_169_profile_compilation','current_effective_status','public_overlay_present','effective_public_source_family','preferred_public_source','effective_source_artifact','request_reason','requested_payload']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 with SRC.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 out=[]
 for r in rows:
  status=r.get('effective_acquisition_status','')
  certified=status in CERT
  expected=r.get('expected_in_169_profile_compilation')=='1'
  request=expected and not certified
  if certified:reason='already_certified_public_profile_no_request'
  elif not expected:reason='reported_unavailable_in_169_compilation_do_not_request_as_if_present'
  elif r.get('public_overlay_present')=='1':reason='public_route_identified_or_candidate_but_not_yet_certified_request_private_compilation_exact_series'
  else:reason='profile_reported_in_169_compilation_but_no_certified_public_numeric_series'
  out.append({
   'galaxy':r['galaxy'],'stationary_role':r['stationary_role'],'request_from_lelli':'1' if request else '0',
   'expected_in_169_profile_compilation':r.get('expected_in_169_profile_compilation',''),
   'current_effective_status':status,'public_overlay_present':r.get('public_overlay_present',''),
   'effective_public_source_family':r.get('effective_public_source_family',''),
   'preferred_public_source':r.get('preferred_public_source',''),
   'effective_source_artifact':r.get('effective_source_artifact',''),
   'request_reason':reason,
   'requested_payload':'radius; radial HI surface density; radius units; surface-density units; helium convention; adopted distance; inclination; beam/radial sampling; original source citation'
  })
 out.sort(key=lambda x:(x['request_from_lelli']!='1',x['stationary_role'],x['galaxy']))
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 req=[x for x in out if x['request_from_lelli']=='1'];cert=[x for x in out if x['request_reason']=='already_certified_public_profile_no_request'];unavail=[x for x in out if x['request_reason'].startswith('reported_unavailable')]
 s={'status':'LELLI_HI_PROFILE_REQUEST_MANIFEST_FROZEN','n_frozen':len(out),'n_request':len(req),'request_role_counts':dict(Counter(x['stationary_role'] for x in req)),'n_already_certified_no_request':len(cert),'certified_role_counts':dict(Counter(x['stationary_role'] for x in cert)),'n_reported_unavailable_in_169_no_request':len(unavail),'unavailable_galaxies':[x['galaxy'] for x in unavail],'requested_payload':req[0]['requested_payload'] if req else '', 'source_reconciliation_sha256':sha(SRC),'manifest_sha256':sha(OUT),'boundary':'Acquisition/provenance only. No persistence outcomes, no blind-fit information, no parameter selection. L_A and C_A remain locked.'}
 SUM.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(s,indent=2))
if __name__=='__main__':main()
