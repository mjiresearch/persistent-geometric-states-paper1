#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
import Rbirth

OUT=Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial')
OUT.mkdir(parents=True,exist_ok=True)
MS_PATH=Path('data/external/sdss/dr20_minesweeper/minesweeper_v1.2.2.parquet')
RNG=np.random.default_rng(20260808)


def clean(d):
    need=['Age','Age_err','R_gal','X_gal','Y_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal','FeH','aFe']
    m=np.ones(len(d),bool)
    for c in need: m &= np.isfinite(pd.to_numeric(d[c],errors='coerce'))
    m &= d['Age'].between(0.05,14.5)
    m &= (d['Age_err']/d['Age']).between(0,0.5)
    m &= d['R_gal'].between(3.0,20.0)
    m &= d['Z_gal'].abs().le(8.0)
    if 'snr' in d.columns: m &= pd.to_numeric(d['snr'],errors='coerce').fillna(0).ge(20)
    q=d.loc[m].copy()
    q['absZ']=q['Z_gal'].abs()
    q['phi_deg']=(np.degrees(np.arctan2(q['Y_gal'],q['X_gal']))+360)%360
    q['R_bin_kpc']=np.floor(q['R_gal']/0.5)*0.5
    q['absZ_bin_kpc']=np.floor(q['absZ']/0.25)*0.25
    q['phi_bin_deg']=np.floor(q['phi_deg']/15)*15
    return q


def partial_resid(y, C):
    y=np.asarray(y,float); C=np.asarray(C,float)
    m=np.isfinite(y)&np.all(np.isfinite(C),axis=1)
    out=np.full(len(y),np.nan)
    if m.sum()<10: return out
    model=LinearRegression().fit(C[m],y[m])
    out[m]=y[m]-model.predict(C[m])
    return out


def perm_test(c,xcol,ycol,nperm=10000,partial=False):
    cols=[xcol,ycol,'R_bin_kpc','absZ_bin_kpc','age_median_gyr','FeH_median','aFe_median']
    d=c[cols].dropna().copy()
    if len(d)<20: return {'n_cells':int(len(d))}
    x=d[xcol].to_numpy(float); y=d[ycol].to_numpy(float)
    if partial:
        C=d[['age_median_gyr','FeH_median','aFe_median']].to_numpy(float)
        x=partial_resid(x,C); y=partial_resid(y,C)
    rho,p=spearmanr(x,y)
    groups=d.groupby(['R_bin_kpc','absZ_bin_kpc']).indices
    null=[]
    for _ in range(nperm):
        xp=x.copy()
        for idx in groups.values():
            idx=np.asarray(idx,int)
            if len(idx)>1: xp[idx]=RNG.permutation(xp[idx])
        rr,_=spearmanr(xp,y)
        if np.isfinite(rr): null.append(abs(float(rr)))
    null=np.asarray(null)
    pp=float((1+np.sum(null>=abs(rho)))/(1+len(null))) if len(null) else None
    return {'n_cells':int(len(d)),'rho':float(rho),'p_spearman':float(p),'p_perm_within_RZ':pp,
            'partial_controls':['age_median_gyr','FeH_median','aFe_median'] if partial else []}


