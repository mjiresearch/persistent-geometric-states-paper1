#!/usr/bin/env python3
"""Outcome-blind LAMOST DR11 RV recovery for frozen OSC Cepheid candidates.

Reads only the purity-qualified OSC candidate list and public LAMOST DR11 VizieR tables.
Never reads H I products or Persistence predictions.
"""
from pathlib import Path
import json, math, time
import numpy as np
import pandas as pd
from astroquery.vizier import Vizier

ROOT = Path(__file__).resolve().parent
CAND = ROOT / 'osc_rv_target_rank' / 'classification_audit' / 'osc_single_pass_candidates_classification_audit.csv'
OUT = ROOT / 'osc_rv_target_rank' / 'lamost_dr11_recovery'
OUT.mkdir(parents=True, exist_ok=True)
TABLES = {
    'LRS': 'V/162/dr11sl',
    'MRS': 'V/162/dr11sm',
}
EXCLUDE = {2072235820984829312}


def truthy(x):
    return str(x).strip().lower() in {'true','1','yes','y'}


def native(x):
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.bool_,)): return bool(x)
    if isinstance(x, dict): return {str(k): native(v) for k,v in x.items()}
    if isinstance(x, (list, tuple)): return [native(v) for v in x]
    return x


def to_float(v):
    try:
        if np.ma.is_masked(v): return np.nan
        x = float(v)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan


def to_text(v):
    try:
        if np.ma.is_masked(v): return ''
    except Exception:
        pass
    if isinstance(v, bytes):
        return v.decode('utf-8','ignore')
    return str(v)


def distinct_epoch_key(row, cols):
    # Prefer true date/MJD-like columns; fallback to observation identifier only for audit,
    # never to satisfy the >=8 distinct epoch rule unless a time-like field exists.
    prefs = ['MJD','mjd','LMJD','lmjd','LMJM','lmjm','Obs.Date','obsdate','ObsDate','date']
    for c in prefs:
        if c in cols:
            val = row[c]
            s = to_text(val).strip()
            if s and s.lower() not in {'nan','--','none'}:
                try:
                    f = float(val)
                    if np.isfinite(f): return (c, round(f, 6))
                except Exception:
                    return (c, s)
    return None


def rv_columns(cols):
    out=[]
    for c in cols:
        u=c.upper()
        if 'RV' not in u: continue
        if any(tok in u for tok in ['ERR','ERROR','SIG','UNC','N_RV','NRV','FLAG']): continue
        if u in {'GAIADR3'}: continue
        out.append(c)
    # Prefer canonical RV-like columns first.
    out.sort(key=lambda c: (0 if c.upper() in {'RV','RV_B','RV_R','VRAD','VHELIO'} else 1, c))
    return out


def err_for(rvcol, cols):
    rvU=rvcol.upper()
    candidates = [
        f'e_{rvcol}', f'E_{rvcol}', f'{rvcol}_err', f'{rvcol}_error',
        f'e{rvcol}', f'{rvcol}err', f'{rvcol}Err'
    ]
    for c in candidates:
        if c in cols: return c
    # fuzzy match: error-ish column containing same RV token/suffix
    suffix = rvU.replace('RV','').strip('_')
    for c in cols:
        u=c.upper()
        if ('RV' in u and any(t in u for t in ['ERR','ERROR','SIG','UNC'])):
            if not suffix or suffix in u:
                return c
    return None


def query_one(sid, branch, catalog):
    viz = Vizier(columns=['**'], row_limit=-1)
    last=None
    for attempt in range(3):
        try:
            tabs = viz.query_constraints(catalog=catalog, GaiaDR3=str(int(sid)))
            if not tabs:
                return [], {'status':'no_match'}
            tab=tabs[0]
            cols=list(tab.colnames)
            rows=[]
            rvs=rv_columns(cols)
            for i,row in enumerate(tab):
                epoch=distinct_epoch_key(row, cols)
                for rvcol in rvs:
                    rv=to_float(row[rvcol])
                    ecol=err_for(rvcol, cols)
                    er=to_float(row[ecol]) if ecol else np.nan
                    if not np.isfinite(rv):
                        continue
                    rows.append({
                        'source_id': int(sid), 'branch': branch, 'catalog': catalog,
                        'row_index': i, 'rv_column': rvcol, 'err_column': ecol or '',
                        'rv_kms': rv, 'rv_err_kms': er,
                        'epoch_field': epoch[0] if epoch else '',
                        'epoch_value': epoch[1] if epoch else '',
                        'ObsID': to_text(row['ObsID']) if 'ObsID' in cols else '',
                        'Target': to_text(row['Target']) if 'Target' in cols else '',
                    })
            return rows, {'status':'matched','n_rows':len(tab),'columns':cols,'rv_columns':rvs}
        except Exception as e:
            last=repr(e); time.sleep(3*(attempt+1))
    return [], {'status':'query_error','error':last}


