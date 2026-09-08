"""
Orbit superposition: solve  rho_s(r) = sum_i w_i rho_i(r)  for w_i >= 0.

Paper II, Sect. 2.3:
  - densities discretised on a 30 x 30 x 30 kpc Cartesian grid, 50 bins per axis
  - each orbit mirrored about all three axes
  - library split into 5 random subsamples, each solved separately
  - repeated 10 times with different random groupings -> 10 realisations of w_i
  - the MEAN of the realisations is used; the scatter is the only available
    handle on weight uncertainty (the papers publish no formal error bars)
  - solution obtained inside R = 15 kpc

UNDERSPECIFIED IN THE PAPER (choices flagged, all configurable):
  * whether each subsample is fit to the full rho_s or to rho_s/5.  The default
    here is rho_s/n_sub, followed by an explicit per-realisation mass
    normalization inside R_fit.  This makes the SAVED orbit weights themselves
    mass-normalized rather than only rescaling a plotted reconstruction later.
  * the residual metric.  Both relative and absolute weighting are available.
    The end-to-end driver defaults to absolute weighting, matching the README.
"""
import numpy as np
import scipy.sparse as sp
from scipy.optimize import lsq_linear

from orbits import MIRRORS

BOX = 30.0
NBINS = 50
R_FIT = 15.0


class Grid:
    def __init__(self, box=BOX, nbins=NBINS, r_fit=R_FIT):
        self.box, self.nbins = box, nbins
        self.edges = np.linspace(-box / 2, box / 2, nbins + 1)
        self.centres = 0.5 * (self.edges[1:] + self.edges[:-1])
        self.cell_volume = (box / nbins)**3
        gx, gy, gz = np.meshgrid(self.centres, self.centres, self.centres,
                                 indexing='ij')
        self.xyz = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])
        r = np.sqrt((self.xyz**2).sum(axis=1))
        self.mask = r < r_fit
        self.ncells = nbins**3

    def digitize(self, xyz):
        idx = np.empty((len(xyz), 3), dtype=np.int64)
        for k in range(3):
            idx[:, k] = np.searchsorted(self.edges, xyz[:, k], side='right') - 1
        bad = (idx < 0).any(axis=1) | (idx >= self.nbins).any(axis=1)
        flat = (idx[:, 0] * self.nbins + idx[:, 1]) * self.nbins + idx[:, 2]
        flat[bad] = -1
        return flat


def target_density(grid, density):
    return np.asarray(density.density(grid.xyz))


def build_design(traj, grid, chunk=2000, dtype=np.float32):
    norb, npts, _ = traj.shape
    cols, rows, vals = [], [], []
    w_point = 1.0 / (npts * len(MIRRORS) * grid.cell_volume)
    for lo in range(0, norb, chunk):
        hi = min(lo + chunk, norb)
        xyz = traj[lo:hi, :, :3].reshape(-1, 3)
        mir = (xyz[None] * MIRRORS[:, None, :]).reshape(-1, 3)
        flat = grid.digitize(mir)
        orb = np.tile(np.repeat(np.arange(lo, hi), npts), len(MIRRORS))
        ok = flat >= 0
        rows.append(flat[ok])
        cols.append(orb[ok])
        vals.append(np.full(ok.sum(), w_point, dtype=dtype))
    rows = np.concatenate(rows)
    cols = np.concatenate(cols)
    vals = np.concatenate(vals)
    A = sp.coo_matrix((vals, (rows, cols)),
                      shape=(grid.ncells, norb), dtype=dtype).tocsr()
    A.sum_duplicates()
    return A


def nnls_mu(A, b, max_iter=400, tol=1e-6, eps=1e-30, w0=None):
    n = A.shape[1]
    w = np.full(n, b.sum() / max(A.sum(), eps)) if w0 is None else w0.copy()
    Atb = A.T @ b
    prev = np.inf
    for it in range(max_iter):
        Aw = A @ w
        w *= Atb / np.maximum(A.T @ Aw, eps)
        if it % 20 == 19:
            r = np.linalg.norm(A @ w - b) / max(np.linalg.norm(b), eps)
            if abs(prev - r) < tol * max(r, eps):
                break
            prev = r
    return w


def solve_subsample(A, rho, mask, cols, relative=True, floor=1e-3, max_iter=400,
                    method='mu'):
    Asub = A[:, cols][mask].astype(np.float64)
    b = rho[mask].astype(np.float64)
    if relative:
        scale = 1.0 / np.maximum(b, floor * b.max())
        Asub = sp.diags(scale) @ Asub
        b = b * scale
    if method == 'mu':
        return nnls_mu(Asub, b, max_iter=max_iter)
    res = lsq_linear(Asub, b, bounds=(0, np.inf), method='trf',
                     lsmr_tol='auto', max_iter=200, verbose=0)
    return res.x


def normalise_weights_to_target_mass(A, w, rho, mask, eps=1e-30):
    model_mass = float(np.asarray(A @ w)[mask].sum())
    target_mass = float(np.asarray(rho)[mask].sum())
    if not np.isfinite(model_mass) or model_mass <= eps:
        raise RuntimeError('cannot mass-normalise weights: non-positive model mass')
    return w * (target_mass / model_mass)


def solve(A, rho, grid, n_sub=5, n_real=10, seed=0, relative=True, verbose=True,
          subsample_target='fractional', normalise_mass=True):
    if subsample_target not in ('fractional', 'full'):
        raise ValueError("subsample_target must be 'fractional' or 'full'")
    norb = A.shape[1]
    rng = np.random.default_rng(seed)
    W = np.zeros((n_real, norb))
    rho_sub = rho / float(n_sub) if subsample_target == 'fractional' else rho
    for r in range(n_real):
        order = rng.permutation(norb)
        for cols in np.array_split(order, n_sub):
            W[r, cols] = solve_subsample(
                A, rho_sub, grid.mask, cols, relative=relative)
        if normalise_mass:
            W[r] = normalise_weights_to_target_mass(A, W[r], rho, grid.mask)
        if verbose:
            mass_ratio = float((A @ W[r])[grid.mask].sum() / rho[grid.mask].sum())
            print('  realisation %2d/%d done; mass ratio %.6f'
                  % (r + 1, n_real, mass_ratio))
    w = W.mean(axis=0)
    if normalise_mass:
        w = normalise_weights_to_target_mass(A, w, rho, grid.mask)
    return w, W


def combine(A, w, rho=None, grid=None, renormalise=False):
    model = A @ w
    if renormalise:
        if rho is None or grid is None:
            raise ValueError('rho and grid are required when renormalise=True')
        m = grid.mask
        num = (model[m] * rho[m]).sum()
        den = (model[m]**2).sum()
        if den <= 0:
            raise RuntimeError('cannot renormalise a zero model')
        model = model * (num / den)
    return model


def residual_stats(model, rho, grid):
    m = grid.mask & (rho > 0)
    rel = (model[m] - rho[m]) / rho[m]
    return dict(median_abs_rel=float(np.median(np.abs(rel))),
                p90_abs_rel=float(np.percentile(np.abs(rel), 90)),
                mass_ratio=float(model[m].sum() / rho[m].sum()))
