"""Candidate L2: causal hereditary tail with local curvature-change deposition.

L2 keeps the parameter-free two-rate L1 transport operator but replaces the
nonlocal field-space deposition D_H Phi_b with the local source

    S_H = 4 pi G kappa c_H^2 tau D_H rho_b
        = kappa c_H^2 tau D_H (Laplacian Phi_b).

This is the minimal local weak-field curvature-change deposition compatible with
Poisson's relation for the ordinary baryonic sector. Static/comoving baryons
have D_H rho_b=0, so they do not continuously regenerate a duplicate Poisson
field. No halo target, galaxy-specific scale, softening length, or fitted
amplitude enters the law.

Transport:

    [ (D_H + 1/tau)(D_H + 2/tau) - c_H^2 Laplacian ] Psi_H = S_H.

For the relaxed-zero initial condition, the free-space retarded Green function
contains a direct light-cone term plus an interior-cone modified-Bessel tail.
For the Gyr-old source-history intervals used here and Galactic source/evaluation
separations, the direct delta-shell term is absent at the present epoch; the
interior tail is evaluated exactly for interval-integrated density changes.

The first exposed Stage 9 run fixed c_H=c. A subluminal c_H is now gated: it may
only be used after an independent parent-action/principal-symbol derivation and
external consistency audit have been frozen before halo comparison.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.special import i1

from analysis.milky_way.candidate_l0 import C_KPC_PER_GYR
from analysis.milky_way.characteristic_speed_gate import (
    CharacteristicSpeedProvenance,
    require_stage9_characteristic_speed,
)
from analysis.milky_way.historical_baryonic_potential import (
    DEFAULT_RMAX_KPC,
    ExponentialDiskSnapshot,
    G_KPC_KMS2_PER_MSUN,
)
from analysis.milky_way.orientation_history import OrientationHistory
from analysis.milky_way.persistence_response import ResponseLawSpecification


@dataclass(frozen=True)
class CandidateL2Parameters:
    tau_gyr: float
    kappa: float = 1.0
    c_h_kpc_per_gyr: float = C_KPC_PER_GYR
    speed_provenance: CharacteristicSpeedProvenance | None = None

    def __post_init__(self) -> None:
        if float(self.tau_gyr) <= 0.0:
            raise ValueError("tau_gyr must be positive")
        if float(self.kappa) != 1.0:
            raise ValueError("Candidate L2 preregistration fixes kappa=1")
        require_stage9_characteristic_speed(
            self.c_h_kpc_per_gyr,
            provenance=self.speed_provenance,
        )

    @property
    def damping_coefficient_per_gyr(self) -> float:
        return 3.0 / float(self.tau_gyr)

    @property
    def restoring_coefficient_per_gyr2(self) -> float:
        return 2.0 / float(self.tau_gyr) ** 2

    @property
    def correlation_length_kpc(self) -> float:
        return float(self.c_h_kpc_per_gyr * self.tau_gyr)


def candidate_l2_specification() -> ResponseLawSpecification:
    return ResponseLawSpecification(
        name="candidate_L2_local_curvature_change_two_rate_tail_unit_deposition",
        causal=True,
        finite_relaxation=True,
        independent_initial_data=True,
        static_source_duplicates_poisson=False,
        gr_recovery=True,
        interaction_vanishes_without_either_sector=True,
        universal_not_galaxy_fitted=True,
        transport_equation_documented=True,
        deposition_law_documented=True,
        interaction_law_documented=True,
        normalization_fixed_without_halo_targets=True,
    )


def cumulative_disk_quadrature(
    snapshot: ExponentialDiskSnapshot,
    orientation: OrientationHistory,
    n_ring: int = 96,
    n_phi: int = 48,
    rmax_kpc: float = DEFAULT_RMAX_KPC,
) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic point quadrature for one cumulative razor-thin disk."""
    if n_ring < 16 or n_phi < 8:
        raise ValueError("n_ring>=16 and n_phi>=8 are required")
    x, w = leggauss(int(n_ring))
    r = 0.5 * (x + 1.0) * float(rmax_kpc)
    drw = 0.5 * float(rmax_kpc) * w
    sigma = snapshot.sigma0_msun_kpc2 * np.exp(-r / snapshot.rd_kpc)
    dm_ring = 2.0 * np.pi * r * sigma * drw

    phi = 2.0 * np.pi * np.arange(n_phi, dtype=float) / float(n_phi)
    cphi, sphi = np.cos(phi), np.sin(phi)
    pts = np.empty((n_ring * n_phi, 3), dtype=float)
    weights = np.repeat(dm_ring / float(n_phi), n_phi)
    for i, rr in enumerate(r):
        sl = slice(i * n_phi, (i + 1) * n_phi)
        pts[sl, 0] = rr * cphi
        pts[sl, 1] = rr * sphi
        pts[sl, 2] = 0.0
    pts = orientation.rotate_points(pts, snapshot.lookback_gyr)
    return pts, weights


