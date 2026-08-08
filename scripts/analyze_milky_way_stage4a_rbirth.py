#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
import Rbirth

OUT = Path('data/persistence_history/milky_way_stage4a_rbirth')
OUT.mkdir(parents=True, exist_ok=True)
MC = Path('data/persistence_history/milky_way_stage3c_interaction/mcmillan_interaction_screen.csv')
MG = Path('data/persistence_history/milky_way_stage3c_interaction/mcgaugh_interaction_screen.csv')
RNG = np.random.default_rng(20260807)


def detrend(r, y):
    r=np.asarray(r,float); y=np.asarray(y,float)
    m=np.isfinite(r)&np.isfinite(y)
    out=np.full(len(y),np.nan)
    if m.sum() < 6: return out
    c=np.polyfit(r[m],y[m],2)
    out[m]=y[m]-np.polyval(c,r[m])
    return out


def corr(r,x,y):
    r=np.asarray(r,float); x=np.asarray(x,float); y=np.asarray(y,float)
    m=np.isfinite(r)&np.isfinite(x)&np.isfinite(y)
    r,x,y=r[m],x[m],y[m]
    if len(r)<6: return {'n':int(len(r))}
    raw=spearmanr(x,y)
    xd=detrend(r,x); yd=detrend(r,y)
    det=spearmanr(xd,yd)
    o=np.argsort(r)
    dif=spearmanr(np.diff(x[o]),np.diff(y[o])) if len(r)>=7 else (np.nan,np.nan)
    return {'n':int(len(r)),'rho_raw':float(raw.statistic),'p_raw':float(raw.pvalue),
            'rho_detrended':float(det.statistic),'p_detrended':float(det.pvalue),
            'rho_first_difference':float(dif.statistic),'p_first_difference':float(dif.pvalue)}


def maxT(r, d, target, predictors, nperm=20000):
    y=detrend(r,d[target].to_numpy(float)); yr=rankdata(y).astype(float); yr=(yr-yr.mean())/yr.std(ddof=0)
    X=[]
    for p in predictors:
        z=detrend(r,d[p].to_numpy(float)); q=rankdata(z).astype(float); q=(q-q.mean())/q.std(ddof=0); X.append(q)
    X=np.column_stack(X); obs=np.abs((X*yr[:,None]).mean(axis=0)); counts=np.zeros(len(predictors),int); maxcounts=np.zeros(len(predictors),int)
    for _ in range(nperm):
        yp=RNG.permutation(yr); vals=np.abs((X*yp[:,None]).mean(axis=0)); counts += vals>=obs-1e-12; maxcounts += vals.max()>=obs-1e-12
    return {p:{'abs_rho_detrended':float(obs[i]),'p_perm':float((counts[i]+1)/(nperm+1)),
               'p_maxT':float((maxcounts[i]+1)/(nperm+1))} for i,p in enumerate(predictors)}


