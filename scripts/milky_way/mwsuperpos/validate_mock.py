"""
End-to-end validation, in the spirit of Paper I: build an orbit library from a mock
sample, solve for the weights, and check that the weighted superposition recovers
the analytic stellar density it was fitted to.
"""
import sys
import time
import numpy as np
import agama

from potential import make_potential, stellar_density
from orbits import integrate_library
from superposition import Grid, target_density, build_design, solve, combine, residual_stats

N_ORBITS = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
SEED = 42


def sample_ics(dens, pot, n, seed=SEED):
    rng = np.random.default_rng(seed)
    xyz = dens.sample(n)[0]
    R = np.hypot(xyz[:, 0], xyz[:, 1])
    Rsafe = np.maximum(R, 0.05)
    probe = np.column_stack([Rsafe, np.zeros(n), np.zeros(n)])
    vc = np.sqrt(np.maximum(-Rsafe * pot.force(probe)[:, 0], 0.0))
    sig_R = 45.0 * np.exp(-(R - 8.0) / 12.0)
    sig_p = 0.7 * sig_R
    sig_z = 0.5 * sig_R
    vR = rng.normal(0, sig_R)
    vphi = vc - 0.5 * sig_R**2 / np.maximum(vc, 50.0) + rng.normal(0, sig_p)
    vz = rng.normal(0, sig_z)
    cosp, sinp = xyz[:, 0] / Rsafe, xyz[:, 1] / Rsafe
    return np.column_stack([
        xyz[:, 0], xyz[:, 1], xyz[:, 2],
        vR * cosp - vphi * sinp,
        vR * sinp + vphi * cosp,
        vz])


def main():
    agama.setUnits(length=1, mass=1, velocity=1)
    t0 = time.time()
    pot = make_potential()
    dens = stellar_density()
    print('[%.1fs] potential ready' % (time.time() - t0))
    ic = sample_ics(dens, pot, N_ORBITS)
    print('[%.1fs] %d initial conditions sampled' % (time.time() - t0, len(ic)))
    traj = integrate_library(ic, pot)
    print('[%.1fs] orbits integrated, array %s (%.0f MB)'
          % (time.time() - t0, traj.shape, traj.nbytes / 1e6))
    grid = Grid()
    rho = target_density(grid, dens)
    A = build_design(traj, grid)
    w, W = solve(A, rho, grid, n_sub=5, n_real=10, seed=SEED,
                 relative=False, subsample_target='fractional', normalise_mass=True)
    model = combine(A, w)
    stats = residual_stats(model, rho, grid)
    print('\n--- recovery of the analytic stellar density (inside 15 kpc) ---')
    print('  median |relative residual| : %.1f%%' % (100 * stats['median_abs_rel']))
    print('  90th pct |rel. residual|   : %.1f%%' % (100 * stats['p90_abs_rel']))
    print('  mass ratio model/target    : %.3f' % stats['mass_ratio'])
    nz = w > 0
    scatter = W.std(axis=0)[nz] / w[nz]
    print('  orbits with w_i > 0        : %d / %d (%.0f%%)'
          % (nz.sum(), len(w), 100 * nz.mean()))
    print('  median fractional scatter across realisations: %.2f' % np.median(scatter))
    np.savez_compressed('mock_solution.npz', weights=w, realisations=W,
                        ic=ic, residual_stats=np.array([stats['median_abs_rel'],
                                                        stats['p90_abs_rel'],
                                                        stats['mass_ratio']]))


if __name__ == '__main__':
    main()
