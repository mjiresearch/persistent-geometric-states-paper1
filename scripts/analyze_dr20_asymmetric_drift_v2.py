#!/usr/bin/env python3
"""Run Test A of the frozen DR20-v2 conventional-dynamics challenge.

This script is additive: it reads the immutable v1 star-level phase-space product and
writes only v2 asymmetric-drift products.  It does not rebuild the v1 sample.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


VEL = ("v_R_kms", "v_phi_kms", "v_z_kms")
VOXEL = ("voxel_ix", "voxel_iy", "voxel_iz")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def select_cohorts(d: pd.DataFrame) -> pd.DataFrame:
    out = d.copy()
    for c in ("age_gyr", "age_err_lower_gyr", "age_err_upper_gyr"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    finite = np.isfinite(out[["age_gyr", "age_err_lower_gyr", "age_err_upper_gyr"]]).all(axis=1)
    finite &= out["age_err_lower_gyr"].to_numpy(float) >= 0
    finite &= out["age_err_upper_gyr"].to_numpy(float) >= 0
    young = finite & ((out["age_gyr"] + out["age_err_upper_gyr"]) <= 1.0)
    old = finite & ((out["age_gyr"] - out["age_err_lower_gyr"]) >= 4.0)
    if np.any(young & old):
        raise AssertionError("Frozen young/old age cuts overlap")
    out = out.loc[young | old].copy()
    out["cohort"] = np.where(young[young | old], "young", "old")
    return out


def assign_voxels(d: pd.DataFrame, v1: dict[str, Any]) -> pd.DataFrame:
    out = d.copy()
    grid = v1["field_test"]["grid"]
    width = np.asarray(grid["cell_width_kpc"], dtype=float)
    origin = np.asarray(grid["origin_kpc"], dtype=float)
    xyz = out[["x_kpc", "y_kpc", "z_kpc"]].to_numpy(float)
    idx = np.floor((xyz - origin) / width).astype(np.int64)
    out[list(VOXEL)] = idx
    out["voxel_id"] = (
        out["voxel_ix"].astype(str) + ":" + out["voxel_iy"].astype(str) + ":" + out["voxel_iz"].astype(str)
    )
    return out


def supported_sample(d: pd.DataFrame, v1: dict[str, Any]) -> tuple[pd.DataFrame, list[str]]:
    minimum = int(v1["field_test"]["grid"]["min_each_cohort_per_voxel"])
    keep: list[str] = []
    for voxel_id, g in d.groupby("voxel_id", sort=True):
        counts = g["cohort"].value_counts()
        if int(counts.get("young", 0)) >= minimum and int(counts.get("old", 0)) >= minimum:
            keep.append(str(voxel_id))
    return d[d["voxel_id"].isin(keep)].copy(), keep


def unbiased_var(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    return float(np.var(x, ddof=1)) if len(x) >= 2 else float("nan")


def moments(g: pd.DataFrame) -> dict[str, float]:
    vr = g["v_R_kms"].to_numpy(float)
    vp = g["v_phi_kms"].to_numpy(float)
    vz = g["v_z_kms"].to_numpy(float)
    return {
        "mean_R": float(np.mean(vr)),
        "mean_phi": float(np.mean(vp)),
        "mean_z": float(np.mean(vz)),
        "sigma_R": float(np.std(vr, ddof=1)),
        "sigma_phi": float(np.std(vp, ddof=1)),
        "sigma_z": float(np.std(vz, ddof=1)),
        "cov_Rz": float(np.cov(vr, vz, ddof=1)[0, 1]),
    }


def z_stratum(abs_z: float) -> str | None:
    if 0.0 <= abs_z < 0.25:
        return "z0_025"
    if 0.25 <= abs_z < 0.50:
        return "z025_050"
    return None


def fit_common_radial_gradients(d: pd.DataFrame, spec: dict[str, Any]) -> tuple[dict[str, float], pd.DataFrame]:
    """Fit d ln(nu sigma_R^2) / d ln R in the two frozen |z| strata.

    Implementation lock: nu is count divided by full cylindrical annulus x slab volume.
    Because only the log-slope is used, the omitted constant azimuthal completeness factor
    would cancel if locally R-independent. This is explicitly a catalog-tracer density.
    """
    width = float(spec["radial_gradient"]["radial_bin_width_kpc"])
    rows: list[dict[str, Any]] = []
    slopes: dict[str, float] = {}
    for label, lo, hi in (("z0_025", 0.0, 0.25), ("z025_050", 0.25, 0.50)):
        s = d[(d["z_kpc"].abs() >= lo) & (d["z_kpc"].abs() < hi)].copy()
        if s.empty:
            slopes[label] = float("nan")
            continue
        s["R_bin"] = np.floor(s["R_kpc"].to_numpy(float) / width).astype(int)
        fit_rows = []
        for rb, g in s.groupby("R_bin", sort=True):
            n = len(g)
            if n < 2:
                continue
            r_lo = rb * width
            r_hi = r_lo + width
            r_mid = 0.5 * (r_lo + r_hi)
            # Both +z and -z are included, so total slab thickness is 2*(hi-lo).
            volume = np.pi * (r_hi**2 - r_lo**2) * (2.0 * (hi - lo))
            nu = n / volume
            sr2 = unbiased_var(g["v_R_kms"].to_numpy(float))
            y = nu * sr2
            if r_mid > 0 and np.isfinite(y) and y > 0:
                fit_rows.append((r_mid, y, n, nu, sr2))
                rows.append({
                    "z_stratum": label, "R_bin": int(rb), "R_mid_kpc": r_mid,
                    "n": int(n), "annulus_slab_volume_kpc3": volume,
                    "nu_tracer_per_kpc3": nu, "sigma_R2_kms2": sr2,
                    "nu_sigma_R2": y,
                })
        min_bins = int(spec["radial_gradient"]["minimum_populated_radial_bins"])
        if len(fit_rows) < min_bins:
            slopes[label] = float("nan")
            continue
        x = np.log([r[0] for r in fit_rows])
        y = np.log([r[1] for r in fit_rows])
        slopes[label] = float(np.polyfit(x, y, 1)[0])
    return slopes, pd.DataFrame(rows)


def predict_vphi(sigma_R: float, sigma_phi: float, gradient: float, vc: float, tilt_term: float = 0.0) -> float:
    rhs = sigma_phi**2 - sigma_R**2 * (1.0 + gradient) - tilt_term
    inside = vc**2 - rhs
    return float(np.sqrt(inside)) if np.isfinite(inside) and inside >= 0 else float("nan")


def radial_bin_index(r: float, width: float) -> int:
    return int(np.floor(float(r) / width))


def z_layer_index(z: float, width: float = 0.1) -> int:
    return int(np.floor(float(z) / width))


def tilt_lookup(d: pd.DataFrame, radial_width: float = 0.5, z_width: float = 0.1) -> dict[tuple[str, int, int], float]:
    """Estimate (R/nu) d(nu <v_R v_z>)/dz for cohort/radial/z cells.

    A centered difference is available only when both adjacent signed-z layers contain
    at least two stars. The geometric density uses full annulus x layer volume.
    """
    work = d.copy()
    work["rb"] = np.floor(work["R_kpc"].to_numpy(float) / radial_width).astype(int)
    work["zb"] = np.floor(work["z_kpc"].to_numpy(float) / z_width).astype(int)
    cell: dict[tuple[str, int, int], tuple[float, float]] = {}
    for (cohort, rb, zb), g in work.groupby(["cohort", "rb", "zb"], sort=True):
        if len(g) < 2:
            continue
        r_lo, r_hi = rb * radial_width, (rb + 1) * radial_width
        volume = np.pi * (r_hi**2 - r_lo**2) * z_width
        nu = len(g) / volume
        cov = float(np.cov(g["v_R_kms"].to_numpy(float), g["v_z_kms"].to_numpy(float), ddof=1)[0, 1])
        cell[(str(cohort), int(rb), int(zb))] = (nu, cov)
    out: dict[tuple[str, int, int], float] = {}
    for key, (nu0, _cov0) in cell.items():
        cohort, rb, zb = key
        low = cell.get((cohort, rb, zb - 1))
        high = cell.get((cohort, rb, zb + 1))
        if low is None or high is None or nu0 <= 0:
            continue
        deriv = (high[0] * high[1] - low[0] * low[1]) / (2.0 * z_width)
        r_mid = (rb + 0.5) * radial_width
        out[key] = float((r_mid / nu0) * deriv)
    return out


def voxel_prediction(g: pd.DataFrame, gradient: float, vc: float, tilt: dict[tuple[str, int, int], float] | None, radial_width: float) -> dict[str, Any]:
    result: dict[str, Any] = {}
    r = float(g["R_kpc"].mean())
    z = float(g["z_kpc"].mean())
    result["R_mean_kpc"] = r
    result["z_mean_kpc"] = z
    result["gradient"] = gradient
    pred = {}
    for cohort in ("young", "old"):
        s = g[g["cohort"] == cohort]
        m = moments(s)
        for k, v in m.items():
            result[f"{cohort}_{k}"] = v
        tilt_term = 0.0
        tilt_available = False
        if tilt is not None:
            key = (cohort, radial_bin_index(r, radial_width), z_layer_index(z))
            if key in tilt:
                tilt_term = tilt[key]
                tilt_available = True
        result[f"{cohort}_tilt_term_kms2"] = float(tilt_term) if tilt_available else None
        result[f"{cohort}_tilt_available"] = bool(tilt_available)
        pred[cohort] = predict_vphi(m["sigma_R"], m["sigma_phi"], gradient, vc, tilt_term)
        result[f"{cohort}_vphi_AD_pred_kms"] = pred[cohort]
    result["delta_vphi_observed_kms"] = result["old_mean_phi"] - result["young_mean_phi"]
    result["delta_vphi_AD_pred_kms"] = pred["old"] - pred["young"]
    result["delta_vphi_residual_kms"] = result["delta_vphi_observed_kms"] - result["delta_vphi_AD_pred_kms"]
    return result


def bootstrap_prediction(groups: list[pd.DataFrame], gradient_by_voxel: list[float], vc: float, nboot: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    values = np.full(nboot, np.nan)
    for b in range(nboot):
        preds = []
        for g, grad in zip(groups, gradient_by_voxel, strict=True):
            cohort_pred = {}
            for cohort in ("young", "old"):
                s = g[g["cohort"] == cohort]
                take = rng.integers(0, len(s), size=len(s))
                bs = s.iloc[take]
                sr = float(np.std(bs["v_R_kms"].to_numpy(float), ddof=1))
                sp = float(np.std(bs["v_phi_kms"].to_numpy(float), ddof=1))
                cohort_pred[cohort] = predict_vphi(sr, sp, grad, vc)
            preds.append(cohort_pred["old"] - cohort_pred["young"])
        values[b] = float(np.nanmean(preds)) if preds else np.nan
    return values


def residual_permutation(groups: list[pd.DataFrame], gradient_by_voxel: list[float], vc: float, nperm: int, seed: int) -> tuple[float, np.ndarray, float]:
    """Permute age labels within voxel and recompute both observed and AD-predicted contrast."""
    observed_residuals = []
    for g, grad in zip(groups, gradient_by_voxel, strict=True):
        p = voxel_prediction(g, grad, vc, None, radial_width=0.5)
        observed_residuals.append(p["delta_vphi_residual_kms"])
    observed = float(np.mean(observed_residuals))
    rng = np.random.default_rng(seed)
    perms = np.full(nperm, np.nan)
    for i in range(nperm):
        vals = []
        for g, grad in zip(groups, gradient_by_voxel, strict=True):
            gp = g.copy()
            gp["cohort"] = rng.permutation(gp["cohort"].to_numpy())
            p = voxel_prediction(gp, grad, vc, None, radial_width=0.5)
            vals.append(p["delta_vphi_residual_kms"])
        perms[i] = float(np.mean(vals))
    # Two-sided permutation test for any residual age contrast.
    pvalue = float((1 + np.sum(np.abs(perms) >= abs(observed))) / (nperm + 1))
    return observed, perms, pvalue


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--star-sample", type=Path, default=Path("data/persistence_history/dr20_independent/field_v1/field_star_sample.csv.gz"))
    p.add_argument("--v1-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json"))
    p.add_argument("--v2-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v2_conventional_challenge.json"))
    p.add_argument("--output-dir", type=Path, default=Path("data/persistence_history/dr20_independent/conventional_challenge_v2/test_A_asymmetric_drift"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    v1 = load_json(args.v1_protocol)
    v2 = load_json(args.v2_protocol)
    if v2.get("status") != "frozen_pre_v2_outcome" or v2.get("outcome_status_at_freeze") != "no_v2_outcome_evaluated":
        raise RuntimeError("Refusing to run: DR20-v2 protocol is not in the frozen pre-outcome state")
    spec = v2["test_A_asymmetric_drift"]
    vc = float(spec["V_c_kms"])
    radial_width = float(spec["radial_gradient"]["radial_bin_width_kpc"])

    raw = pd.read_csv(args.star_sample, low_memory=False)
    required = {"x_kpc", "y_kpc", "z_kpc", "R_kpc", *VEL, "age_gyr", "age_err_lower_gyr", "age_err_upper_gyr"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"v1 star sample missing required columns: {missing}")
    for c in required:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    raw = raw[np.isfinite(raw[list(required)].to_numpy(float)).all(axis=1)].copy()
    d = assign_voxels(select_cohorts(raw), v1)
    supported, voxel_ids = supported_sample(d, v1)

    slopes, gradient_bins = fit_common_radial_gradients(d, spec)
    tilt = tilt_lookup(d, radial_width=radial_width, z_width=0.1)

    rows = []
    baseline_groups: list[pd.DataFrame] = []
    baseline_gradients: list[float] = []
    for voxel_id in voxel_ids:
        g = supported[supported["voxel_id"] == voxel_id].copy()
        stratum = z_stratum(abs(float(g["z_kpc"].mean())))
        grad = slopes.get(stratum, float("nan")) if stratum else float("nan")
        row = {"voxel_id": voxel_id, "z_stratum": stratum}
        if np.isfinite(grad):
            row.update(voxel_prediction(g, grad, vc, None, radial_width))
            baseline_groups.append(g)
            baseline_gradients.append(grad)
            tilt_row = voxel_prediction(g, grad, vc, tilt, radial_width)
            row["tilt_delta_vphi_AD_pred_kms"] = tilt_row["delta_vphi_AD_pred_kms"]
            row["tilt_delta_vphi_residual_kms"] = tilt_row["delta_vphi_residual_kms"]
            row["tilt_both_cohorts_available"] = bool(tilt_row["young_tilt_available"] and tilt_row["old_tilt_available"])
        else:
            row["gradient"] = None
            row["excluded_reason"] = "no_frozen_stratum_gradient"
        rows.append(row)
    voxel_table = pd.DataFrame(rows)

    nboot = int(spec["bootstrap"]["resamples"])
    boot_seed = int(spec["bootstrap"]["seed"])
    bootstrap = bootstrap_prediction(baseline_groups, baseline_gradients, vc, nboot, boot_seed)
    finite_boot = bootstrap[np.isfinite(bootstrap)]
    ci_low, ci_high = (np.quantile(finite_boot, [0.025, 0.975]) if len(finite_boot) else [np.nan, np.nan])

    nperm = int(spec["residual_permutation"]["permutations"])
    # Protocol fixes 20260821 for Test-A bootstrap and does not separately specify a seed
    # for residual permutation; schema-only implementation lock derives seed+1.
    perm_seed = boot_seed + 1
    obs_resid, perms, p_resid = residual_permutation(baseline_groups, baseline_gradients, vc, nperm, perm_seed)

    valid = voxel_table[np.isfinite(pd.to_numeric(voxel_table.get("delta_vphi_AD_pred_kms"), errors="coerce"))].copy()
    observed_delta = float(valid["delta_vphi_observed_kms"].mean()) if len(valid) else float("nan")
    predicted_delta = float(valid["delta_vphi_AD_pred_kms"].mean()) if len(valid) else float("nan")
    inside = bool(np.isfinite(observed_delta) and np.isfinite(ci_low) and ci_low <= observed_delta <= ci_high)
    alpha = float(spec["residual_permutation"]["alpha"])
    residual_null = bool(np.isfinite(p_resid) and p_resid > alpha)
    sufficient = bool(inside and residual_null)

    tilt_valid = valid[valid.get("tilt_both_cohorts_available", False) == True] if len(valid) else valid
    summary = {
        "protocol_id": v2["protocol_id"],
        "test": "A_asymmetric_drift",
        "input_star_rows": int(len(raw)),
        "young_old_rows": int(len(d)),
        "v1_supported_voxels": int(len(voxel_ids)),
        "baseline_voxels_with_valid_common_gradient": int(len(valid)),
        "common_radial_gradient_by_z_stratum": {k: (float(v) if np.isfinite(v) else None) for k, v in slopes.items()},
        "V_c_kms": vc,
        "observed_equal_voxel_delta_vphi_old_minus_young_kms": observed_delta if np.isfinite(observed_delta) else None,
        "predicted_equal_voxel_delta_vphi_AD_kms": predicted_delta if np.isfinite(predicted_delta) else None,
        "bootstrap_prediction_interval_95_kms": [float(ci_low) if np.isfinite(ci_low) else None, float(ci_high) if np.isfinite(ci_high) else None],
        "bootstrap_resamples": nboot,
        "bootstrap_seed": boot_seed,
        "observed_inside_AD_prediction_interval": inside,
        "equal_voxel_residual_observed_minus_AD_kms": float(obs_resid) if np.isfinite(obs_resid) else None,
        "residual_permutations": nperm,
        "residual_permutation_seed": perm_seed,
        "residual_permutation_p_two_sided": p_resid,
        "residual_alpha": alpha,
        "residual_not_significant": residual_null,
        "asymmetric_drift_quantitatively_sufficient": sufficient,
        "tilt_sensitivity": {
            "voxels_with_both_cohort_tilt_terms": int(len(tilt_valid)),
            "equal_voxel_delta_vphi_AD_kms": float(tilt_valid["tilt_delta_vphi_AD_pred_kms"].mean()) if len(tilt_valid) else None,
            "equal_voxel_residual_kms": float(tilt_valid["tilt_delta_vphi_residual_kms"].mean()) if len(tilt_valid) else None,
            "selection_rule": "reported sensitivity only; baseline Test-A decision is never replaced post hoc",
        },
        "interpretation": (
            "asymmetric_drift_sufficient_under_frozen_v2" if sufficient else "asymmetric_drift_alone_insufficient_under_frozen_v2"
        ),
        "guardrail": "Failure of Test A is not evidence for persistence; subsequent frozen Tests B-D remain mandatory.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    voxel_table.to_csv(args.output_dir / "test_A_voxel_moments_and_predictions.csv", index=False)
    gradient_bins.to_csv(args.output_dir / "test_A_radial_gradient_bins.csv", index=False)
    pd.DataFrame({"delta_vphi_AD_bootstrap_kms": bootstrap}).to_csv(args.output_dir / "test_A_bootstrap_prediction.csv.gz", index=False, compression="gzip")
    pd.DataFrame({"residual_permuted_kms": perms}).to_csv(args.output_dir / "test_A_residual_permutation.csv.gz", index=False, compression="gzip")
    (args.output_dir / "test_A_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
