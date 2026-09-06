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
    last=None; body=''
    for k in range(4):
        try:
            r=requests.post(TAP,data={'request':'doQuery','lang':'adql','format':'csv','query':q},timeout=120)
            body=r.text
            r.raise_for_status(); return pd.read_csv(io.StringIO(r.text))
        except Exception as e:
            last=e; time.sleep(2*(k+1))
    raise RuntimeError(f'{last}; response={body[:1000]}')

def main():
    r=pd.read_csv(RANK); c=r[r.passes_single_sigmaRV_2==True].copy()
    rows=[]
    radius=2.0/3600.0
    for _,x in c.iterrows():
        ra=float(x.ra_deg); dec=float(x.dec_deg)
        q=("SELECT TOP 1 basic.main_id,basic.ra,basic.dec,basic.otype,basic.rvz_radvel,basic.rvz_err,basic.rvz_bibcode "
           "FROM basic WHERE 1=CONTAINS(POINT('ICRS',basic.ra,basic.dec),"
           f"CIRCLE('ICRS',{ra},{dec},{radius}))")
        try:s=tap(q)
        except Exception as e:
            rows.append(dict(source_id=int(x.source_id),query_error=str(e))); continue
        if len(s):
            d=s.iloc[0].to_dict(); d['source_id']=int(x.source_id); rows.append(d)
        else: rows.append(dict(source_id=int(x.source_id)))
    s=pd.DataFrame(rows); s.to_csv(OUT/'simbad_top31.csv',index=False)
    summary={'status':'OUTCOME_BLIND_AUXILIARY_LOOKUP','single_pass_candidates':int(len(c)),'simbad_matches':int(s.main_id.notna().sum()) if 'main_id' in s else 0,'simbad_matches_with_rv':int(s.rvz_radvel.notna().sum()) if 'rvz_radvel' in s else 0,'query_errors':int(s.query_error.notna().sum()) if 'query_error' in s else 0,'guardrail':'No H I or Persistence outcome was read. SIMBAD RV entries are registry values and are not automatically accepted as Cepheid systemic velocities.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
