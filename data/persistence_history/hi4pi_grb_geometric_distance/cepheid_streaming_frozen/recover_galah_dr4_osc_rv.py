#!/usr/bin/env python3
from pathlib import Path
import json,time
import numpy as np
import pandas as pd
from astroquery.vizier import Vizier

ROOT=Path(__file__).resolve().parent
CAND=ROOT/'osc_rv_target_rank'/'classification_audit'/'osc_single_pass_candidates_classification_audit.csv'
OUT=ROOT/'osc_rv_target_rank'/'galah_dr4_recovery'; OUT.mkdir(parents=True,exist_ok=True)
CAT='J/other/PASA/42.51/allspec'; EXCLUDE={2072235820984829312}

def truthy(x): return str(x).strip().lower() in {'true','1','yes','y'}
def f(v):
    try:
        if np.ma.is_masked(v): return np.nan
        x=float(v); return x if np.isfinite(x) else np.nan
    except Exception:return np.nan
def native(x):
    if isinstance(x,np.integer): return int(x)
    if isinstance(x,np.floating): return None if not np.isfinite(x) else float(x)
    if isinstance(x,np.bool_): return bool(x)
    if isinstance(x,dict): return {str(k):native(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [native(v) for v in x]
    return x

def query(sid):
    v=Vizier(columns=['**'],row_limit=-1); last=None
    for i in range(3):
        try:
            t=v.query_constraints(catalog=CAT,GaiaDR3=str(int(sid)))
            return (t[0] if t else None),None
        except Exception as e:
            last=repr(e); time.sleep(2*(i+1))
    return None,last

def main():
    c=pd.read_csv(CAND,dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy(); c=c[~c.source_id.astype('int64').isin(EXCLUDE)]
    raw=[]; audit=[]; qual=[]
    for j,r in c.reset_index(drop=True).iterrows():
        sid=int(r.source_id); tab,err=query(sid)
        if tab is None or len(tab)==0:
            audit.append({'source_id':sid,'status':'no_match' if err is None else 'query_error','error':err});
            print(f'[{j+1}/{len(c)}] {sid}: no match',flush=True); continue
        cols=list(tab.colnames); acc=[]
        for i,row in enumerate(tab):
            rv=f(row['rv_comp_1']) if 'rv_comp_1' in cols else np.nan
            er=f(row['e_rv_comp_1']) if 'e_rv_comp_1' in cols else np.nan
            mjd=f(row['MJD']) if 'MJD' in cols else np.nan
            flag=f(row['flag_sp']) if 'flag_sp' in cols else 0
            nr=f(row['rv_comp_nr']) if 'rv_comp_nr' in cols else 1
            rec={'source_id':sid,'row_index':i,'mjd':mjd,'rv_kms':rv,'rv_err_kms':er,'flag_sp':flag,'rv_comp_nr':nr}; raw.append(rec)
            if np.isfinite(rv) and np.isfinite(er) and er>0 and np.isfinite(mjd) and (('flag_sp' not in cols) or flag==0) and (('rv_comp_nr' not in cols) or nr==1): acc.append(rec)
        g=pd.DataFrame(acc)
        if len(g):
            ne=int(g.mjd.round(6).nunique()); w=1/np.square(g.rv_err_kms.to_numpy(float)); vv=g.rv_kms.to_numpy(float)
            mean=float(np.sum(w*vv)/np.sum(w)); formal=float(np.sqrt(1/np.sum(w))); sem=float(np.std(vv,ddof=1)/np.sqrt(len(vv))) if len(vv)>1 else np.nan
            assigned=float(max(formal,sem if np.isfinite(sem) else 0,1.0))
        else: ne=0; mean=formal=sem=assigned=np.nan
        ok=bool(ne>=8 and np.isfinite(assigned) and assigned<=5)
        rec={'source_id':sid,'status':'matched','catalog_rows':len(tab),'accepted_spectra':len(g),'distinct_mjd':ne,'weighted_mean_rv_kms':mean,'formal_error_kms':formal,'empirical_sem_kms':sem,'assigned_systemic_rv_error_kms':assigned,'qualifies_frozen_rule':ok}
        audit.append(rec)
        if ok: qual.append(rec)
        print(f'[{j+1}/{len(c)}] {sid}: rows={len(tab)} epochs={ne} qualify={ok}',flush=True)
    pd.DataFrame(raw).to_csv(OUT/'galah_dr4_raw_spectra.csv',index=False)
    pd.DataFrame(audit).to_csv(OUT/'galah_dr4_candidate_audit.csv',index=False)
    pd.DataFrame(qual).to_csv(OUT/'galah_dr4_qualifying_systemic_rv.csv',index=False)
    s={'protocol':'GALAH_DR4_OSC_RV_RECOVERY_FREEZE','candidate_rows':len(c),'matched_sources':sum(x.get('status')=='matched' for x in audit),'qualifying_unique_sources':len(qual),'qualifying_sources':qual,'outcome_firewall':'No H I spectrum, H I velocity, H I residual, GRB comparison outcome, or Persistence prediction was read.'}
    json.dump(native(s),open(OUT/'summary.json','w'),indent=2); print(json.dumps(native(s),indent=2))
if __name__=='__main__': main()
