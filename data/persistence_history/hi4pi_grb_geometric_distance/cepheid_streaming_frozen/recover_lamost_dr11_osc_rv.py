#!/usr/bin/env python3
"""Outcome-blind LAMOST DR11 RV recovery for frozen OSC Cepheid candidates."""
from pathlib import Path
import json, time
import numpy as np
import pandas as pd
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

ROOT = Path(__file__).resolve().parent
CAND = ROOT/'osc_rv_target_rank'/'classification_audit'/'osc_single_pass_candidates_classification_audit.csv'
OUT = ROOT/'osc_rv_target_rank'/'lamost_dr11_recovery'
OUT.mkdir(parents=True, exist_ok=True)
TABLES={'LRS':'V/162/dr11sl','MRS':'V/162/dr11sm'}
EXCLUDE={2072235820984829312}
POSITIVE_CONTROL_LRS=167356085046961408  # GaiaDR3 ID explicitly shown in the DR11 VizieR table interface.


def truthy(x): return str(x).strip().lower() in {'true','1','yes','y'}
def to_text(v):
    try:
        if np.ma.is_masked(v): return ''
    except Exception: pass
    return v.decode('utf-8','ignore') if isinstance(v,bytes) else str(v)
def to_float(v):
    try:
        if np.ma.is_masked(v): return np.nan
        x=float(v); return x if np.isfinite(x) else np.nan
    except Exception: return np.nan
def to_int(v):
    try:
        if np.ma.is_masked(v): return None
        s=to_text(v).strip()
        if not s or s.lower() in {'nan','--','none'}: return None
        return int(s)
    except Exception:
        try: return int(float(v))
        except Exception: return None