def main():
    d=clean(pd.read_parquet(MS_PATH))
    grad=Rbirth.get_gradient('Anders23'); feh0=Rbirth.get_Feh0('Anders23')
    rb=np.asarray(Rbirth.get_Rb(age=d['Age'].to_numpy(float),feh=d['FeH'].to_numpy(float),gradientDF=grad,feh0DF=feh0),float)
    d['Rbirth_proxy_kpc']=rb
    d['deltaR_present_birth_kpc']=d['R_gal']-d['Rbirth_proxy_kpc']
    d['outward_present_gt1']=(d['deltaR_present_birth_kpc']>1).astype(float)
    d['inward_present_gt1']=(d['deltaR_present_birth_kpc']<-1).astype(float)
    d['inner_born_lt6']=(d['Rbirth_proxy_kpc']<6).astype(float)
    d=d[np.isfinite(d['Rbirth_proxy_kpc'])].copy()

    rows=[]
    key=['R_bin_kpc','absZ_bin_kpc','phi_bin_deg']
    for k,g in d.groupby(key,observed=True):
        if len(g)<20: continue
        rows.append({
            'R_bin_kpc':float(k[0]),'absZ_bin_kpc':float(k[1]),'phi_bin_deg':float(k[2]),'n':int(len(g)),
            'Rbirth_median_kpc':float(g['Rbirth_proxy_kpc'].median()),
            'deltaR_present_birth_median_kpc':float(g['deltaR_present_birth_kpc'].median()),
            'outward_fraction_gt1':float(g['outward_present_gt1'].mean()),
            'inward_fraction_gt1':float(g['inward_present_gt1'].mean()),
            'inner_born_fraction_lt6':float(g['inner_born_lt6'].mean()),
            'age_median_gyr':float(g['Age'].median()),'FeH_median':float(g['FeH'].median()),'aFe_median':float(g['aFe'].median()),
            'Vr_median_kms':float(g['Vr_gal'].median()),'Vphi_median_kms':float(g['Vphi_gal'].median()),'Vz_median_kms':float(g['Vz_gal'].median()),
        })
    c=pd.DataFrame(rows)
    for col in ['Rbirth_median_kpc','deltaR_present_birth_median_kpc','outward_fraction_gt1','inward_fraction_gt1','inner_born_fraction_lt6',
                'age_median_gyr','FeH_median','aFe_median','Vr_median_kms','Vphi_median_kms','Vz_median_kms']:
        c[col+'_anom']=c[col]-c.groupby(['R_bin_kpc','absZ_bin_kpc'])[col].transform('median')

    preds=['Rbirth_median_kpc_anom','deltaR_present_birth_median_kpc_anom','outward_fraction_gt1_anom','inward_fraction_gt1_anom','inner_born_fraction_lt6_anom']
    outs=['Vr_median_kms_anom','Vphi_median_kms_anom','Vz_median_kms_anom']
    tests={}
    for p in preds:
        tests[p]={}
        for y in outs:
            tests[p][y]={'unadjusted':perm_test(c,p,y,partial=False),'age_chem_adjusted':perm_test(c,p,y,partial=True)}

    age_tests={y:perm_test(c,'age_median_gyr_anom',y,partial=False) for y in outs}

    selected=['source_id','R_gal','Z_gal','phi_deg','Rbirth_proxy_kpc','deltaR_present_birth_kpc','outward_present_gt1','inward_present_gt1',
              'Age','FeH','aFe','Vr_gal','Vphi_gal','Vz_gal']
    d[selected].to_csv(OUT/'mwm_rbirth_star_history.csv.gz',index=False,compression='gzip')
    c.to_csv(OUT/'mwm_rbirth_spatial_cells.csv',index=False)
    report={
        'analysis_name':'Milky Way Stage 4D MWM-wide inferred birth-radius spatial history screen',
        'quality_rows_before_rbirth':int(len(clean(pd.read_parquet(MS_PATH)))),
        'rows_with_finite_rbirth':int(len(d)),
        'cells_n_ge20':int(len(c)),
        'rbirth_method':'Ratcliffe public Rbirth package with Anders23 gradient/central metallicity applied to MWM MINESweeper Age and FeH',
        'migration_definition':'R_now - Rbirth_proxy, used to avoid circular dependence on present velocity/orbital actions',
        'tests':tests,'age_only_reference':age_tests,
        'guardrail':('The Ratcliffe relation is calibrated on APOGEE/Anders-age data and is being transferred here to the MINESweeper age/metallicity scale; this is an exploratory source-history proxy, not a validated cross-survey birth radius. Because Rbirth is constructed from age and FeH, age/chemistry-adjusted tests are primary. The kinematic outcomes are streaming residuals, not yet a gravitational force residual.')
    }
    (OUT/'stage4d_summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
# workflow trigger 2026-08-08
