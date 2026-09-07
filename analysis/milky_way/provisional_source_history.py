"""Provisional Milky Way baryonic-history adapter for Stage 9.

This module converts the public Ratcliffe et al. (2026) Table A.1 global disc
history into a deliberately limited radial source-history representation. It
must not be treated as the final spatial SFH: Stage 7 established that Mstar(t)
and one effective radius per epoch do not uniquely determine the formation-site
history.

Two source envelopes are retained:

* ``signed_mininfo`` keeps the literal difference between adjacent cumulative
  exponential profiles. This exposes where the compressed reconstruction
  becomes unphysical (negative newly assembled mass).
* ``nonnegative_clipped`` clips negative increments to zero. This is a
  conservative physical envelope, not a claim about the true SFH.

Neither branch reads halo forces, Delta a(R), pulsar residuals, or orbit-weight
targets.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from analysis.milky_way.orientation_history import OrientationHistory, exponential_memory_weight

REFF_TO_RD = 1.6783469900166605
DEFAULT_SOURCE = Path(
    "data/external/ratcliffe2026_sfh/ratcliffe2026_tableA1_global_disc_history.csv"
)


@dataclass(frozen=True)
class RadialIncrement:
    older_lookback_gyr: float
    younger_lookback_gyr: float
    representative_lookback_gyr: float
    radius_kpc: np.ndarray
    delta_sigma_msun_kpc2: np.ndarray

    @property
    def dt_gyr(self) -> float:
        return self.older_lookback_gyr - self.younger_lookback_gyr


def _sigma_exp(radius_kpc: np.ndarray, mass_msun: float, reff_kpc: float) -> np.ndarray:
    rd = float(reff_kpc) / REFF_TO_RD
    r = np.asarray(radius_kpc, dtype=float)
    return float(mass_msun) / (2.0 * np.pi * rd**2) * np.exp(-r / rd)


def load_table_a1(path: str | Path = DEFAULT_SOURCE) -> pd.DataFrame:
    df = pd.read_csv(path).copy()
    required = {
        "lookback_time_gyr",
        "stellar_mass_1e10_msun",
        "Reff_birth_radius_kpc",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing required Table A.1 columns: {sorted(missing)}")
    return df.sort_values("lookback_time_gyr", ascending=False).reset_index(drop=True)


def build_radial_increments(
    table: pd.DataFrame,
    radius_kpc: Iterable[float] | None = None,
    envelope: str = "signed_mininfo",
) -> list[RadialIncrement]:
    if envelope not in {"signed_mininfo", "nonnegative_clipped"}:
        raise ValueError("envelope must be signed_mininfo or nonnegative_clipped")

    radius = np.asarray(
        np.linspace(0.001, 25.0, 2000) if radius_kpc is None else tuple(radius_kpc),
        dtype=float,
    )
    if radius.ndim != 1 or radius.size < 2 or np.any(np.diff(radius) <= 0):
        raise ValueError("radius_kpc must be a strictly increasing 1D grid")

    cumulative = []
    for _, row in table.iterrows():
        cumulative.append(
            _sigma_exp(
                radius,
                float(row.stellar_mass_1e10_msun) * 1e10,
                float(row.Reff_birth_radius_kpc),
            )
        )

    out: list[RadialIncrement] = []
    for i in range(len(table) - 1):
        older = float(table.iloc[i].lookback_time_gyr)
        younger = float(table.iloc[i + 1].lookback_time_gyr)
        delta = cumulative[i + 1] - cumulative[i]
        if envelope == "nonnegative_clipped":
            delta = np.clip(delta, 0.0, None)
        out.append(
            RadialIncrement(
                older_lookback_gyr=older,
                younger_lookback_gyr=younger,
                representative_lookback_gyr=0.5 * (older + younger),
                radius_kpc=radius.copy(),
                delta_sigma_msun_kpc2=delta,
            )
        )
    return out


def ring_quadrature_points(
    increment: RadialIncrement,
    n_phi: int = 72,
) -> tuple[np.ndarray, np.ndarray]:
    """Return deterministic in-plane source points and signed mass weights.

    Each radial cell is represented at its midpoint with uniformly spaced
    azimuthal points. The weights integrate the radial surface-density
    increment; they are source quadrature weights, not orbit weights.
    """
    if n_phi < 4:
        raise ValueError("n_phi must be at least 4")
    r = increment.radius_kpc
    edges = np.empty(r.size + 1)
    edges[1:-1] = 0.5 * (r[:-1] + r[1:])
    edges[0] = max(0.0, r[0] - 0.5 * (r[1] - r[0]))
    edges[-1] = r[-1] + 0.5 * (r[-1] - r[-2])
    area_annulus = np.pi * (edges[1:] ** 2 - edges[:-1] ** 2)
    mass_annulus = increment.delta_sigma_msun_kpc2 * area_annulus

    phi = 2.0 * np.pi * np.arange(n_phi, dtype=float) / float(n_phi)
    cosphi, sinphi = np.cos(phi), np.sin(phi)
    xyz = np.empty((r.size * n_phi, 3), dtype=float)
    weights = np.repeat(mass_annulus / float(n_phi), n_phi)
    for i, rr in enumerate(r):
        sl = slice(i * n_phi, (i + 1) * n_phi)
        xyz[sl, 0] = rr * cosphi
        xyz[sl, 1] = rr * sinphi
        xyz[sl, 2] = 0.0
    return xyz, weights


def build_memory_source_cloud(
    increments: list[RadialIncrement],
    orientation: OrientationHistory,
    tau_gyr: float,
    n_phi: int = 72,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Accumulate rotated, exponentially memory-weighted source quadrature."""
    points_all = []
    weights_all = []
    times_all = []
    for inc in increments:
        pts, mass = ring_quadrature_points(inc, n_phi=n_phi)
        t = inc.representative_lookback_gyr
        pts = orientation.rotate_points(pts, t)
        w = mass * exponential_memory_weight(t, tau_gyr)
        points_all.append(pts)
        weights_all.append(w)
        times_all.append(np.full(w.shape, t, dtype=float))
    return np.vstack(points_all), np.concatenate(weights_all), np.concatenate(times_all)


def source_cloud_moments(points: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    """Compact geometry diagnostics of a signed or non-negative source cloud."""
    p = np.asarray(points, dtype=float)
    w = np.asarray(weights, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or w.shape != (p.shape[0],):
        raise ValueError("points/weights shape mismatch")
    absw = np.abs(w)
    norm = float(absw.sum())
    if norm <= 0.0:
        raise ValueError("source cloud has zero absolute weight")
    centroid = (absw[:, None] * p).sum(axis=0) / norm
    q = p - centroid
    second = (absw[:, None, None] * q[:, :, None] * q[:, None, :]).sum(axis=0) / norm
    evals = np.linalg.eigvalsh(second)
    return {
        "signed_memory_mass_msun": float(w.sum()),
        "absolute_memory_mass_msun": norm,
        "negative_weight_fraction": float(absw[w < 0.0].sum() / norm),
        "centroid_x_kpc": float(centroid[0]),
        "centroid_y_kpc": float(centroid[1]),
        "centroid_z_kpc": float(centroid[2]),
        "second_moment_eigenvalue_min_kpc2": float(evals[0]),
        "second_moment_eigenvalue_mid_kpc2": float(evals[1]),
        "second_moment_eigenvalue_max_kpc2": float(evals[2]),
    }