def interval_integrated_density_change_clouds(
    snapshots: list[ExponentialDiskSnapshot],
    orientation: OrientationHistory,
    n_ring: int = 96,
    n_phi: int = 48,
    rmax_kpc: float = DEFAULT_RMAX_KPC,
) -> list[tuple[float, np.ndarray, np.ndarray]]:
    """Return midpoint-time signed clouds approximating integral D_H rho_b dt.

    For each adjacent old->young interval the integrated density change is
    represented exactly at quadrature level as +rho_young - rho_old, including
    historical reorientation of the entire cumulative disk. This captures both
    mass-profile evolution and physical disk reorientation without differentiating
    a delta-function disk plane analytically.
    """
    snaps = sorted(snapshots, key=lambda s: s.lookback_gyr, reverse=True)
    out = []
    for old, young in zip(snaps[:-1], snaps[1:]):
        p_old, m_old = cumulative_disk_quadrature(
            old, orientation, n_ring=n_ring, n_phi=n_phi, rmax_kpc=rmax_kpc
        )
        p_yng, m_yng = cumulative_disk_quadrature(
            young, orientation, n_ring=n_ring, n_phi=n_phi, rmax_kpc=rmax_kpc
        )
        pts = np.vstack([p_yng, p_old])
        dm = np.concatenate([m_yng, -m_old])
        midpoint = 0.5 * (old.lookback_gyr + young.lookback_gyr)
        out.append((float(midpoint), pts, dm))
    return out


def _interior_tail_green_per_kpc3_gyr(
    lookback_gyr: float,
    separation_kpc: np.ndarray,
    params: CandidateL2Parameters,
) -> np.ndarray:
    """Free-space L2 interior-cone Green function at the present epoch.

    Units are Gyr/kpc^3. The direct delta-shell light-cone term is not included
    here; interval midpoints are Gyr old whereas Galactic r/c is <~1e-3 Gyr.
    """
    T = float(lookback_gyr)
    r = np.asarray(separation_kpc, dtype=float)
    c = float(params.c_h_kpc_per_gyr)
    tau = float(params.tau_gyr)
    inside = T > (r / c)
    s2 = np.maximum(T * T - (r / c) ** 2, 0.0)
    s = np.sqrt(s2)
    mu = 1.0 / (2.0 * tau)
    damping = np.exp(-1.5 * T / tau)
    out = np.zeros_like(r, dtype=float)
    mask = inside & (s > 0.0)
    if np.any(mask):
        out[mask] = (
            damping
            * mu
            * i1(mu * s[mask])
            / (4.0 * np.pi * c**3 * s[mask])
        )
    edge = inside & ~mask
    if np.any(edge):
        out[edge] = damping * mu * mu / (8.0 * np.pi * c**3)
    return out


def present_psi_from_interval_clouds(
    evaluation_xyz_kpc: np.ndarray,
    interval_clouds: list[tuple[float, np.ndarray, np.ndarray]],
    params: CandidateL2Parameters,
    chunk_size: int = 256,
) -> np.ndarray:
    """Evaluate present Psi_H from local interval-integrated density changes."""
    eval_pts = np.asarray(evaluation_xyz_kpc, dtype=float)
    if eval_pts.shape[-1] != 3:
        raise ValueError("evaluation_xyz_kpc must have final dimension 3")
    flat = eval_pts.reshape(-1, 3)
    result = np.zeros(flat.shape[0], dtype=float)
    prefactor = (
        4.0
        * np.pi
        * G_KPC_KMS2_PER_MSUN
        * float(params.kappa)
        * float(params.c_h_kpc_per_gyr) ** 2
        * float(params.tau_gyr)
    )

    for lookback, src_pts, delta_mass in interval_clouds:
        src = np.asarray(src_pts, dtype=float)
        dm = np.asarray(delta_mass, dtype=float)
        if src.shape != (dm.size, 3):
            raise ValueError("source cloud shape mismatch")
        for start in range(0, flat.shape[0], int(chunk_size)):
            stop = min(start + int(chunk_size), flat.shape[0])
            diff = flat[start:stop, None, :] - src[None, :, :]
            rr = np.linalg.norm(diff, axis=-1)
            green = _interior_tail_green_per_kpc3_gyr(lookback, rr, params)
            result[start:stop] += prefactor * (green * dm[None, :]).sum(axis=1)
    return result.reshape(eval_pts.shape[:-1])


def acceleration_from_regular_grid(
    psi: np.ndarray,
    axes_kpc: tuple[np.ndarray, ...],
) -> tuple[np.ndarray, ...]:
    """Return -grad Psi on a regular 1D/2D/3D Cartesian-style grid."""
    arr = np.asarray(psi, dtype=float)
    if arr.ndim != len(axes_kpc):
        raise ValueError("number of axes must match psi dimensions")
    gradients = np.gradient(arr, *[np.asarray(a, dtype=float) for a in axes_kpc], edge_order=2)
    return tuple(-g for g in gradients)
