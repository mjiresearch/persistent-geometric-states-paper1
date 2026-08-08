#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
import Rbirth

OUT = Path('data/persistence_history/milky_way_stage4b_guiding_migration')
OUT.mkdir(parents=True, exist_ok=True)
MC = Path('data/persistence_history/milky_way_stage3c_interaction/mcmillan_interaction_screen.csv')
MG = Path('data/persistence_history/milky_way_stage3c_interaction/mcgaugh_interaction_screen.csv')
RNG = np.random.default_rng(20260807)


def detrend(r, y):
    r=np.asarray(r,float); y=np.asarray(y,float)
    m=np.isfinite(r)&np.isfinite(y)
    out=np.full(len(y),np.nan)
    if m.sum()<6: return out
    c=np.polyfit(r[m], y[m], 2)
    out[m]=y[m]-np.polyval(c,r[m])
    return out


def corr(r,x,y):
    r=np.asarray(r,float); x=np.asarray(x,float); y=np.asarray(y,float)
    m=np.isfinite(r)&np.isfinite(x)&np.isfinite(y)
    r,x,y=r[m],x[m],y[m]
    if len(r)<6: return {'n':int(len(r))}
    a=spearmanr(x,y)
    xd,yd=detrend(r,x),detrend(r,y)
    b=spearmanr(xd,yd)
    o=np.argsort(r)
    c=spearmanr(np.diff(x[o]),np.diff(y[o])) if len(r)>=7 else (np.nan,np.nan)
    return {'n':int(len(r)), 'rho_raw':float(a.statistic),'p_raw':float(a.pvalue),
            'rho_detrended':float(b.statistic),'p_detrended':float(b.pvalue),
            'rho_first_difference':float(c.statistic),'p_first_difference':float(c.pvalue)}


def maxT(r,d,target,predictors,nperm=20000):
    y=detrend(r,d[target].to_numpy(float)); yr=rankdata(y).astype(float); yr=(yr-yr.mean())/yr.std(ddof=0)
    X=[]
    for p in predictors:
        z=detrend(r,d[p].to_numpy(float)); zr=rankdata(z).astype(float); zr=(zr-zr.mean())/zr.std(ddof=0); X.append(zr)
    X=np.column_stack(X); obs=np.abs((X*yr[:,None]).mean(axis=0))
    cnt=np.zeros(len(predictors),int); mcnt=np.zeros(len(predictors),int)
    for _ in range(nperm):
        yp=RNG.permutation(yr); vals=np.abs((X*yp[:,None]).mean(axis=0))
        cnt += vals>=obs-1e-12; mcnt += vals.max()>=obs-1e-12
    return {p:{'abs_rho_detrended':float(obs[i]),'p_perm':float((cnt[i]+1)/(nperm+1)),
               'p_maxT':float((mcnt[i]+1)/(nperm+1))} for i,p in enumerate(predictors)}


