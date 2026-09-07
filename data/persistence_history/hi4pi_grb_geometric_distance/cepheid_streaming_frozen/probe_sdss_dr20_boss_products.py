#!/usr/bin/env python3
from pathlib import Path
import json,requests
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'osc_rv_target_rank'/'sdss_dr20_recovery'; OUT.mkdir(parents=True,exist_ok=True)
SUMMARY=json.load(open(OUT/'discovery_summary.json'))
BASE='https://api.sdss.org/valis'

def req(path,params):
    try:
        r=requests.get(BASE+path,params=params,timeout=12)
        try: data=r.json()
        except Exception: data={'text':r.text[:10000]}
        return {'status_code':r.status_code,'url':r.url,'data':data}
    except Exception as e: return {'error':repr(e)}

def main():
    out=[]
    for x in SUMMARY['matched_sources']:
        sd=int(x['sdss_id']); sid=int(x['source_id'])
        rec={'source_id':sid,'sdss_id':sd,
             'boss_daily':req(f'/target/pipe/boss/{sd}',{'coadd':'daily','release':'DR20'}),
             'pipelines_boss':req(f'/target/pipelines/{sd}',{'pipe':'boss','release':'DR20'}),
             'query_sdssid':req('/query/sdssid',{'sdss_id':sd,'release':'DR20'})}
        out.append(rec)
        print(sid,sd,'boss',rec['boss_daily'].get('status_code'), 'pipes',rec['pipelines_boss'].get('status_code'),flush=True)
    with open(OUT/'sdss_dr20_boss_fast_probe.json','w') as f: json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2)[:30000])
if __name__=='__main__': main()
