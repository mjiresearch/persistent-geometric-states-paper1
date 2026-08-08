#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

OUT=Path('data/persistence_history/milky_way_stage5a_jeans_history'); OUT.mkdir(parents=True,exist_ok=True)
SRC=Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial/mwm_rbirth_star_history.csv.gz')
HIST=Path('data/persistence_history/milky_way_stage4b_guiding_migration/guiding_migration_radial_profile.csv')
MC=Path('data/persistence_history/milky_way_stage3c_interaction/mcmillan_interaction_screen.csv')
MG=Path('data/persistence_history/milky_way_stage3c_interaction/mcgaugh_interaction_screen.csv')
RNG=np.random.default_rng(20260808)
R0,VC0,DVC_DR=8.122,229.0,-1.7
RC=np.arange(5.0,10.5+0.001,0.5)
ZCUTS=[0.5,1.0,1.5,2.0]
HNU=[2.0,2.5,3.0,3.5]
PRED=['Rbirth_median_kpc','deltaR_guide_median_kpc','abs_deltaR_guide_median_kpc','outward_guide_fraction_gt1','inward_guide_fraction_gt1','inner_born_fraction_lt6','guide_history_distance_time_median','age_median_gyr']

def eilers(r): return VC0+DVC_DR*(np.asarray(r,float)-R0)
def detrend(r,y):
    r=np.asarray(r,float);y=np.asarray(y,float);m=np.isfinite(r)&np.isfinite(y);o=np.full(len(y),np.nan)
    if m.sum()<6:return o
    c=np.polyfit(r[m],y[m],2);o[m]=y[m]-np.polyval(c,r[m]);return o

def corr_stats(r,x,y):
    r=np.asarray(r,float);x=np.asarray(x,float);y=np.asarray(y,float);m=np.isfinite(r)&np.isfinite(x)&np.isfinite(y);r,x,y=r[m],x[m],y[m]
    if len(r)<6:return {'n':int(len(r))}
    rr,pr=spearmanr(x,y);rd,pd=spearmanr(detrend(r,x),detrend(r,y));o=np.argsort(r);rf,pf=spearmanr(np.diff(x[o]),np.diff(y[o]))
    return {'n':int(len(r)),'rho_raw':float(rr),'p_raw':float(pr),'rho_detrended':float(rd),'p_detrended':float(pd),'rho_first_difference':float(rf),'p_first_difference':float(pf)}

def maxT(d,target,nperm=20000):
    q=d.dropna(subset=['R_kpc',target]+PRED).copy();r=q.R_kpc.to_numpy(float)
    if len(q)<6:return {p:{'rho_detrended_rank':None,'p_perm':None,'p_maxT':None} for p in PRED}
    y=detrend(r,q[target].to_numpy(float));X=np.column_stack([detrend(r,q[p].to_numpy(float)) for p in PRED])
    yr=rankdata(y);yr=(yr-yr.mean())/yr.std(ddof=0);XR=[]
    for j in range(X.shape[1]):
        z=rankdata(X[:,j]);z=(z-z.mean())/z.std(ddof=0);XR.append(z)
    XR=np.column_stack(XR);obs_s=(XR*yr[:,None]).mean(axis=0);obs=np.abs(obs_s);cnt=np.zeros(len(PRED),int);mxcnt=np.zeros(len(PRED),int)
    for _ in range(nperm):
        yp=RNG.permutation(yr);v=np.abs((XR*yp[:,None]).mean(axis=0));cnt+=v>=obs;mxcnt+=v.max()>=obs
    return {p:{'rho_detrended_rank':float(obs_s[i]),'p_perm':float((cnt[i]+1)/(nperm+1)),'p_maxT':float((mxcnt[i]+1)/(nperm+1))} for i,p in enumerate(PRED)}

