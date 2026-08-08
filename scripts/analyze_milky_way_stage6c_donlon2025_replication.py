#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from galpy.potential import mwpotentials, evaluateRforces, evaluatezforces
from galpy.util.conversion import get_physical

OUT=Path('data/persistence_history/milky_way_stage6c_donlon2025_replication');OUT.mkdir(parents=True,exist_ok=True)
DON=Path('data/external/galactic_acceleration/donlon2025_v3/donlon2025_v3_accelerations_normalized.csv')
MOR=Path('data/external/galactic_acceleration/moran2024_pulsar_accelerations.csv')
SRC=Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial/mwm_rbirth_star_history.csv.gz')
KPC_M=3.085677581491367e19
RSUN=8.210
ZSUN=0.0
SIGMAS=[1.0,1.5]
ANGLE_STEP_DEG=2.0
OFFSETS=np.arange(0.0,360.0,ANGLE_STEP_DEG)
PRIMARY_PREDICTOR='deltaR_mean_kpc'
PREDICTED_SIGN='negative'


def canonical_name(s):
    s=str(s).strip()
    if s.startswith('J0737-3039'): return 'J0737-3039'
    return s

def force_scale(vo,ro): return (vo*1000.0)**2/(ro*KPC_M)
def accel_xyz(pot,x,y,z,ro,vo):
    R=float(np.hypot(x,y));fR=float(evaluateRforces(pot,R/ro,z/ro,use_physical=False));fz=float(evaluatezforces(pot,R/ro,z/ro,use_physical=False));sc=force_scale(vo,ro);aR=fR*sc;return np.array([aR*x/R,aR*y/R,fz*sc])
def los_pred(pot,rb,rsun,ro,vo):
    dr=rb-rsun;rh=dr/np.linalg.norm(dr);return float(np.dot(accel_xyz(pot,*rb,ro,vo)-accel_xyz(pot,*rsun,ro,vo),rh))
def rank_corr(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float);m=np.isfinite(x)&np.isfinite(y)
    if m.sum()<8:return np.nan,int(m.sum())
    r,_=spearmanr(x[m],y[m]);return float(r),int(m.sum())
def weighted_field(sx,sy,sz,vals,px,py,pz,sigma):
    d2=(sx-px)**2+(sy-py)**2+(sz-pz)**2;m=d2<=(3*sigma)**2
    if m.sum()==0:return {k:np.nan for k in vals}|{'source_weight':0.0,'source_neff':0.0,'nearest_source_kpc':float(np.sqrt(np.min(d2)))}
    w=np.exp(-.5*d2[m]/sigma**2);sw=float(w.sum());neff=float(sw*sw/np.sum(w*w));out={k:float(np.sum(w*v[m])/sw) for k,v in vals.items()};out.update({'source_weight':sw,'source_neff':neff,'nearest_source_kpc':float(np.sqrt(np.min(d2)))});return out
def build_fields(pul,src,sigma):
    R=src.R_gal.to_numpy(float);ph=np.deg2rad(src.phi_deg.to_numpy(float));sx=R*np.cos(ph);sy=R*np.sin(ph);sz=src.Z_gal.to_numpy(float)
    vals={'deltaR_mean_kpc':src.deltaR_present_birth_kpc.to_numpy(float),'Rbirth_mean_kpc':src.Rbirth_proxy_kpc.to_numpy(float),'Age_mean_gyr':src.Age.to_numpy(float),'FeH_mean':src.FeH.to_numpy(float),'aFe_mean':src.aFe.to_numpy(float)}
    px0=pul.X_mwm_kpc.to_numpy(float);py0=pul.Y_mwm_kpc.to_numpy(float);pz=pul.Z_mwm_kpc.to_numpy(float);Rp=np.hypot(px0,py0);phi0=np.arctan2(py0,px0);data={k:np.full((len(OFFSETS),len(pul)),np.nan) for k in list(vals)+['source_weight','source_neff','nearest_source_kpc']}
    for ia,off in enumerate(np.deg2rad(OFFSETS)):
        p=phi0+off;px=Rp*np.cos(p);py=Rp*np.sin(p)
        for i in range(len(pul)):
            f=weighted_field(sx,sy,sz,vals,px[i],py[i],pz[i],sigma)
            for k,v in f.items():data[k][ia,i]=v
    return data

