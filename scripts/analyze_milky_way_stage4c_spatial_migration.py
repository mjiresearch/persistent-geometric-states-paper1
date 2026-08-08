#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import Rbirth

OUT = Path('data/persistence_history/milky_way_stage4c_spatial_migration')
OUT.mkdir(parents=True, exist_ok=True)
MS_PATH = Path('data/external/sdss/dr20_minesweeper/minesweeper_v1.2.2.parquet')
STAGE2_CELLS = Path('data/persistence_history/milky_way_stage2/azimuthal_history_cells.csv')
RNG = np.random.default_rng(20260808)


def canon(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    return x.where(~x.isin(['', 'nan', 'None', '<NA>']))


def quality_mwm(d: pd.DataFrame) -> pd.DataFrame:
    need = ['Age','Age_err','R_gal','X_gal','Y_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal','FeH','aFe']
    m = np.ones(len(d), dtype=bool)
    for c in need:
        m &= np.isfinite(pd.to_numeric(d[c], errors='coerce'))
    m &= pd.to_numeric(d['Age'], errors='coerce').between(0.05,14.5)
    m &= (pd.to_numeric(d['Age_err'], errors='coerce') / pd.to_numeric(d['Age'], errors='coerce')).between(0,0.5)
    m &= pd.to_numeric(d['R_gal'], errors='coerce').between(3.0,20.0)
    m &= pd.to_numeric(d['Z_gal'], errors='coerce').abs().le(8.0)
    if 'snr' in d.columns:
        m &= pd.to_numeric(d['snr'], errors='coerce').fillna(0).ge(20)
    q = d.loc[m].copy()
    q['absZ'] = pd.to_numeric(q['Z_gal'], errors='coerce').abs()
    q['phi_deg'] = (np.degrees(np.arctan2(pd.to_numeric(q['Y_gal'], errors='coerce'),
                                          pd.to_numeric(q['X_gal'], errors='coerce'))) + 360.0) % 360.0
    q['R_bin_kpc'] = np.floor(pd.to_numeric(q['R_gal'], errors='coerce')/0.5)*0.5
    q['absZ_bin_kpc'] = np.floor(q['absZ']/0.25)*0.25
    q['phi_bin_deg'] = np.floor(q['phi_deg']/15.0)*15.0
    return q


def within_rz_perm(c: pd.DataFrame, xcol: str, ycol: str, nperm: int = 10000) -> dict:
    d = c[[xcol,ycol,'R_bin_kpc','absZ_bin_kpc']].dropna().copy()
    if len(d) < 20:
        return {'n_cells': int(len(d)), 'rho': None, 'p_spearman': None, 'p_perm_within_RZ': None}
    x = d[xcol].to_numpy(float); y = d[ycol].to_numpy(float)
    rho, p = spearmanr(x,y)
    groups = d.groupby(['R_bin_kpc','absZ_bin_kpc']).indices
    vals=[]
    for _ in range(nperm):
        xp=x.copy()
        for idx in groups.values():
            idx=np.asarray(idx,int)
            if len(idx)>1:
                xp[idx]=RNG.permutation(xp[idx])
        rr,_=spearmanr(xp,y)
        if np.isfinite(rr): vals.append(abs(float(rr)))
    vals=np.asarray(vals)
    pp=float((1+np.sum(vals>=abs(rho)))/(1+len(vals))) if len(vals) else None
    return {'n_cells':int(len(d)),'rho':float(rho),'p_spearman':float(p),'p_perm_within_RZ':pp}


def main() -> None:
    # Published birth-radius reconstruction on Ratcliffe's public APOGEE sample.
    ap = Rbirth.load_apogee().copy()
    grad = Rbirth.get_gradient('Anders23')
    feh0 = Rbirth.get_Feh0('Anders23')
    ap['Rbirth_kpc'] = np.asarray(Rbirth.get_Rb(age=ap['age'], feh=ap['feh'], gradientDF=grad, feh0DF=feh0), float)
    ap['Rguide_kpc'] = pd.to_numeric(ap['rguide'], errors='coerce')
    ap['deltaR_guide_kpc'] = ap['Rguide_kpc'] - ap['Rbirth_kpc']
    ap['outward_gt0p5'] = (ap['deltaR_guide_kpc'] > 0.5).astype(float)
    ap['inward_gt0p5'] = (ap['deltaR_guide_kpc'] < -0.5).astype(float)
    ap['outward_gt1'] = (ap['deltaR_guide_kpc'] > 1.0).astype(float)
    ap['inward_gt1'] = (ap['deltaR_guide_kpc'] < -1.0).astype(float)
    ap['_gaia'] = canon(ap['GAIAEDR3_SOURCE_ID'])
    ap = ap.dropna(subset=['_gaia','Rbirth_kpc','Rguide_kpc']).copy()

    ms = quality_mwm(pd.read_parquet(MS_PATH))
    ms['_gaia'] = canon(ms['source_id'])
    keep_ms = ['_gaia','source_id','R_gal','X_gal','Y_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal','FeH','aFe','Age',
               'R_bin_kpc','absZ_bin_kpc','phi_bin_deg']
    keep_ap = ['_gaia','APOGEE_ID','age','feh','Rbirth_kpc','Rguide_kpc','deltaR_guide_kpc',
               'outward_gt0p5','inward_gt0p5','outward_gt1','inward_gt1']
    j = ms[keep_ms].merge(ap[keep_ap], on='_gaia', how='inner', suffixes=('_mwm','_rbirth'))

    # External Stage-2 all-star spatial kinematic anomalies provide a present-location baseline.
    base = pd.read_csv(STAGE2_CELLS)
    key=['R_bin_kpc','absZ_bin_kpc','phi_bin_deg']
    kin_anom=['Vr_median_kms_anom','Vphi_median_kms_anom','Vz_median_kms_anom']
    base_small=base[key+['n']+kin_anom].copy()

    # Summarize migration history among crossmatched stars in the exact same spatial cells.
    rows=[]
    for k,g in j.groupby(key, observed=True):
        if len(g) < 5: continue
        rows.append({
            'R_bin_kpc':float(k[0]),'absZ_bin_kpc':float(k[1]),'phi_bin_deg':float(k[2]),
            'n_crossmatch':int(len(g)),
            'Rbirth_median_kpc':float(g['Rbirth_kpc'].median()),
            'Rguide_median_kpc':float(g['Rguide_kpc'].median()),
            'deltaR_guide_median_kpc':float(g['deltaR_guide_kpc'].median()),
            'abs_deltaR_guide_median_kpc':float(g['deltaR_guide_kpc'].abs().median()),
            'outward_guide_fraction_gt0p5':float(g['outward_gt0p5'].mean()),
            'inward_guide_fraction_gt0p5':float(g['inward_gt0p5'].mean()),
            'outward_guide_fraction_gt1':float(g['outward_gt1'].mean()),
            'inward_guide_fraction_gt1':float(g['inward_gt1'].mean()),
            'age_rbirth_sample_median_gyr':float(pd.to_numeric(g['age'], errors='coerce').median()),
        })
    cells=pd.DataFrame(rows)
    if not cells.empty:
        cells=cells.merge(base_small,on=key,how='inner')

    predictors=['Rbirth_median_kpc','deltaR_guide_median_kpc','abs_deltaR_guide_median_kpc',
                'outward_guide_fraction_gt0p5','inward_guide_fraction_gt0p5',
                'outward_guide_fraction_gt1','inward_guide_fraction_gt1','age_rbirth_sample_median_gyr']
    tests={}
    for p in predictors:
        tests[p]={}
        for y in kin_anom:
            tests[p][y]=within_rz_perm(cells,p,y) if not cells.empty else {'n_cells':0}

    # Matched-cell directional comparison at fixed present R,|z|.
    direction_summary={}
    if not cells.empty:
        for frac in ['outward_guide_fraction_gt1','inward_guide_fraction_gt1']:
            med=float(cells[frac].median())
            lo=cells[cells[frac] <= med]; hi=cells[cells[frac] > med]
            direction_summary[frac]={
                'median_split':med,'n_low_cells':int(len(lo)),'n_high_cells':int(len(hi)),
                'mean_Vr_anom_low':float(lo['Vr_median_kms_anom'].mean()) if len(lo) else None,
                'mean_Vr_anom_high':float(hi['Vr_median_kms_anom'].mean()) if len(hi) else None,
                'mean_Vphi_anom_low':float(lo['Vphi_median_kms_anom'].mean()) if len(lo) else None,
                'mean_Vphi_anom_high':float(hi['Vphi_median_kms_anom'].mean()) if len(hi) else None,
            }

    star_keep=['source_id','APOGEE_ID','R_gal','Z_gal','R_bin_kpc','absZ_bin_kpc','phi_bin_deg','Vr_gal','Vphi_gal','Vz_gal',
               'Rbirth_kpc','Rguide_kpc','deltaR_guide_kpc','outward_gt1','inward_gt1','Age','age','FeH','feh']
    j[star_keep].to_csv(OUT/'rbirth_mwm_exact_crossmatch.csv.gz',index=False,compression='gzip')
    cells.to_csv(OUT/'spatial_migration_cells.csv',index=False)

    report={
        'analysis_name':'Milky Way Stage 4C star-level birth-radius spatial migration screen',
        'ratcliffe_input_rows':int(len(Rbirth.load_apogee())),
        'mwm_quality_rows':int(len(ms)),
        'exact_gaia_crossmatch_rows':int(len(j)),
        'exact_gaia_crossmatch_unique_ids':int(j['_gaia'].nunique()) if len(j) else 0,
        'spatial_cells_crossmatch_n_ge5_and_stage2_baseline':int(len(cells)),
        'cell_geometry':{'R_kpc':0.5,'absZ_kpc':0.25,'phi_deg':15},
        'migration_definition':'Rguide - Rbirth; positive = outward guiding-center migration',
        'tests_within_same_R_absZ_strata':tests,
        'direction_median_split_summary':direction_summary,
        'guardrail':(
            'This is a local kinematic-residual precursor, not yet a local gravitational force residual. '
            'The outcomes are non-axisymmetric streaming anomalies relative to the Stage-2 axisymmetric R-|z| baseline. '
            'A positive result would justify constructing a spatial Jeans/force-residual map; a null result would argue that the radial Stage-4B signal was decomposition-specific or radial-structure driven. '
            'Rbirth remains an inferred history variable based on age and metallicity.'
        )
    }
    (OUT/'stage4c_summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
