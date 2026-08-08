#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from astropy import units as u
from astropy.coordinates import SkyCoord, Galactocentric, CartesianDifferential

OUT = Path('data/persistence_history/milky_way_stage4e_young_tracer')
OUT.mkdir(parents=True, exist_ok=True)
HOT = Path('data/external/sdss/bossnet_hot_stars/bossnet_hot_stars_selected.csv.gz')
HIST = Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial/mwm_rbirth_spatial_cells.csv')
RNG = np.random.default_rng(20260808)
R0_KPC = 8.2
Z_SUN_KPC = 0.025
V_SUN_CART_KMS = [11.0, 232.24, 7.25]
HISTORY = ['Rbirth_median_kpc_anom','deltaR_present_birth_median_kpc_anom','outward_fraction_gt1_anom','inward_fraction_gt1_anom','inner_born_fraction_lt6_anom']
CONTROLS = ['age_median_gyr_anom','FeH_median_anom','aFe_median_anom']

def finite_numeric(s): return pd.to_numeric(s, errors='coerce')

def build_phase_space(raw: pd.DataFrame) -> pd.DataFrame:
    d=raw.copy()
    for c in ['ra','dec','pmra','pmde','r_med_photogeo','v_rad','e_v_rad','teff','snr']: d[c]=finite_numeric(d[c])
    bad=finite_numeric(d['flag_bad']).fillna(0) if 'flag_bad' in d.columns else pd.Series(0,index=d.index)
    if 'r_lo_photogeo' in d.columns and 'r_hi_photogeo' in d.columns:
        dlo=finite_numeric(d['r_lo_photogeo']); dhi=finite_numeric(d['r_hi_photogeo']); frac=(dhi-dlo).abs()/(2*d['r_med_photogeo'].abs())
    else: frac=pd.Series(np.nan,index=d.index)
    q=(np.isfinite(d.ra)&np.isfinite(d.dec)&np.isfinite(d.pmra)&np.isfinite(d.pmde)&np.isfinite(d.r_med_photogeo)&(d.r_med_photogeo>0)&np.isfinite(d.v_rad)&np.isfinite(d.e_v_rad)&(d.e_v_rad<=25)&np.isfinite(d.teff)&d.teff.between(10000,60000)&np.isfinite(d.snr)&(d.snr>=10)&(bad==0))
    q &= (~np.isfinite(frac)) | (frac<=0.5)
    d=d.loc[q].copy(); d['distance_kpc']=d.r_med_photogeo/1000.; d['distance_frac_halfwidth']=frac.loc[d.index]
    c=SkyCoord(ra=d.ra.to_numpy(float)*u.deg,dec=d.dec.to_numpy(float)*u.deg,distance=d.distance_kpc.to_numpy(float)*u.kpc,pm_ra_cosdec=d.pmra.to_numpy(float)*u.mas/u.yr,pm_dec=d.pmde.to_numpy(float)*u.mas/u.yr,radial_velocity=d.v_rad.to_numpy(float)*u.km/u.s,frame='icrs')
    frame=Galactocentric(galcen_distance=R0_KPC*u.kpc,z_sun=Z_SUN_KPC*u.kpc,galcen_v_sun=CartesianDifferential(np.array(V_SUN_CART_KMS)*u.km/u.s))
    g=c.transform_to(frame); x=g.cartesian.x.to_value(u.kpc); y=g.cartesian.y.to_value(u.kpc); z=g.cartesian.z.to_value(u.kpc); vx=g.velocity.d_x.to_value(u.km/u.s); vy=g.velocity.d_y.to_value(u.km/u.s); vz=g.velocity.d_z.to_value(u.km/u.s)
    R=np.sqrt(x*x+y*y); phi=(np.degrees(np.arctan2(y,x))+360)%360; Vr=(x*vx+y*vy)/R; vp=(-y*vx+x*vy)/R; sign=-1. if np.nanmedian(vp)<0 else 1.; Vphi=sign*vp
    d['R_gal_kpc']=R; d['phi_deg']=phi; d['Z_gal_kpc']=z; d['Vr_gal_kms']=Vr; d['Vphi_gal_kms']=Vphi; d['Vz_gal_kms']=vz; d['vphi_sign_applied']=sign
    d['R_bin_kpc']=np.floor(R/0.5)*0.5; d['absZ_bin_kpc']=np.floor(np.abs(z)/0.25)*0.25; d['phi_bin_deg']=np.floor(phi/15.)*15.
    return d

