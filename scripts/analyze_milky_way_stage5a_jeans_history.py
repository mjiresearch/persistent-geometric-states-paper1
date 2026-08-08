#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

OUT = Path('data/persistence_history/milky_way_stage5a_jeans_history')
OUT.mkdir(parents=True, exist_ok=True)
SRC = Path('data/persistence_history/milky_way_stage4d_mwm_rbirth_spatial/mwm_rbirth_star_history.csv.gz')
HIST = Path('data/persistence_history/milky_way_stage4b_guiding_migration/guiding_migration_radial_profile.csv')
MC = Path('data/persistence_history/milky_way_stage3c_interaction/mcmillan_interaction_screen.csv')
MG = Path('data/persistence_history/milky_way_stage3c_interaction/mcgaugh_interaction_screen.csv')
RNG = np.random.default_rng(20260808)

R0 = 8.122
VC0 = 229.0
DVC_DR = -1.7
R_CENTERS = np.arange(5.0, 10.5 + 0.001, 0.5)
ZCUTS = [0.3, 0.5, 0.8]
HNU = [2.0, 2.5, 3.0, 3.5]
PRED = [
    'Rbirth_median_kpc',
    'deltaR_guide_median_kpc',
    'abs_deltaR_guide_median_kpc',
    'outward_guide_fraction_gt1',
    'inward_guide_fraction_gt1',
    'inner_born_fraction_lt6',
    'guide_history_distance_time_median',
    'age_median_gyr',
]


def eilers_vc(r):
    return VC0 + DVC_DR * (np.asarray(r, float) - R0)


def detrend(r, y):
    r = np.asarray(r, float); y = np.asarray(y, float)
    m = np.isfinite(r) & np.isfinite(y)
    out = np.full(len(y), np.nan)
    if m.sum() < 6:
        return out
    c = np.polyfit(r[m], y[m], 2)
    out[m] = y[m] - np.polyval(c, r[m])
    return out


def corr_stats(r, x, y):
    r = np.asarray(r, float); x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(r) & np.isfinite(x) & np.isfinite(y)
    r, x, y = r[m], x[m], y[m]
    if len(r) < 6:
        return {'n': int(len(r))}
    rr, pr = spearmanr(x, y)
    xd, yd = detrend(r, x), detrend(r, y)
    rd, pd = spearmanr(xd, yd)
    o = np.argsort(r)
    rf, pf = spearmanr(np.diff(x[o]), np.diff(y[o]))
    return {
        'n': int(len(r)),
        'rho_raw': float(rr), 'p_raw': float(pr),
        'rho_detrended': float(rd), 'p_detrended': float(pd),
        'rho_first_difference': float(rf), 'p_first_difference': float(pf),
    }


def maxT_history(d, target, nperm=20000):
    q = d.dropna(subset=['R_kpc', target] + PRED).copy()
    r = q['R_kpc'].to_numpy(float)
    y = detrend(r, q[target].to_numpy(float))
    X = np.column_stack([detrend(r, q[p].to_numpy(float)) for p in PRED])
    yr = rankdata(y); yr = (yr - yr.mean()) / yr.std(ddof=0)
    XR = []
    for j in range(X.shape[1]):
        z = rankdata(X[:, j]); z = (z - z.mean()) / z.std(ddof=0); XR.append(z)
    XR = np.column_stack(XR)
    obs_signed = (XR * yr[:, None]).mean(axis=0)
    obs = np.abs(obs_signed)
    counts = np.zeros(len(PRED), int); maxcounts = np.zeros(len(PRED), int)
    for _ in range(nperm):
        yp = RNG.permutation(yr)
        v = np.abs((XR * yp[:, None]).mean(axis=0))
        counts += v >= obs
        maxcounts += v.max() >= obs
    return {
        p: {
            'rho_detrended_rank': float(obs_signed[i]),
            'p_perm': float((counts[i] + 1) / (nperm + 1)),
            'p_maxT': float((maxcounts[i] + 1) / (nperm + 1)),
        }
        for i, p in enumerate(PRED)
    }


def prepare_disk(d, zcut):
    q = d.copy()
    for c in ['R_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal','Age','FeH','aFe']:
        q[c] = pd.to_numeric(q[c], errors='coerce')
    q = q[np.isfinite(q[['R_gal','Z_gal','Vr_gal','Vphi_gal','Vz_gal']]).all(axis=1)].copy()
    q = q[q['R_gal'].between(4.75, 10.75) & q['Z_gal'].abs().le(zcut)].copy()
    # Standardize the rotation sign so the dominant disk population is prograde-positive.
    sign = -1.0 if np.nanmedian(q['Vphi_gal']) < 0 else 1.0
    q['Vphi_pro'] = sign * q['Vphi_gal']
    # Remove obvious halo/runaway contamination while retaining a broad disk population.
    q = q[q['Vphi_pro'].between(100, 320) & q['Vr_gal'].abs().le(180) & q['Vz_gal'].abs().le(150)].copy()
    q['R_kpc'] = np.floor((q['R_gal'] + 0.25) / 0.5) * 0.5
    return q, sign


