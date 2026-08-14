#!/usr/bin/env python3
"""Frozen statistical core for the independent DR20 current-field block.

This module deliberately has no repository-data paths.  Synthetic validation and the
real builders call the same functions so that the pre-outcome statistic is executable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


VELOCITY_COLUMNS = ("v_R_kms", "v_phi_kms", "v_z_kms")
POSITION_COLUMNS = ("x_kpc", "y_kpc", "z_kpc")


def load_protocol(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _finite_frame(frame: pd.DataFrame, columns: list[str] | tuple[str, ...]) -> np.ndarray:
    return np.isfinite(frame.loc[:, list(columns)].to_numpy(dtype=float)).all(axis=1)


def select_age_cohorts(frame: pd.DataFrame, protocol: dict[str, Any]) -> pd.DataFrame:
    """Return the two disjoint, uncertainty-separated cohorts."""
    required = ["age_gyr", "age_err_lower_gyr", "age_err_upper_gyr"]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing age columns: {missing}")
    d = frame.copy()
    for name in required:
        d[name] = pd.to_numeric(d[name], errors="coerce")
    finite = _finite_frame(d, required)
    finite &= (d["age_err_lower_gyr"].to_numpy() >= 0)
    finite &= (d["age_err_upper_gyr"].to_numpy() >= 0)
    young = finite & ((d["age_gyr"] + d["age_err_upper_gyr"]) <= 1.0)
    old = finite & ((d["age_gyr"] - d["age_err_lower_gyr"]) >= 4.0)
    if np.any(young & old):
        raise AssertionError("Frozen cohort cuts unexpectedly overlap")
    d = d.loc[young | old].copy()
    d["cohort"] = np.where(young[young | old], "young", "old")
    return d


def assign_voxels(frame: pd.DataFrame, protocol: dict[str, Any]) -> pd.DataFrame:
    grid = protocol["field_test"]["grid"]
    width = np.asarray(grid["cell_width_kpc"], dtype=float)
    origin = np.asarray(grid["origin_kpc"], dtype=float)
    if width.shape != (3,) or np.any(width <= 0):
        raise ValueError("Frozen voxel widths must be three positive numbers")
    d = frame.copy()
    xyz = d.loc[:, POSITION_COLUMNS].to_numpy(dtype=float)
    idx = np.floor((xyz - origin) / width).astype(np.int64)
    d[["voxel_ix", "voxel_iy", "voxel_iz"]] = idx
    d["voxel_id"] = (
        d["voxel_ix"].astype(str)
        + ":"
        + d["voxel_iy"].astype(str)
        + ":"
        + d["voxel_iz"].astype(str)
    )
    return d


def _mean_covariance(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or values.shape[0] < 2:
        raise ValueError("Mean covariance requires an n-by-3 array with n >= 2")
    mean = values.mean(axis=0)
    covariance_of_mean = np.cov(values, rowvar=False, ddof=1) / values.shape[0]
    return mean, np.asarray(covariance_of_mean, dtype=float)


def _voxel_distance(velocities: np.ndarray, labels: np.ndarray, ridge_fraction: float) -> float:
    young = velocities[labels == 0]
    old = velocities[labels == 1]
    young_mean, young_cov = _mean_covariance(young)
    old_mean, old_cov = _mean_covariance(old)
    covariance = young_cov + old_cov
    scale = max(float(np.trace(covariance) / 3.0), 1.0)
    covariance = covariance + np.eye(3) * ridge_fraction * scale
    delta = old_mean - young_mean
    return float(delta @ np.linalg.pinv(covariance, hermitian=True) @ delta)


def _supported_groups(frame: pd.DataFrame, protocol: dict[str, Any]) -> list[dict[str, Any]]:
    minimum = int(protocol["field_test"]["grid"]["min_each_cohort_per_voxel"])
    groups: list[dict[str, Any]] = []
    for voxel_id, group in frame.groupby("voxel_id", sort=True, observed=True):
        labels = (group["cohort"].to_numpy() == "old").astype(np.int8)
        n_young = int(np.sum(labels == 0))
        n_old = int(np.sum(labels == 1))
        if min(n_young, n_old) < minimum:
            continue
        groups.append(
            {
                "voxel_id": str(voxel_id),
                "frame": group.copy(),
                "velocities": group.loc[:, VELOCITY_COLUMNS].to_numpy(dtype=float),
                "labels": labels,
                "n_young": n_young,
                "n_old": n_old,
            }
        )
    return groups


def _field_statistic(groups: list[dict[str, Any]], label_sets: list[np.ndarray], ridge: float) -> float:
    if not groups:
        return float("nan")
    distances = [
        _voxel_distance(group["velocities"], labels, ridge)
        for group, labels in zip(groups, label_sets, strict=True)
    ]
    return float(np.mean(distances))


def _voxel_audit(groups: list[dict[str, Any]], protocol: dict[str, Any]) -> pd.DataFrame:
    widths = np.asarray(protocol["field_test"]["grid"]["cell_width_kpc"], dtype=float)
    origin = np.asarray(protocol["field_test"]["grid"]["origin_kpc"], dtype=float)
    volume = float(np.prod(widths))
    rows: list[dict[str, Any]] = []
    for item in groups:
        group = item["frame"]
        young = group[group["cohort"] == "young"]
        old = group[group["cohort"] == "old"]
        n_young, n_old = len(young), len(old)
        harmonic_count = 2.0 * n_young * n_old / (n_young + n_old)
        rho_match = harmonic_count / volume
        indices = group[["voxel_ix", "voxel_iy", "voxel_iz"]].iloc[0].to_numpy(dtype=int)
        row: dict[str, Any] = {
            "voxel_id": item["voxel_id"],
            "voxel_ix": int(indices[0]),
            "voxel_iy": int(indices[1]),
            "voxel_iz": int(indices[2]),
            "x_center_kpc": float(origin[0] + (indices[0] + 0.5) * widths[0]),
            "y_center_kpc": float(origin[1] + (indices[1] + 0.5) * widths[1]),
            "z_center_kpc": float(origin[2] + (indices[2] + 0.5) * widths[2]),
            "voxel_volume_kpc3": volume,
            "n_young": int(n_young),
            "n_old": int(n_old),
            "rho_young_tracer_per_kpc3": float(n_young / volume),
            "rho_old_tracer_per_kpc3": float(n_old / volume),
            "rho_match_tracer_per_kpc3": float(rho_match),
        }
        for cohort_name, sample in (("young", young), ("old", old)):
            means = sample.loc[:, VELOCITY_COLUMNS].mean().to_numpy(dtype=float)
            for component, mean_value in zip(("R", "phi", "z"), means, strict=True):
                row[f"v_{component}_{cohort_name}_mean_kms"] = float(mean_value)
                row[f"J_{component}_{cohort_name}_raw_tracer_kms_per_kpc3"] = float(
                    mean_value * len(sample) / volume
                )
                row[f"J_{component}_{cohort_name}_matched_tracer_kms_per_kpc3"] = float(
                    mean_value * rho_match
                )
        for component in ("R", "phi", "z"):
            row[f"delta_v_{component}_old_minus_young_kms"] = (
                row[f"v_{component}_old_mean_kms"] - row[f"v_{component}_young_mean_kms"]
            )
            row[f"delta_J_{component}_matched_old_minus_young_tracer_kms_per_kpc3"] = (
                row[f"J_{component}_old_matched_tracer_kms_per_kpc3"]
                - row[f"J_{component}_young_matched_tracer_kms_per_kpc3"]
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("voxel_id").reset_index(drop=True) if rows else pd.DataFrame()


def analyze_current_field(
    frame: pd.DataFrame,
    protocol: dict[str, Any],
    *,
    n_permutations: int | None = None,
    seed: int | None = None,
) -> tuple[dict[str, Any], pd.DataFrame, np.ndarray]:
    """Run the frozen field test on a standardized phase-space frame."""
    required = set(POSITION_COLUMNS + VELOCITY_COLUMNS) | {
        "age_gyr",
        "age_err_lower_gyr",
        "age_err_upper_gyr",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing standardized field columns: {missing}")
    d = frame.copy()
    numeric = list(required)
    for name in numeric:
        d[name] = pd.to_numeric(d[name], errors="coerce")
    phase_finite = _finite_frame(d, POSITION_COLUMNS + VELOCITY_COLUMNS)
    d = d.loc[phase_finite].copy()
    phase_rows = len(d)
    d = select_age_cohorts(d, protocol)
    cohort_counts = d["cohort"].value_counts().to_dict()
    d = assign_voxels(d, protocol)
    groups = _supported_groups(d, protocol)
    primary = protocol["field_test"]["primary_statistic"]
    ridge = float(primary["covariance_ridge_fraction"])
    observed = _field_statistic(groups, [item["labels"] for item in groups], ridge)
    nperm = int(primary["permutations"] if n_permutations is None else n_permutations)
    actual_seed = int(primary["seed"] if seed is None else seed)
    rng = np.random.default_rng(actual_seed)
    permutation_values = np.full(nperm, np.nan, dtype=float)
    for index in range(nperm):
        permuted = [rng.permutation(item["labels"]) for item in groups]
        permutation_values[index] = _field_statistic(groups, permuted, ridge)
    p_value = (
        float((1 + np.sum(permutation_values >= observed)) / (nperm + 1))
        if np.isfinite(observed)
        else None
    )
    voxel_audit = _voxel_audit(groups, protocol)
    minimum_voxels = int(protocol["field_test"]["grid"]["minimum_powered_voxels"])
    powered = len(groups) >= minimum_voxels
    alpha = float(primary["alpha"])
    if not powered:
        verdict = "underpowered"
    elif p_value is not None and p_value <= alpha:
        verdict = "reject_within_voxel_exchangeability"
    else:
        verdict = "do_not_reject_within_voxel_exchangeability"
    component_contrasts = {}
    if not voxel_audit.empty:
        for component in ("R", "phi", "z"):
            column = f"delta_v_{component}_old_minus_young_kms"
            component_contrasts[component] = {
                "equal_voxel_mean_old_minus_young_kms": float(voxel_audit[column].mean()),
                "equal_voxel_median_old_minus_young_kms": float(voxel_audit[column].median()),
            }
    summary = {
        "protocol_id": protocol["protocol_id"],
        "analysis": "young-old selection-balanced 3D tracer-current comparison",
        "input_rows": int(len(frame)),
        "finite_phase_space_rows": int(phase_rows),
        "young_rows_after_age_bounds": int(cohort_counts.get("young", 0)),
        "old_rows_after_age_bounds": int(cohort_counts.get("old", 0)),
        "supported_voxels": int(len(groups)),
        "minimum_powered_voxels": minimum_voxels,
        "powered": bool(powered),
        "primary_statistic_T": float(observed) if np.isfinite(observed) else None,
        "n_permutations": nperm,
        "permutation_seed": actual_seed,
        "p_value_greater_equal": p_value,
        "alpha": alpha,
        "field_verdict": verdict,
        "secondary_signed_velocity_contrasts": component_contrasts,
        "guardrail": (
            "This is a matched tracer-current test, not a calibrated stellar-mass current or "
            "a direct gravitational-acceleration measurement."
        ),
    }
    return summary, voxel_audit, permutation_values


def analyze_cluster_control(
    age_gyr: np.ndarray,
    present_radius_kpc: np.ndarray,
    guiding_radius_kpc: np.ndarray,
    protocol: dict[str, Any],
    *,
    n_permutations: int | None = None,
    seed: int | None = None,
) -> tuple[dict[str, Any], np.ndarray]:
    """Run the frozen one-sided age-versus-guiding-offset control."""
    control = protocol["open_cluster_control"]
    age = np.asarray(age_gyr, dtype=float)
    present = np.asarray(present_radius_kpc, dtype=float)
    guiding = np.asarray(guiding_radius_kpc, dtype=float)
    finite = np.isfinite(age) & np.isfinite(present) & np.isfinite(guiding) & (age > 0)
    age = age[finite]
    offset = np.abs(guiding[finite] - present[finite])
    observed = float(spearmanr(age, offset).statistic) if len(age) >= 3 else float("nan")
    nperm = int(control["permutations"] if n_permutations is None else n_permutations)
    actual_seed = int(control["seed"] if seed is None else seed)
    rng = np.random.default_rng(actual_seed)
    permuted = np.full(nperm, np.nan, dtype=float)
    for index in range(nperm):
        permuted[index] = float(spearmanr(rng.permutation(age), offset).statistic)
    p_value = (
        float((1 + np.sum(permuted >= observed)) / (nperm + 1))
        if np.isfinite(observed)
        else None
    )
    minimum = int(control["minimum_clusters"])
    powered = len(age) >= minimum
    alpha = float(control["alpha"])
    positive = bool(powered and p_value is not None and p_value <= alpha and observed > 0)
    return (
        {
            "protocol_id": protocol["protocol_id"],
            "analysis": "open-cluster age versus absolute guiding-radius offset control",
            "clusters": int(len(age)),
            "minimum_clusters": minimum,
            "powered": bool(powered),
            "spearman_rho": float(observed) if np.isfinite(observed) else None,
            "n_permutations": nperm,
            "permutation_seed": actual_seed,
            "p_value_positive_tail": p_value,
            "alpha": alpha,
            "positive_confound_control": positive,
        },
        permuted,
    )