def prep(stars,zcut):
    q=stars.copy()
    for c in ['R_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal']:q[c]=pd.to_numeric(q[c],errors='coerce')
    q=q.dropna(subset=['R_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal'])
    q=q[q.R_gal.between(4.75,10.75)&q.Z_gal.abs().le(zcut)].copy()
    plus=((q.Vphi_gal>=100)&(q.Vphi_gal<=320)).sum();minus=((-q.Vphi_gal>=100)&(-q.Vphi_gal<=320)).sum();sign=1.0 if plus>=minus else -1.0
    q['Vphi_pro']=sign*q.Vphi_gal
    q=q[q.Vphi_pro.between(100,320)&q.Vr_gal.abs().le(180)&q.Vz_gal.abs().le(150)].copy();q['R_kpc']=np.floor((q.R_gal+0.25)/0.5)*0.5
    return q,sign

def moments(stars,zcut,min_pre=30,min_post=25):
    q,sign=prep(stars,zcut);rows=[]
    for r,g in q.groupby('R_kpc'):
        if not np.any(np.isclose(r,RC)) or len(g)<min_pre:continue
        vr=g.Vr_gal.to_numpy(float);vp=g.Vphi_pro.to_numpy(float);vz=g.Vz_gal.to_numpy(float);keep=np.ones(len(g),bool)
        for a in (vr,vp,vz):
            med=np.median(a);mad=1.4826*np.median(np.abs(a-med))
            if np.isfinite(mad) and mad>0:keep&=np.abs(a-med)<=4*mad
        vr,vp,vz=vr[keep],vp[keep],vz[keep]
        if len(vr)<min_post:continue
        rows.append({'R_kpc':float(r),'n':int(len(vr)),'mean_vphi_kms':float(np.mean(vp)),'sigma_R_kms':float(np.std(vr,ddof=1)),'sigma_phi_kms':float(np.std(vp,ddof=1)),'sigma_z_kms':float(np.std(vz,ddof=1)),'mean_vr_kms':float(np.mean(vr)),'mean_vz_kms':float(np.mean(vz))})
    m=pd.DataFrame(rows).sort_values('R_kpc') if rows else pd.DataFrame()
    if len(m)<6:return m,sign,None
    x=m.R_kpc.to_numpy(float);y=np.log(np.square(m.sigma_R_kms.to_numpy(float)));w=np.sqrt(m.n.to_numpy(float));b,a=np.polyfit(x,y,1,w=w);m['dln_sigmaR2_dR_per_kpc']=float(b)
    return m,sign,float(b)

def jeans(m,hnu):
    q=m.copy();r=q.R_kpc.to_numpy(float);sr2=q.sigma_R_kms.to_numpy(float)**2;sp2=q.sigma_phi_kms.to_numpy(float)**2;vp2=q.mean_vphi_kms.to_numpy(float)**2;b=q.dln_sigmaR2_dR_per_kpc.to_numpy(float)
    dln=r*(-1.0/hnu+b);vc2=vp2+sp2-sr2*(1+dln);q['hnu_kpc']=hnu;q['dln_nusigR2_dlnR']=dln;q['Vc_jeans_kms']=np.sqrt(np.maximum(vc2,0));q['Vc_eilers_kms']=eilers(r);q['Vc_minus_eilers_kms']=q.Vc_jeans_kms-q.Vc_eilers_kms;return q

def analyze(q,vbcol,label):
    vb=q[vbcol].to_numpy(float);vc=q.Vc_jeans_kms.to_numpy(float);q=q.copy();q['chi_jeans']=(vc**2-vb**2)/(vb**2);q['gres_jeans_kms2perkpc']=(vc**2-vb**2)/q.R_kpc.to_numpy(float)
    return q,{'decomposition':label,'n_bins':int(len(q)),'positive_baryonic_deficit_bins':int((q.chi_jeans>0).sum()),'median_chi_jeans':float(q.chi_jeans.median()),'rms_Vc_minus_eilers_kms':float(np.sqrt(np.mean(q.Vc_minus_eilers_kms**2))),'median_Vc_minus_eilers_kms':float(q.Vc_minus_eilers_kms.median()),'correlations':{p:corr_stats(q.R_kpc,q[p],q.chi_jeans) for p in PRED},'maxT_permutation':maxT(q,'chi_jeans',20000)}

