#!/usr/bin/env python3
"""Fast outcome-blind batch XMatch of purity-qualified OSC Cepheid candidates.

This is a discovery-only acceleration of the already frozen legacy RV sweep.
It does not read any H I outcome or Persistence prediction and does not change
any acceptance threshold.
"""
from pathlib import Path
import json
import pandas as pd
from astropy.table import Table
import astropy.units as u
from astroquery.xmatch import XMatch

HERE=Path(__file__).resolve().parent
CAND=HERE/'osc_rv_target_rank'/'classification_audit'/'osc_single_pass_candidates_classification_audit.csv'
OUT=HERE/'osc_rv_target_rank'/'legacy_rv_sweep_fast'
OUT.mkdir(parents=True,exist_ok=True)
EXCLUDE={2072235820984829312}

# Position-bearing tables for the frozen catalog families.
TABLES={
 'gorynya_stars':'vizier:III/229/stars',
 'borgniet_stars':'vizier:J/A+A/631/A37/tablea1',
 'crav_table2':'vizier:J/AJ/150/13/table2',
 'crav_table6':'vizier:J/AJ/150/13/table6',
 'cruz_reyes_astrometry':'vizier:J/A+A/672/A85/table10',
 'rave_dr6':'vizier:III/283/ravedr6',
}

def truthy(x): return str(x).strip().lower() in {'true','1','yes','y'}

def main():
    c=pd.read_csv(CAND,dtype={'source_id':'Int64'})
    c=c[c.target_quality_pass.map(truthy)].copy()
    c=c[~c.source_id.astype('int64').isin(EXCLUDE)].copy()
    base=c[['source_id','ra_deg','dec_deg']].copy()
    t=Table.from_pandas(base)
    summary={'protocol':'LEGACY_CEPHEID_RV_OSC_SWEEP_FREEZE',
             'stage':'FAST_BATCH_XMATCH_DISCOVERY_ONLY',
             'candidate_sources':int(len(base)),
             'catalogs':{},
             'matched_unique_sources':[],
             'outcome_firewall':'No H I spectrum, H I velocity, H I residual, unblinded Outer-arm result, or Persistence prediction was read.'}
    all_sids=set()
    for label,cat in TABLES.items():
        rec={'catalog':cat}
        try:
            m=XMatch.query(cat1=t,cat2=cat,max_distance=2*u.arcsec,
                           colRA1='ra_deg',colDec1='dec_deg')
            df=m.to_pandas() if len(m) else pd.DataFrame()
            df.to_csv(OUT/f'{label}_xmatch.csv',index=False)
            rec['status']='matched' if len(df) else 'no_match'
            rec['rows']=int(len(df))
            sidcol='source_id' if 'source_id' in df.columns else None
            if sidcol:
                sids=sorted({int(x) for x in df[sidcol].dropna().tolist()})
            else:
                sids=[]
            rec['source_ids']=sids
            all_sids.update(sids)
            rec['columns']=list(df.columns)
        except Exception as e:
            rec={'catalog':cat,'status':'query_error','error':repr(e),'rows':0,'source_ids':[]}
        summary['catalogs'][label]=rec
        print(label,rec,flush=True)
    summary['matched_unique_sources']=sorted(all_sids)
    summary['matched_unique_source_count']=len(all_sids)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
