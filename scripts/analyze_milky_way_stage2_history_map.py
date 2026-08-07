#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path('data/persistence_history/milky_way_stage2')
ROOT.mkdir(parents=True, exist_ok=True)
MS_PATH = Path('data/external/sdss/dr20_minesweeper/minesweeper_v1.2.2.parquet')
RNG = np.random.default_rng(20260807)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    need = ['Age','Age_err','R_gal','X_gal','Y_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal','FeH','aFe','ecc_mw22','R_apo_mw22','R_peri_mw22','z_max_mw22']
    mask = np.ones(len(d), dtype=bool)
    for c in need:
        mask &= np.isfinite(pd.to_numeric(d[c], errors='coerce'))
    mask &= d['Age'].between(0.05,14.5)
    mask &= (d['Age_err'] / d['Age']).between(0,0.5)
    mask &= d['R_gal'].between(3.0,20.0)
    mask &= d['Z_gal'].abs().le(8.0)
    if 'snr' in d.columns:
        mask &= pd.to_numeric(d['snr'], errors='coerce').fillna(0).ge(20)
    d = d.loc[mask].copy()
    d['absZ'] = d['Z_gal'].abs()
    d['phi_deg'] = (np.degrees(np.arctan2(d['Y_gal'], d['X_gal'])) + 360.0) % 360.0
    d['R_bin'] = np.floor(d['R_gal']/0.5)*0.5
    d['Z_bin'] = np.floor(d['absZ']/0.25)*0.25
    d['phi_bin'] = np.floor(d['phi_deg']/15.0)*15.0
    d['radial_excursion'] = d['R_apo_mw22'] - d['R_peri_mw22']
    return d


def make_cells(d: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for (r,z,p),g in d.groupby(['R_bin','Z_bin','phi_bin'], observed=True):
        if len(g) < 20:
            continue
        rows.append({
            'R_bin_kpc':r,'absZ_bin_kpc':z,'phi_bin_deg':p,'n':len(g),
            'age_median_gyr':g['Age'].median(),'old_fraction_gt8':(g['Age']>8).mean(),
            'FeH_median':g['FeH'].median(),'aFe_median':g['aFe'].median(),
            'ecc_median':g['ecc_mw22'].median(),'zmax_median_kpc':g['z_max_mw22'].median(),
            'radial_excursion_median_kpc':g['radial_excursion'].median(),
            'Vr_median_kms':g['Vr_gal'].median(),'Vphi_median_kms':g['Vphi_gal'].median(),'Vz_median_kms':g['Vz_gal'].median(),
            'Vr_sigma_kms':g['Vr_gal'].std(ddof=1),'Vphi_sigma_kms':g['Vphi_gal'].std(ddof=1),'Vz_sigma_kms':g['Vz_gal'].std(ddof=1),
        })
    c = pd.DataFrame(rows)
    if c.empty:
        return c
    # Remove smooth axisymmetric R-|z| trend: anomalies are deviations among azimuth bins at the same R, |z|.
    hist_cols = ['age_median_gyr','old_fraction_gt8','FeH_median','aFe_median','ecc_median','zmax_median_kpc','radial_excursion_median_kpc']
    kin_cols = ['Vr_median_kms','Vphi_median_kms','Vz_median_kms']
    for col in hist_cols + kin_cols:
        baseline = c.groupby(['R_bin_kpc','absZ_bin_kpc'])[col].transform('median')
        c[col+'_anom'] = c[col] - baseline
    return c


def perm_spearman(c: pd.DataFrame, xcol: str, ycol: str, nperm=500) -> dict:
    x = c[xcol].to_numpy(float); y = c[ycol].to_numpy(float)
    m = np.isfinite(x)&np.isfinite(y)
    cc = c.loc[m].copy(); x=x[m]; y=y[m]
    if len(x) < 20:
        return {'n':int(len(x)),'rho':None,'p_spearman':None,'p_perm':None}
    rho,p = spearmanr(x,y)
    # Shuffle x only within the same R-|z| stratum, preserving radial/vertical selection structure.
    perm=[]
    strata = cc.groupby(['R_bin_kpc','absZ_bin_kpc']).indices
    for _ in range(nperm):
        xp = x.copy()
        for idx in strata.values():
            idx=np.asarray(idx,dtype=int)
            if len(idx)>1:
                xp[idx]=RNG.permutation(xp[idx])
        rr,_=spearmanr(xp,y)
        perm.append(rr)
    perm=np.asarray(perm)
    pperm=(1+np.sum(np.abs(perm)>=abs(rho)))/(1+len(perm))
    return {'n':int(len(x)),'rho':float(rho),'p_spearman':float(p),'p_perm_within_RZ':float(pperm)}


def main():
    d=clean(pd.read_parquet(MS_PATH))
    c=make_cells(d)
    c.to_csv(ROOT/'azimuthal_history_cells.csv',index=False)
    history = ['age_median_gyr_anom','old_fraction_gt8_anom','FeH_median_anom','aFe_median_anom','ecc_median_anom','zmax_median_kpc_anom','radial_excursion_median_kpc_anom']
    kin = ['Vr_median_kms_anom','Vphi_median_kms_anom','Vz_median_kms_anom']
    corr={}
    for h in history:
        corr[h]={}
        for k in kin:
            corr[h][k]=perm_spearman(c,h,k)
    # Rank cells as candidates only; this is not a persistence detection statistic.
    if not c.empty:
        score_cols=[]
        for col in ['age_median_gyr_anom','old_fraction_gt8_anom','FeH_median_anom','aFe_median_anom']:
            sd=c[col].std(ddof=1)
            z=(c[col]-c[col].median())/(sd if np.isfinite(sd) and sd>0 else 1)
            name=col+'_z'; c[name]=z; score_cols.append(name)
        kin_score=[]
        for col in ['Vr_median_kms_anom','Vphi_median_kms_anom','Vz_median_kms_anom']:
            sd=c[col].std(ddof=1)
            z=(c[col]-c[col].median())/(sd if np.isfinite(sd) and sd>0 else 1)
            name=col+'_z'; c[name]=z; kin_score.append(name)
        c['history_anomaly_strength']=np.sqrt(np.sum(c[score_cols].to_numpy()**2,axis=1))
        c['kinematic_anomaly_strength']=np.sqrt(np.sum(c[kin_score].to_numpy()**2,axis=1))
        c['candidate_score']=c['history_anomaly_strength']*c['kinematic_anomaly_strength']
        c.sort_values('candidate_score',ascending=False).head(50).to_csv(ROOT/'top_candidate_cells.csv',index=False)
    report={
        'analysis_name':'Milky Way Stage 2 azimuthal source-history anomaly screen',
        'quality_rows':int(len(d)),
        '3d_cells_n_ge_20':int(len(c)),
        'cell_geometry':{'R_bin_kpc':0.5,'absZ_bin_kpc':0.25,'phi_bin_deg':15},
        'correlations':corr,
        'guardrail':'Correlations here identify candidate non-axisymmetric history/kinematic structure. Bar/spiral dynamics, accretion, selection effects and ordinary Galactic evolution are standard explanations. Persistence requires a force residual tied to present baryons and an independently reconstructed source history.',
    }
    (ROOT/'stage2_summary.json').write_text(json.dumps(report,indent=2))
    # Rewrite full cells with candidate diagnostics if calculated.
    c.to_csv(ROOT/'azimuthal_history_cells.csv',index=False)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
