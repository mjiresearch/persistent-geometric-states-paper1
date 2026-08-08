#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

OUT=Path('data/persistence_history/milky_way_stage4g_young_rotation_residual'); OUT.mkdir(parents=True,exist_ok=True)
YNG=Path('data/persistence_history/milky_way_stage4e_young_tracer/young_hot_tracer_phase_space.csv.gz')
HIST=Path('data/persistence_history/milky_way_stage4b_guiding_migration/guiding_migration_radial_profile.csv')
MC=Path('data/persistence_history/milky_way_stage3c_interaction/mcmillan_interaction_screen.csv')
MG=Path('data/persistence_history/milky_way_stage3c_interaction/mcgaugh_interaction_screen.csv')
RNG=np.random.default_rng(20260808)
PRED=['Rbirth_median_kpc','deltaR_guide_median_kpc','abs_deltaR_guide_median_kpc','outward_guide_fraction_gt1','inward_guide_fraction_gt1','inner_born_fraction_lt6','guide_history_distance_time_median','age_median_gyr']

def detrend(r,y):
    r=np.asarray(r,float);y=np.asarray(y,float);m=np.isfinite(r)&np.isfinite(y);out=np.full(len(y),np.nan)
    if m.sum()<6:return out
    c=np.polyfit(r[m],y[m],2);out[m]=y[m]-np.polyval(c,r[m]);return out

def stats(r,x,y):
    r=np.asarray(r,float);x=np.asarray(x,float);y=np.asarray(y,float);m=np.isfinite(r)&np.isfinite(x)&np.isfinite(y);r,x,y=r[m],x[m],y[m]
    if len(r)<6:return {'n':int(len(r))}
    rr,pp=spearmanr(x,y);xd=detrend(r,x);yd=detrend(r,y);rd,pd=spearmanr(xd,yd);o=np.argsort(r);rf,pf=spearmanr(np.diff(x[o]),np.diff(y[o]))
    return {'n':int(len(r)),'rho_raw':float(rr),'p_raw':float(pp),'rho_detrended':float(rd),'p_detrended':float(pd),'rho_first_difference':float(rf),'p_first_difference':float(pf)}
def maxT(r,d,target,nperm=20000):
    r=np.asarray(r,float); y=detrend(r,d[target].to_numpy(float)); X=np.column_stack([detrend(r,d[p].to_numpy(float)) for p in PRED]);
    yr=rankdata(y);yr=(yr-yr.mean())/yr.std(ddof=0);XR=[]
    for j in range(X.shape[1]):
        z=rankdata(X[:,j]);z=(z-z.mean())/z.std(ddof=0);XR.append(z)
    XR=np.column_stack(XR);obs=np.abs((XR*yr[:,None]).mean(axis=0));counts=np.zeros(len(PRED),int);mxcounts=np.zeros(len(PRED),int)
    for _ in range(nperm):
        yp=RNG.permutation(yr);v=np.abs((XR*yp[:,None]).mean(axis=0));counts+=v>=obs;mxcounts+=v.max()>=obs
    return {p:{'abs_rho_detrended':float(obs[i]),'p_perm':float((counts[i]+1)/(nperm+1)),'p_maxT':float((mxcounts[i]+1)/(nperm+1))} for i,p in enumerate(PRED)}
def rotation_profile(d,cold=False):
    q=d.copy()
    if cold:q=q[q.Vphi_gal_kms.between(190,250)&q.Vr_gal_kms.abs().le(80)&q.Vz_gal_kms.abs().le(80)].copy()
    q=q[q.R_gal_kpc.between(4.75,10.75)&q.Z_gal_kpc.abs().le(1.0)].copy();q['R_kpc']=np.floor((q.R_gal_kpc+0.25)/0.5)*0.5
    rows=[]
    for r,g in q.groupby('R_kpc'):
        if len(g)<30:continue
        v=g.Vphi_gal_kms.to_numpy(float); boot=[]
        for _ in range(1000):boot.append(float(np.median(RNG.choice(v,size=len(v),replace=True))))
        rows.append({'R_kpc':float(r),'n_young':int(len(g)),'Vphi_young_median_kms':float(np.median(v)),'Vphi_young_bootstrap_se_kms':float(np.std(boot,ddof=1)),'Vr_young_median_kms':float(g.Vr_gal_kms.median()),'Vz_young_median_kms':float(g.Vz_gal_kms.median())})
    return pd.DataFrame(rows).sort_values('R_kpc')
def analyze(label,prof,hist,bary):
    j=hist.merge(prof,on='R_kpc',how='inner').merge(bary,on='R_kpc',how='inner')
    if label.startswith('mcmillan'):vbar=j.Vbar_mcmillan17_kms.to_numpy(float)
    else:vbar=j.Vbar_mcgaugh_kms.to_numpy(float)
    vo=j.Vphi_young_median_kms.to_numpy(float);j['chi_young']=(vo*vo-vbar*vbar)/(vbar*vbar);j['gres_young_kms2perkpc']=(vo*vo-vbar*vbar)/j.R_kpc
    corr={p:stats(j.R_kpc,j[p],j.chi_young) for p in PRED};perm=maxT(j.R_kpc.to_numpy(float),j,'chi_young',20000)
    j.to_csv(OUT/f'{label}.csv',index=False)
    return {'n_bins':int(len(j)),'R_range':[float(j.R_kpc.min()),float(j.R_kpc.max())] if len(j) else None,'positive_baryonic_deficit_bins':int((j.chi_young>0).sum()),'median_Vphi_young_kms':float(j.Vphi_young_median_kms.median()) if len(j) else None,'median_chi_young':float(j.chi_young.median()) if len(j) else None,'correlations':corr,'maxT_permutation':perm}
def main():
    y=pd.read_csv(YNG,low_memory=False);h=pd.read_csv(HIST);mc=pd.read_csv(MC)[['R_kpc','Vbar_mcmillan17_kms']];mg=pd.read_csv(MG)[['R_kpc','Vbar_mcgaugh_kms']]
    gen=rotation_profile(y,False);cold=rotation_profile(y,True);gen.to_csv(OUT/'young_rotation_profile_general.csv',index=False);cold.to_csv(OUT/'young_rotation_profile_cold.csv',index=False)
    report={'analysis_name':'Milky Way Stage 4G independent BOSSNet young-star radial rotation-residual test','general_profile':{'stars_by_bin':gen[['R_kpc','n_young']].to_dict('records'),'mcmillan17':analyze('mcmillan17_general',gen,h,mc),'mcgaugh2019':analyze('mcgaugh2019_general',gen,h,mg)},'cold_profile':{'stars_by_bin':cold[['R_kpc','n_young']].to_dict('records'),'mcmillan17':analyze('mcmillan17_cold',cold,h,mc),'mcgaugh2019':analyze('mcgaugh2019_cold',cold,h,mg)},'decision_rule':'A radial migration-history signal is considered independently replicated only if its detrended sign is consistent in general and cold young-star profiles, survives maxT correction, and is not confined to only one baryonic decomposition.','guardrail':'Median young-star Vphi is a circular-speed proxy, not a formal Jeans circular-speed estimate. Young stars have low asymmetric drift but bar/spiral streaming and selection can bias radial medians. This test is an independent tracer arbitration, not a final force reconstruction.'};(OUT/'stage4g_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
# trigger
