#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

OUT = Path('data/persistence_history/milky_way_stage3c_interaction')
OUT.mkdir(parents=True, exist_ok=True)

MC = Path('data/persistence_history/milky_way_stage3/milky_way_rotation_residual_history.csv')
MG = Path('data/persistence_history/milky_way_stage3b_mcgaugh/mcgaugh_history_residual_join.csv')
RNG = np.random.default_rng(20260807)

HISTORY = [
    'age_median_gyr','old_fraction_gt8','FeH_median','aFe_median',
    'ecc_median','zmax_median_kpc','radial_excursion_median_kpc'
]


def detrend(r: np.ndarray, y: np.ndarray) -> np.ndarray:
    m = np.isfinite(r) & np.isfinite(y)
    out = np.full_like(y, np.nan, dtype=float)
    if m.sum() < 6:
        return out
    c = np.polyfit(r[m], y[m], 2)
    out[m] = y[m] - np.polyval(c, r[m])
    return out


def corr(r: np.ndarray, x: np.ndarray, y: np.ndarray) -> dict:
    m = np.isfinite(r) & np.isfinite(x) & np.isfinite(y)
    r, x, y = r[m], x[m], y[m]
    if len(r) < 6:
        return {'n': int(len(r))}
    raw = spearmanr(x, y)
    xd, yd = detrend(r, x), detrend(r, y)
    det = spearmanr(xd, yd)
    order = np.argsort(r)
    dif = spearmanr(np.diff(x[order]), np.diff(y[order]))
    return {
        'n': int(len(r)),
        'rho_raw': float(raw.statistic), 'p_raw': float(raw.pvalue),
        'rho_detrended': float(det.statistic), 'p_detrended': float(det.pvalue),
        'rho_first_difference': float(dif.statistic), 'p_first_difference': float(dif.pvalue),
    }


def maxT_permutation(r: np.ndarray, d: pd.DataFrame, target: str, nperm: int = 20000) -> dict:
    y = detrend(r, d[target].to_numpy(float))
    xs = np.column_stack([detrend(r, d[h].to_numpy(float)) for h in HISTORY])
    yr = rankdata(y).astype(float)
    xr = np.column_stack([rankdata(xs[:,j]) for j in range(xs.shape[1])]).astype(float)
    yr = (yr - yr.mean()) / yr.std(ddof=0)
    xr = (xr - xr.mean(axis=0)) / xr.std(axis=0, ddof=0)
    obs = np.abs((xr * yr[:,None]).mean(axis=0))
    raw_counts = np.zeros(len(HISTORY), dtype=int)
    max_counts = np.zeros(len(HISTORY), dtype=int)
    for _ in range(nperm):
        yp = RNG.permutation(yr)
        vals = np.abs((xr * yp[:,None]).mean(axis=0))
        raw_counts += vals >= obs - 1e-12
        max_counts += vals.max() >= obs - 1e-12
    return {
        h: {
            'abs_rho_detrended': float(obs[i]),
            'p_perm': float((raw_counts[i]+1)/(nperm+1)),
            'p_maxT_across_history_proxies': float((max_counts[i]+1)/(nperm+1)),
        } for i,h in enumerate(HISTORY)
    }


def prepare_mcmillan() -> pd.DataFrame:
    d = pd.read_csv(MC)
    d = d[(d['stars_weight'] >= 100) & (d['azimuth_vertical_cells'] >= 5)].copy()
    d['g_b_kms2_per_kpc'] = d['Vbar_mcmillan17_kms']**2 / d['R_kpc']
    d['chi_interaction'] = d['gres_kms2_per_kpc'] / d['g_b_kms2_per_kpc']
    d['chi_interaction_v2'] = d['Vres2_kms2'] / (d['Vbar_mcmillan17_kms']**2)
    return d


