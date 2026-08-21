#!/usr/bin/env python3
"""Run Test C of the frozen DR20-v2 conventional-dynamics challenge.

Reports raw component decomposition and the mandatory asymmetric-drift-corrected
repeat. Reads the immutable v1 star sample and frozen v1/v2 protocol authorities.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analyze_dr20_asymmetric_drift_v2 import (
    assign_voxels,
    fit_common_radial_gradients,
    predict_vphi,
    select_cohorts,
    supported_sample,
    z_stratum,
)

VEL = ("v_R_kms", "v_phi_kms", "v_z_kms")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def mean_cov(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values, float)
    return values.mean(axis=0), np.asarray(np.cov(values, rowvar=False, ddof=1) / len(values), float)


def ridge_cov(cov: np.ndarray, frac: float) -> np.ndarray:
    dim = cov.shape[0]
    scale = max(float(np.trace(cov) / dim), 1.0)
    return cov + np.eye(dim) * frac * scale


def predicted_delta_phi(g: pd.DataFrame, gradient: float, vc: float) -> float:
    pred = {}
    for cohort in ("young", "old"):
        s = g[g["cohort"] == cohort]
        sr = float(np.std(s["v_R_kms"].to_numpy(float), ddof=1))
        sp = float(np.std(s["v_phi_kms"].to_numpy(float), ddof=1))
        pred[cohort] = predict_vphi(sr, sp, gradient, vc)
    return float(pred["old"] - pred["young"])


def voxel_stats(g: pd.DataFrame, ridge: float, gradient: float | None = None, vc: float | None = None) -> dict[str, float]:
    young = g[g["cohort"] == "young"]
    old = g[g["cohort"] == "old"]
    y = young.loc[:, VEL].to_numpy(float)
    o = old.loc[:, VEL].to_numpy(float)
    ym, yc = mean_cov(y)
    om, oc = mean_cov(o)
    delta = om - ym
    cov3 = yc + oc

    q = []
    for k in range(3):
        var = float(cov3[k, k])
        denom = var + ridge * max(var, 1.0)
        q.append(float(delta[k] ** 2 / denom))

    cov3r = ridge_cov(cov3, ridge)
    t3 = float(delta @ np.linalg.pinv(cov3r, hermitian=True) @ delta)
    idx = [0, 2]
    covrz = cov3[np.ix_(idx, idx)]
    covrzr = ridge_cov(covrz, ridge)
    drz = delta[idx]
    trz = float(drz @ np.linalg.pinv(covrzr, hermitian=True) @ drz)

    out = {
        "Q_R": q[0], "Q_phi": q[1], "Q_z": q[2],
        "T_3D": t3, "T_Rz": trz,
        "delta_R": float(delta[0]), "delta_phi": float(delta[1]), "delta_z": float(delta[2]),
    }

    if gradient is not None and vc is not None and np.isfinite(gradient):
        ad = predicted_delta_phi(g, gradient, vc)
        dc = delta.copy()
        dc[1] = dc[1] - ad
        qcorr = q.copy()
        varphi = float(cov3[1, 1])
        qcorr[1] = float(dc[1] ** 2 / (varphi + ridge * max(varphi, 1.0)))
        t3c = float(dc @ np.linalg.pinv(cov3r, hermitian=True) @ dc)
        out.update({
            "AD_delta_phi": ad,
            "delta_phi_residual": float(dc[1]),
            "Q_phi_corrected": qcorr[1],
            "T_3D_corrected": t3c,
        })
    return out


def aggregate(rows: list[dict[str, float]], corrected: bool = False) -> dict[str, float]:
    if not rows:
        return {}
    key_phi = "Q_phi_corrected" if corrected else "Q_phi"
    key_t3 = "T_3D_corrected" if corrected else "T_3D"
    qr = np.asarray([r["Q_R"] for r in rows], float)
    qp = np.asarray([r[key_phi] for r in rows], float)
    qz = np.asarray([r["Q_z"] for r in rows], float)
    total = float(np.sum(qr + qp + qz))
    return {
        "T_3D": float(np.mean([r[key_t3] for r in rows])),
        "T_R": float(np.mean(qr)),
        "T_phi": float(np.mean(qp)),
        "T_z": float(np.mean(qz)),
        "T_Rz": float(np.mean([r["T_Rz"] for r in rows])),
        "T_minus_phi": float(np.mean([r["T_Rz"] for r in rows])),
        "f_phi": float(np.sum(qp) / total) if total > 0 else float("nan"),
        "delta_R_equal_voxel_kms": float(np.mean([r["delta_R"] for r in rows])),
        "delta_phi_equal_voxel_kms": float(np.mean([r["delta_phi_residual" if corrected else "delta_phi"] for r in rows])),
        "delta_z_equal_voxel_kms": float(np.mean([r["delta_z"] for r in rows])),
    }


def pvalues(observed: dict[str, float], perm: dict[str, np.ndarray], nperm: int) -> dict[str, float]:
    out = {}
    for key in ("T_3D", "T_R", "T_phi", "T_z", "T_Rz", "T_minus_phi"):
        vals = perm[key]
        out[key] = float((1 + np.sum(vals >= observed[key])) / (nperm + 1))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--star-sample", type=Path, default=Path("data/persistence_history/dr20_independent/field_v1/field_star_sample.csv.gz"))
    p.add_argument("--v1-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json"))
    p.add_argument("--v2-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v2_conventional_challenge.json"))
    p.add_argument("--output-dir", type=Path, default=Path("data/persistence_history/dr20_independent/conventional_challenge_v2/test_C_component_decomposition"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    v1 = load_json(args.v1_protocol)
    v2 = load_json(args.v2_protocol)
    if v2.get("status") != "frozen_pre_v2_outcome":
        raise RuntimeError("Refusing to run: v2 protocol is not frozen")
    spec = v2["test_C_component_decomposition"]
    drift_spec = v2["test_A_asymmetric_drift"]
    ridge = float(v1["field_test"]["primary_statistic"]["covariance_ridge_fraction"])
    vc = float(drift_spec["V_c_kms"])
    nperm = int(spec["permutation"]["permutations"])
    seed = int(spec["permutation"]["seed"])
    alpha = float(spec["permutation"]["alpha"])

    raw = pd.read_csv(args.star_sample, low_memory=False)
    d_all = assign_voxels(select_cohorts(raw), v1)
    supported, keep = supported_sample(d_all, v1)
    # Match Test A exactly: fit the common radial gradient on the full young+old
    # cohort population, not only the supported 13 outcome voxels.
    slopes, gradient_audit = fit_common_radial_gradients(d_all, drift_spec)

    groups: list[pd.DataFrame] = []
    gradients: list[float] = []
    voxel_ids: list[str] = []
    for voxel_id in keep:
        g = supported[supported["voxel_id"] == voxel_id].copy()
        zs = z_stratum(abs(float(g["z_kpc"].mean())))
        grad = slopes.get(zs, float("nan")) if zs else float("nan")
        if not np.isfinite(grad):
            continue
        groups.append(g)
        gradients.append(float(grad))
        voxel_ids.append(str(voxel_id))
    if not groups:
        raise RuntimeError("Test C has zero valid supported voxels after applying the frozen Test-A gradient strata")

    raw_rows = [voxel_stats(g, ridge) for g in groups]
    corr_rows = [voxel_stats(g, ridge, grad, vc) for g, grad in zip(groups, gradients, strict=True)]
    raw_obs = aggregate(raw_rows, corrected=False)
    corr_obs = aggregate(corr_rows, corrected=True)

    rng = np.random.default_rng(seed)
    keys = ("T_3D", "T_R", "T_phi", "T_z", "T_Rz", "T_minus_phi")
    raw_perm = {k: np.full(nperm, np.nan) for k in keys}
    corr_perm = {k: np.full(nperm, np.nan) for k in keys}
    for i in range(nperm):
        prow = []
        pcorr = []
        for g, grad in zip(groups, gradients, strict=True):
            gp = g.copy()
            gp["cohort"] = rng.permutation(gp["cohort"].to_numpy())
            prow.append(voxel_stats(gp, ridge))
            pcorr.append(voxel_stats(gp, ridge, grad, vc))
        a = aggregate(prow, corrected=False)
        b = aggregate(pcorr, corrected=True)
        for k in keys:
            raw_perm[k][i] = a[k]
            corr_perm[k][i] = b[k]

    raw_p = pvalues(raw_obs, raw_perm, nperm)
    corr_p = pvalues(corr_obs, corr_perm, nperm)
    vphi_dominated = bool(raw_obs["f_phi"] >= 0.80 and raw_p["T_Rz"] > alpha)

    summary = {
        "protocol_id": v2["protocol_id"],
        "test": "C_component_decomposition",
        "supported_voxels": len(groups),
        "permutations": nperm,
        "seed": seed,
        "alpha": alpha,
        "raw": {**raw_obs, "p_values": raw_p},
        "drift_corrected": {**corr_obs, "p_values": corr_p},
        "vphi_dominated_rule": {"f_phi_min": 0.80, "p_T_Rz_gt": alpha},
        "vphi_dominated": vphi_dominated,
        "interpretation": (
            "v1_omnibus_is_vphi_dominated_and_not_independent_persistence_support"
            if vphi_dominated else
            "v1_omnibus_not_classified_vphi_dominated_under_frozen_rule"
        ),
        "guardrail": "Test C describes signal geometry. A surviving component is not by itself evidence for persistence.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "test_C_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    audit = pd.DataFrame([
        {"voxel_id": vid, **r, **{f"corrected_{k}": v for k, v in cr.items() if k not in r}}
        for vid, r, cr in zip(voxel_ids, raw_rows, corr_rows, strict=True)
    ])
    audit.to_csv(args.output_dir / "test_C_voxel_audit.csv", index=False)
    gradient_audit.to_csv(args.output_dir / "test_C_gradient_audit.csv", index=False)
    pd.DataFrame({f"raw_{k}": raw_perm[k] for k in keys} | {f"corrected_{k}": corr_perm[k] for k in keys}).to_csv(
        args.output_dir / "test_C_permutations.csv.gz", index=False, compression="gzip"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
