#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

OUT = Path('data/persistence_history/milky_way_stage7a_source_history_calibration')
OUT.mkdir(parents=True, exist_ok=True)
RAT = Path('data/external/ratcliffe2026_sfh/ratcliffe2026_tableA1_global_disc_history.csv')

# Frankel et al. 2019 fixed best-fit low-alpha model.
X_IO = 0.75
TAU_SFR = 3.9
TAU_M = 7.5
RD = 3.1
SIGMA_RM7 = 3.9

R0 = np.linspace(0.001, 30.0, 700)
TAU = np.linspace(0.0, TAU_M, 700)


def trapz(y, x, axis=-1):
    return np.trapezoid(y, x, axis=axis)


def normalized_model_terms():
    # Eq. 10 and Eq. 12: p(R0) includes the cylindrical 2*pi*R0 Jacobian.
    p_r0 = R0 * np.exp(-R0 / RD)
    p_r0 /= trapz(p_r0, R0)

    # Eq. 11. The exp(-tau_m/tau_SFR) term cancels in the R0-dependent normalization.
    A = (1.0 - X_IO * R0 / 8.0) / TAU_SFR
    I = np.empty_like(A)
    nz = np.abs(A) > 1e-10
    I[nz] = np.expm1(A[nz] * TAU_M) / A[nz]
    I[~nz] = TAU_M
    return p_r0, A, I


P_R0, A_R0, SFH_NORM = normalized_model_terms()


def sfh_tau_r0(tau):
    tau = np.asarray(tau, float)
    return np.exp(A_R0[:, None] * tau[None, :]) / SFH_NORM[:, None]


def total_sfr_fraction_per_gyr(t):
    sf = np.exp(A_R0 * float(t)) / SFH_NORM
    return float(trapz(P_R0 * sf, R0))


def cumulative_mass_fraction(tlook):
    if tlook >= TAU_M:
        return 0.0
    tt = np.linspace(float(tlook), TAU_M, 500)
    sf = sfh_tau_r0(tt)
    frac_r0 = trapz(sf, tt, axis=1)
    return float(trapz(P_R0 * frac_r0, R0))


def birth_cdf(radius, tlook):
    tt = np.linspace(float(tlook), TAU_M, 500)
    sf = sfh_tau_r0(tt)
    frac_r0 = trapz(sf, tt, axis=1)
    w = P_R0 * frac_r0
    total = trapz(w, R0)
    return float(trapz(w[R0 <= radius], R0[R0 <= radius]) / total)


def truncated_normal_cdf(radius, mean, sigma):
    mean = np.asarray(mean, float)
    sigma = np.asarray(sigma, float)
    out = np.empty_like(mean)
    zero = sigma < 1e-8
    out[zero] = (radius >= mean[zero]).astype(float)
    if np.any(~zero):
        m = mean[~zero]
        s = sigma[~zero]
        lo = ndtr(-m / s)
        hi = ndtr((radius - m) / s)
        den = np.maximum(1.0 - lo, 1e-15)
        out[~zero] = np.clip((hi - lo) / den, 0.0, 1.0)
    return out


def migrated_cdf(radius, tlook):
    if tlook >= TAU_M:
        return np.nan
    tt = np.linspace(float(tlook), TAU_M, 320)
    # Integrand is over birth radius and birth lookback time.
    sf = sfh_tau_r0(tt)
    elapsed = tt - float(tlook)
    sigma = SIGMA_RM7 * np.sqrt(np.maximum(elapsed, 0.0) / 7.0)
    accum_tau = np.empty(len(tt))
    for j, s in enumerate(sigma):
        cdf = truncated_normal_cdf(radius, R0, np.full_like(R0, s))
        accum_tau[j] = trapz(P_R0 * sf[:, j] * cdf, R0)
    mass_inside = trapz(accum_tau, tt)
    total = cumulative_mass_fraction(tlook)
    return float(mass_inside / total)