def make_tracer_cells(d,min_n=5):
    rows=[]; key=['R_bin_kpc','absZ_bin_kpc','phi_bin_deg']
    for k,g in d.groupby(key,observed=True):
        if len(g)<min_n: continue
        vp=g.Vphi_gal_kms.to_numpy(float); R=g.R_gal_kpc.to_numpy(float)
        rows.append({'R_bin_kpc':float(k[0]),'absZ_bin_kpc':float(k[1]),'phi_bin_deg':float(k[2]),'n_young':int(len(g)),'Vr_young_median_kms':float(np.nanmedian(g.Vr_gal_kms)),'Vphi_young_median_kms':float(np.nanmedian(vp)),'Vz_young_median_kms':float(np.nanmedian(g.Vz_gal_kms)),'acirc_proxy_young_median_kms2perkpc':float(np.nanmedian(vp*vp/R)),'teff_young_median_K':float(np.nanmedian(g.teff)),'distance_young_median_kpc':float(np.nanmedian(g.distance_kpc))})
    c=pd.DataFrame(rows)
    if c.empty:return c
    for col in ['Vr_young_median_kms','Vphi_young_median_kms','Vz_young_median_kms','acirc_proxy_young_median_kms2perkpc']:
        c[col+'_anom']=c[col]-c.groupby(['R_bin_kpc','absZ_bin_kpc'])[col].transform('median')
    return c

def residualize(v,C):
    v=np.asarray(v,float);C=np.asarray(C,float);m=np.isfinite(v)&np.all(np.isfinite(C),axis=1);out=np.full(len(v),np.nan)
    if m.sum()<12:return out
    fit=LinearRegression().fit(C[m],v[m]);out[m]=v[m]-fit.predict(C[m]);return out

def corr_stat(x,y):
    m=np.isfinite(x)&np.isfinite(y)
    if m.sum()<12:return np.nan,np.nan,int(m.sum())
    r,p=spearmanr(np.asarray(x)[m],np.asarray(y)[m]);return float(r),float(p),int(m.sum())

def permutation_family(d,predictors,outcomes,adjusted,nperm=10000):
    q=d.dropna(subset=predictors+outcomes+CONTROLS+['R_bin_kpc','absZ_bin_kpc']).copy()
    if len(q)<20:return {'n_cells':int(len(q)),'tests':{}}
    C=q[CONTROLS].to_numpy(float); X=np.column_stack([q[p].to_numpy(float) for p in predictors]);Y=np.column_stack([q[o].to_numpy(float) for o in outcomes])
    if adjusted:
        X=np.column_stack([residualize(X[:,j],C) for j in range(X.shape[1])]);Y=np.column_stack([residualize(Y[:,j],C) for j in range(Y.shape[1])])
    obs=np.full((len(predictors),len(outcomes)),np.nan);ps=np.full_like(obs,np.nan)
    for i in range(len(predictors)):
        for j in range(len(outcomes)):obs[i,j],ps[i,j],_=corr_stat(X[:,i],Y[:,j])
    counts=np.zeros_like(obs,int);mxcounts=np.zeros_like(obs,int);groups=q.groupby(['R_bin_kpc','absZ_bin_kpc']).indices;valid=0
    for _ in range(nperm):
        pi=np.arange(len(q))
        for inds in groups.values():
            inds=np.asarray(inds,int)
            if len(inds)>1:pi[inds]=RNG.permutation(inds)
        vals=np.full_like(obs,np.nan)
        for i in range(len(predictors)):
            for j in range(len(outcomes)):vals[i,j],_,_=corr_stat(X[pi,i],Y[:,j])
        if not np.any(np.isfinite(vals)):continue
        valid+=1;av=np.abs(vals);ao=np.abs(obs);counts+=np.nan_to_num(av>=ao,nan=False);mx=np.nanmax(av);mxcounts+=np.nan_to_num(mx>=ao,nan=False)
    tests={}
    for i,p in enumerate(predictors):
        tests[p]={}
        for j,o in enumerate(outcomes):tests[p][o]={'rho':float(obs[i,j]) if np.isfinite(obs[i,j]) else None,'p_spearman':float(ps[i,j]) if np.isfinite(ps[i,j]) else None,'p_perm_within_RZ':float((counts[i,j]+1)/(valid+1)) if valid else None,'p_maxT_all_history_outcome_tests':float((mxcounts[i,j]+1)/(valid+1)) if valid else None}
    return {'n_cells':int(len(q)),'adjusted_for_source_age_chemistry':adjusted,'n_permutations':valid,'tests':tests}

