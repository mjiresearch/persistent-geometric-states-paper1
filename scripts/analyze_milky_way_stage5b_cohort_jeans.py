#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

OUT=Path('data/persistence_history/milky_way_stage5b_cohort_jeans');OUT.mkdir(parents=True,exist_ok=True)
SRC=Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial/mwm_rbirth_star_history.csv.gz')
HIST=Path('data/persistence_history/milky_way_stage4b_guiding_migration/guiding_migration_radial_profile.csv')
MC=Path('data/persistence_history/milky_way_stage3c_interaction/mcmillan_interaction_screen.csv')
MG=Path('data/persistence_history/milky_way_stage3c_interaction/mcgaugh_interaction_screen.csv')
RNG=np.random.default_rng(20260808)
R0,VC0,SLOPE=8.122,229.0,-1.7
RC=np.arange(5.0,10.5+0.001,0.5);ZCUTS=[1.0,1.5];HNU=[2.0,2.5,3.0,3.5]
PRED=['Rbirth_median_kpc','deltaR_guide_median_kpc','abs_deltaR_guide_median_kpc','outward_guide_fraction_gt1','inward_guide_fraction_gt1','inner_born_fraction_lt6','guide_history_distance_time_median','age_median_gyr']
COHORTS={
'low_alpha':lambda d:(d.aFe>=-0.05)&(d.aFe<=0.15)&d.FeH.between(-0.8,0.4)&d.Age.between(1.0,10.0),
'midage_low_alpha':lambda d:(d.aFe>=-0.05)&(d.aFe<=0.15)&d.FeH.between(-0.8,0.4)&d.Age.between(3.0,8.0),
'solar_metal_low_alpha':lambda d:(d.aFe>=-0.05)&(d.aFe<=0.12)&d.FeH.between(-0.5,0.2)&d.Age.between(2.0,8.0),
}

def detrend(r,y):
 r=np.asarray(r,float);y=np.asarray(y,float);m=np.isfinite(r)&np.isfinite(y);o=np.full(len(y),np.nan)
 if m.sum()<6:return o
 c=np.polyfit(r[m],y[m],2);o[m]=y[m]-np.polyval(c,r[m]);return o

def maxT(d,target,nperm=20000):
 q=d.dropna(subset=['R_kpc',target]+PRED).copy();r=q.R_kpc.to_numpy(float)
 if len(q)<6:return {p:{'rho':None,'p_maxT':None} for p in PRED}
 yr=rankdata(detrend(r,q[target].to_numpy(float)));yr=(yr-yr.mean())/yr.std(ddof=0);X=[]
 for p in PRED:
  z=rankdata(detrend(r,q[p].to_numpy(float)));z=(z-z.mean())/z.std(ddof=0);X.append(z)
 X=np.column_stack(X);obs_s=(X*yr[:,None]).mean(axis=0);obs=np.abs(obs_s);cnt=np.zeros(len(PRED),int);mx=np.zeros(len(PRED),int)
 for _ in range(nperm):
  yp=RNG.permutation(yr);v=np.abs((X*yp[:,None]).mean(axis=0));cnt+=v>=obs;mx+=v.max()>=obs
 return {p:{'rho':float(obs_s[i]),'p_perm':float((cnt[i]+1)/(nperm+1)),'p_maxT':float((mx[i]+1)/(nperm+1))} for i,p in enumerate(PRED)}

def prep(stars,cohort,zcut):
 d=stars.copy()
 for c in ['R_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal','Age','FeH','aFe']:d[c]=pd.to_numeric(d[c],errors='coerce')
 d=d.dropna(subset=['R_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal','Age','FeH','aFe']);d=d[COHORTS[cohort](d)&d.R_gal.between(4.75,10.75)&d.Z_gal.abs().le(zcut)].copy()
 plus=d.Vphi_gal.between(100,320).sum();minus=(-d.Vphi_gal).between(100,320).sum();sgn=1.0 if plus>=minus else -1.0;d['vp']=sgn*d.Vphi_gal;d=d[d.vp.between(100,320)&d.Vr_gal.abs().le(180)&d.Vz_gal.abs().le(150)].copy();d['R_kpc']=np.floor((d.R_gal+0.25)/.5)*.5
 return d,sgn

