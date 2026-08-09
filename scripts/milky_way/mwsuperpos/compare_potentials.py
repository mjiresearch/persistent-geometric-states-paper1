"""Controlled four-way Milky Way potential comparison for persistence studies.

Runs the SAME selected APOGEE initial conditions and, by default, the SAME
Portail17 stellar target through:

  portail17 + halo
  portail17 baryons only
  hunter24  + halo
  hunter24  baryons only

This isolates force-model sensitivity from target-density changes.  The output
contains reconstruction diagnostics, normalized weight comparisons, orbit-shift
statistics, and force-equivalent circular-speed curves.  The full-minus-baryon
acceleration is a conventional-halo *replacement target* for a persistence
operator; it is not itself evidence for persistence.
"""
import argparse
import csv
import os
import time

import numpy as np
import agama

import ingest
from orbits import integrate_library
from potential import make_potential, target_stellar_density, OMEGA_BAR, BAR_ANGLE
from superposition import Grid, target_density, build_design, solve, combine, residual_stats


VARIANTS = [
    ('portail17_dark', 'portail17', True),
    ('portail17_baryons', 'portail17', False),
    ('hunter24_dark', 'hunter24', True),
    ('hunter24_baryons', 'hunter24', False),
]


def force_curve(pot, radii):
    """Radial force and force-equivalent speed along the bar x-axis."""
    xyz = np.column_stack([radii, np.zeros_like(radii), np.zeros_like(radii)])
    ax = np.asarray(pot.force(xyz))[:, 0]
    ar = np.maximum(-ax, 0.0)
    veq = np.sqrt(radii * ar)
    return ar, veq


def weighted_orbit_rms(traj_a, traj_b, weights):
    """Weight-averaged RMS positional separation of paired orbit libraries."""
    d2 = np.sum((traj_a[:, :, :3].astype(float) - traj_b[:, :, :3].astype(float))**2,
                axis=2)
    per_orbit = np.sqrt(np.mean(d2, axis=1))
    w = np.maximum(np.asarray(weights, float), 0.0)
    return float(np.sum(w * per_orbit) / np.sum(w)), per_orbit


def corr_positive(a, b):
    sel = (a > 0) & (b > 0) & np.isfinite(a) & np.isfinite(b)
    if sel.sum() < 3:
        return np.nan
    return float(np.corrcoef(np.log10(a[sel]), np.log10(b[sel]))[0, 1])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--allstar', required=True)
    ap.add_argument('--distmass', required=True)
    ap.add_argument('--outdir', default='comparison_results')
    ap.add_argument('--target-density', choices=['portail17', 'hunter24'], default='portail17')
    ap.add_argument('--time', type=float, default=5.0)
    ap.add_argument('--npoints', type=int, default=500)
    ap.add_argument('--nsub', type=int, default=5)
    ap.add_argument('--nreal', type=int, default=10)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--relative', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    agama.setUnits(length=1, mass=1, velocity=1)
    t0 = time.time()
    def log(msg):
        print('[%7.1fs] %s' % (time.time() - t0, msg), flush=True)

    sample_path = os.path.join(args.outdir, 'sample.fits')
    tab = ingest.build_sample(args.allstar, args.distmass, sample_path)
    if args.limit:
        tab = tab[:args.limit]
    ic, meta = ingest.to_initial_conditions(tab)
    log('sample fixed: %d stars' % len(ic))

    grid = Grid()
    dens = target_stellar_density(args.target_density)
    rho = target_density(grid, dens)
    radii = np.linspace(0.5, 20.0, 80)

    results = {}
    ref_traj = None
    ref_w = None
    for tag, model_name, include_dark in VARIANTS:
        d = os.path.join(args.outdir, tag)
        os.makedirs(d, exist_ok=True)
        pot = make_potential(model=model_name, include_dark=include_dark,
                             cache=os.path.join(d, tag + '.ini'))
        ar, veq = force_curve(pot, radii)
        traj = integrate_library(ic, pot, time=args.time, trajsize=args.npoints)
        np.save(os.path.join(d, 'orbits.npy'), traj)
        A = build_design(traj, grid)
        w, W = solve(A, rho, grid, n_sub=args.nsub, n_real=args.nreal,
                     seed=args.seed, relative=args.relative,
                     subsample_target='fractional', normalise_mass=True)
        recon = combine(A, w)
        stats = residual_stats(recon, rho, grid)
        np.savez_compressed(
            os.path.join(d, 'solution.npz'),
            weight=w, weight_realisations=W,
            apogee_id=np.asarray(meta['APOGEE_ID']).astype('U32'),
            ic=ic, radii=radii, radial_accel=ar, force_equiv_speed=veq,
            residuals=np.array([stats['median_abs_rel'], stats['p90_abs_rel'],
                                stats['mass_ratio']]),
            potential_model=model_name, include_dark=include_dark,
            target_density_model=args.target_density,
            omega_bar=OMEGA_BAR, bar_angle=BAR_ANGLE)
        if tag == 'portail17_dark':
            ref_traj = traj
            ref_w = w.copy()
            orbit_rms = 0.0
        else:
            orbit_rms, _ = weighted_orbit_rms(ref_traj, traj, ref_w)
        results[tag] = dict(w=w, ar=ar, veq=veq, stats=stats, orbit_rms=orbit_rms)
        if tag != 'portail17_dark':
            del traj
        del A, recon, W
        log('%s: median residual %.3f, p90 %.3f, mass ratio %.6f'
            % (tag, stats['median_abs_rel'], stats['p90_abs_rel'], stats['mass_ratio']))

    ref = results['portail17_dark']
    rows = []
    for tag, _, _ in VARIANTS:
        r = results[tag]
        rows.append(dict(
            variant=tag,
            median_abs_rel=r['stats']['median_abs_rel'],
            p90_abs_rel=r['stats']['p90_abs_rel'],
            mass_ratio=r['stats']['mass_ratio'],
            log_weight_corr_vs_portail17_dark=corr_positive(ref['w'], r['w']),
            weighted_orbit_rms_kpc_vs_portail17_dark=r['orbit_rms'],
        ))

    with open(os.path.join(args.outdir, 'comparison_summary.csv'), 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader(); wr.writerows(rows)

    p_full, p_bar = results['portail17_dark'], results['portail17_baryons']
    h_full, h_bar = results['hunter24_dark'], results['hunter24_baryons']
    np.savez_compressed(
        os.path.join(args.outdir, 'persistence_replacement_target.npz'),
        radii=radii,
        portail_delta_a=p_full['ar'] - p_bar['ar'],
        hunter_delta_a=h_full['ar'] - h_bar['ar'],
        portail_v_full=p_full['veq'], portail_v_baryons=p_bar['veq'],
        hunter_v_full=h_full['veq'], hunter_v_baryons=h_bar['veq'])
    log('wrote comparison_summary.csv and persistence_replacement_target.npz')


if __name__ == '__main__':
    main()
