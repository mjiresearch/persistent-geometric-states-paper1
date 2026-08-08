#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from galpy.potential import mwpotentials, evaluateRforces, evaluatezforces
from galpy.util.conversion import get_physical

OUT = Path('data/persistence_history/milky_way_stage6a_pulsar_acceleration')
OUT.mkdir(parents=True, exist_ok=True)
CAT = Path('data/external/galactic_acceleration/moran2024_pulsar_accelerations.csv')

KPC_M = 3.085677581491367e19
MORAN_AX_PRIME = 0.39  # units 1e-10 m s^-2 kpc^-1
MORAN_AZ_PRIME = -0.70
SUN_CONFIGS = [
    ('R8.122_z0', 8.122, 0.0),
    ('R8.200_z0', 8.200, 0.0),
    ('R8.210_z0', 8.210, 0.0),
    ('R8.230_z0', 8.230, 0.0),
    ('R8.210_z0.0208', 8.210, 0.0208),
]


def huber_location(x, scale=None, c=1.345, maxiter=100):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan
    mu = float(np.median(x))
    if scale is None:
        mad = 1.4826 * np.median(np.abs(x - mu))
        scale = float(mad if mad > 0 else np.std(x))
    if not np.isfinite(scale) or scale <= 0:
        return mu
    for _ in range(maxiter):
        r = (x - mu) / scale
        w = np.ones_like(r)
        m = np.abs(r) > c
        w[m] = c / np.abs(r[m])
        new = float(np.sum(w * x) / np.sum(w))
        if abs(new - mu) < 1e-12:
            break
        mu = new
    return mu


def robust_summary(obs, pred, sigma, mask):
    o = np.asarray(obs, float)[mask]
    p = np.asarray(pred, float)[mask]
    s = np.asarray(sigma, float)[mask]
    res = o - p
    z = res / s
    good = np.isfinite(o) & np.isfinite(p) & np.isfinite(s) & (s > 0)
    o, p, s, res, z = o[good], p[good], s[good], res[good], z[good]
    if len(o) == 0:
        return {'n': 0}
    rho, prho = spearmanr(o, p) if len(o) >= 3 else (np.nan, np.nan)
    return {
        'n': int(len(o)),
        'median_observed_1e10': float(np.median(o)),
        'median_predicted_1e10': float(np.median(p)),
        'median_residual_1e10': float(np.median(res)),
        'huber_residual_1e10': float(huber_location(res)),
        'median_abs_residual_1e10': float(np.median(np.abs(res))),
        'median_abs_standardized_residual': float(np.median(np.abs(z))),
        'naive_chi2': float(np.sum(z*z)),
        'naive_reduced_chi2': float(np.mean(z*z)),
        'spearman_observed_predicted_rho': float(rho) if np.isfinite(rho) else None,
        'spearman_observed_predicted_p': float(prho) if np.isfinite(prho) else None,
        'n_abs_z_gt3': int(np.sum(np.abs(z) > 3)),
    }


def force_scale_m_s2(vo_kms, ro_kpc):
    return (vo_kms * 1000.0)**2 / (ro_kpc * KPC_M)


def accel_xyz(pot, x_kpc, y_kpc, z_kpc, ro, vo):
    R = float(np.hypot(x_kpc, y_kpc))
    if R <= 0:
        raise ValueError('R=0 not supported')
    Rn = R / ro
    zn = z_kpc / ro
    fR = float(evaluateRforces(pot, Rn, zn, use_physical=False))
    fz = float(evaluatezforces(pot, Rn, zn, use_physical=False))
    scale = force_scale_m_s2(vo, ro)
    aR = fR * scale
    az = fz * scale
    return np.array([aR * x_kpc / R, aR * y_kpc / R, az], float)


def los_prediction(pot, rb, rsun, ro, vo):
    dr = rb - rsun
    dist = np.linalg.norm(dr)
    if dist <= 0:
        return np.nan
    rhat = dr / dist
    ab = accel_xyz(pot, *rb, ro, vo)
    asun = accel_xyz(pot, *rsun, ro, vo)
    # Moran Eq. 4 is the difference in gravitational acceleration projected along Earth->pulsar LOS.
    return float(np.dot(ab - asun, rhat))


def moran_linear_prediction(rb, rsun):
    dr = rb - rsun
    dist = np.linalg.norm(dr)
    if dist <= 0:
        return np.nan
    rhat = dr / dist
    # Their Eq. 5 models the local differential acceleration vector in x and z.
    avec = np.array([MORAN_AX_PRIME * dr[0], 0.0, MORAN_AZ_PRIME * dr[2]], float)
    return float(np.dot(avec, rhat))