def solve_half_radius(cdf_func, tlook, lo=0.001, hi=25.0):
    for _ in range(52):
        mid = 0.5 * (lo + hi)
        if cdf_func(mid, tlook) < 0.5:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def model_at_lookback(t):
    return {
        'lookback_time_gyr': float(t),
        'frankel_mass_fraction_of_present_lowalpha': cumulative_mass_fraction(t),
        'frankel_sfr_fraction_per_gyr': total_sfr_fraction_per_gyr(t),
        'frankel_Rhalf_birth_kpc': solve_half_radius(birth_cdf, t),
        'frankel_Rhalf_migrated_at_epoch_kpc': solve_half_radius(migrated_cdf, t),
    }


def main():
    rat = pd.read_csv(RAT).sort_values('lookback_time_gyr').copy()
    # Cross-model comparison is restricted to the Frankel low-alpha trusted age domain.
    common = rat[rat['lookback_time_gyr'] < TAU_M].copy()
    model_rows = [model_at_lookback(t) for t in common['lookback_time_gyr']]
    mod = pd.DataFrame(model_rows)
    j = common.merge(mod, on='lookback_time_gyr', how='inner')

    near_mass = float(j.iloc[0]['stellar_mass_1e10_msun'])
    near_t = float(j.iloc[0]['lookback_time_gyr'])
    j['ratcliffe_mass_fraction_relative_to_first_common_epoch'] = j['stellar_mass_1e10_msun'] / near_mass
    j['frankel_mass_fraction_relative_to_first_common_epoch'] = j['frankel_mass_fraction_of_present_lowalpha'] / float(j.iloc[0]['frankel_mass_fraction_of_present_lowalpha'])
    # Convert Ratcliffe SFR to fraction of the near-present tabulated stellar mass per Gyr.
    j['ratcliffe_sfr_fraction_per_gyr_using_near_mass'] = j['SFR_msun_per_yr'] * 1e9 / (near_mass * 1e10)

    j['current_size_fractional_offset_frankel_minus_ratcliffe'] = (
        j['frankel_Rhalf_migrated_at_epoch_kpc'] / j['Reff_current_radius_kpc'] - 1.0
    )
    j['birth_size_fractional_offset_frankel_minus_ratcliffe'] = (
        j['frankel_Rhalf_birth_kpc'] / j['Reff_birth_radius_kpc'] - 1.0
    )
    j['ratcliffe_current_size_normalized'] = j['Reff_current_radius_kpc'] / float(j.iloc[0]['Reff_current_radius_kpc'])
    j['frankel_migrated_size_normalized'] = j['frankel_Rhalf_migrated_at_epoch_kpc'] / float(j.iloc[0]['frankel_Rhalf_migrated_at_epoch_kpc'])
    j['ratcliffe_birth_size_normalized'] = j['Reff_birth_radius_kpc'] / float(j.iloc[0]['Reff_birth_radius_kpc'])
    j['frankel_birth_size_normalized'] = j['frankel_Rhalf_birth_kpc'] / float(j.iloc[0]['frankel_Rhalf_birth_kpc'])
    j.to_csv(OUT / 'ratcliffe2026_frankel2019_common_epoch_comparison.csv', index=False)

    # Dense Frankel history is source-side output only; no force data enter here.
    dense_times = np.concatenate([np.arange(0.0, 7.01, 0.5), np.array([7.4])])
    dense = pd.DataFrame([model_at_lookback(t) for t in dense_times])
    dense.to_csv(OUT / 'frankel2019_reconstructed_lowalpha_history.csv', index=False)

    # Internal reproduction of Frankel's published half-mass result.
    present = model_at_lookback(0.0)
    early = model_at_lookback(7.4)
    growth_pct = 100.0 * (present['frankel_Rhalf_migrated_at_epoch_kpc'] / early['frankel_Rhalf_migrated_at_epoch_kpc'] - 1.0)

    # Source-side comparison metrics are descriptive, not a refit.
    rms_current_norm = float(np.sqrt(np.mean((j['frankel_migrated_size_normalized'] - j['ratcliffe_current_size_normalized'])**2)))
    rms_birth_norm = float(np.sqrt(np.mean((j['frankel_birth_size_normalized'] - j['ratcliffe_birth_size_normalized'])**2)))
    mass_rel_oldest = float(j.iloc[-1]['frankel_mass_fraction_relative_to_first_common_epoch'])
    rat_mass_rel_oldest = float(j.iloc[-1]['ratcliffe_mass_fraction_relative_to_first_common_epoch'])
    recent_sfr_ratio = float(j.iloc[0]['frankel_sfr_fraction_per_gyr'] / j.iloc[0]['ratcliffe_sfr_fraction_per_gyr_using_near_mass'])

    verdict = (
        'NOT_ACCEPTED_AS_TOTAL_DISC_HISTORY_OPERATOR. The fixed Frankel low-alpha model reproduces its own published size evolution and has broadly '
        'similar normalized radial-size growth over the 0.7--6.76 Gyr overlap, but its cumulative mass assembly is structurally incompatible with '
        'Ratcliffe\'s all-disc reconstruction: by the oldest common epoch the Frankel low-alpha component contains only a small fraction of its late-time '
        'mass while Ratcliffe already has most of the disc mass assembled. The Frankel operator may therefore be retained only as a late low-alpha '
        'redistribution component inside a future multi-component source-history model.'
    )

    report = {
        'analysis_name': 'Milky Way Stage 7A source-side Frankel2019 versus Ratcliffe2026 history calibration',
        'force_or_pulsar_data_used': False,
        'frankel_fixed_parameters': {
            'x': X_IO, 'tau_SFR_gyr': TAU_SFR, 'tau_m_gyr': TAU_M,
            'Rd_kpc': RD, 'sigma_RM7_kpc': SIGMA_RM7,
        },
        'common_lookback_epochs_gyr': j['lookback_time_gyr'].tolist(),
        'internal_frankel_reproduction': {
            'model_present_migrated_half_mass_radius_kpc': present['frankel_Rhalf_migrated_at_epoch_kpc'],
            'paper_present_half_mass_radius_kpc_approx': 5.9,
            'model_7p4Gyr_migrated_half_mass_radius_kpc': early['frankel_Rhalf_migrated_at_epoch_kpc'],
            'paper_early_half_mass_radius_kpc_approx': 4.2,
            'model_size_growth_percent_7p4Gyr_to_present': growth_pct,
            'paper_size_growth_percent_approx': 43.0,
        },
        'cross_model_metrics': {
            'rms_difference_normalized_current_size_track': rms_current_norm,
            'rms_difference_normalized_birth_size_track': rms_birth_norm,
            'oldest_common_epoch_gyr': float(j.iloc[-1]['lookback_time_gyr']),
            'frankel_mass_fraction_relative_to_0p7Gyr_at_oldest_common_epoch': mass_rel_oldest,
            'ratcliffe_mass_fraction_relative_to_0p7Gyr_at_oldest_common_epoch': rat_mass_rel_oldest,
            'recent_0p7Gyr_specific_SFR_ratio_frankel_over_ratcliffe': recent_sfr_ratio,
            'median_absolute_current_size_offset_fraction': float(np.median(np.abs(j['current_size_fractional_offset_frankel_minus_ratcliffe']))),
            'median_absolute_birth_size_offset_fraction': float(np.median(np.abs(j['birth_size_fractional_offset_frankel_minus_ratcliffe']))),
        },
        'verdict': verdict,
        'stage7_use_rule': (
            'Do not use Frankel2019 as the Milky Way total baryonic source history in a persistence-force test. It can be used only as a low-alpha, '
            'late-time radial redistribution kernel if an independently reconstructed early/high-alpha mass history is supplied. No pulsar residual '
            'correlation may be evaluated from this Stage 7A calibration.'
        ),
        'guardrails': [
            'Frankel2019 models the low-alpha disk and explicitly treats tau_m as the maximum trusted model age, not the age of the full disk.',
            'Ratcliffe2026 Table A.1 is an all-disc reconstruction with orbit-superposition mass weights and therefore is not expected to match Frankel in absolute size normalization.',
            'The comparison uses fixed published best-fit Frankel parameters; no parameter was fit to Ratcliffe.',
            'The Frankel migration operator is axisymmetric and statistical and provides neither individual trajectories nor azimuthal/current history.'
        ]
    }
    (OUT / 'stage7a_summary.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