def frozen_rotation_test(field,y,mask):
    y=np.asarray(y,float);mask=np.asarray(mask,bool);rhos=np.full(len(OFFSETS),np.nan);ns=np.zeros(len(OFFSETS),int)
    for ia in range(len(OFFSETS)):rhos[ia],ns[ia]=rank_corr(field[PRIMARY_PREDICTOR][ia,mask],y[mask])
    obs=rhos[0];null=rhos[1:];good=np.isfinite(null)
    if not np.isfinite(obs):return {'rho_actual':None,'n_actual':int(ns[0])}
    # Frozen directional hypothesis: rho < 0.
    pone=float((1+np.sum(null[good]<=obs))/(1+good.sum()))
    ptwo=float((1+np.sum(np.abs(null[good])>=abs(obs)))/(1+good.sum()))
    return {'rho_actual':float(obs),'n_actual':int(ns[0]),'p_one_sided_frozen_negative':pone,'p_two_sided_rotation':ptwo,'null_rho_median':float(np.nanmedian(null)),'null_rho_05pct':float(np.nanpercentile(null,5)),'null_rho_95pct':float(np.nanpercentile(null,95))}
def diagnostic_test(field,pred,y,mask):
    r, n=rank_corr(field[pred][0,mask],np.asarray(y,float)[mask]);return {'rho_actual':float(r) if np.isfinite(r) else None,'n_actual':n}

