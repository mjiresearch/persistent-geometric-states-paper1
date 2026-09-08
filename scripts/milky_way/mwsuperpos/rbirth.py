"""
Stellar birth radii, following Minchev et al. (2018) as refined by Ratcliffe
et al. (2023, 2025) and used in Paper IV/V (Ratcliffe et al., A&A 2026).

This module is intentionally retained as an approximate auxiliary estimator.
The full Ratcliffe gradient-history inference is not reproduced here; Stage 8
must not treat these R_birth values as a direct hereditary state variable.
"""
import numpy as np

GRAD_PRESENT = -0.064
GRAD_STEEPEST = -0.151
TAU_STEEPEST = 8.0
R_INNER = 0.0
R_MAX = 20.0


def gradient_evolution(tau, grad_present=GRAD_PRESENT, grad_steepest=GRAD_STEEPEST,
                       tau_steepest=TAU_STEEPEST, flatten_old=True,
                       grad_oldest=None):
    tau = np.atleast_1d(np.asarray(tau, dtype=float))
    if grad_oldest is None:
        grad_oldest = 0.5 * grad_steepest
    g = np.empty_like(tau)
    young = tau <= tau_steepest
    g[young] = grad_present + (grad_steepest - grad_present) * (tau[young] / tau_steepest)
    if flatten_old:
        tmax = max(tau.max(), tau_steepest + 1e-6)
        frac = (tau[~young] - tau_steepest) / (tmax - tau_steepest)
        g[~young] = grad_steepest + (grad_oldest - grad_steepest) * frac
    else:
        g[~young] = grad_steepest
    return g


def gradient_from_table(tau, tau_table, grad_table):
    return np.interp(np.asarray(tau, float), np.asarray(tau_table, float),
                     np.asarray(grad_table, float))


def intercept_from_data(age, feh, grad, bins, percentile=99.5, min_count=50):
    centres, bvals = [], []
    idx = np.digitize(age, bins) - 1
    for i in range(len(bins) - 1):
        sel = idx == i
        if sel.sum() < min_count:
            continue
        c = 0.5 * (bins[i] + bins[i + 1])
        centres.append(c)
        bvals.append(np.percentile(feh[sel], percentile))
    if len(centres) < 2:
        raise ValueError('too few populated age bins to build the intercept')
    centres = np.array(centres)
    bvals = np.array(bvals)
    b_star = np.interp(age, centres, bvals)
    g_at_centres = gradient_evolution(centres)
    b_star = b_star - np.interp(age, centres, g_at_centres) * R_INNER
    return b_star, centres, bvals


def birth_radius(age, feh, grad_present=GRAD_PRESENT, grad_steepest=GRAD_STEEPEST,
                 tau_steepest=TAU_STEEPEST, age_bins=None, percentile=99.5,
                 flatten_old=True, r_max=R_MAX):
    age = np.asarray(age, float)
    feh = np.asarray(feh, float)
    if age_bins is None:
        age_bins = np.arange(0.0, np.nanmax(age) + 0.5, 0.5)
    grad = gradient_evolution(age, grad_present, grad_steepest, tau_steepest,
                              flatten_old=flatten_old)
    b, _, _ = intercept_from_data(age, feh, grad, age_bins, percentile=percentile)
    with np.errstate(divide='ignore', invalid='ignore'):
        rb = (feh - b) / grad
    rb = np.clip(rb, 0.0, r_max)
    return rb, grad


def calibrate_steepest(age, feh, R_now, young_max=2.0, trial=None, **kw):
    if trial is None:
        trial = np.arange(-0.30, -0.065, 0.002)
    young = np.asarray(age, float) < young_max
    if young.sum() < 100:
        raise ValueError('not enough young stars (%d) to calibrate' % young.sum())
    scores = []
    for g in trial:
        rb, _ = birth_radius(age, feh, grad_steepest=g, **kw)
        scores.append(np.median(np.abs(np.asarray(R_now)[young] - rb[young])))
    scores = np.array(scores)
    return float(trial[np.argmin(scores)]), trial, scores


def sample_along_orbit(values, errors, n_points, rng=None):
    rng = np.random.default_rng() if rng is None else rng
    v = np.asarray(values, float)[:, None]
    e = np.asarray(errors, float)[:, None]
    return v + e * rng.standard_normal((len(v), n_points))