def radial_moments(d, zcut):
    q, sign = prepare_disk(d, zcut)
    rows = []
    for r, g in q.groupby('R_kpc'):
        if r not in R_CENTERS or len(g) < 80:
            continue
        vr = g['Vr_gal'].to_numpy(float)
        vp = g['Vphi_pro'].to_numpy(float)
        vz = g['Vz_gal'].to_numpy(float)
        # 4-sigma clipping around robust medians, then classical moments for Jeans equation.
        keep = np.ones(len(g), bool)
        for arr in (vr, vp, vz):
            med = np.nanmedian(arr); mad = 1.4826 * np.nanmedian(np.abs(arr - med))
            if np.isfinite(mad) and mad > 0:
                keep &= np.abs(arr - med) <= 4.0 * mad
        vr, vp, vz = vr[keep], vp[keep], vz[keep]
        if len(vr) < 60:
            continue
        rows.append({
            'R_kpc': float(r), 'n': int(len(vr)),
            'mean_vphi_kms': float(np.mean(vp)),
            'sigma_R_kms': float(np.std(vr, ddof=1)),
            'sigma_phi_kms': float(np.std(vp, ddof=1)),
            'sigma_z_kms': float(np.std(vz, ddof=1)),
            'mean_vr_kms': float(np.mean(vr)),
            'mean_vz_kms': float(np.mean(vz)),
        })
    m = pd.DataFrame(rows).sort_values('R_kpc')
    if len(m) < 8:
        raise RuntimeError(f'Insufficient radial Jeans bins for zcut={zcut}: {len(m)}')
    # Smooth stress gradient: ln sigma_R^2 = a + b R. This is equivalent to an exponential stress scale.
    x = m['R_kpc'].to_numpy(float)
    y = np.log(np.square(m['sigma_R_kms'].to_numpy(float)))
    w = np.sqrt(m['n'].to_numpy(float))
    b, a = np.polyfit(x, y, 1, w=w)
    m['dln_sigmaR2_dR_per_kpc'] = float(b)
    return m, sign, float(b)


def add_jeans(m, hnu):
    q = m.copy()
    r = q['R_kpc'].to_numpy(float)
    sr2 = np.square(q['sigma_R_kms'].to_numpy(float))
    sp2 = np.square(q['sigma_phi_kms'].to_numpy(float))
    vbar2 = np.square(q['mean_vphi_kms'].to_numpy(float))
    b = q['dln_sigmaR2_dR_per_kpc'].to_numpy(float)
    dln_nusig_dlnR = r * (-1.0 / hnu + b)
    vc2 = vbar2 + sp2 - sr2 * (1.0 + dln_nusig_dlnR)
    q['hnu_kpc'] = float(hnu)
    q['dln_nusigR2_dlnR'] = dln_nusig_dlnR
    q['Vc_jeans_kms'] = np.sqrt(np.maximum(vc2, 0.0))
    q['Vc_eilers_kms'] = eilers_vc(r)
    q['Vc_minus_eilers_kms'] = q['Vc_jeans_kms'] - q['Vc_eilers_kms']
    return q


def analyze_decomp(j, vbar_col, label):
    q = j.copy()
    vb = q[vbar_col].to_numpy(float); vc = q['Vc_jeans_kms'].to_numpy(float)
    q['chi_jeans'] = (vc * vc - vb * vb) / (vb * vb)
    q['gres_jeans_kms2perkpc'] = (vc * vc - vb * vb) / q['R_kpc'].to_numpy(float)
    correlations = {p: corr_stats(q['R_kpc'], q[p], q['chi_jeans']) for p in PRED}
    perm = maxT_history(q, 'chi_jeans', 20000)
    return q, {
        'decomposition': label,
        'n_bins': int(len(q)),
        'positive_baryonic_deficit_bins': int((q['chi_jeans'] > 0).sum()),
        'median_chi_jeans': float(q['chi_jeans'].median()),
        'rms_Vc_minus_eilers_kms': float(np.sqrt(np.mean(np.square(q['Vc_minus_eilers_kms'])))),
        'median_Vc_minus_eilers_kms': float(q['Vc_minus_eilers_kms'].median()),
        'correlations': correlations,
        'maxT_permutation': perm,
    }


