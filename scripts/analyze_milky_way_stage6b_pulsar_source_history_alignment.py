#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OUT=Path('data/persistence_history/milky_way_stage6b_pulsar_history_alignment');OUT.mkdir(parents=True,exist_ok=True)
PUL=Path('data/persistence_history/milky_way_stage6a_pulsar_acceleration/pulsar_residuals_R8.210_z0.csv')
SRC=Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial/mwm_rbirth_star_history.csv.gz')
SIGMAS=[1.0,1.5]
ANGLE_STEP_DEG=2.0
OFFSETS=np.arange(0.0,360.0,ANGLE_STEP_DEG)
HISTORY=['deltaR_mean_kpc','migration_direction_mean','Rbirth_mean_kpc']
REFERENCES=['Age_mean_gyr','FeH_mean','aFe_mean','log_source_weight']
SAMPLES={
 'all_29': lambda d: np.ones(len(d),bool),
 'exclude_five_published_outliers': lambda d: d.model_outlier_ge3sigma.to_numpy(int)==0,
 'authors_modified_catalog': lambda d: d.modified_catalog_excluded.to_numpy(int)==0,
 'exclude_both_flag_sets': lambda d:(d.model_outlier_ge3sigma.to_numpy(int)==0)&(d.modified_catalog_excluded.to_numpy(int)==0),
}


def rank_corr(x,y):
 x=np.asarray(x,float);y=np.asarray(y,float);m=np.isfinite(x)&np.isfinite(y)
 if m.sum()<8:return np.nan,int(m.sum())
 r,_=spearmanr(x[m],y[m]);return float(r),int(m.sum())

def weighted_field(sx,sy,sz,vals,px,py,pz,sigma):
 d2=(sx-px)**2+(sy-py)**2+(sz-pz)**2
 m=d2<=(3.0*sigma)**2
 if m.sum()==0:return {k:np.nan for k in vals}|{'source_weight':0.0,'source_neff':0.0,'nearest_source_kpc':float(np.sqrt(np.min(d2)))}
 w=np.exp(-0.5*d2[m]/sigma**2);sw=float(w.sum());neff=float(sw*sw/np.sum(w*w))
 out={k:float(np.sum(w*v[m])/sw) for k,v in vals.items()}
 out.update({'source_weight':sw,'source_neff':neff,'nearest_source_kpc':float(np.sqrt(np.min(d2)))})
 return out

def build_fields(pul,src,sigma,y_sign):
 R=src.R_gal.to_numpy(float);ph=np.deg2rad(src.phi_deg.to_numpy(float));sx=R*np.cos(ph);sy=R*np.sin(ph);sz=src.Z_gal.to_numpy(float)
 delta=src.deltaR_present_birth_kpc.to_numpy(float);outward=src.outward_present_gt1.to_numpy(float);inward=src.inward_present_gt1.to_numpy(float)
 vals={'deltaR_mean_kpc':delta,'migration_direction_mean':outward-inward,'Rbirth_mean_kpc':src.Rbirth_proxy_kpc.to_numpy(float),'Age_mean_gyr':src.Age.to_numpy(float),'FeH_mean':src.FeH.to_numpy(float),'aFe_mean':src.aFe.to_numpy(float)}
 n=len(pul);na=len(OFFSETS);data={k:np.full((na,n),np.nan) for k in list(vals)+['source_weight','source_neff','nearest_source_kpc','log_source_weight']}
 x0=-pul.x_pc.to_numpy(float)/1000.0;y0=y_sign*pul.y_pc.to_numpy(float)/1000.0;z0=pul.z_pc.to_numpy(float)/1000.0;Rp=np.hypot(x0,y0);phi0=np.arctan2(y0,x0)
 for ia,off in enumerate(np.deg2rad(OFFSETS)):
  p=phi0+off;px=Rp*np.cos(p);py=Rp*np.sin(p)
  for i in range(n):
   f=weighted_field(sx,sy,sz,vals,px[i],py[i],z0[i],sigma)
   for k,v in f.items():data[k][ia,i]=v
   data['log_source_weight'][ia,i]=np.log(max(f['source_weight'],1e-300))
 return data,Rp,np.rad2deg((phi0%(2*np.pi)))

def rotation_test(pul,field,target,sample_mask,predictors):
 y=pul[target].to_numpy(float);rhos=np.full((len(OFFSETS),len(predictors)),np.nan);ns=np.zeros_like(rhos,int)
 for ia in range(len(OFFSETS)):
  for j,p in enumerate(predictors):rhos[ia,j],ns[ia,j]=rank_corr(field[p][ia,sample_mask],y[sample_mask])
 obs=rhos[0].copy();null=np.abs(rhos[1:]);tests={}
 maxnull=np.nanmax(null,axis=1)
 for j,p in enumerate(predictors):
  if not np.isfinite(obs[j]):tests[p]={'rho_actual':None};continue
  good=np.isfinite(null[:,j]);pperm=float((1+np.sum(null[good,j]>=abs(obs[j])))/(1+good.sum()))
  gm=np.isfinite(maxnull);pmax=float((1+np.sum(maxnull[gm]>=abs(obs[j])))/(1+gm.sum()))
  tests[p]={'rho_actual':float(obs[j]),'n_actual':int(ns[0,j]),'p_azimuth_rotation':pperm,'p_maxT_predictor_family':pmax,'null_abs_rho_median':float(np.nanmedian(null[:,j])),'null_abs_rho_95pct':float(np.nanpercentile(null[:,j],95))}
 return tests,rhos