def native(x):
    if isinstance(x,np.integer): return int(x)
    if isinstance(x,np.floating): return None if not np.isfinite(x) else float(x)
    if isinstance(x,np.bool_): return bool(x)
    if isinstance(x,dict): return {str(k):native(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [native(v) for v in x]
    return x

def distinct_epoch_key(row,cols):
    for c in ['MJD','mjd','LMJD','lmjd','LMJM','lmjm','Obs.Date','obsdate','ObsDate','date']:
        if c in cols:
            s=to_text(row[c]).strip()
            if s and s.lower() not in {'nan','--','none'}:
                try:
                    f=float(row[c]); return (c,round(f,6)) if np.isfinite(f) else None
                except Exception: return (c,s)
    return None

def rv_columns(cols):
    out=[]
    for c in cols:
        U=c.upper()
        if 'RV' not in U or U=='GAIADR3': continue
        if any(t in U for t in ['ERR','ERROR','SIG','UNC','N_RV','NRV','FLAG']): continue
        out.append(c)
    out.sort(key=lambda c:(0 if c.upper() in {'RV','RV_B','RV_R','VRAD','VHELIO'} else 1,c))
    return out

def err_for(rvcol,cols):
    for c in [f'e_{rvcol}',f'E_{rvcol}',f'{rvcol}_err',f'{rvcol}_error',f'e{rvcol}',f'{rvcol}err',f'{rvcol}Err']:
        if c in cols: return c
    suffix=rvcol.upper().replace('RV','').strip('_')
    for c in cols:
        U=c.upper()
        if 'RV' in U and any(t in U for t in ['ERR','ERROR','SIG','UNC']) and (not suffix or suffix in U): return c
    return None

def exact_filter(tab,sid):
    if 'GaiaDR3' not in tab.colnames: return tab[:0]
    keep=[to_int(v)==int(sid) for v in tab['GaiaDR3']]
    return tab[np.array(keep,dtype=bool)]

def run_query(viz,catalog,**kwargs):
    last=None
    for attempt in range(3):
        try:
            if 'coord' in kwargs:
                return viz.query_region(kwargs['coord'],radius=3*u.arcsec,catalog=catalog),None
            return viz.query_constraints(catalog=catalog,GaiaDR3=str(int(kwargs['sid']))),None
        except Exception as e:
            last=repr(e); time.sleep(2*(attempt+1))
    return None,last

def extract_rows(tab,sid,branch,catalog,mode):
    cols=list(tab.colnames); rvs=rv_columns(cols); rows=[]
    for i,row in enumerate(tab):
        epoch=distinct_epoch_key(row,cols)
        for rvcol in rvs:
            rv=to_float(row[rvcol]); ecol=err_for(rvcol,cols); er=to_float(row[ecol]) if ecol else np.nan
            if not np.isfinite(rv): continue
            rows.append({'source_id':int(sid),'branch':branch,'catalog':catalog,'query_mode':mode,
                         'row_index':i,'rv_column':rvcol,'err_column':ecol or '',
                         'rv_kms':rv,'rv_err_kms':er,'epoch_field':epoch[0] if epoch else '',
                         'epoch_value':epoch[1] if epoch else '',
                         'ObsID':to_text(row['ObsID']) if 'ObsID' in cols else '',
                         'Target':to_text(row['Target']) if 'Target' in cols else ''})
    return rows,cols,rvs

def query_one(sid,ra,dec,branch,catalog):
    viz=Vizier(columns=['**'],row_limit=-1)
    tabs,err=run_query(viz,catalog,sid=sid)
    if tabs is not None and len(tabs):
        tab=exact_filter(tabs[0],sid)
        if len(tab):
            rows,cols,rvs=extract_rows(tab,sid,branch,catalog,'GaiaDR3_constraint')
            return rows,{'status':'matched_exact','n_rows':len(tab),'columns':cols,'rv_columns':rvs}
    # Validation fallback: 3-arcsec sky query, but accept ONLY rows whose returned GaiaDR3 is exactly the frozen source ID.
    coord=SkyCoord(float(ra)*u.deg,float(dec)*u.deg,frame='icrs')
    tabs2,err2=run_query(viz,catalog,coord=coord)
    if tabs2 is not None and len(tabs2):
        tab2=exact_filter(tabs2[0],sid)
        if len(tab2):
            rows,cols,rvs=extract_rows(tab2,sid,branch,catalog,'3arcsec_then_exact_GaiaDR3')
            return rows,{'status':'matched_region_exact_id','n_rows':len(tab2),'columns':cols,'rv_columns':rvs}
        returned=[]
        if 'GaiaDR3' in tabs2[0].colnames:
            returned=sorted({x for x in (to_int(v) for v in tabs2[0]['GaiaDR3']) if x is not None})
        return [],{'status':'region_rows_but_no_exact_gaia_id','region_rows':len(tabs2[0]),'returned_gaia_ids':returned}
    if err or err2: return [],{'status':'query_error','exact_error':err,'region_error':err2}
    return [],{'status':'no_match'}

def summarize(raw):
    if raw.empty: return pd.DataFrame(),pd.DataFrame()
    recs=[]; qual=[]
    for (sid,branch,rvcol),g in raw.groupby(['source_id','branch','rv_column']):
        gg=g[np.isfinite(g.rv_kms)&np.isfinite(g.rv_err_kms)&(g.rv_err_kms>0)].copy()
        gg=gg[gg.epoch_value.astype(str).str.len()>0]
        n=gg[['epoch_field','epoch_value']].drop_duplicates().shape[0] if len(gg) else 0
        if len(gg):
            w=1/np.square(gg.rv_err_kms.to_numpy(float)); v=gg.rv_kms.to_numpy(float)
            wm=float(np.sum(w*v)/np.sum(w)); formal=float(np.sqrt(1/np.sum(w)))
            sem=float(np.std(v,ddof=1)/np.sqrt(len(v))) if len(v)>1 else np.nan
            assigned=float(max(formal,sem if np.isfinite(sem) else 0,1.0))
        else: wm=formal=sem=assigned=np.nan
        ok=bool(n>=8 and np.isfinite(assigned) and assigned<=5)
        r={'source_id':int(sid),'branch':branch,'rv_column':rvcol,'n_spectra':len(gg),'n_distinct_epochs':int(n),
           'weighted_mean_rv_kms':wm,'formal_weighted_error_kms':formal,'empirical_sem_kms':sem,
           'assigned_systemic_rv_error_kms':assigned,'qualifies_frozen_rule':ok}
        recs.append(r)
        if ok: qual.append(r)
    return pd.DataFrame(recs),pd.DataFrame(qual)

def choose(qual):
    if qual.empty: return pd.DataFrame()
    q=qual.copy(); q['rank']=q.branch.map({'MRS':0,'LRS':1}).fillna(9)
    q=q.sort_values(['source_id','rank','assigned_systemic_rv_error_kms','n_distinct_epochs'],ascending=[True,True,True,False])
    return q.groupby('source_id',as_index=False).first().drop(columns=['rank'])

def main():
    c=pd.read_csv(CAND,dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy(); c=c[~c.source_id.astype('int64').isin(EXCLUDE)].copy()
    # Positive-control check of the exact-ID VizieR constraint, independent of candidate results.
    pc_viz=Vizier(columns=['GaiaDR3'],row_limit=5)
    pc_tabs,pc_err=run_query(pc_viz,TABLES['LRS'],sid=POSITIVE_CONTROL_LRS)
    pc_n=len(pc_tabs[0]) if pc_tabs is not None and len(pc_tabs) else 0
    positive_control={'gaia_source_id':POSITIVE_CONTROL_LRS,'catalog':TABLES['LRS'],'rows_returned':pc_n,'error':pc_err,'passes':bool(pc_n>0)}
    print('positive_control',positive_control,flush=True)
    raw=[]; audit=[]
    for j,r in c.reset_index(drop=True).iterrows():
        sid=int(r.source_id); ra=float(r.ra_deg); dec=float(r.dec_deg)
        for branch,cat in TABLES.items():
            rows,meta=query_one(sid,ra,dec,branch,cat); raw.extend(rows)
            audit.append({'source_id':sid,'ra_deg':ra,'dec_deg':dec,'branch':branch,'catalog':cat,**meta})
            print(f'[{j+1}/{len(c)}] {sid} {branch}: {meta.get("status")} rows={meta.get("n_rows",0)}',flush=True)
    rawdf=pd.DataFrame(raw); rawdf.to_csv(OUT/'lamost_dr11_raw_rv_matches.csv',index=False)
    groups,qual=summarize(rawdf); groups.to_csv(OUT/'lamost_dr11_rv_group_summary.csv',index=False)
    chosen=choose(qual); chosen.to_csv(OUT/'lamost_dr11_qualifying_systemic_rv.csv',index=False)
    with open(OUT/'lamost_dr11_query_audit.json','w') as f: json.dump(native(audit),f,indent=2)
    summary={'protocol':'LAMOST_DR11_OSC_RV_RECOVERY_FREEZE','status':'OUTCOME_BLIND_DATA_RECOVERY',
             'positive_control':positive_control,'candidate_rows':len(c),'candidate_source_ids':len(c),
             'raw_rv_measurements':len(rawdf),'measurement_groups':len(groups),'qualifying_groups':len(qual),
             'qualifying_unique_sources':int(chosen.source_id.nunique()) if not chosen.empty else 0,
             'qualifying_sources':chosen.to_dict('records') if not chosen.empty else [],
             'outcome_firewall':'No H I spectrum, H I velocity, H I residual, GRB comparison outcome, or Persistence prediction was read.'}
    with open(OUT/'summary.json','w') as f: json.dump(native(summary),f,indent=2)
    print(json.dumps(native(summary),indent=2))
if __name__=='__main__': main()