def main():
    d=pd.read_csv(DON);moran=pd.read_csv(MOR);src=pd.read_csv(SRC,low_memory=False)
    for c in ['aGal_1e10_m_s2','aGal_err_1e10_m_s2','x_moranlike_kpc','y_moranlike_kpc','z_moranlike_kpc','X_mwm_kpc','Y_mwm_kpc','Z_mwm_kpc']:d[c]=pd.to_numeric(d[c],errors='coerce')
    for c in ['R_gal','Z_gal','phi_deg','Rbirth_proxy_kpc','deltaR_present_birth_kpc','Age','FeH','aFe']:src[c]=pd.to_numeric(src[c],errors='coerce')
    src=src.dropna(subset=['R_gal','Z_gal','phi_deg','Rbirth_proxy_kpc','deltaR_present_birth_kpc','Age','FeH','aFe']);src=src[src.R_gal.between(4,11)&src.Z_gal.abs().le(3)].copy()
    d['canon']=d.NAME.map(canonical_name);moran['canon']=moran.pulsar.map(canonical_name);moran_set=set(moran.canon)
    d['present_in_moran_discovery_catalog']=d.canon.isin(moran_set).astype(int)
    # Avoid double-weighting J0737 A/B at one location: keep alphabetical first representative.
    d=d.sort_values('NAME').copy();d['keep_independent_position']=~d.duplicated('sky_key',keep='first');q=d[d.keep_independent_position].copy().reset_index(drop=True)
    pot=mwpotentials.McMillan17;bary=[p for p in pot if type(p).__name__!='NFWPotential'];phys=get_physical(pot);ro=float(phys['ro']);vo=float(phys['vo']);rsun=np.array([RSUN,0.0,ZSUN])
    pred=[]
    for _,r in q.iterrows():pred.append(los_pred(bary,np.array([r.x_moranlike_kpc,r.y_moranlike_kpc,r.z_moranlike_kpc]),rsun,ro,vo)/1e-10)
    q['a_baryon_pred_1e10']=pred;q['resid_baryon_1e10']=q.aGal_1e10_m_s2-q.a_baryon_pred_1e10;q['zresid_baryon']=q.resid_baryon_1e10/q.aGal_err_1e10_m_s2
    # Binary-channel unit/sign validation against Moran by canonical name.
    v=q[q.accel_source.eq('binary_orbital')][['canon','aGal_1e10_m_s2']].merge(moran[['canon','aGal_1e10_m_s2']],on='canon',suffixes=('_donlon','_moran'))
    vrho,vp=spearmanr(v.aGal_1e10_m_s2_donlon,v.aGal_1e10_m_s2_moran) if len(v)>=3 else (np.nan,np.nan)
    validation={'n_overlap_binary_with_moran':int(len(v)),'spearman_rho':float(vrho) if np.isfinite(vrho) else None,'spearman_p':float(vp) if np.isfinite(vp) else None,'median_donlon_minus_moran_1e10':float(np.median(v.aGal_1e10_m_s2_donlon-v.aGal_1e10_m_s2_moran)) if len(v) else None,'same_sign_fraction_nonzero':float(np.mean(np.sign(v.aGal_1e10_m_s2_donlon)==np.sign(v.aGal_1e10_m_s2_moran))) if len(v) else None}
    masks={
      'PRIMARY_new_systems_not_in_moran':q.present_in_moran_discovery_catalog.eq(0).to_numpy(),
      'spin_inferred_only':q.accel_source.eq('spin_inferred').to_numpy(),
      'binary_orbital_only':q.accel_source.eq('binary_orbital').to_numpy(),
      'combined_independent_positions':np.ones(len(q),bool),
    }
    runs={};matrix=[]
    for sigma in SIGMAS:
        field=build_fields(q,src,sigma);key=f'sigma{sigma:.1f}';runs[key]={'sigma_kpc':sigma,'actual_source_neff_median':float(np.nanmedian(field['source_neff'][0])),'actual_source_neff_min':float(np.nanmin(field['source_neff'][0])),'actual_nearest_source_median_kpc':float(np.nanmedian(field['nearest_source_kpc'][0])),'samples':{}}
        actual=q[['NAME','canon','accel_source','present_in_moran_discovery_catalog','aGal_1e10_m_s2','aGal_err_1e10_m_s2','a_baryon_pred_1e10','resid_baryon_1e10','zresid_baryon','R_gal_kpc','phi_mwm_deg','Z_mwm_kpc']].copy();actual[PRIMARY_PREDICTOR]=field[PRIMARY_PREDICTOR][0];actual['Rbirth_mean_kpc']=field['Rbirth_mean_kpc'][0];actual['Age_mean_gyr']=field['Age_mean_gyr'][0];actual['FeH_mean']=field['FeH_mean'][0];actual['source_neff']=field['source_neff'][0];actual['nearest_source_kpc']=field['nearest_source_kpc'][0];actual.to_csv(OUT/f'actual_fields_{key}.csv',index=False)
        for name,mask in masks.items():
            test=frozen_rotation_test(field,q.resid_baryon_1e10.to_numpy(float),mask);runs[key]['samples'][name]={'n_catalog_mask':int(mask.sum()),'frozen_deltaR_test':test,'diagnostics':{'age':diagnostic_test(field,'Age_mean_gyr',q.resid_baryon_1e10,mask),'FeH':diagnostic_test(field,'FeH_mean',q.resid_baryon_1e10,mask),'Rbirth':diagnostic_test(field,'Rbirth_mean_kpc',q.resid_baryon_1e10,mask)}};matrix.append({'sigma_kpc':sigma,'sample':name,**test})
    pd.DataFrame(matrix).to_csv(OUT/'stage6c_frozen_test_matrix.csv',index=False);q.to_csv(OUT/'donlon2025_baryonic_residuals_independent_positions.csv',index=False)
    primary1=runs['sigma1.0']['samples']['PRIMARY_new_systems_not_in_moran']['frozen_deltaR_test'];primary15=runs['sigma1.5']['samples']['PRIMARY_new_systems_not_in_moran']['frozen_deltaR_test']
    replicated=bool(primary1.get('rho_actual',1)<0 and primary1.get('p_one_sided_frozen_negative',1)<0.05 and primary15.get('rho_actual',1)<0 and primary15.get('p_one_sided_frozen_negative',1)<0.05)
    report={'analysis_name':'Milky Way Stage 6C frozen replication in Donlon et al. 2025 expanded pulsar catalog','frozen_before_result':{'primary_predictor':PRIMARY_PREDICTOR,'predicted_sign':PREDICTED_SIGN,'primary_sigma_kpc':1.0,'robustness_sigma_kpc':1.5,'physical_coordinate_mapping':'X_MWM=-x_awayGC; Y_MWM=+y_l90; Z_MWM=+z_north','primary_replication_sample':'independent sky positions whose canonical pulsar system was absent from Moran 2024 discovery catalog'},'catalog':{'rows_ingested':int(len(d)),'independent_positions':int(len(q)),'new_systems_not_in_moran':int(masks['PRIMARY_new_systems_not_in_moran'].sum()),'binary_orbital_positions':int(masks['binary_orbital_only'].sum()),'spin_inferred_positions':int(masks['spin_inferred_only'].sum()),'new_system_accel_source_counts':q.loc[masks['PRIMARY_new_systems_not_in_moran'],'accel_source'].value_counts().to_dict()},'binary_overlap_validation':validation,'baryonic_model':{'McMillan17_ro_kpc':ro,'McMillan17_vo_kms':vo,'rule':'all McMillan17 components except NFWPotential; identical to Stages 3 and 6A'},'azimuth_rotation_null':{'step_deg':ANGLE_STEP_DEG,'orientations':int(len(OFFSETS)),'one_sided_direction':'rho <= observed because negative sign was frozen before viewing Donlon result'},'runs':runs,'strict_replication_pass':replicated,'strict_rule':'PASS only if the primary new-system sample has rho<0 and one-sided azimuth-rotation p<0.05 at BOTH the frozen 1.0-kpc primary kernel and the 1.5-kpc robustness kernel. Binary-only and combined samples are supporting diagnostics, not substitutes for this out-of-sample rule.','guardrail':'The spin-inferred acceleration channel is empirically calibrated from pulsar spindown and is not as direct as binary-orbital acceleration. It is nevertheless independent of the MWM source-history reconstruction. No predictor, sign, kernel scale, or migration threshold is selected from the Stage 6C result.'};(OUT/'stage6c_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