def main():
 pul=pd.read_csv(PUL);src=pd.read_csv(SRC,low_memory=False)
 for c in ['x_pc','y_pc','z_pc','resid_baryon_1e10','zresid_baryon']:pul[c]=pd.to_numeric(pul[c],errors='coerce')
 for c in ['R_gal','Z_gal','phi_deg','Rbirth_proxy_kpc','deltaR_present_birth_kpc','outward_present_gt1','inward_present_gt1','Age','FeH','aFe']:src[c]=pd.to_numeric(src[c],errors='coerce')
 src=src.dropna(subset=['R_gal','Z_gal','phi_deg','Rbirth_proxy_kpc','deltaR_present_birth_kpc','Age','FeH','aFe']).copy();src=src[src.R_gal.between(4.0,11.0)&src.Z_gal.abs().le(3.0)].copy()
 runs={};flat=[]
 for ysign in [1.0,-1.0]:
  hand='Ysame' if ysign>0 else 'Yreflected'
  runs[hand]={}
  for sigma in SIGMAS:
   field,Rp,phi=build_fields(pul,src,sigma,ysign);key=f'sigma{sigma:.1f}';runs[hand][key]={'source_kernel_sigma_kpc':sigma,'actual_pulsar_R_range_kpc':[float(Rp.min()),float(Rp.max())],'actual_phi_range_deg':[float(phi.min()),float(phi.max())],'actual_source_neff_median':float(np.nanmedian(field['source_neff'][0])),'actual_source_neff_min':float(np.nanmin(field['source_neff'][0])),'actual_nearest_source_median_kpc':float(np.nanmedian(field['nearest_source_kpc'][0])),'samples':{}}
   actual=pd.DataFrame({'pulsar':pul.pulsar,'R_kpc':Rp,'phi_mwm_deg':phi,'z_kpc':pul.z_pc/1000.0,'resid_baryon_1e10':pul.resid_baryon_1e10,'zresid_baryon':pul.zresid_baryon})
   for p in HISTORY+REFERENCES:actual[p]=field[p][0]
   actual['source_neff']=field['source_neff'][0];actual['nearest_source_kpc']=field['nearest_source_kpc'][0];actual.to_csv(OUT/f'actual_fields_{hand}_{key}.csv',index=False)
   for sname,fn in SAMPLES.items():
    mask=fn(pul)&np.isfinite(pul.resid_baryon_1e10.to_numpy(float))
    ht,hr=rotation_test(pul,field,'resid_baryon_1e10',mask,HISTORY);rt,rr=rotation_test(pul,field,'resid_baryon_1e10',mask,REFERENCES);zt,zr=rotation_test(pul,field,'zresid_baryon',mask,HISTORY)
    runs[hand][key]['samples'][sname]={'n_pulsars':int(mask.sum()),'history_vs_baryonic_residual':ht,'reference_fields_vs_baryonic_residual':rt,'history_vs_standardized_residual':zt}
    for p,v in ht.items():flat.append({'handedness':hand,'sigma_kpc':sigma,'sample':sname,'target':'resid_baryon_1e10','predictor':p,**v})
    for p,v in zt.items():flat.append({'handedness':hand,'sigma_kpc':sigma,'sample':sname,'target':'zresid_baryon','predictor':p,**v})
 pd.DataFrame(flat).to_csv(OUT/'stage6b_history_test_matrix.csv',index=False)
 # Strict replication summary: primary unstandardized residual only.
 f=pd.DataFrame(flat);f=f[f.target=='resid_baryon_1e10'].copy();cons={}
 for p,g in f.groupby('predictor'):
  cons[p]={'n_tests':int(len(g)),'n_maxT_lt_0p05':int((g.p_maxT_predictor_family<.05).sum()),'n_rotation_lt_0p05':int((g.p_azimuth_rotation<.05).sum()),'positive_rho_fraction':float((g.rho_actual>0).mean()),'negative_rho_fraction':float((g.rho_actual<0).mean()),'min_p_maxT':float(g.p_maxT_predictor_family.min()),'rho_range':[float(g.rho_actual.min()),float(g.rho_actual.max())]}
 report={'analysis_name':'Milky Way Stage 6B direct pulsar acceleration residual versus local MWM source-history field','pulsars':int(len(pul)),'source_stars':int(len(src)),'pulsar_to_mwm_coordinate_mapping':'Moran +x away from Galactic center is mapped to MWM/Astropy-like X=-x; both Y=+y and Y=-y are retained as handedness sensitivity tests.','kernel_sigmas_kpc':SIGMAS,'azimuth_rotation_null':{'angle_step_deg':ANGLE_STEP_DEG,'n_global_orientations':int(len(OFFSETS)),'description':'Rotate the complete pulsar pattern relative to the source field while preserving each pulsar R and z; offset 0 is the observed alignment.'},'history_predictors':HISTORY,'reference_fields':REFERENCES,'runs':runs,'history_consistency':cons,'decision_rule':'A persistence-compatible precursor is not accepted unless one predeclared history predictor survives family-wise maxT azimuth-rotation correction with the same correlation sign across both coordinate handedness choices, both kernel scales, and the published outlier-sensitivity samples. A signal that appears only in the all-pulsar or only in a cleaned subset is not accepted.','guardrail':'The MWM birth-radius field is an inferred age/metallicity-based source-history proxy, not a measured trajectory/current history. Source-density selection effects are retained as an explicit reference field. The direct pulsar acceleration observable is independent of the MWM source population, but the pulsar catalog contains known heavy-tailed nuisance acceleration.'};(OUT/'stage6b_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
