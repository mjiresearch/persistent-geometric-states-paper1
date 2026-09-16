"""
End-to-end driver: APOGEE DR17 -> orbit library -> weights -> birth radii.

    python run_pipeline.py --allstar allStar-dr17-synspec_rev1.fits \
                           --distmass apogee_distmass-dr17.fits \
                           --outdir results/

Produces, in --outdir:

    sample.fits        the selected input catalogue (~80k stars)
    orbits.npy         (N, 500, 6) UNMIRRORED bar-frame trajectories, float32
                       -- this is the pre-symmetry-augmentation library
    weights.npz        w_i (mean), the 10 per-realisation weight vectors,
                       APOGEE_ID and Gaia source_id, [Fe/H], [Mg/Fe], age,
                       age_err, R_birth, and the residual diagnostics
    <potential>_<dark|baryons>.ini   exported AGAMA potential definition

Every item on a standard "please send me your data" request list is in there.
"""
import argparse
import os
import time

import numpy as np
import agama

from potential import make_potential, target_stellar_density, OMEGA_BAR, BAR_ANGLE
from orbits import integrate_library, T_INTEGRATE, N_POINTS
from superposition import (Grid, target_density, build_design, solve, combine,
                           residual_stats)
import ingest
import rbirth


def surface_density(vec, grid):
    n = grid.nbins
    return vec.reshape(n, n, n).sum(axis=2) * (grid.box / n)


def surface_residual(model, rho, grid, floor_frac=0.01):
    St, Sm = surface_density(rho, grid), surface_density(model, grid)
    R = np.hypot(*np.meshgrid(grid.centres, grid.centres, indexing='ij'))
    sel = (R < 15.0) & (St > floor_frac * St.max())
    return float(np.median(np.abs(Sm[sel] - St[sel]) / St[sel]))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--allstar', required=True)
    p.add_argument('--distmass', required=True)
    p.add_argument('--outdir', default='results')
    p.add_argument('--time', type=float, default=T_INTEGRATE, help='Gyr')
    p.add_argument('--npoints', type=int, default=N_POINTS)
    p.add_argument('--nsub', type=int, default=5)
    p.add_argument('--nreal', type=int, default=10)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--relative', action='store_true',
                   help='fit relative rather than absolute density residuals')
    p.add_argument('--potential', choices=['portail17', 'hunter24'], default='portail17',
                   help='force model used for orbit integration')
    p.add_argument('--baryons-only', action='store_true',
                   help='remove the dark halo from the chosen force model')
    p.add_argument('--target-density', choices=['portail17', 'hunter24'], default='portail17',
                   help='stellar density fitted by the orbit weights; keep portail17 for controlled potential comparisons')
    p.add_argument('--subsample-target', choices=['fractional', 'full'], default='fractional',
                   help='fit each orbit subset to rho/nsub (recommended) or the full rho; saved weights are mass-normalised either way')
    p.add_argument('--calibrate-gradient', action='store_true',
                   help='refit the steepest metallicity gradient from the data')
    p.add_argument('--limit', type=int, default=0, help='debug: cap sample size')
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    agama.setUnits(length=1, mass=1, velocity=1)
    t0 = time.time()

    def log(msg):
        print('[%7.1fs] %s' % (time.time() - t0, msg), flush=True)

    tab = ingest.build_sample(args.allstar, args.distmass,
                              os.path.join(args.outdir, 'sample.fits'))
    if args.limit:
        tab = tab[:args.limit]
    ic, meta = ingest.to_initial_conditions(tab)
    log('sample ready: %d stars' % len(ic))

    force_tag = '%s_%s' % (args.potential, 'baryons' if args.baryons_only else 'dark')
    cache = os.path.join(args.outdir, force_tag + '.ini')
    pot = make_potential(model=args.potential, include_dark=not args.baryons_only,
                         cache=cache)
    dens = target_stellar_density(args.target_density)
    log('potential ready: %s; target density: %s' % (force_tag, args.target_density))

    traj = integrate_library(ic, pot, time=args.time, trajsize=args.npoints)
    np.save(os.path.join(args.outdir, 'orbits.npy'), traj)
    log('orbits done: %s, %.1f GB' % (traj.shape, traj.nbytes / 1e9))

    grid = Grid()
    rho = target_density(grid, dens)
    A = build_design(traj, grid)
    log('design matrix %s, %d nonzeros' % (A.shape, A.nnz))
    w, W = solve(A, rho, grid, n_sub=args.nsub, n_real=args.nreal,
                 seed=args.seed, relative=args.relative,
                 subsample_target=args.subsample_target, normalise_mass=True)
    model = combine(A, w)
    stats = residual_stats(model, rho, grid)
    stats['surface_median_rel'] = surface_residual(model, rho, grid)
    log('weights solved; surface-density residual %.1f%%, mass ratio %.3f'
        % (100 * stats['surface_median_rel'], stats['mass_ratio']))

    age = np.asarray(meta['age'], float)
    feh = np.asarray(meta['FE_H'], float)
    R_now = np.hypot(np.asarray(meta['x'], float), np.asarray(meta['y'], float))
    grad_steep = rbirth.GRAD_STEEPEST
    if args.calibrate_gradient:
        grad_steep, trial, scores = rbirth.calibrate_steepest(age, feh, R_now)
        np.savez(os.path.join(args.outdir, 'gradient_scan.npz'), trial=trial, scores=scores)
        log('recalibrated steepest gradient: %.3f dex/kpc (published -0.151)'
            % grad_steep)
    R_birth, grad = rbirth.birth_radius(age, feh, grad_steepest=grad_steep)
    log('R_birth done: median %.2f kpc, median |R - R_birth| %.2f kpc'
        % (np.median(R_birth), np.median(np.abs(R_now - R_birth))))

    out = os.path.join(args.outdir, 'weights.npz')
    np.savez_compressed(
        out,
        apogee_id=np.asarray(meta['APOGEE_ID']).astype('U32'),
        gaia_source_id=np.asarray(meta['GAIA_SOURCE_ID']),
        weight=w, weight_realisations=W,
        weight_scatter=W.std(axis=0),
        feh=feh, feh_err=np.asarray(meta['FE_H_ERR'], float),
        mgfe=np.asarray(meta['MG_FE'], float),
        mgfe_err=np.asarray(meta['MG_FE_ERR'], float),
        age=age, age_err=np.asarray(meta['age_err'], float),
        R_now=R_now, R_birth=R_birth, feh_gradient=grad,
        ic=ic,
        omega_bar=OMEGA_BAR, bar_angle=BAR_ANGLE,
        integration_time=args.time, n_points=args.npoints,
        potential_model=args.potential, include_dark=not args.baryons_only,
        target_density_model=args.target_density,
        subsample_target=args.subsample_target,
        residuals=np.array([stats['median_abs_rel'], stats['p90_abs_rel'],
                            stats['mass_ratio'], stats['surface_median_rel']]))
    log('wrote %s' % out)
    log('DONE')


if __name__ == '__main__':
    main()
