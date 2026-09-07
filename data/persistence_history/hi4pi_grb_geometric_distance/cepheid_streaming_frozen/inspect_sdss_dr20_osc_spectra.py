#!/usr/bin/env python3
from pathlib import Path
import json,time,requests

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'osc_rv_target_rank'/'sdss_dr20_recovery'
SUMMARY=OUT/'discovery_summary.json'
BASE='https://api.sdss.org/valis'

def get(path,params=None):
    last=None
    for i in range(4):
        try:
            r=requests.get(BASE+path,params=params,timeout=60)
            if r.status_code==200:
                try: return r.json(),None,r.url
                except Exception: return {'raw_text':r.text[:20000]},None,r.url
            last=f'HTTP {r.status_code}: {r.text[:1000]}'
        except Exception as e: last=repr(e)
        time.sleep(2*(i+1))
    return None,last,None

def main():
    s=json.load(open(SUMMARY))
    audit=[]
    for x in s['matched_sources']:
        sdss=int(x['sdss_id']); sid=int(x['source_id'])
        rec={'source_id':sid,'sdss_id':sdss}
        for label,path in [
            ('spectra',f'/target/spectra/{sdss}'),
            ('boss_pipe',f'/target/pipe/boss/{sdss}'),
            ('pipelines',f'/target/pipelines/{sdss}'),
            ('target',f'/target/sdssid/{sdss}')]:
            data,err,url=get(path,{'release':'DR20'})
            rec[label]={'url':url,'error':err,'data':data}
            size=len(data) if isinstance(data,(list,dict)) else 0
            print(f'{sid} sdss={sdss} {label}: error={err} size={size}',flush=True)
        audit.append(rec)
    with open(OUT/'sdss_dr20_target_product_audit.json','w') as f: json.dump(audit,f,indent=2)
    # Also store compact structural summary so endpoint shapes are easy to inspect.
    compact=[]
    for r in audit:
        z={'source_id':r['source_id'],'sdss_id':r['sdss_id']}
        for label in ['spectra','boss_pipe','pipelines','target']:
            d=r[label]['data']
            z[label+'_error']=r[label]['error']
            if isinstance(d,list):
                z[label+'_type']='list'; z[label+'_n']=len(d); z[label+'_sample']=d[:2]
            elif isinstance(d,dict):
                z[label+'_type']='dict'; z[label+'_keys']=list(d.keys()); z[label+'_sample']=d
            else:
                z[label+'_type']=type(d).__name__; z[label+'_sample']=d
        compact.append(z)
    with open(OUT/'sdss_dr20_target_product_structure.json','w') as f: json.dump(compact,f,indent=2)
    print(json.dumps(compact[:2],indent=2)[:12000])
if __name__=='__main__': main()