def summarize_measurements(raw):
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame()
    group_rows=[]; qual=[]
    for (sid,branch,rvcol),g in raw.groupby(['source_id','branch','rv_column'], dropna=False):
        gg=g.copy()
        gg=gg[np.isfinite(gg.rv_kms)]
        # Frozen rule requires finite quoted uncertainty on every contributing spectrum.
        gg=gg[np.isfinite(gg.rv_err_kms) & (gg.rv_err_kms>0)]
        epoch_ok=gg.epoch_value.astype(str).str.len()>0
        gg=gg[epoch_ok]
        if gg.empty:
            n_epochs=0; wm=we=scatter=assigned=np.nan
        else:
            n_epochs=gg[['epoch_field','epoch_value']].drop_duplicates().shape[0]
            w=1.0/np.square(gg.rv_err_kms.to_numpy(float))
            v=gg.rv_kms.to_numpy(float)
            wm=float(np.sum(w*v)/np.sum(w))
            we=float(np.sqrt(1.0/np.sum(w)))
            if len(v)>1:
                scatter=float(np.std(v,ddof=1)/np.sqrt(len(v)))
            else:
                scatter=np.nan
            assigned=float(max(we, scatter if np.isfinite(scatter) else 0.0, 1.0))
        q=bool(n_epochs>=8 and np.isfinite(assigned) and assigned<=5.0)
        rec=dict(source_id=int(sid),branch=branch,rv_column=rvcol,n_spectra=int(len(gg)),
                 n_distinct_epochs=int(n_epochs),weighted_mean_rv_kms=wm,
                 formal_weighted_error_kms=we,empirical_sem_kms=scatter,
                 assigned_systemic_rv_error_kms=assigned,qualifies_frozen_rule=q)
        group_rows.append(rec)
        if q: qual.append(rec)
    return pd.DataFrame(group_rows), pd.DataFrame(qual)


def choose_qualifying(qual):
    if qual.empty: return pd.DataFrame()
    # Prefer MRS over LRS if both qualify; within branch prefer smaller assigned uncertainty,
    # then more distinct epochs. No value-agreement criterion is used.
    q=qual.copy()
    q['branch_rank']=q.branch.map({'MRS':0,'LRS':1}).fillna(9)
    q=q.sort_values(['source_id','branch_rank','assigned_systemic_rv_error_kms','n_distinct_epochs'],
                    ascending=[True,True,True,False])
    return q.groupby('source_id',as_index=False).first().drop(columns=['branch_rank'])


def main():
    c=pd.read_csv(CAND, dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy()
    c=c[~c.source_id.astype('int64').isin(EXCLUDE)].copy()
    sids=[int(x) for x in c.source_id.dropna().astype('int64').tolist()]
    raw=[]; audit=[]
    for j,sid in enumerate(sids,1):
        for branch,cat in TABLES.items():
            rows,meta=query_one(sid,branch,cat)
            raw.extend(rows)
            audit.append({'source_id':sid,'branch':branch,'catalog':cat,**meta})
            print(f'[{j}/{len(sids)}] {sid} {branch}: {meta.get("status")} rows={meta.get("n_rows",0)} rv={meta.get("rv_columns",[])}', flush=True)
    rawdf=pd.DataFrame(raw)
    rawdf.to_csv(OUT/'lamost_dr11_raw_rv_matches.csv',index=False)
    groups,qual=summarize_measurements(rawdf)
    groups.to_csv(OUT/'lamost_dr11_rv_group_summary.csv',index=False)
    chosen=choose_qualifying(qual)
    chosen.to_csv(OUT/'lamost_dr11_qualifying_systemic_rv.csv',index=False)
    with open(OUT/'lamost_dr11_query_audit.json','w') as f:
        json.dump(native(audit),f,indent=2)
    summary={
        'protocol':'LAMOST_DR11_OSC_RV_RECOVERY_FREEZE',
        'status':'OUTCOME_BLIND_DATA_RECOVERY',
        'candidate_rows':len(c), 'candidate_source_ids':len(sids),
        'raw_rv_measurements':int(len(rawdf)),
        'measurement_groups':int(len(groups)),
        'qualifying_groups':int(len(qual)),
        'qualifying_unique_sources':int(chosen.source_id.nunique()) if not chosen.empty else 0,
        'qualifying_sources':chosen.to_dict('records') if not chosen.empty else [],
        'outcome_firewall':'No H I spectrum, H I velocity, H I residual, GRB comparison outcome, or Persistence prediction was read.'
    }
    with open(OUT/'summary.json','w') as f: json.dump(native(summary),f,indent=2)
    print(json.dumps(native(summary),indent=2))

if __name__=='__main__':
    main()
