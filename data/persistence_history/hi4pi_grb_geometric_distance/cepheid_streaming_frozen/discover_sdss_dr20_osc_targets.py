#!/usr/bin/env python3
from pathlib import Path
import json,time,requests
import pandas as pd

ROOT=Path(__file__).resolve().parent
CAND=ROOT/'osc_rv_target_rank'/'classification_audit'/'osc_single_pass_candidates_classification_audit.csv'
OUT=ROOT/'osc_rv_target_rank'/'sdss_dr20_recovery'; OUT.mkdir(parents=True,exist_ok=True)
BASE='https://api.sdss.org/valis'
EXCLUDE={2072235820984829312}

def truthy(x): return str(x).strip().lower() in {'true','1','yes','y'}
def get_json(url,params=None):
    last=None
    for i in range(4):
        try:
            r=requests.get(url,params=params,timeout=45)
            if r.status_code==200: return r.json(),None,r.url
            last=f'HTTP {r.status_code}: {r.text[:500]}'
        except Exception as e: last=repr(e)
        time.sleep(2*(i+1))
    return None,last,None

def main():
    c=pd.read_csv(CAND,dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy(); c=c[~c.source_id.astype('int64').isin(EXCLUDE)].copy()
    openapi,err,ourl=get_json(BASE+'/openapi.json')
    paths=sorted(openapi.get('paths',{}).keys()) if isinstance(openapi,dict) else []
    relevant=[p for p in paths if any(k in p.lower() for k in ['target','spect','visit','query','astra','radial','rv'])]
    with open(OUT/'valis_openapi_relevant_paths.json','w') as f: json.dump({'error':err,'url':ourl,'paths':relevant},f,indent=2)
    rows=[]
    for j,r in c.reset_index(drop=True).iterrows():
        sid=int(r.source_id); ra=float(r.ra_deg); dec=float(r.dec_deg)
        data,e,url=get_json(BASE+'/query/cone',{'ra':ra,'dec':dec,'radius':1.5/3600.0,'units':'degree','release':'DR20'})
        if not isinstance(data,list): data=[]
        ids=sorted({int(x['sdss_id']) for x in data if x.get('sdss_id') is not None})
        rec={'source_id':sid,'ra_deg':ra,'dec_deg':dec,'query_error':e,'n_rows':len(data),'sdss_ids':ids,
             'unique_sdss_id':ids[0] if len(ids)==1 else None,
             'has_unique_match':len(ids)==1,
             'any_observed':any(bool(x.get('has_been_observed')) for x in data),
             'any_boss':any(bool(x.get('in_boss')) for x in data),
             'any_apogee':any(bool(x.get('in_apogee')) for x in data),
             'any_astra':any(bool(x.get('in_astra')) for x in data),
             'raw_rows':data}
        rows.append(rec)
        print(f'[{j+1}/{len(c)}] {sid}: rows={len(data)} ids={ids} observed={rec["any_observed"]} boss={rec["any_boss"]}',flush=True)
    with open(OUT/'sdss_dr20_cone_audit.json','w') as f: json.dump(rows,f,indent=2)
    flat=pd.DataFrame([{k:v for k,v in x.items() if k!='raw_rows'} for x in rows])
    flat.to_csv(OUT/'sdss_dr20_candidate_matches.csv',index=False)
    summary={'protocol':'SDSS_DR20_OSC_RV_RECOVERY_FREEZE','status':'OUTCOME_BLIND_TARGET_DISCOVERY',
             'candidate_rows':len(c),'unique_matches':sum(x['has_unique_match'] for x in rows),
             'observed_unique_matches':sum(x['has_unique_match'] and x['any_observed'] for x in rows),
             'boss_unique_matches':sum(x['has_unique_match'] and x['any_boss'] for x in rows),
             'apogee_unique_matches':sum(x['has_unique_match'] and x['any_apogee'] for x in rows),
             'astra_unique_matches':sum(x['has_unique_match'] and x['any_astra'] for x in rows),
             'matched_sources':[{'source_id':x['source_id'],'sdss_id':x['unique_sdss_id'],'observed':x['any_observed'],'in_boss':x['any_boss'],'in_apogee':x['any_apogee'],'in_astra':x['any_astra']} for x in rows if x['has_unique_match']],
             'outcome_firewall':'No H I spectrum, H I velocity, H I residual, GRB comparison outcome, or Persistence prediction was read.'}
    with open(OUT/'discovery_summary.json','w') as f: json.dump(summary,f,indent=2)
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