def main():
    ap=Rbirth.load_apogee().copy()
    grad=Rbirth.get_gradient('Anders23')
    feh0=Rbirth.get_Feh0('Anders23')
    rb=np.asarray(Rbirth.get_Rb(age=ap['age'],feh=ap['feh'],gradientDF=grad,feh0DF=feh0),float)
    ap['Rbirth_kpc']=rb
    ap['Rnow_kpc']=pd.to_numeric(ap['r'],errors='coerce')
    ap['age_gyr']=pd.to_numeric(ap['age'],errors='coerce')
    ap['feh_used']=pd.to_numeric(ap['feh'],errors='coerce')
    ap['migration_delta_r_kpc']=ap['Rnow_kpc']-ap['Rbirth_kpc']
    ap['migration_abs_delta_r_kpc']=ap['migration_delta_r_kpc'].abs()
    ap['outward_migrator']=(ap['migration_delta_r_kpc']>0.5).astype(float)
    ap['inward_migrator']=(ap['migration_delta_r_kpc']<-0.5).astype(float)
    ap['inner_born_lt6']=(ap['Rbirth_kpc']<6.0).astype(float)
    ap['history_distance_time_proxy']=ap['migration_abs_delta_r_kpc']*ap['age_gyr']
    ap=ap[np.isfinite(ap['Rbirth_kpc'])&np.isfinite(ap['Rnow_kpc'])&np.isfinite(ap['age_gyr'])].copy()
    ap=ap[ap['Rnow_kpc'].between(4.75,10.75)].copy()
    ap['R_bin_kpc']=(np.floor((ap['Rnow_kpc']+0.25)/0.5)*0.5).clip(5.0,10.5)

    rows=[]
    for r,g in ap.groupby('R_bin_kpc'):
        rows.append({'R_kpc':float(r),'n_stars':int(len(g)),
                     'Rbirth_median_kpc':float(g.Rbirth_kpc.median()),
                     'migration_delta_r_median_kpc':float(g.migration_delta_r_kpc.median()),
                     'migration_abs_delta_r_median_kpc':float(g.migration_abs_delta_r_kpc.median()),
                     'outward_fraction_gt0p5':float(g.outward_migrator.mean()),
                     'inward_fraction_gt0p5':float(g.inward_migrator.mean()),
                     'inner_born_fraction_lt6':float(g.inner_born_lt6.mean()),
                     'age_median_gyr':float(g.age_gyr.median()),
                     'history_distance_time_median':float(g.history_distance_time_proxy.median())})
    radial=pd.DataFrame(rows).sort_values('R_kpc').reset_index(drop=True)

    predictors=['Rbirth_median_kpc','migration_delta_r_median_kpc','migration_abs_delta_r_median_kpc',
                'outward_fraction_gt0p5','inward_fraction_gt0p5','inner_born_fraction_lt6','age_median_gyr',
                'history_distance_time_median']
    results={}
    for label,path in [('mcmillan17_eilers',MC),('mcgaugh2019',MG)]:
        q=pd.read_csv(path)[['R_kpc','chi_interaction']].copy()
        j=radial.merge(q,on='R_kpc',how='inner')
        j.to_csv(OUT/f'{label}_rbirth_interaction_join.csv',index=False)
        r=j.R_kpc.to_numpy(float)
        results[label]={'n_bins':int(len(j)),'R_range_kpc':[float(j.R_kpc.min()),float(j.R_kpc.max())],
                        'correlations':{p:corr(r,j[p],j['chi_interaction']) for p in predictors},
                        'maxT_permutation':maxT(r,j,'chi_interaction',predictors)}

    keep=['Rnow_kpc','Rbirth_kpc','migration_delta_r_kpc','migration_abs_delta_r_kpc','age_gyr','feh_used',
          'outward_migrator','inward_migrator','inner_born_lt6','history_distance_time_proxy']
    extra=[c for c in ['vphi','ecc','zmax','rguid','source_id','APOGEE_ID'] if c in ap.columns]
    ap[keep+extra].to_csv(OUT/'ratcliffe_rbirth_star_sample.csv.gz',index=False,compression='gzip')
    radial.to_csv(OUT/'ratcliffe_rbirth_radial_history_profile.csv',index=False)

    report={'analysis_name':'Milky Way Stage 4A public birth-radius and migration-history screen',
            'rbirth_source':'Bridget Ratcliffe public Rbirth package; Anders23 gradient and central metallicity',
            'input_apogee_rows':int(len(Rbirth.load_apogee())), 'usable_rows_4p75_to_10p75':int(len(ap)),
            'input_columns':[str(c) for c in Rbirth.load_apogee().columns],
            'history_predictors':predictors,'results':results,
            'guardrail':('Rbirth is inferred from age and [Fe/H], not a directly observed trajectory. This Stage 4A screen uses radial summaries, so shared radial structure remains a major confounder. Detrended, first-difference and maxT permutation results carry the most weight. A decisive test still requires a spatial force-residual map and independently reconstructed time-resolved source trajectories/currents.')}
    (OUT/'stage4a_summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
