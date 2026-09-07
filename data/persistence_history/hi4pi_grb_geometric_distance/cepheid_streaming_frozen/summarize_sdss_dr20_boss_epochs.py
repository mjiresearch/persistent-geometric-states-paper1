#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'osc_rv_target_rank'/'sdss_dr20_recovery'
data=json.load(open(OUT/'sdss_dr20_boss_fast_probe.json'))
rows=[]
for r in data:
    p=r.get('pipelines_boss',{}).get('data',{})
    boss=p.get('boss',[]) if isinstance(p,dict) else []
    daily=[x for x in boss if x.get('coadd')=='daily']
    mjds=sorted({int(x['mjd']) for x in daily if x.get('mjd') is not None})
    rows.append({'source_id':int(r['source_id']),'sdss_id':int(r['sdss_id']),
                 'n_daily_products':len(daily),'n_distinct_daily_mjd':len(mjds),'daily_mjds':mjds,
                 'meets_frozen_8_epoch_requirement':len(mjds)>=8,
                 'astra_pipelines':p.get('astra_pipelines',[]) if isinstance(p,dict) else []})
summary={'protocol':'SDSS_DR20_OSC_RV_RECOVERY_FREEZE','stage':'EPOCH_SUPPORT_ONLY',
         'matched_sources':len(rows),'sources_meeting_8_epoch_requirement':sum(x['meets_frozen_8_epoch_requirement'] for x in rows),
         'rows':rows,
         'outcome_firewall':'No RV values, H I spectrum, H I velocity, H I residual, GRB comparison outcome, or Persistence prediction was used in this epoch-count gate.'}
json.dump(summary,open(OUT/'sdss_dr20_epoch_support_summary.json','w'),indent=2)
print(json.dumps(summary,indent=2))
