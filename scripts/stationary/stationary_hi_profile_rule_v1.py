#!/usr/bin/env python3
"""Frozen stationary H I tabulated-profile evaluation rule v1.

This module contains observational source-construction logic only. It does not
read velocities, evaluate persistence quantities, or inspect blind outcomes.
"""
from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class TabulatedEvaluation:
    sigma: float
    method: str
    lower_index: int
    upper_index: int


def validate_tabulated_profile(
    radii_kpc: Sequence[float], sigma_msun_pc2: Sequence[float]
) -> None:
    if len(radii_kpc) != len(sigma_msun_pc2) or len(radii_kpc) < 2:
        raise ValueError("need at least two paired radius/surface-density points")
    if any(not math.isfinite(radius) or radius < 0 for radius in radii_kpc):
        raise ValueError("radii must be finite and nonnegative")
    if any(
        radii_kpc[index + 1] <= radii_kpc[index]
        for index in range(len(radii_kpc) - 1)
    ):
        raise ValueError("radii must be strictly increasing")
    if any(not math.isfinite(value) or value < 0 for value in sigma_msun_pc2):
        raise ValueError("surface density must be finite and nonnegative")


def evaluate_tabulated_profile(
    radii_kpc: Sequence[float],
    sigma_msun_pc2: Sequence[float],
    target_radius_kpc: float,
) -> TabulatedEvaluation:
    """Evaluate the frozen piecewise-linear/constant-inner/zero-outer rule."""
    validate_tabulated_profile(radii_kpc, sigma_msun_pc2)
    if not math.isfinite(target_radius_kpc) or target_radius_kpc < 0:
        raise ValueError("target radius must be finite and nonnegative")

    if target_radius_kpc < radii_kpc[0]:
        return TabulatedEvaluation(
            sigma=float(sigma_msun_pc2[0]),
            method="inner_constant",
            lower_index=0,
            upper_index=0,
        )
    if target_radius_kpc > radii_kpc[-1]:
        last = len(radii_kpc) - 1
        return TabulatedEvaluation(
            sigma=0.0,
            method="outer_zero",
            lower_index=last,
            upper_index=last,
        )

    upper = bisect_left(radii_kpc, target_radius_kpc)
    if upper < len(radii_kpc) and target_radius_kpc == radii_kpc[upper]:
        return TabulatedEvaluation(
            sigma=float(sigma_msun_pc2[upper]),
            method="measured_node",
            lower_index=upper,
            upper_index=upper,
        )
    if upper == 0 or upper == len(radii_kpc):
        raise RuntimeError("validated profile produced an invalid interpolation bracket")

    lower = upper - 1
    fraction = (target_radius_kpc - radii_kpc[lower]) / (
        radii_kpc[upper] - radii_kpc[lower]
    )
    sigma = sigma_msun_pc2[lower] + fraction * (
        sigma_msun_pc2[upper] - sigma_msun_pc2[lower]
    )
    if sigma < 0 and abs(sigma) < 1e-12:
        sigma = 0.0
    if not math.isfinite(sigma) or sigma < 0:
        raise RuntimeError("interpolation produced invalid surface density")
    return TabulatedEvaluation(
        sigma=float(sigma),
        method="piecewise_linear",
        lower_index=lower,
        upper_index=upper,
    )