def main():
    ap=Rbirth.load_apogee().copy()
    rb=np.asarray(Rbirth.get_Rb(age=ap['age'],feh=ap['feh'],gradientDF=Rbirth.get_gradient('Anders23'),feh0DF=Rbirth.get_Feh0('Anders23')),float)
    ap['Rbirth_kpc']=rb
    ap['Rnow_kpc']=pd.to_numeric(ap['r'],errors='coerce')
    ap['Rguide_kpc']=pd.to_numeric(ap['rguide'],errors='coerce')
    ap['age_gyr']=pd.to_numeric(ap['age'],errors='coerce')
    ap['feh_used']=pd.to_numeric(ap['feh'],errors='coerce')
    ap['deltaR_now_kpc']=ap['Rnow_kpc']-ap['Rbirth_kpc']
    ap['deltaR_guide_kpc']=ap['Rguide_kpc']-ap['Rbirth_kpc']
    ap['abs_deltaR_guide_kpc']=ap['deltaR_guide_kpc'].abs()
    ap['outward_guide_gt0p5']=(ap['deltaR_guide_kpc']>0.5).astype(float)
    ap['inward_guide_gt0p5']=(ap['deltaR_guide_kpc']<-0.5).astype(float)
    ap['outward_guide_gt1']=(ap['deltaR_guide_kpc']>1.0).astype(float)
    ap['inward_guide_gt1']=(ap['deltaR_guide_kpc']<-1.0).astype(float)
    ap['inner_born_lt6']=(ap['Rbirth_kpc']<6.0).astype(float)
    ap['guide_history_distance_time']=ap['abs_deltaR_guide_kpc']*ap['age_gyr']
    ap['epicycle_offset_kpc']=ap['Rnow_kpc']-ap['Rguide_kpc']
    good=np.isfinite(ap[['Rbirth_kpc','Rnow_kpc','Rguide_kpc','age_gyr']]).all(axis=1)
    ap=ap.loc[good & ap['Rnow_kpc'].between(4.75,10.75)].copy()
    ap['R_bin_kpc']=(np.floor((ap['Rnow_kpc']+0.25)/0.5)*0.5).clip(5.0,10.5)

    rows=[]
    for r,g in ap.groupby('R_bin_kpc'):
        rows.append({
            'R_kpc':float(r),'n_stars':int(len(g)),
            'Rbirth_median_kpc':float(g.Rbirth_kpc.median()),
            'Rguide_median_kpc':float(g.Rguide_kpc.median()),
            'deltaR_guide_median_kpc':float(g.deltaR_guide_kpc.median()),
            'abs_deltaR_guide_median_kpc':float(g.abs_deltaR_guide_kpc.median()),
            'outward_guide_fraction_gt0p5':float(g.outward_guide_gt0p5.mean()),
            'inward_guide_fraction_gt0p5':float(g.inward_guide_gt0p5.mean()),
            'outward_guide_fraction_gt1':float(g.outward_guide_gt1.mean()),
            'inward_guide_fraction_gt1':float(g.inward_guide_gt1.mean()),
            'inner_born_fraction_lt6':float(g.inner_born_lt6.mean()),
            'guide_history_distance_time_median':float(g.guide_history_distance_time.median()),
            'epicycle_offset_median_kpc':float(g.epicycle_offset_kpc.median()),
            'age_median_gyr':float(g.age_gyr.median())})
    radial=pd.DataFrame(rows).sort_values('R_kpc').reset_index(drop=True)
    predictors=['Rbirth_median_kpc','deltaR_guide_median_kpc','abs_deltaR_guide_median_kpc',
                'outward_guide_fraction_gt0p5','inward_guide_fraction_gt0p5',
                'outward_guide_fraction_gt1','inward_guide_fraction_gt1','inner_born_fraction_lt6',
                'guide_history_distance_time_median','age_median_gyr']
    results={}
    for label,path in [('mcmillan17_eilers',MC),('mcgaugh2019',MG)]:
        q=pd.read_csv(path)[['R_kpc','chi_interaction']]
        j=radial.merge(q,on='R_kpc',how='inner')
        j.to_csv(OUT/f'{label}_guiding_migration_join.csv',index=False)
        rr=j.R_kpc.to_numpy(float)
        results[label]={'n_bins':int(len(j)),'correlations':{p:corr(rr,j[p],j.chi_interaction) for p in predictors},
                        'maxT_permutation':maxT(rr,j,'chi_interaction',predictors)}
    radial.to_csv(OUT/'guiding_migration_radial_profile.csv',index=False)
    ap[['APOGEE_ID','GAIAEDR3_SOURCE_ID','Rnow_kpc','Rguide_kpc','Rbirth_kpc','deltaR_now_kpc','deltaR_guide_kpc','age_gyr','feh_used']].to_csv(OUT/'guiding_migration_star_sample.csv.gz',index=False,compression='gzip')
    report={'analysis_name':'Milky Way Stage 4B guiding-radius birth-migration interaction screen',
            'input_rows':int(len(Rbirth.load_apogee())),'usable_rows':int(len(ap)),
            'migration_definition':'primary migration = Rguide - Rbirth; current R is used only to assign the present spatial radial bin',
            'predictors':predictors,'results':results,
            'interpretation_rule':'Require consistency across baryonic decompositions and prioritize detrended, first-difference, and maxT-corrected permutation statistics. A signal in only one decomposition is not accepted as persistence evidence.'}
    (OUT/'stage4b_summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
