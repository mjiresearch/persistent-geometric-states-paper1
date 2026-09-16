"""Time-dependent orientation operator for Milky Way persistence tests.

This module is deliberately source-side only. It rotates historical baryonic
source snapshots into the present-day Galactic frame without consulting a dark
matter halo, a force residual, or orbit-weight targets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


_EPS = 1e-15


def _unit_vector(axis: Iterable[float]) -> np.ndarray:
    vec = np.asarray(tuple(axis), dtype=float)
    if vec.shape != (3,):
        raise ValueError("rotation axis must contain exactly three components")
    norm = float(np.linalg.norm(vec))
    if norm <= _EPS:
        raise ValueError("rotation axis must be non-zero")
    return vec / norm


def rotation_matrix_axis_angle(axis: Iterable[float], angle_deg: float) -> np.ndarray:
    """Return a right-handed 3x3 Rodrigues rotation matrix."""
    x, y, z = _unit_vector(axis)
    theta = np.deg2rad(float(angle_deg))
    c = np.cos(theta)
    s = np.sin(theta)
    one_c = 1.0 - c
    return np.array(
        [
            [c + x * x * one_c, x * y * one_c - z * s, x * z * one_c + y * s],
            [y * x * one_c + z * s, c + y * y * one_c, y * z * one_c - x * s],
            [z * x * one_c - y * s, z * y * one_c + x * s, c + z * z * one_c],
        ],
        dtype=float,
    )


def _smoothstep01(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


@dataclass(frozen=True)
class OrientationHistory:
    """Parametric historical reorientation relative to today's Galactic frame.

    total_angle_deg is the ancient-to-present reorientation amplitude. Zero is
    the canonical non-flipped Stage 9A baseline. Sensitivity cases are
    predeclared rather than optimized against halo solutions.
    """

    total_angle_deg: float = 0.0
    axis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    transition_lookback_gyr: float = 8.0
    transition_duration_gyr: float = 2.0

    def __post_init__(self) -> None:
        if not (0.0 <= float(self.total_angle_deg) <= 180.0):
            raise ValueError("total_angle_deg must lie in [0, 180]")
        _unit_vector(self.axis)
        if float(self.transition_lookback_gyr) < 0.0:
            raise ValueError("transition_lookback_gyr must be non-negative")
        if float(self.transition_duration_gyr) < 0.0:
            raise ValueError("transition_duration_gyr must be non-negative")

    @property
    def unit_axis(self) -> np.ndarray:
        return _unit_vector(self.axis)

    def historical_angle_deg(self, lookback_gyr: float) -> float:
        """Historical orientation angle relative to the present-day disk."""
        t = max(float(lookback_gyr), 0.0)
        duration = float(self.transition_duration_gyr)
        centre = float(self.transition_lookback_gyr)
        angle = float(self.total_angle_deg)

        if duration <= _EPS:
            return angle if t >= centre else 0.0

        younger_edge = max(centre - 0.5 * duration, 0.0)
        older_edge = centre + 0.5 * duration
        if t <= younger_edge:
            return 0.0
        if t >= older_edge:
            return angle

        frac = (t - younger_edge) / max(older_edge - younger_edge, _EPS)
        return angle * _smoothstep01(frac)

    def rotation_matrix(self, lookback_gyr: float) -> np.ndarray:
        return rotation_matrix_axis_angle(self.axis, self.historical_angle_deg(lookback_gyr))

    def rotate_points(self, xyz: np.ndarray, lookback_gyr: float) -> np.ndarray:
        """Rotate one or many historical source positions into today's frame."""
        arr = np.asarray(xyz, dtype=float)
        if arr.shape[-1] != 3:
            raise ValueError("xyz must have final dimension 3")
        rot = self.rotation_matrix(lookback_gyr)
        return arr @ rot.T

    def rotate_vectors(self, vec: np.ndarray, lookback_gyr: float) -> np.ndarray:
        """Rotate vector source quantities (e.g. velocity/current) consistently."""
        return self.rotate_points(vec, lookback_gyr)

    def rotate_snapshot(
        self,
        positions: np.ndarray,
        lookback_gyr: float,
        vectors: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """Rotate a density/current snapshot with one shared historical frame."""
        rotated_positions = self.rotate_points(positions, lookback_gyr)
        rotated_vectors = None if vectors is None else self.rotate_vectors(vectors, lookback_gyr)
        return rotated_positions, rotated_vectors


def exponential_memory_weight(lookback_gyr: float, tau_gyr: float) -> float:
    """Relative temporal attenuation exp(-t/tau) for sensitivity calculations."""
    t = max(float(lookback_gyr), 0.0)
    tau = float(tau_gyr)
    if tau <= 0.0:
        raise ValueError("tau_gyr must be positive")
    return float(np.exp(-t / tau))
