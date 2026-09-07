#!/usr/bin/env python3
from pathlib import Path
import json,time
import numpy as np
import pandas as pd
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

ROOT=Path(__file__).resolve().parent
CAND=ROOT/'osc_rv_target_rank'/'classification_audit'/'osc_single_pass_candidates_classification_audit.csv'
OUT=ROOT/'osc_rv_target_rank'/'apogee_dr17_recovery'; OUT.mkdir(parents=True,exist_ok=True)
CAT='III/286/allvis'; EXCLUDE={2072235820984829312}

def truthy(x): return str(x).strip().lower() in {'true','1','yes','y'}
def txt(v):
    try:
        if np.ma.is_masked(v): return ''
    except Exception: pass
    return v.decode('utf-8','ignore') if isinstance(v,bytes) else str(v)
def flt(v):
    try:
        if np.ma.is_masked(v): return np.nan
        x=float(v); return x if np.isfinite(x) else np.nan
    except Exception: return np.nan

def query_region(ra,dec):
    viz=Vizier(columns=['**'],row_limit=-1)
    last=None
    for i in range(3):
        try:
            t=viz.query_region(SkyCoord(ra*u.deg,dec*u.deg),radius=1.5*u.arcsec,catalog=CAT)
            return (t[0] if t else None),None
        except Exception as e:
            last=repr(e); time.sleep(2*(i+1))
    return None,last

def native(x):
    if isinstance(x,np.integer): return int(x)
    if isinstance(x,np.floating): return None if not np.isfinite(x) else float(x)
    if isinstance(x,np.bool_): return bool(x)
    if isinstance(x,dict): return {str(k):native(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [native(v) for v in x]
    return x

def main():
    c=pd.read_csv(CAND,dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy(); c=c[~c.source_id.astype('int64').isin(EXCLUDE)]
    raw=[]; audit=[]; qualifying=[]
    for j,r in c.reset_index(drop=True).iterrows():
        sid=int(r.source_id); ra=float(r.ra_deg); dec=float(r.dec_deg)
        tab,err=query_region(ra,dec)
        if tab is None or len(tab)==0:
            audit.append({'source_id':sid,'status':'no_match' if err is None else 'query_error','error':err})
            print(f'[{j+1}/{len(c)}] {sid}: no match',flush=True); continue
        cols=list(tab.colnames)
        ids=sorted({txt(v).strip() for v in tab['APOGEE']}) if 'APOGEE' in cols else []
        ids=[x for x in ids if x]
        if len(ids)!=1:
            audit.append({'source_id':sid,'status':'ambiguous_apogee_ids','n_rows':len(tab),'apogee_ids':ids})
            print(f'[{j+1}/{len(c)}] {sid}: ambiguous {ids}',flush=True); continue
        aid=ids[0]; accepted=[]
        for i,row in enumerate(tab):
            if txt(row['APOGEE']).strip()!=aid: continue
            v=flt(row['VHelio']) if 'VHelio' in cols else np.nan
            e=flt(row['e_RV']) if 'e_RV' in cols else np.nan
            mjd=flt(row['MJD']) if 'MJD' in cols else np.nan
            flag=flt(row['FlRV']) if 'FlRV' in cols else 0.0
            rec={'source_id':sid,'apogee_id':aid,'row_index':i,'mjd':mjd,'vhelio_kms':v,'rv_err_kms':e,'rv_flag':flag}
            raw.append(rec)
            if np.isfinite(v) and np.isfinite(e) and e>0 and np.isfinite(mjd) and (('FlRV' not in cols) or flag==0):
                accepted.append(rec)
        g=pd.DataFrame(accepted)
        if len(g):
            n_epoch=g.mjd.round(6).nunique(); w=1/np.square(g.rv_err_kms.to_numpy(float)); vv=g.vhelio_kms.to_numpy(float)
            mean=float(np.sum(w*vv)/np.sum(w)); formal=float(np.sqrt(1/np.sum(w)))
            sem=float(np.std(vv,ddof=1)/np.sqrt(len(vv))) if len(vv)>1 else np.nan
            assigned=float(max(formal,sem if np.isfinite(sem) else 0,1.0))
        else:
            n_epoch=0; mean=formal=sem=assigned=np.nan
        ok=bool(n_epoch>=8 and np.isfinite(assigned) and assigned<=5.0)
        rec={'source_id':sid,'status':'matched_unique','apogee_id':aid,'n_rows':len(tab),'n_accepted_visits':len(g),
             'n_distinct_mjd':int(n_epoch),'weighted_mean_vhelio_kms':mean,'formal_error_kms':formal,
             'empirical_sem_kms':sem,'assigned_systemic_rv_error_kms':assigned,'qualifies_frozen_rule':ok}
        audit.append(rec)
        if ok: qualifying.append(rec)
        print(f'[{j+1}/{len(c)}] {sid}: APOGEE={aid} visits={len(g)} epochs={n_epoch} qualify={ok}',flush=True)
    pd.DataFrame(raw).to_csv(OUT/'apogee_dr17_raw_visits.csv',index=False)
    pd.DataFrame(audit).to_csv(OUT/'apogee_dr17_candidate_audit.csv',index=False)
    pd.DataFrame(qualifying).to_csv(OUT/'apogee_dr17_qualifying_systemic_rv.csv',index=False)
    s={'protocol':'APOGEE_DR17_OSC_RV_RECOVERY_FREEZE','status':'OUTCOME_BLIND_DATA_RECOVERY','candidate_rows':len(c),
       'matched_unique_sources':sum(1 for x in audit if x.get('status')=='matched_unique'),
       'qualifying_unique_sources':len(qualifying),'qualifying_sources':qualifying,
       'outcome_firewall':'No H I spectrum, H I velocity, H I residual, GRB comparison outcome, or Persistence prediction was read.'}
    with open(OUT/'summary.json','w') as f: json.dump(native(s),f,indent=2)
    print(json.dumps(native(s),indent=2))
if __name__=='__main__': main()