def main():
    stars=pd.read_csv(SRC,low_memory=False);hist=pd.read_csv(HIST);mc=pd.read_csv(MC)[['R_kpc','Vbar_mcmillan17_kms']];mg=pd.read_csv(MG)[['R_kpc','Vbar_mcgaugh_kms']]
    scenarios={};skipped={};rows=[]
    for zcut in ZCUTS:
        m,sign,b=moments(stars,zcut)
        if len(m)<6:
            skipped[str(zcut)]={'radial_bins':int(len(m)),'reason':'fewer than 6 usable radial bins'};continue
        m.to_csv(OUT/f'radial_moments_z{zcut:.1f}.csv',index=False)
        for hnu in HNU:
            base=jeans(m,hnu).merge(hist,on='R_kpc',how='inner');key=f'z{zcut:.1f}_hnu{hnu:.1f}';scenarios[key]={'zcut_kpc':zcut,'hnu_kpc':hnu,'prograde_sign_applied':sign,'dln_sigmaR2_dR_per_kpc':b,'radial_bins_before_history_join':int(len(m))}
            for lab,bt,col in [('mcmillan17',mc,'Vbar_mcmillan17_kms'),('mcgaugh2019',mg,'Vbar_mcgaugh_kms')]:
                j=base.merge(bt,on='R_kpc',how='inner');out,res=analyze(j,col,lab);out.to_csv(OUT/f'{key}_{lab}.csv',index=False);scenarios[key][lab]=res
                for p,v in res['maxT_permutation'].items():rows.append({'scenario':key,'zcut_kpc':zcut,'hnu_kpc':hnu,'decomposition':lab,'predictor':p,**v})
    cons=pd.DataFrame(rows);cons.to_csv(OUT/'history_consistency_all_scenarios.csv',index=False)
    by={}
    if len(cons):
        for p,g in cons.groupby('predictor'):
            s=np.sign(g.rho_detrended_rank.to_numpy(float));by[p]={'n_scenario_decomposition_tests':int(len(g)),'n_maxT_lt_0p05':int((g.p_maxT<.05).sum()),'n_maxT_lt_0p10':int((g.p_maxT<.10).sum()),'positive_sign_fraction':float((s>0).mean()),'negative_sign_fraction':float((s<0).mean()),'median_abs_rho_detrended_rank':float(np.median(np.abs(g.rho_detrended_rank))),'min_p_maxT':float(g.p_maxT.min())}
    rep={'analysis_name':'Milky Way Stage 5A axisymmetric radial Jeans force-residual history screen','input_star_rows':int(len(stars)),'radial_range_kpc':[5.0,10.5],'radial_bin_width_kpc':0.5,'z_cuts_kpc':ZCUTS,'tracer_density_scale_lengths_kpc':HNU,'jeans_equation':'Vc^2 = <Vphi>^2 + sigma_phi^2 - sigma_R^2 [1 + d ln(nu sigma_R^2)/d ln R]','stress_gradient_model':'weighted linear fit to ln(sigma_R^2) versus R within each z cut','tracer_density_model':'nu proportional to exp(-R/h_nu); h_nu varied as a sensitivity envelope','tilt_term':'omitted; vertical-cut sensitivity is the first robustness screen','skipped_vertical_cuts':skipped,'scenarios':scenarios,'history_consistency':by,'decision_rule':'Accept no history predictor unless it survives maxT with stable sign across h_nu, vertical cuts, and both baryonic decompositions; Jeans/Eilers agreement is a prerequisite sanity check.','guardrail':'Sensitivity-bracketed axisymmetric Jeans estimate, not a fully selection-function-corrected 3D Jeans model. The density gradient is imposed via an h_nu envelope and the R-z tilt term is omitted. Birth radii remain transferred Ratcliffe age/metallicity proxies.'};(OUT/'stage5a_summary.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
if __name__=='__main__':main()
