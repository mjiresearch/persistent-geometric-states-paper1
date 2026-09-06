#!/usr/bin/env python3
"""Auxiliary SIMBAD lookup for the 31 outcome-blind single-pass OSC RV targets."""
from pathlib import Path
import io, json, time
import pandas as pd, requests
HERE=Path(__file__).resolve().parent
RANK=HERE/'osc_rv_target_rank'/'osc_missing_systemic_rv_candidates_ranked.csv'
OUT=HERE/'osc_rv_target_rank'/'simbad_lookup'; OUT.mkdir(parents=True,exist_ok=True)
TAP='https://simbad.cds.unistra.fr/simbad/sim-tap/sync'

def tap(q):
    last=None
    for k in range(5):
        try:
            r=requests.post(TAP,data={'request':'doQuery','lang':'adql','format':'csv','query':q},timeout=180)
            r.raise_for_status(); return pd.read_csv(io.StringIO(r.text))
        except Exception as e:
            last=e; time.sleep(2*(k+1))
    raise RuntimeError(last)

def main():
    r=pd.read_csv(RANK); c=r[r.passes_single_sigmaRV_2==True].copy(); ids=[int(x) for x in c.source_id]
    clauses=' OR '.join("ident.id='Gaia DR3 %d'"%x for x in ids)
    q=f"SELECT ident.id, basic.main_id, basic.ra, basic.dec, basic.otype, basic.rvz_radvel, basic.rvz_error, basic.rvz_bibcode, basic.rvz_qual, basic.rvz_type FROM basic JOIN ident ON basic.oid=ident.oidref WHERE {clauses}"
    s=tap(q); s.to_csv(OUT/'simbad_top31.csv',index=False)
    # All identifiers for matched objects, useful for literature searching.
    if len(s):
        mids=[str(x).replace("'","''") for x in s.main_id.dropna().unique()]
        where=' OR '.join("basic.main_id='%s'"%x for x in mids)
        q2=f"SELECT basic.main_id, ident.id FROM basic JOIN ident ON basic.oid=ident.oidref WHERE {where}" if where else ''
        a=tap(q2) if q2 else pd.DataFrame(); a.to_csv(OUT/'simbad_identifiers_top31.csv',index=False)
    else:a=pd.DataFrame()
    summary={'status':'OUTCOME_BLIND_AUXILIARY_LOOKUP','single_pass_candidates':len(ids),'simbad_matches':int(s.main_id.nunique()) if len(s) else 0,'simbad_matches_with_rv':int(s.rvz_radvel.notna().sum()) if len(s) and 'rvz_radvel' in s else 0,'guardrail':'No H I or Persistence outcome was read. SIMBAD RV entries are registry values and are not automatically accepted as Cepheid systemic velocities.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