def main():
    stars = pd.read_csv(SRC, low_memory=False)
    hist = pd.read_csv(HIST)
    mc = pd.read_csv(MC)[['R_kpc','Vbar_mcmillan17_kms']]
    mg = pd.read_csv(MG)[['R_kpc','Vbar_mcgaugh_kms']]
    scenarios = {}
    consistency_rows = []

    for zcut in ZCUTS:
        moments, sign, stress_slope = radial_moments(stars, zcut)
        moments.to_csv(OUT / f'radial_moments_z{zcut:.1f}.csv', index=False)
        for hnu in HNU:
            base = add_jeans(moments, hnu).merge(hist, on='R_kpc', how='inner')
            key = f'z{zcut:.1f}_hnu{hnu:.1f}'
            scenarios[key] = {
                'zcut_kpc': float(zcut), 'hnu_kpc': float(hnu),
                'prograde_sign_applied': float(sign),
                'dln_sigmaR2_dR_per_kpc': float(stress_slope),
            }
            for decomp, btab, bcol in [
                ('mcmillan17', mc, 'Vbar_mcmillan17_kms'),
                ('mcgaugh2019', mg, 'Vbar_mcgaugh_kms'),
            ]:
                joined = base.merge(btab, on='R_kpc', how='inner')
                out, result = analyze_decomp(joined, bcol, decomp)
                out.to_csv(OUT / f'{key}_{decomp}.csv', index=False)
                scenarios[key][decomp] = result
                for p in PRED:
                    pm = result['maxT_permutation'][p]
                    consistency_rows.append({
                        'scenario': key, 'zcut_kpc': zcut, 'hnu_kpc': hnu,
                        'decomposition': decomp, 'predictor': p,
                        'rho_detrended_rank': pm['rho_detrended_rank'],
                        'p_perm': pm['p_perm'], 'p_maxT': pm['p_maxT'],
                    })

    cons = pd.DataFrame(consistency_rows)
    cons.to_csv(OUT / 'history_consistency_all_scenarios.csv', index=False)
    summary_by_pred = {}
    for p, g in cons.groupby('predictor'):
        signs = np.sign(g['rho_detrended_rank'].to_numpy(float))
        summary_by_pred[p] = {
            'n_scenario_decomposition_tests': int(len(g)),
            'n_maxT_lt_0p05': int((g['p_maxT'] < 0.05).sum()),
            'n_maxT_lt_0p10': int((g['p_maxT'] < 0.10).sum()),
            'positive_sign_fraction': float((signs > 0).mean()),
            'negative_sign_fraction': float((signs < 0).mean()),
            'median_abs_rho_detrended_rank': float(np.median(np.abs(g['rho_detrended_rank']))),
            'min_p_maxT': float(g['p_maxT'].min()),
        }

    report = {
        'analysis_name': 'Milky Way Stage 5A axisymmetric radial Jeans force-residual history screen',
        'input_star_rows': int(len(stars)),
        'radial_range_kpc': [5.0, 10.5],
        'radial_bin_width_kpc': 0.5,
        'z_cuts_kpc': ZCUTS,
        'tracer_density_scale_lengths_kpc': HNU,
        'jeans_equation': 'Vc^2 = <Vphi>^2 + sigma_phi^2 - sigma_R^2 [1 + d ln(nu sigma_R^2)/d ln R]',
        'stress_gradient_model': 'weighted linear fit to ln(sigma_R^2) versus R within each z cut',
        'tracer_density_model': 'nu proportional to exp(-R/h_nu); h_nu varied as a sensitivity envelope',
        'tilt_term': 'omitted; low-|z| cuts and z-cut sensitivity are used as a first robustness screen',
        'scenarios': scenarios,
        'history_consistency': summary_by_pred,
        'decision_rule': ('No persistence-compatible history predictor is accepted unless it survives family-wise maxT correction '
                          'with a stable sign across tracer-density scale lengths, z cuts, and both baryonic decompositions. '
                          'Agreement of Vc_jeans with the Eilers scale is treated as a prerequisite sanity check, not as a fitted constraint.'),
        'guardrail': ('This is a sensitivity-bracketed axisymmetric Jeans estimate, not yet a fully selection-function-corrected 3D Jeans model. '
                      'The density gradient is imposed through a plausible scale-length envelope rather than inferred from raw MWM counts; '
                      'the R-z stress tilt term is omitted. Birth radii remain transferred Ratcliffe age/metallicity proxies.'),
    }
    (OUT / 'stage5a_summary.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
