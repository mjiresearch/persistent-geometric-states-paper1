#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression

OUT=Path('data/persistence_history/milky_way_stage4f_common_grid_young_tracer')
OUT.mkdir(parents=True,exist_ok=True)
SRC=Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial/mwm_rbirth_star_history.csv.gz')
YNG=Path('data/persistence_history/milky_way_stage4e_young_tracer/young_hot_tracer_phase_space.csv.gz')
RNG=np.random.default_rng(20260808)

PRED=['Rbirth_anom','deltaR_birth_anom','outward_gt1_frac_anom','inward_gt1_frac_anom','innerborn_lt6_frac_anom']
CTRL=['age_anom','FeH_anom','aFe_anom']
OUTCOMES=['Vr_young_anom','Vphi_young_anom','Vz_young_anom','acirc_young_anom']


def residualize(v,C):
    v=np.asarray(v,float); C=np.asarray(C,float); m=np.isfinite(v)&np.all(np.isfinite(C),axis=1); out=np.full(len(v),np.nan)
    if m.sum()<10:return out
    f=LinearRegression().fit(C[m],v[m]);out[m]=v[m]-f.predict(C[m]);return out

def corr(x,y):
    m=np.isfinite(x)&np.isfinite(y)
    if m.sum()<10:return np.nan,np.nan
    r,p=spearmanr(np.asarray(x)[m],np.asarray(y)[m]);return float(r),float(p)

def family_perm(d,preds,outcomes,adjusted,nperm=20000):
    q=d.dropna(subset=preds+outcomes+CTRL+['R_bin','Z_bin']).copy()
    if len(q)<10:return {'n_cells':int(len(q)),'tests':{}}
    X=q[preds].to_numpy(float);Y=q[outcomes].to_numpy(float);C=q[CTRL].to_numpy(float)
    if adjusted:
        X=np.column_stack([residualize(X[:,i],C) for i in range(X.shape[1])]);Y=np.column_stack([residualize(Y[:,j],C) for j in range(Y.shape[1])])
    obs=np.empty((len(preds),len(outcomes))); ps=np.empty_like(obs)
    for i in range(len(preds)):
        for j in range(len(outcomes)):obs[i,j],ps[i,j]=corr(X[:,i],Y[:,j])
    counts=np.zeros_like(obs,int);maxcounts=np.zeros_like(obs,int);groups=q.groupby(['R_bin','Z_bin']).indices;valid=0
    for _ in range(nperm):
        pi=np.arange(len(q))
        for inds in groups.values():
            inds=np.asarray(inds,int)
            if len(inds)>1:pi[inds]=RNG.permutation(inds)
        vals=np.empty_like(obs)
        for i in range(len(preds)):
            for j in range(len(outcomes)):vals[i,j],_=corr(X[pi,i],Y[:,j])
        if not np.any(np.isfinite(vals)):continue
        valid+=1;av=np.abs(vals);ao=np.abs(obs);counts+=np.nan_to_num(av>=ao,nan=False);mx=np.nanmax(av);maxcounts+=np.nan_to_num(mx>=ao,nan=False)
    tests={}
    for i,p in enumerate(preds):
        tests[p]={}
        for j,o in enumerate(outcomes):tests[p][o]={'rho':float(obs[i,j]) if np.isfinite(obs[i,j]) else None,'p_spearman':float(ps[i,j]) if np.isfinite(ps[i,j]) else None,'p_perm_within_RZ':float((counts[i,j]+1)/(valid+1)) if valid else None,'p_maxT_all_tests':float((maxcounts[i,j]+1)/(valid+1)) if valid else None}
    return {'n_cells':int(len(q)),'adjusted':adjusted,'n_permutations':valid,'tests':tests}


def bins(df,Rw,Zw,Pw,Rcol,Zcol,Pcol):
    d=df.copy();d['R_bin']=np.floor(pd.to_numeric(d[Rcol],errors='coerce')/Rw)*Rw;d['Z_bin']=np.floor(pd.to_numeric(d[Zcol],errors='coerce').abs()/Zw)*Zw;d['P_bin']=np.floor(pd.to_numeric(d[Pcol],errors='coerce')/Pw)*Pw;return d

