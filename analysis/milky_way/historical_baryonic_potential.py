"""Historical ordinary baryonic potential for Stage 9 Candidate L0.

The provisional Ratcliffe et al. (2026) Table A.1 history is represented at each
published epoch by the same minimum-information razor-thin exponential disk used
at the Stage 7 source-history boundary.  This module computes the *ordinary*
Newtonian potential Phi_b of that disk; it is not a persistence force law.

No vertical scale height or softening length is introduced.  The axisymmetric
ring integral is evaluated with Gauss-Legendre quadrature and the exact complete
elliptic-integral potential of a circular ring.  Historical orientation is
handled by rotating evaluation points into the disk frame.

The youngest public Table A.1 epoch is 0.70 Gyr lookback.  For the provisional
Stage 9A source build we append a present-day endpoint by holding that youngest
baryonic model fixed from 0.70 Gyr to 0.0 Gyr.  This deliberately generates no
new deposition over the unobserved final interval rather than extrapolating a
new source history.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.polynomial.legendre import leggauss
from scipy.special import ellipk

from analysis.milky_way.orientation_history import OrientationHistory
from analysis.milky_way.provisional_source_history import REFF_TO_RD

# kpc (km/s)^2 / Msun
G_KPC_KMS2_PER_MSUN = 4.30091e-6
DEFAULT_RMAX_KPC = 25.0


@dataclass(frozen=True)
class ExponentialDiskSnapshot:
    lookback_gyr: float
    mass_msun: float
    reff_kpc: float

    @property
    def rd_kpc(self) -> float:
        return float(self.reff_kpc) / REFF_TO_RD

    @property
    def sigma0_msun_kpc2(self) -> float:
        rd = self.rd_kpc
        return float(self.mass_msun) / (2.0 * np.pi * rd * rd)


def snapshots_from_table_a1(
    table: pd.DataFrame,
    append_present_hold: bool = True,
) -> list[ExponentialDiskSnapshot]:
    required = {"lookback_time_gyr", "stellar_mass_1e10_msun", "Reff_birth_radius_kpc"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    d = table.sort_values("lookback_time_gyr", ascending=False).reset_index(drop=True)
    out = [
        ExponentialDiskSnapshot(
            lookback_gyr=float(row.lookback_time_gyr),
            mass_msun=float(row.stellar_mass_1e10_msun) * 1e10,
            reff_kpc=float(row.Reff_birth_radius_kpc),
        )
        for _, row in d.iterrows()
    ]
    if append_present_hold and out:
        youngest = out[-1]
        if youngest.lookback_gyr > 0.0:
            out.append(
                ExponentialDiskSnapshot(
                    lookback_gyr=0.0,
                    mass_msun=youngest.mass_msun,
                    reff_kpc=youngest.reff_kpc,
                )
            )
    return out


def _ring_nodes(snapshot: ExponentialDiskSnapshot, n_ring: int, rmax_kpc: float):
    if n_ring < 16:
        raise ValueError("n_ring must be at least 16")
    if rmax_kpc <= 0.0:
        raise ValueError("rmax_kpc must be positive")
    x, w = leggauss(int(n_ring))
    a = 0.5 * (x + 1.0) * float(rmax_kpc)
    da_weight = 0.5 * float(rmax_kpc) * w
    sigma = snapshot.sigma0_msun_kpc2 * np.exp(-a / snapshot.rd_kpc)
    # dM = 2 pi a Sigma(a) da
    dm = 2.0 * np.pi * a * sigma * da_weight
    return a, dm


def exponential_disk_potential(
    xyz_kpc: np.ndarray,
    snapshot: ExponentialDiskSnapshot,
    orientation: OrientationHistory | None = None,
    n_ring: int = 192,
    rmax_kpc: float = DEFAULT_RMAX_KPC,
) -> np.ndarray:
    """Return ordinary Newtonian Phi_b in (km/s)^2 at one historical epoch.

    The potential of each quadrature ring is evaluated exactly as

        dPhi = -2 G dM K(m) / [pi sqrt((R+a)^2 + z^2)],
        m = 4 R a / ((R+a)^2 + z^2).

    No Plummer or other softening is used.  Gauss-Legendre source radii avoid
    placing source mass on a uniform evaluation grid by construction; callers
    should still avoid deliberately evaluating exactly on a quadrature ring in
    the razor-thin disk plane.
    """
    pts = np.asarray(xyz_kpc, dtype=float)
    if pts.shape[-1] != 3:
        raise ValueError("xyz_kpc must have final dimension 3")
    flat = pts.reshape(-1, 3)
    if orientation is not None:
        rot = orientation.rotation_matrix(snapshot.lookback_gyr)
        # Present/state-frame point -> historical disk coordinates.
        flat = flat @ rot

    R = np.hypot(flat[:, 0], flat[:, 1])[:, None]
    z = np.abs(flat[:, 2])[:, None]
    a, dm = _ring_nodes(snapshot, n_ring=n_ring, rmax_kpc=rmax_kpc)
    aa = a[None, :]
    denom2 = (R + aa) ** 2 + z**2
    m = np.divide(4.0 * R * aa, denom2, out=np.zeros_like(denom2), where=denom2 > 0)
    # Protect only against roundoff above one; no physical softening is added.
    m = np.clip(m, 0.0, np.nextafter(1.0, 0.0))
    kernel = ellipk(m) / np.sqrt(denom2)
    phi = -(2.0 * G_KPC_KMS2_PER_MSUN / np.pi) * (kernel * dm[None, :]).sum(axis=1)
    return phi.reshape(pts.shape[:-1])


def potential_history(
    xyz_kpc: np.ndarray,
    snapshots: list[ExponentialDiskSnapshot],
    orientation: OrientationHistory,
    n_ring: int = 192,
    rmax_kpc: float = DEFAULT_RMAX_KPC,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (lookback_gyr, Phi_b[epoch,...]) sorted from oldest to present."""
    if len(snapshots) < 2:
        raise ValueError("at least two snapshots are required")
    snaps = sorted(snapshots, key=lambda s: s.lookback_gyr, reverse=True)
    lookback = np.array([s.lookback_gyr for s in snaps], dtype=float)
    phi = np.stack(
        [
            exponential_disk_potential(
                xyz_kpc, s, orientation=orientation, n_ring=n_ring, rmax_kpc=rmax_kpc
            )
            for s in snaps
        ],
        axis=0,
    )
    return lookback, phi


def state_frame_time_derivative(
    lookback_gyr: np.ndarray,
    phi_history: np.ndarray,
) -> np.ndarray:
    """Finite-difference D_H Phi_b for the frozen state frame.

    Candidate L0's first implementation takes the persistent-state frame to be
    the coordinate frame in which the evaluation grid is fixed.  Historical
    source reorientation is already included in Phi_b(x,t), so D_H reduces here
    to the forward-time derivative at fixed state-frame position.  Since cosmic
    forward time increases as lookback time decreases, t_forward = -lookback.
    """
    lb = np.asarray(lookback_gyr, dtype=float)
    phi = np.asarray(phi_history, dtype=float)
    if phi.shape[0] != lb.size:
        raise ValueError("phi_history first axis must match lookback_gyr")
    if lb.size < 2 or not np.all(np.diff(lb) < 0.0):
        raise ValueError("lookback_gyr must be strictly decreasing")
    t_forward = -lb
    edge_order = 2 if lb.size >= 3 else 1
    return np.gradient(phi, t_forward, axis=0, edge_order=edge_order)
