#!/usr/bin/env python3
# Trigger Stage 3 rotation-residual run after workflow creation.
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from astropy import units as u
from galpy.potential import vcirc, mwpotentials

OUT = Path('data/persistence_history/milky_way_stage3')
OUT.mkdir(parents=True, exist_ok=True)
CELLS = Path('data/persistence_history/milky_way_stage2/azimuthal_history_cells.csv')

EILERS_R0_KPC = 8.122
EILERS_V0_KMS = 229.0
EILERS_SLOPE_KMS_PER_KPC = -1.7


def weighted_mean(g: pd.DataFrame, col: str) -> float:
    x = pd.to_numeric(g[col], errors='coerce').to_numpy(float)
    w = pd.to_numeric(g['n'], errors='coerce').to_numpy(float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    if not np.any(m):
        return np.nan
    return float(np.average(x[m], weights=w[m]))


def as_kms(v) -> float:
    if hasattr(v, 'to_value'):
        return float(v.to_value(u.km/u.s))
    return float(v)


def quadratic_detrend(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    m = np.isfinite(x) & np.isfinite(y)
    out = np.full_like(y, np.nan, dtype=float)
    if m.sum() < 5:
        return out
    deg = 2 if m.sum() >= 6 else 1
    coef = np.polyfit(x[m], y[m], deg)
    out[m] = y[m] - np.polyval(coef, x[m])
    return out


def corr_stats(r: np.ndarray, x: np.ndarray, y: np.ndarray) -> dict:
    m = np.isfinite(r) & np.isfinite(x) & np.isfinite(y)
    rr, xx, yy = r[m], x[m], y[m]
    if len(rr) < 6:
        return {'n': int(len(rr)), 'rho_raw': None, 'p_raw': None,
                'rho_detrended': None, 'p_detrended': None,
                'rho_first_difference': None, 'p_first_difference': None,
                'p_circular_shift_raw': None}
    rho, p = spearmanr(xx, yy)
    xd = quadratic_detrend(rr, xx)
    yd = quadratic_detrend(rr, yy)
    md = np.isfinite(xd) & np.isfinite(yd)
    rho_d, p_d = spearmanr(xd[md], yd[md])
    order = np.argsort(rr)
    dx = np.diff(xx[order]); dy = np.diff(yy[order])
    rho_diff, p_diff = spearmanr(dx, dy) if len(dx) >= 5 else (np.nan, np.nan)
    shifted = []
    for k in range(1, len(xx)):
        sr, _ = spearmanr(np.roll(xx, k), yy)
        if np.isfinite(sr):
            shifted.append(abs(float(sr)))
    p_shift = ((1 + np.sum(np.asarray(shifted) >= abs(rho))) /
               (1 + len(shifted))) if shifted else np.nan
    return {
        'n': int(len(rr)),
        'rho_raw': float(rho), 'p_raw': float(p),
        'rho_detrended': float(rho_d), 'p_detrended': float(p_d),
        'rho_first_difference': float(rho_diff) if np.isfinite(rho_diff) else None,
        'p_first_difference': float(p_diff) if np.isfinite(p_diff) else None,
        'p_circular_shift_raw': float(p_shift) if np.isfinite(p_shift) else None,
    }


def main() -> None:
    cells = pd.read_csv(CELLS)
    cells = cells[cells['R_bin_kpc'].between(5.0, 20.0)].copy()

    history_cols = [
        'age_median_gyr', 'old_fraction_gt8', 'FeH_median', 'aFe_median',
        'ecc_median', 'zmax_median_kpc', 'radial_excursion_median_kpc',
        'history_anomaly_strength', 'kinematic_anomaly_strength'
    ]
    rows = []
    for r, g in cells.groupby('R_bin_kpc'):
        row = {'R_kpc': float(r), 'stars_weight': int(pd.to_numeric(g['n'], errors='coerce').fillna(0).sum()),
               'azimuth_vertical_cells': int(len(g))}
        for c in history_cols:
            if c in g.columns:
                row[c] = weighted_mean(g, c)
        rows.append(row)
    radial = pd.DataFrame(rows).sort_values('R_kpc').reset_index(drop=True)

    pot = mwpotentials.McMillan17
    component_names = [type(p).__name__ for p in pot]
    baryons = [p for p in pot if 'NFW' not in type(p).__name__]
    halos = [p for p in pot if 'NFW' in type(p).__name__]
    if not baryons or not halos:
        raise RuntimeError(f'Unexpected McMillan17 component structure: {component_names}')

    vbar = []
    vhalo_model = []
    vtotal_model = []
    vobs = []
    for r in radial['R_kpc'].to_numpy(float):
        vbar.append(as_kms(vcirc(baryons, r*u.kpc)))
        vhalo_model.append(as_kms(vcirc(halos, r*u.kpc)))
        vtotal_model.append(as_kms(vcirc(pot, r*u.kpc)))
        vobs.append(EILERS_V0_KMS + EILERS_SLOPE_KMS_PER_KPC*(r-EILERS_R0_KPC))

    radial['Vobs_eilers_kms'] = np.asarray(vobs)
    radial['Vbar_mcmillan17_kms'] = np.asarray(vbar)
    radial['Vhalo_mcmillan17_kms'] = np.asarray(vhalo_model)
    radial['Vtotal_mcmillan17_kms'] = np.asarray(vtotal_model)
    residual_v2 = radial['Vobs_eilers_kms']**2 - radial['Vbar_mcmillan17_kms']**2
    radial['Vres2_kms2'] = residual_v2
    radial['Vres_equiv_kms'] = np.sqrt(np.clip(residual_v2, 0, None))
    radial['gres_kms2_per_kpc'] = residual_v2 / radial['R_kpc']
    radial['mass_discrepancy_fraction_v2'] = residual_v2 / (radial['Vobs_eilers_kms']**2)
    radial['baryon_fraction_v2'] = (radial['Vbar_mcmillan17_kms']**2) / (radial['Vobs_eilers_kms']**2)
    radial['model_halo_minus_empirical_residual_kms'] = radial['Vhalo_mcmillan17_kms'] - radial['Vres_equiv_kms']

    r = radial['R_kpc'].to_numpy(float)
    target_cols = ['Vres_equiv_kms', 'gres_kms2_per_kpc', 'mass_discrepancy_fraction_v2']
    test_history = [c for c in history_cols if c in radial.columns]
    correlations = {}
    for h in test_history:
        correlations[h] = {}
        for t in target_cols:
            correlations[h][t] = corr_stats(r, radial[h].to_numpy(float), radial[t].to_numpy(float))

    radial.to_csv(OUT/'milky_way_rotation_residual_history.csv', index=False)
    radial.to_parquet(OUT/'milky_way_rotation_residual_history.parquet', index=False)

    checkpoints = {}
    for rc in [6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0]:
        if radial.empty:
            continue
        i = int(np.argmin(np.abs(radial['R_kpc'].to_numpy(float)-rc)))
        q = radial.iloc[i]
        checkpoints[str(rc)] = {
            'R_kpc': float(q['R_kpc']),
            'Vobs_kms': float(q['Vobs_eilers_kms']),
            'Vbar_kms': float(q['Vbar_mcmillan17_kms']),
            'Vres_equiv_kms': float(q['Vres_equiv_kms']),
            'mass_discrepancy_fraction_v2': float(q['mass_discrepancy_fraction_v2']),
        }

    report = {
        'analysis_name': 'Milky Way Stage 3 baryonic rotation residual versus source-history screen',
        'radial_bins': int(len(radial)),
        'radial_range_kpc': [float(radial['R_kpc'].min()), float(radial['R_kpc'].max())] if len(radial) else None,
        'observed_rotation_reference': {
            'reference': 'Eilers et al. 2019 published linear circular-speed summary',
            'R0_kpc': EILERS_R0_KPC,
            'V0_kms': EILERS_V0_KMS,
            'slope_kms_per_kpc': EILERS_SLOPE_KMS_PER_KPC,
            'validity_range_kpc': [5.0, 25.0]
        },
        'baryonic_model_reference': {
            'reference': 'McMillan 2017 as implemented in galpy McMillan17',
            'galpy_components': component_names,
            'baryonic_components_rule': 'all McMillan17 components except NFWPotential',
            'halo_components_rule': 'NFWPotential only'
        },
        'positive_empirical_baryonic_deficit_bins': int((radial['Vres2_kms2'] > 0).sum()),
        'fraction_positive_empirical_baryonic_deficit_bins': float((radial['Vres2_kms2'] > 0).mean()),
        'checkpoints': checkpoints,
        'history_residual_correlations': correlations,
        'guardrail': (
            'This is a screening comparison, not a persistence detection. The observed curve is represented by the '
            'Eilers et al. linear summary, and the baryonic prediction is one published Milky Way mass model. '
            'Baryonic morphology uncertainties, Jeans/asymmetric-drift systematics, radial selection, and ordinary '
            'Galactic evolution remain major confounders. Raw radial correlations are not persuasive unless they '
            'survive detrending/first-difference or a later spatial force-residual test.'
        )
    }
    (OUT/'stage3_summary.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