def source_cells(src,Rw,Zw,Pw,min_n=30):
    s=bins(src,Rw,Zw,Pw,'R_gal','Z_gal','phi_deg');s=s[s.R_gal.between(4,13)&s.Z_gal.abs().le(2)].copy();s['innerborn']=(s.Rbirth_proxy_kpc<6).astype(float)
    rows=[]
    for k,g in s.groupby(['R_bin','Z_bin','P_bin'],observed=True):
        if len(g)<min_n:continue
        rows.append({'R_bin':float(k[0]),'Z_bin':float(k[1]),'P_bin':float(k[2]),'n_source':int(len(g)),'Rbirth':float(g.Rbirth_proxy_kpc.median()),'deltaR_birth':float(g.deltaR_present_birth_kpc.median()),'outward_gt1_frac':float(g.outward_present_gt1.mean()),'inward_gt1_frac':float(g.inward_present_gt1.mean()),'innerborn_lt6_frac':float(g.innerborn.mean()),'age':float(g.Age.median()),'FeH':float(g.FeH.median()),'aFe':float(g.aFe.median())})
    c=pd.DataFrame(rows)
    if c.empty:return c
    for col in ['Rbirth','deltaR_birth','outward_gt1_frac','inward_gt1_frac','innerborn_lt6_frac','age','FeH','aFe']:
        c[col+'_anom']=c[col]-c.groupby(['R_bin','Z_bin'])[col].transform('median')
    return c

def young_cells(y,Rw,Zw,Pw,min_n=5,cold=False):
    d=y.copy()
    if cold:d=d[d.Vphi_gal_kms.between(190,250)&d.Vr_gal_kms.abs().le(80)&d.Vz_gal_kms.abs().le(80)].copy()
    d=bins(d,Rw,Zw,Pw,'R_gal_kpc','Z_gal_kpc','phi_deg');d=d[d.R_gal_kpc.between(4,13)&d.Z_gal_kpc.abs().le(2)].copy()
    rows=[]
    for k,g in d.groupby(['R_bin','Z_bin','P_bin'],observed=True):
        if len(g)<min_n:continue
        vp=g.Vphi_gal_kms.to_numpy(float);R=g.R_gal_kpc.to_numpy(float)
        rows.append({'R_bin':float(k[0]),'Z_bin':float(k[1]),'P_bin':float(k[2]),'n_young':int(len(g)),'Vr_young':float(g.Vr_gal_kms.median()),'Vphi_young':float(g.Vphi_gal_kms.median()),'Vz_young':float(g.Vz_gal_kms.median()),'acirc_young':float(np.nanmedian(vp*vp/R))})
    c=pd.DataFrame(rows)
    if c.empty:return c
    for col in ['Vr_young','Vphi_young','Vz_young','acirc_young']:c[col+'_anom']=c[col]-c.groupby(['R_bin','Z_bin'])[col].transform('median')
    return c

def run_grid(src,yng,Rw,Zw,Pw):
    sc=source_cells(src,Rw,Zw,Pw,30);results={}
    for label,cold in [('general',False),('cold',True)]:
        yc=young_cells(yng,Rw,Zw,Pw,5,cold);j=sc.merge(yc,on=['R_bin','Z_bin','P_bin'],how='inner');j.to_csv(OUT/f'grid_R{Rw}_Z{Zw}_P{Pw}_{label}_joined.csv',index=False)
        results[label]={'source_cells':int(len(sc)),'young_cells':int(len(yc)),'joined_cells':int(len(j)),'R_range':[float(j.R_bin.min()),float(j.R_bin.max())] if len(j) else None,'unadjusted':family_perm(j,PRED,OUTCOMES,False,20000),'age_chem_adjusted':family_perm(j,PRED,OUTCOMES,True,20000),'age_only':family_perm(j,['age_anom'],OUTCOMES,False,20000)}
    return results

def main():
    src=pd.read_csv(SRC,low_memory=False);yng=pd.read_csv(YNG,low_memory=False)
    configs=[(1.0,0.5,30.0),(1.0,0.5,45.0)]
    runs={}
    for Rw,Zw,Pw in configs:runs[f'R{Rw}_Z{Zw}_P{Pw}']=run_grid(src,yng,Rw,Zw,Pw)
    report={'analysis_name':'Milky Way Stage 4F coarsened common-grid independent young-tracer test','source_star_rows':int(len(src)),'young_general_star_rows':int(len(yng)),'primary_grid':{'R_kpc':1.0,'absZ_kpc':0.5,'phi_deg':30.0},'robustness_grid':{'R_kpc':1.0,'absZ_kpc':0.5,'phi_deg':45.0},'runs':runs,'decision_rule':'A compelling precursor should have the same directional sign in general and cold samples, survive source age/FeH/aFe adjustment, within-RZ permutation and family-wise maxT correction on the primary grid, and not reverse on the 45-degree robustness grid.','guardrail':'This is independent-tracer kinematics and a circular-acceleration proxy, not yet a Jeans-derived local gravitational force residual. Birth radii are transferred Ratcliffe proxies on the MWM age/FeH scale; standard bar/spiral structure can correlate source population history and young-star streaming.'}
    (OUT/'stage4f_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