def prepare_mcgaugh() -> pd.DataFrame:
    d = pd.read_csv(MG)
    d = d[(d['stars_weight'] >= 100) & (d['cells'] >= 5)].copy()
    d['g_b_kms2_per_kpc'] = d['Vbar_mcgaugh_kms']**2 / d['R_kpc']
    d['chi_interaction'] = d['gres_kms2_per_kpc'] / d['g_b_kms2_per_kpc']
    d['chi_interaction_v2'] = d['Vres2_kms2'] / (d['Vbar_mcgaugh_kms']**2)
    return d


def analyze(label: str, d: pd.DataFrame) -> dict:
    r = d['R_kpc'].to_numpy(float)
    targets = ['gres_kms2_per_kpc','chi_interaction']
    correlations = {}
    for h in HISTORY:
        correlations[h] = {t: corr(r, d[h].to_numpy(float), d[t].to_numpy(float)) for t in targets}
    return {
        'label': label,
        'n_supported_bins': int(len(d)),
        'R_range_kpc': [float(d.R_kpc.min()), float(d.R_kpc.max())],
        'correlations': correlations,
        'interaction_maxT_permutation': maxT_permutation(r, d, 'chi_interaction'),
    }


def mc_mcgaugh(d: pd.DataFrame, nmc: int = 2000) -> dict:
    r = d['R_kpc'].to_numpy(float)
    vb = d['Vbar_mcgaugh_kms'].to_numpy(float)
    vo = d['Vobs_mcgaugh_kms'].to_numpy(float)
    hi = d['Vobs_err_hi_kms'].to_numpy(float)
    lo = d['Vobs_err_lo_kms'].to_numpy(float)
    gb = vb**2/r
    tracks = {h: [] for h in HISTORY}
    for _ in range(nmc):
        z = RNG.normal(size=len(d))
        sig = np.where(z >= 0, hi, lo)
        vv = vo + z*sig
        gres = (vv**2-vb**2)/r
        chi = gres/gb
        yd = detrend(r, chi)
        for h in HISTORY:
            xd = detrend(r, d[h].to_numpy(float))
            tracks[h].append(float(spearmanr(xd, yd).statistic))
    out = {}
    for h, vals in tracks.items():
        a = np.asarray(vals)
        out[h] = {
            'n_mc': nmc,
            'rho_detrended_median': float(np.median(a)),
            'rho_detrended_q16': float(np.quantile(a, .16)),
            'rho_detrended_q84': float(np.quantile(a, .84)),
            'fraction_positive': float(np.mean(a > 0)),
        }
    return out


def main() -> None:
    mcm = prepare_mcmillan()
    mcg = prepare_mcgaugh()
    mcm.to_csv(OUT/'mcmillan_interaction_screen.csv', index=False)
    mcg.to_csv(OUT/'mcgaugh_interaction_screen.csv', index=False)

    report = {
        'analysis_name': 'Milky Way Stage 3C inherited-contemporary interaction screen',
        'hypothesis_screened': (
            'Leading multiplicative surrogate: Delta g approximately proportional to g_b * H. '
            'Therefore chi_interaction = Delta g / g_b is the observational quantity compared with source-history proxies.'
        ),
        'important_limitation': (
            'This is not a derivation of the manuscript interaction tensor I_mu_nu[h^(b),H]. '
            'It is the lowest-complexity, zero-new-parameter multiplicative screen motivated by the revised Section II. '
            'The public age/chemistry/orbit variables remain proxies for source history rather than a reconstructed H field.'
        ),
        'mcmillan17_eilers': analyze('McMillan17 baryons + Eilers circular-speed summary', mcm),
        'mcgaugh2019': analyze('McGaugh 2019 independent baryonic decomposition and rotation curve', mcg),
        'mcgaugh_velocity_uncertainty_monte_carlo': mc_mcgaugh(mcg),
        'interpretation_rule': (
            'Raw radial correlations are not evidence because both history tracers and chi_interaction can vary smoothly with radius. '
            'Primary weight is assigned to quadratic-detrended, first-difference, permutation, maxT-corrected, and independent-baryonic-model consistency.'
        ),
    }
    (OUT/'stage3c_summary.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