def analyze_sample(label,young,hist):
    cells=make_tracer_cells(young,5);key=['R_bin_kpc','absZ_bin_kpc','phi_bin_deg'];joined=hist.merge(cells,on=key,how='inner');outs=['Vr_young_median_kms_anom','Vphi_young_median_kms_anom','Vz_young_median_kms_anom','acirc_proxy_young_median_kms2perkpc_anom']
    un=permutation_family(joined,HISTORY,outs,False,10000);ad=permutation_family(joined,HISTORY,outs,True,10000);age=permutation_family(joined,['age_median_gyr_anom'],outs,False,10000);joined.to_csv(OUT/f'{label}_source_history_young_tracer_cells.csv',index=False)
    return {'young_stars':int(len(young)),'young_cells_n_ge5':int(len(cells)),'joined_source_history_cells':int(len(joined)),'R_range_joined_kpc':[float(joined.R_bin_kpc.min()),float(joined.R_bin_kpc.max())] if len(joined) else None,'unadjusted':un,'source_age_chemistry_adjusted':ad,'age_only_reference':age}

def main():
    raw=pd.read_csv(HOT,low_memory=False);young=build_phase_space(raw);young=young[young.R_gal_kpc.between(4,13)&young.Z_gal_kpc.abs().le(2)].copy();general=young[young.Vphi_gal_kms.between(120,320)&young.Vr_gal_kms.abs().le(180)&young.Vz_gal_kms.abs().le(150)].copy();cold=general[general.Vphi_gal_kms.between(190,250)&general.Vr_gal_kms.abs().le(80)&general.Vz_gal_kms.abs().le(80)].copy()
    hist=pd.read_csv(HIST);needed=['R_bin_kpc','absZ_bin_kpc','phi_bin_deg']+HISTORY+CONTROLS;hist=hist[needed].dropna().copy()
    keep=['sdss_id','gaia_dr3_source_id','ra','dec','distance_kpc','teff','snr','v_rad','e_v_rad','R_gal_kpc','phi_deg','Z_gal_kpc','Vr_gal_kms','Vphi_gal_kms','Vz_gal_kms','R_bin_kpc','absZ_bin_kpc','phi_bin_deg'];general[keep].to_csv(OUT/'young_hot_tracer_phase_space.csv.gz',index=False,compression='gzip')
    report={'analysis_name':'Milky Way Stage 4E independent young-tracer response to source-history map','raw_bossnet_hot_rows':int(len(raw)),'quality_6d_disk_rows':int(len(young)),'coordinate_model':{'galcen_distance_kpc':R0_KPC,'z_sun_kpc':Z_SUN_KPC,'galcen_v_sun_cartesian_kms':V_SUN_CART_KMS,'note':'Vphi sign standardized so median prograde disk rotation is positive; inference uses within-cell anomalies.'},'general_disk_sample':analyze_sample('general',general,hist),'cold_near_circular_sample':analyze_sample('cold',cold,hist),'primary_interpretation_rule':'Primary weight: source-history predictor survives within-R-|z| permutation, source age/FeH/aFe adjustment, family-wise maxT correction, and has consistent sign in general and cold independent young-tracer samples. Vphi^2/R is an acceleration proxy, not a full force measurement.'}
    (OUT/'stage4e_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
# trigger
