#!/usr/bin/env python3
"""Fast mirror-based discovery-only crossmatch for final OSC legacy RV sweep.

Uses the frozen purity-qualified OSC candidate coordinates and the same catalog
families as LEGACY_CEPHEID_RV_OSC_SWEEP_FREEZE.md. No H I/Persistence outcomes
are read and no acceptance threshold is changed.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import io, json, urllib.parse
import pandas as pd
import requests
from astropy.io.votable import parse_single_table

HERE=Path(__file__).resolve().parent
CAND=HERE/'osc_rv_target_rank'/'classification_audit'/'osc_single_pass_candidates_classification_audit.csv'
OUT=HERE/'osc_rv_target_rank'/'legacy_rv_sweep_mirror'
OUT.mkdir(parents=True,exist_ok=True)
EXCLUDE={2072235820984829312}
BASE='https://vizier.cfa.harvard.edu/viz-bin/votable'
TABLES={
 'gorynya_stars':'III/229/stars',
 'borgniet_stars':'J/A+A/631/A37/tablea1',
 'crav_table2':'J/AJ/150/13/table2',
 'crav_table6':'J/AJ/150/13/table6',
 'cruz_reyes_astrometry':'J/A+A/672/A85/table10',
 'rave_dr6':'III/283/ravedr6',
}

def truthy(x): return str(x).strip().lower() in {'true','1','yes','y'}

def one(label,table,sid,ra,dec):
    params={'-source':table,'-c':f'{ra} {dec}','-c.rs':'2','-out.max':'20','-out.all':'1'}
    url=BASE+'?'+urllib.parse.urlencode(params)
    try:
        r=requests.get(url,timeout=25,headers={'User-Agent':'Mozilla/5.0 OSC-data-audit'})
        r.raise_for_status()
        text=r.text
        # Fast no-row signal used by VizieR.
        if 'No astronomical object found' in text or '<TABLEDATA></TABLEDATA>' in text:
            return {'source_id':sid,'label':label,'table':table,'status':'no_match','rows':0,'url':url}
        try:
            tab=parse_single_table(io.BytesIO(r.content)).to_table()
            n=len(tab)
            rows=[]
            for rr in tab[:20]:
                d={}
                for c in tab.colnames:
                    try:
                        v=rr[c]
                        if hasattr(v,'item'): v=v.item()
                        if isinstance(v,bytes): v=v.decode('utf-8','ignore')
                        if pd.isna(v): v=None
                        if not isinstance(v,(str,int,float,bool,type(None))): v=str(v)
                    except Exception:
                        v=None
                    d[c]=v
                rows.append(d)
            return {'source_id':sid,'label':label,'table':table,'status':'matched' if n else 'no_match','rows':int(n),'sample':rows,'url':url}
        except Exception as e:
            return {'source_id':sid,'label':label,'table':table,'status':'parse_error','error':repr(e),'rows':0,'url':url,'head':text[:500]}
    except Exception as e:
        return {'source_id':sid,'label':label,'table':table,'status':'query_error','error':repr(e),'rows':0,'url':url}

def main():
    c=pd.read_csv(CAND,dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy()
    c=c[~c.source_id.astype('int64').isin(EXCLUDE)].copy()
    tasks=[]
    for _,r in c.iterrows():
        sid=int(r.source_id); ra=float(r.ra_deg); dec=float(r.dec_deg)
        for label,table in TABLES.items(): tasks.append((label,table,sid,ra,dec))
    out=[]
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs={ex.submit(one,*t):t for t in tasks}
        for k,f in enumerate(as_completed(futs),1):
            rec=f.result(); out.append(rec)
            print(f'[{k}/{len(tasks)}] {rec["source_id"]} {rec["label"]}: {rec["status"]} rows={rec.get("rows",0)}',flush=True)
    out=sorted(out,key=lambda x:(x['source_id'],x['label']))
    (OUT/'mirror_query_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    matched=[x for x in out if x['status']=='matched' and x.get('rows',0)>0]
    errors=[x for x in out if x['status'] in {'query_error','parse_error'}]
    summary={
      'protocol':'LEGACY_CEPHEID_RV_OSC_SWEEP_FREEZE',
      'stage':'MIRROR_PARALLEL_DISCOVERY_ONLY',
      'candidate_sources':int(len(c)),
      'queries':len(out),
      'matched_candidate_catalog_pairs':len(matched),
      'matched_unique_sources':sorted(set(int(x['source_id']) for x in matched)),
      'errors':len(errors),
      'error_records':[{'source_id':x['source_id'],'label':x['label'],'status':x['status'],'error':x.get('error')} for x in errors],
      'matches':[{'source_id':x['source_id'],'label':x['label'],'table':x['table'],'rows':x['rows'],'sample':x.get('sample',[])} for x in matched],
      'outcome_firewall':'No H I spectrum, H I velocity, H I residual, unblinded Outer-arm result, or Persistence prediction was read.'
    }
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