def moments(stars,cohort,zcut):
 d,sgn=prep(stars,cohort,zcut);rows=[]
 for r,g in d.groupby('R_kpc'):
  if not np.any(np.isclose(r,RC)) or len(g)<25:continue
  vr=g.Vr_gal.to_numpy(float);vp=g.vp.to_numpy(float);vz=g.Vz_gal.to_numpy(float);keep=np.ones(len(g),bool)
  for a in (vr,vp,vz):
   med=np.median(a);mad=1.4826*np.median(np.abs(a-med));
   if mad>0:keep&=np.abs(a-med)<=4*mad
  vr,vp,vz=vr[keep],vp[keep],vz[keep]
  if len(vr)<20:continue
  rows.append({'R_kpc':r,'n':len(vr),'mean_vphi':np.mean(vp),'sigR':np.std(vr,ddof=1),'sigphi':np.std(vp,ddof=1),'sigz':np.std(vz,ddof=1),'age_med':g.Age.median(),'FeH_med':g.FeH.median(),'aFe_med':g.aFe.median()})
 m=pd.DataFrame(rows).sort_values('R_kpc') if rows else pd.DataFrame()
 if len(m)<8:return m,sgn,None,{'pass':False,'reason':'fewer than 8 radial bins'}
 x=m.R_kpc.to_numpy(float);y=np.log(m.sigR.to_numpy(float)**2);w=np.sqrt(m.n.to_numpy(float));b,a=np.polyfit(x,y,1,w=w);pred=a+b*x;ssr=np.sum((y-pred)**2);sst=np.sum((y-y.mean())**2);r2=1-ssr/sst if sst>0 else np.nan;adj=np.maximum(m.sigR.to_numpy(float)[1:]/m.sigR.to_numpy(float)[:-1],m.sigR.to_numpy(float)[:-1]/m.sigR.to_numpy(float)[1:]);maxratio=float(np.max(adj))
 m['dln_sigR2_dR']=b;san={'pass':bool(maxratio<2.5 and (not np.isfinite(r2) or r2>-0.5)),'max_adjacent_sigR_ratio':maxratio,'ln_sigR2_linear_R2':float(r2),'stress_slope_per_kpc':float(b)}
 return m,sgn,float(b),san

def jeans(m,h):
 q=m.copy();r=q.R_kpc.to_numpy(float);sr2=q.sigR.to_numpy(float)**2;sp2=q.sigphi.to_numpy(float)**2;vp2=q.mean_vphi.to_numpy(float)**2;b=q.dln_sigR2_dR.to_numpy(float);dln=r*(-1/h+b);vc2=vp2+sp2-sr2*(1+dln);q['hnu']=h;q['Vc']=np.sqrt(np.maximum(vc2,0));q['Veilers']=VC0+SLOPE*(r-R0);q['dV_eilers']=q.Vc-q.Veilers;return q

def analyze(q,col):
 vb=q[col].to_numpy(float);vc=q.Vc.to_numpy(float);q=q.copy();q['chi']=(vc**2-vb**2)/(vb**2);return q,{'n_bins':len(q),'positive_bins':int((q.chi>0).sum()),'median_chi':float(q.chi.median()),'rms_dV_eilers':float(np.sqrt(np.mean(q.dV_eilers**2))),'median_dV_eilers':float(q.dV_eilers.median()),'history':maxT(q,'chi')}

def main():
 stars=pd.read_csv(SRC,low_memory=False);hist=pd.read_csv(HIST);mc=pd.read_csv(MC)[['R_kpc','Vbar_mcmillan17_kms']];mg=pd.read_csv(MG)[['R_kpc','Vbar_mcgaugh_kms']];res={};flat=[]
 for cohort in COHORTS:
  res[cohort]={}
  for zcut in ZCUTS:
   m,sgn,b,san=moments(stars,cohort,zcut);key=f'z{zcut:.1f}';res[cohort][key]={'n_bins':int(len(m)),'sign':sgn,'sanity':san}
   if len(m):m.to_csv(OUT/f'{cohort}_{key}_moments.csv',index=False)
   if len(m)<8 or not san['pass']:continue
   for h in HNU:
    base=jeans(m,h).merge(hist,on='R_kpc',how='inner');hk=f'h{h:.1f}';res[cohort][key][hk]={}
    for lab,bt,col in [('mcmillan17',mc,'Vbar_mcmillan17_kms'),('mcgaugh2019',mg,'Vbar_mcgaugh_kms')]:
     q=base.merge(bt,on='R_kpc',how='inner');o,s=analyze(q,col);o.to_csv(OUT/f'{cohort}_{key}_{hk}_{lab}.csv',index=False);res[cohort][key][hk][lab]=s
     for p,v in s['history'].items():flat.append({'cohort':cohort,'zcut':zcut,'hnu':h,'decomp':lab,'predictor':p,**v,'rms_dV_eilers':s['rms_dV_eilers']})
 f=pd.DataFrame(flat);f.to_csv(OUT/'all_valid_cohort_history_tests.csv',index=False);cons={}
 if len(f):
  for p,g in f.groupby('predictor'):
   s=np.sign(g.rho.to_numpy(float));cons[p]={'n':len(g),'n_maxT_lt_0p05':int((g.p_maxT<.05).sum()),'n_maxT_lt_0p10':int((g.p_maxT<.10).sum()),'positive_fraction':float((s>0).mean()),'negative_fraction':float((s<0).mean()),'min_p_maxT':float(g.p_maxT.min()),'median_rms_dV_eilers':float(g.rms_dV_eilers.median())}
 rep={'analysis_name':'Milky Way Stage 5B homogeneous-cohort radial Jeans screen','cohorts':list(COHORTS),'z_cuts':ZCUTS,'hnu':HNU,'results':res,'history_consistency_valid_scenarios':cons,'acceptance_rule':'Interpret only cohorts with >=8 radial bins and smooth sigma_R; history then must survive maxT with stable sign across hnu, zcut, cohort and both baryonic decompositions.','guardrail':'Axisymmetric radial Jeans with imposed tracer scale length and omitted tilt term; cohorting reduces population-mixing bias but does not replace a full selection-function-corrected 3D Jeans analysis.'};(OUT/'stage5b_summary.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
if __name__=='__main__':main()
