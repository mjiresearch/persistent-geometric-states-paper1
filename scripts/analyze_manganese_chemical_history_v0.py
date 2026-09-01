#!/usr/bin/env python3
"""Execute the frozen GALAH DR4 manganese chemical-history v0.2 protocol."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

VOX = (0.25, 0.25, 0.10)
MIN_PER_VOX = 20
MIN_VOX = 12
N_PERM = 5000
SEED = 20260901
ALPHA = 0.01
VELS = ["vR_Rzphi", "vT_Rzphi", "vz_Rzphi"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_protocol(path: Path) -> dict:
    p = json.loads(path.read_text())
    if p.get("protocol_id") != "manganese-chemical-history-v0.2":
        raise RuntimeError("Refusing to run: wrong manganese protocol")
    if p.get("status") != "frozen_pre_outcome":
        raise RuntimeError("Refusing to run: v0.2 is not frozen_pre_outcome")
    if p.get("outcome_status_at_freeze") != "no_manganese_dynamical_outcome_calculated_or_inspected":
        raise RuntimeError("Refusing to run: v0.2 pre-outcome guard is not intact")
    return p


def read_cols(path: Path, columns: list[str]) -> pd.DataFrame:
    with fits.open(path, memmap=True) as hdul:
        data = hdul[1].data
        names = set(data.names)
        missing = [c for c in columns if c not in names]
        if missing:
            raise RuntimeError(f"{path.name}: missing required columns: {missing}")
        return pd.DataFrame({c: np.asarray(data[c]) for c in columns})


def standardize(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, float)
    sd = np.nanstd(a)
    if not np.isfinite(sd) or sd <= 0:
        raise RuntimeError("zero/nonfinite nuisance standard deviation")
    return (a - np.nanmean(a)) / sd


def within_demean(arr: np.ndarray, groups: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, float)
    g = np.asarray(groups, np.int64)
    ngrp = int(g.max()) + 1
    cnt = np.bincount(g, minlength=ngrp)
    if arr.ndim == 1:
        sums = np.bincount(g, weights=arr, minlength=ngrp)
        return arr - sums[g] / cnt[g]
    out = np.empty_like(arr, dtype=float)
    for j in range(arr.shape[1]):
        sums = np.bincount(g, weights=arr[:, j], minlength=ngrp)
        out[:, j] = arr[:, j] - sums[g] / cnt[g]
    return out


def residualize(y: np.ndarray, X: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    yw = within_demean(y, groups)
    Xw = within_demean(X, groups)
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    return yw - Xw @ beta, beta


def slope_hc1(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(x)), x])
    xtx_inv = np.linalg.inv(X.T @ X)
    b = xtx_inv @ (X.T @ y)
    e = y - X @ b
    meat = (X * e[:, None]).T @ (X * e[:, None])
    n, k = X.shape
    cov = (n / (n - k)) * xtx_inv @ meat @ xtx_inv
    se = float(np.sqrt(max(cov[1, 1], 0.0)))
    beta = float(b[1])
    return beta, se, beta / se if se > 0 else math.nan


def codes(keys: pd.DataFrame) -> np.ndarray:
    c, _ = pd.factorize(pd.MultiIndex.from_frame(keys), sort=True)
    return c.astype(np.int64)


def add_voxels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    R = out["R_Rzphi"].to_numpy(float)
    phi = out["phi_Rzphi"].to_numpy(float)
    x = R * np.cos(phi)
    y = R * np.sin(phi)
    z = out["z_Rzphi"].to_numpy(float)
    out["vxbin"] = np.floor(x / VOX[0]).astype(np.int32)
    out["vybin"] = np.floor(y / VOX[1]).astype(np.int32)
    out["vzbin"] = np.floor(z / VOX[2]).astype(np.int32)
    return out


def support_filter(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = df.groupby(["vxbin", "vybin", "vzbin"], sort=True).size().rename("n").reset_index()
    keep = c[c["n"] >= MIN_PER_VOX].copy()
    if keep.empty:
        return df.iloc[0:0].copy(), keep
    return df.merge(keep[["vxbin", "vybin", "vzbin"]], on=["vxbin", "vybin", "vzbin"], how="inner"), keep


def design(df: pd.DataFrame, age_col: str) -> tuple[np.ndarray, list[str]]:
    cols = ["fe_h", "mg_fe", age_col, "teff", "logg", "phot_g_mean_mag", "bp_rp", "ruwe"]
    z = {c: standardize(df[c].to_numpy(float)) for c in cols}
    names = cols + ["fe_h_z2", f"{age_col}_z2"]
    return np.column_stack([z[c] for c in cols] + [z["fe_h"] ** 2, z[age_col] ** 2]), names


def permutation_packs(df: pd.DataFrame, voxel: np.ndarray, age_col: str) -> tuple[dict[int, np.ndarray], dict]:
    s = pd.DataFrame({
        "voxel": voxel,
        "age": np.floor(df[age_col].to_numpy(float) / 1.0).astype(np.int32),
        "feh": np.floor(df["fe_h"].to_numpy(float) / 0.20).astype(np.int32),
        "mg": np.floor(df["mg_fe"].to_numpy(float) / 0.10).astype(np.int32),
    })
    sc = codes(s)
    order = np.argsort(sc, kind="stable")
    ss = sc[order]
    br = np.flatnonzero(np.r_[True, ss[1:] != ss[:-1], True])
    groups = [order[br[i]:br[i + 1]] for i in range(len(br) - 1) if br[i + 1] - br[i] > 1]
    sizes = np.asarray([len(g) for g in groups], int)
    packs: dict[int, np.ndarray] = {}
    for size in np.unique(sizes):
        packs[int(size)] = np.stack([g for g in groups if len(g) == size])
    info = {
        "population_strata_total": int(sc.max() + 1 if len(sc) else 0),
        "permutable_strata": int(len(groups)),
        "stars_in_permutable_strata": int(sizes.sum()) if len(sizes) else 0,
        "median_permutable_stratum_size": float(np.median(sizes)) if len(sizes) else 0.0,
        "max_permutable_stratum_size": int(sizes.max()) if len(sizes) else 0,
        "group_size_classes": {str(k): int(v.shape[0]) for k, v in packs.items()},
    }
    return packs, info


def analyze(df: pd.DataFrame, age_col: str, n_perm: int, seed: int) -> dict:
    d = df[np.isfinite(df[age_col].to_numpy(float))].copy()
    d, vc = support_filter(d)
    out = {
        "age_column": age_col,
        "rows_after_age_and_support": int(len(d)),
        "supported_voxels": int(len(vc)),
        "minimum_stars_per_voxel": MIN_PER_VOX,
        "minimum_supported_voxels": MIN_VOX,
        "power_gate_pass": bool(len(vc) >= MIN_VOX),
    }
    if len(vc) < MIN_VOX:
        out["classification"] = "underpowered_frozen_v0.2"
        return out

    vg = codes(d[["vxbin", "vybin", "vzbin"]])
    X, names = design(d, age_col)
    mh, mb = residualize(d["mn_fe"].to_numpy(float), X, vg)
    vres: dict[str, np.ndarray] = {}
    comp: dict[str, dict[str, float]] = {}
    for v in VELS:
        r, _ = residualize(d[v].to_numpy(float), X, vg)
        vres[v] = r
        b, se, t = slope_hc1(mh, r)
        comp[v] = {"beta_kms_per_dex": b, "hc1_se": se, "t": t}
    T = float(sum(x["t"] ** 2 for x in comp.values()))

    packs, pinfo = permutation_packs(d, vg, age_col)
    rng = np.random.default_rng(seed)
    base = mh.copy()
    work = mh.copy()
    null = np.empty(n_perm, float)
    for p in range(n_perm):
        work[:] = base
        for idx in packs.values():
            ranks = np.argsort(rng.random(idx.shape), axis=1)
            src = np.take_along_axis(idx, ranks, axis=1)
            work[idx] = base[src]
        tt = 0.0
        for v in VELS:
            _, _, t = slope_hc1(work, vres[v])
            tt += t * t
        null[p] = tt
    pp = float((1 + np.count_nonzero(null >= T)) / (n_perm + 1))
    out.update({
        "nuisance_columns": names,
        "mn_nuisance_coefficients_within_voxel": {k: float(v) for k, v in zip(names, mb)},
        "mn_history_sd_dex": float(np.std(mh, ddof=1)),
        "components": comp,
        "T_Mn_3D": T,
        "permutations": int(n_perm),
        "permutation_seed": int(seed),
        "permutation_p": pp,
        "alpha": ALPHA,
        "null_T_quantiles": {q: float(np.quantile(null, f)) for q, f in [("q50", .5), ("q90", .9), ("q95", .95), ("q99", .99)]},
        "permutation_grouping": pinfo,
        "classification": "manganese_history_sensitive" if pp <= ALPHA else "null_primary_v0.2",
    })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True, type=Path)
    ap.add_argument("--allstar", required=True, type=Path)
    ap.add_argument("--dynamics", required=True, type=Path)
    ap.add_argument("--ages", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--permutations", type=int, default=N_PERM)
    a = ap.parse_args()
    protocol = load_protocol(a.protocol)
    a.out.mkdir(parents=True, exist_ok=True)

    ac = ["sobject_id", "flag_sp", "snr_px_ccd3", "teff", "logg", "fe_h", "mg_fe", "mn_fe", "e_mn_fe", "flag_mn_fe", "phot_g_mean_mag", "bp_rp", "ruwe", "age"]
    dc = ["sobject_id", "R_Rzphi", "z_Rzphi", "phi_Rzphi", "vR_Rzphi", "vT_Rzphi", "vz_Rzphi"]
    gc = ["sobject_id", "age_bstep", "e_age_bstep"]
    aa, dd, gg = read_cols(a.allstar, ac), read_cols(a.dynamics, dc), read_cols(a.ages, gc)
    raw_counts = {"allstar": len(aa), "dynamics": len(dd), "ages": len(gg)}
    m = aa.merge(dd, on="sobject_id", how="inner", validate="one_to_one").merge(gg, on="sobject_id", how="inner", validate="one_to_one")
    finite = ["teff", "logg", "fe_h", "mg_fe", "mn_fe", "e_mn_fe", "age_bstep", "e_age_bstep", "R_Rzphi", "z_Rzphi", "phi_Rzphi", "vR_Rzphi", "vT_Rzphi", "vz_Rzphi", "phot_g_mean_mag", "bp_rp", "ruwe"]
    mask = (m["flag_sp"].to_numpy() == 0) & (m["flag_mn_fe"].to_numpy() == 0) & (m["snr_px_ccd3"].to_numpy(float) > 30)
    for c in finite:
        mask &= np.isfinite(m[c].to_numpy(float))
    q = add_voxels(m.loc[mask].copy())

    result = {
        "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["version"],
        "input_files": {
            "allstar": {"name": a.allstar.name, "sha256": sha256(a.allstar), "bytes": a.allstar.stat().st_size},
            "dynamics": {"name": a.dynamics.name, "sha256": sha256(a.dynamics), "bytes": a.dynamics.stat().st_size},
            "ages": {"name": a.ages.name, "sha256": sha256(a.ages), "bytes": a.ages.stat().st_size},
        },
        "raw_row_counts": raw_counts,
        "joined_rows": int(len(m)),
        "quality_rows_before_voxel_support": int(len(q)),
        "voxel_kpc": list(VOX),
        "primary": analyze(q, "age_bstep", a.permutations, SEED),
        "main_age_sensitivity": analyze(q, "age", a.permutations, SEED + 1),
        "guardrails": {
            "direct_gravity_test": False,
            "persistence_detection_claim_allowed": False,
            "positive_primary_requires_conventional_challenge": True,
            "vT_only_signal_not_persistence_evidence": True
        },
    }
    (a.out / "galah_manganese_v0_2_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    q.groupby(["vxbin", "vybin", "vzbin"], sort=True).size().rename("n_quality").reset_index().to_csv(a.out / "galah_manganese_v0_2_voxel_counts.csv", index=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