def main():
    d = pd.read_csv(CAT)
    for c in ['x_pc','y_pc','z_pc','aGal_1e10_m_s2','aGal_err_1e10_m_s2']:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d = d.dropna(subset=['x_pc','y_pc','z_pc','aGal_1e10_m_s2','aGal_err_1e10_m_s2']).copy()

    pot = mwpotentials.McMillan17
    component_names = [type(p).__name__ for p in pot]
    baryons = [p for p in pot if type(p).__name__ != 'NFWPotential']
    halos = [p for p in pot if type(p).__name__ == 'NFWPotential']
    if not baryons or not halos:
        raise RuntimeError(f'Unexpected McMillan17 component structure: {component_names}')
    physical = get_physical(pot)
    ro = float(physical['ro'])
    vo = float(physical['vo'])

    obs = d['aGal_1e10_m_s2'].to_numpy(float)
    sig = d['aGal_err_1e10_m_s2'].to_numpy(float)
    masks = {
        'all_29': np.ones(len(d), bool),
        'exclude_five_ge3sigma_model_outliers': d['model_outlier_ge3sigma'].to_numpy(int) == 0,
        'authors_modified_catalog_rule': d['modified_catalog_excluded'].to_numpy(int) == 0,
        'exclude_both_flag_sets': (d['model_outlier_ge3sigma'].to_numpy(int) == 0) & (d['modified_catalog_excluded'].to_numpy(int) == 0),
    }

    configs = {}
    primary_table = None
    for label, rsun_x, rsun_z in SUN_CONFIGS:
        rsun = np.array([rsun_x, 0.0, rsun_z], float)
        pb, pt, pl = [], [], []
        distances = []
        for _, row in d.iterrows():
            rb = np.array([row.x_pc, row.y_pc, row.z_pc], float) / 1000.0
            distances.append(float(np.linalg.norm(rb-rsun)))
            pb.append(los_prediction(baryons, rb, rsun, ro, vo) / 1e-10)
            pt.append(los_prediction(pot, rb, rsun, ro, vo) / 1e-10)
            pl.append(moran_linear_prediction(rb, rsun))
        pb = np.asarray(pb); pt = np.asarray(pt); pl = np.asarray(pl)
        tab = d.copy()
        tab['sun_R_kpc'] = rsun_x
        tab['sun_z_kpc'] = rsun_z
        tab['distance_from_assumed_sun_kpc'] = distances
        tab['a_moran_linear_pred_1e10'] = pl
        tab['a_mcmillan_baryon_pred_1e10'] = pb
        tab['a_mcmillan_total_pred_1e10'] = pt
        tab['resid_moran_linear_1e10'] = obs-pl
        tab['resid_baryon_1e10'] = obs-pb
        tab['resid_total_1e10'] = obs-pt
        tab['zresid_baryon'] = (obs-pb)/sig
        tab['zresid_total'] = (obs-pt)/sig
        tab.to_csv(OUT/f'pulsar_residuals_{label}.csv', index=False)
        if label == 'R8.210_z0':
            primary_table = tab.copy()
        configs[label] = {
            'sun_position_kpc': [rsun_x, 0.0, rsun_z],
            'distance_range_kpc': [float(np.min(distances)), float(np.max(distances))],
            'moran_linear_validation': {k: robust_summary(obs, pl, sig, m) for k,m in masks.items()},
            'mcmillan17_baryons_only': {k: robust_summary(obs, pb, sig, m) for k,m in masks.items()},
            'mcmillan17_full_baryons_plus_nfw': {k: robust_summary(obs, pt, sig, m) for k,m in masks.items()},
        }

    # Sun-position sensitivity of the baryonic residual on non-outlier pulsars.
    clean_label = 'exclude_both_flag_sets'
    sensitivity = []
    for label in configs:
        s = configs[label]['mcmillan17_baryons_only'][clean_label]
        sensitivity.append({
            'config': label,
            'n': s['n'],
            'median_residual_1e10': s['median_residual_1e10'],
            'huber_residual_1e10': s['huber_residual_1e10'],
            'median_abs_residual_1e10': s['median_abs_residual_1e10'],
        })

    if primary_table is not None:
        # Rank the clean pulsars by how strongly they prefer a residual beyond baryons.
        q = primary_table[(primary_table.model_outlier_ge3sigma == 0) & (primary_table.modified_catalog_excluded == 0)].copy()
        q['abs_zresid_baryon'] = np.abs(q['zresid_baryon'])
        q.sort_values('abs_zresid_baryon', ascending=False).to_csv(OUT/'primary_clean_pulsars_ranked_by_baryon_residual.csv', index=False)

    report = {
        'analysis_name': 'Milky Way Stage 6A direct binary-pulsar acceleration residual',
        'input_pulsars': int(len(d)),
        'observable': 'direct Earth-to-pulsar differential line-of-sight Galactic acceleration from binary timing',
        'observable_units': 'catalog values are in 1e-10 m s^-2',
        'moran_reference_linear_model': {
            'a_x_prime_1e10_m_s2_per_kpc': MORAN_AX_PRIME,
            'a_z_prime_1e10_m_s2_per_kpc': MORAN_AZ_PRIME,
            'purpose': 'sign/coordinate sanity check only, not the baryonic residual model',
        },
        'baryonic_model_reference': {
            'reference': 'McMillan 2017 as implemented in galpy McMillan17, identical component rule to Stage 3',
            'galpy_components': component_names,
            'natural_unit_scaling': {'ro_kpc': ro, 'vo_kms': vo},
            'baryonic_components_rule': 'all McMillan17 components except NFWPotential',
            'full_model_rule': 'all McMillan17 components including NFWPotential',
        },
        'sun_position_sensitivity_configs': SUN_CONFIGS,
        'configs': configs,
        'baryonic_residual_sensitivity_clean_sample': sensitivity,
        'interpretation_rule': ('Stage 6A is accepted as a valid direct-force observable only if the Moran linear-model sign check is sensible and '
                                'the McMillan total model is not catastrophically inconsistent with the non-outlier catalog. The baryons-only residual '
                                'is then carried to Stage 6B without selecting pulsars by residual sign or size.'),
        'guardrail': ('The pulsar paper reports substantial unmodeled acceleration noise. The five >=3-sigma local-model outliers and the three systems '
                      'used in the authors modified-catalog test are preserved as flags. Naive chi-square is diagnostic only; robust summaries and '
                      'flag-sensitivity are primary. Sun position is treated as a sensitivity parameter.'),
    }
    (OUT/'stage6a_summary.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
