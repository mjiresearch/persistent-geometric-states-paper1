#!/usr/bin/env python3
"""Outcome-blind sweep of remaining public legacy RV catalogs for OSC Cepheid candidates."""
from pathlib import Path
import json, time
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.vizier import Vizier

HERE=Path(__file__).resolve().parent
CAND=HERE/'osc_rv_target_rank'/'classification_audit'/'osc_single_pass_candidates_classification_audit.csv'
OUT=HERE/'osc_rv_target_rank'/'legacy_rv_sweep'
OUT.mkdir(parents=True,exist_ok=True)
EXCLUDE={2072235820984829312}
CATALOGS={
 'gorynya_cepheid':'III/229',
 'borgniet_cepheid':'J/A+A/631/A37',
 'crav':'J/AJ/150/13',
 'cruz_reyes_cluster_cepheid':'J/A+A/672/A85',
 'rave_dr6':'III/283',
}


def truthy(x): return str(x).strip().lower() in {'true','1','yes','y'}

def native(v):
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,)): return None if not np.isfinite(v) else float(v)
    if isinstance(v,(np.bool_,)): return bool(v)
    if isinstance(v,bytes): return v.decode('utf-8','ignore')
    if np.ma.is_masked(v): return None
    return str(v) if not isinstance(v,(str,int,float,bool,type(None))) else v

def useful_columns(cols):
    keep=[]
    for c in cols:
        u0=c.upper()
        if any(k in u0 for k in ['RV','VRAD','HRV','VGAMMA','GAMMA','MJD','JD','DATE','YEAR','EPOCH','NOBS','N_RV','NRV','NUMBER','NAME','STAR','SOURCE','GAIA']):
            keep.append(c)
    return keep

def row_dict(row, cols):
    return {c:native(row[c]) for c in cols}

def query_one(label,cat,sid,ra,dec):
    viz=Vizier(columns=['**'],row_limit=-1)
    coord=SkyCoord(ra=ra*u.deg,dec=dec*u.deg,frame='icrs')
    last=None
    for attempt in range(3):
        try:
            tabs=viz.query_region(coord,radius=2*u.arcsec,catalog=cat)
            out=[]
            for key,tab in tabs.items():
                cols=list(tab.colnames)
                ucols=useful_columns(cols)
                sample=[]
                for row in tab[:200]:
                    sample.append(row_dict(row,ucols))
                out.append({'table':str(key),'n_rows':int(len(tab)),'columns':cols,'useful_columns':ucols,'sample_rows':sample})
            return {'source_id':sid,'label':label,'catalog':cat,'status':'matched' if out else 'no_match','tables':out}
        except Exception as e:
            last=repr(e); time.sleep(3*(attempt+1))
    return {'source_id':sid,'label':label,'catalog':cat,'status':'query_error','error':last,'tables':[]}

def main():
    c=pd.read_csv(CAND,dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy()
    c=c[~c.source_id.astype('int64').isin(EXCLUDE)].copy()
    audit=[]
    for j,r in c.reset_index(drop=True).iterrows():
        sid=int(r.source_id); ra=float(r.ra_deg); dec=float(r.dec_deg)
        print(f'[{j+1}/{len(c)}] {sid}',flush=True)
        for label,cat in CATALOGS.items():
            rec=query_one(label,cat,sid,ra,dec)
            audit.append(rec)
            print(' ',label,rec['status'],[(x['table'],x['n_rows']) for x in rec.get('tables',[])],flush=True)
    (OUT/'legacy_catalog_query_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    matched=[x for x in audit if x['status']=='matched']
    summary={
      'protocol':'LEGACY_CEPHEID_RV_OSC_SWEEP_FREEZE',
      'candidate_sources':int(len(c)),
      'catalog_families':list(CATALOGS.keys()),
      'matched_candidate_catalog_pairs':int(len(matched)),
      'matched_unique_sources':int(len(set(x['source_id'] for x in matched))),
      'matches':[{ 'source_id':x['source_id'],'label':x['label'],'catalog':x['catalog'],'tables':[(t['table'],t['n_rows']) for t in x['tables']] } for x in matched],
      'outcome_firewall':'No H I spectrum, H I velocity, H I residual, unblinded Outer-arm result, or Persistence prediction was read.'
    }
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
