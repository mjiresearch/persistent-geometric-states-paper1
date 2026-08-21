#!/usr/bin/env python3
"""Run Test B of the frozen DR20-v2 conventional-dynamics challenge.

This script is additive and uses the immutable v1 star sample. It may query Gaia DR3
for phot_g_mean_mag and bp_rp by the already-fixed source_id values only; this is a
covariate augmentation and does not alter sample membership. Chemistry is optional
and must be supplied as a source_id keyed table with finite recommended-quality
[Fe/H] and [alpha/M] values. Missing chemistry is reported as unavailable rather than
imputed.
"""
from __future__ import annotations

import argparse
import json
import time
from io import StringIO
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
GAIA_TAP_SYNC = "https://gea.esac.esa.int/tap-server/tap/sync"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def source_text(s: pd.Series) -> pd.Series:
    return s.astype("string").str.replace(r"\.0$", "", regex=True).str.strip()


def fetch_gaia_photometry(ids: list[str], batch_size: int = 400) -> pd.DataFrame:
    import requests
    rows = []
    for start in range(0, len(ids), batch_size):
        batch = ids[start:start + batch_size]
        q = (
            "SELECT source_id,phot_g_mean_mag,bp_rp FROM gaiadr3.gaia_source "
            "WHERE source_id IN (" + ",".join(batch) + ")"
        )
        payload = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q}
        last = None
        for attempt in range(4):
            try:
                r = requests.post(GAIA_TAP_SYNC, data=payload, timeout=180)
                r.raise_for_status()
                rows.append(pd.read_csv(StringIO(r.text), dtype={"source_id": "string"}))
                last = None
                break
            except Exception as e:
                last = e
                time.sleep(2 ** attempt)
        if last is not None:
            raise RuntimeError(f"Gaia photometry batch failed: {last}")
    if not rows:
        return pd.DataFrame(columns=["source_id", "phot_g_mean_mag", "bp_rp"])
    out = pd.concat(rows, ignore_index=True)
    out["source_id"] = source_text(out["source_id"])
    return out.drop_duplicates("source_id")


def get_photometry(d: pd.DataFrame, cache: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    if {"phot_g_mean_mag", "bp_rp"}.issubset(d.columns):
        return d, {"source": "already_in_star_sample", "rows": int(len(d))}
    if cache.exists():
        p = pd.read_csv(cache, dtype={"source_id": "string"})
        source = "local_cache"
    else:
        ids = source_text(d["source_id"]).dropna().drop_duplicates().tolist()
        p = fetch_gaia_photometry(ids)
        cache.parent.mkdir(parents=True, exist_ok=True)
        p.to_csv(cache, index=False)
        source = "Gaia_DR3_TAP_exact_source_id_covariate_augmentation"
    out = d.copy()
    out["source_id"] = source_text(out["source_id"])
    out = out.merge(p, on="source_id", how="left", validate="many_to_one")
    return out, {"source": source, "rows_returned": int(len(p))}


def moments(g: pd.DataFrame) -> dict[str, float]:
    return {
        "delta_R_kms": float(g[g.cohort == "old"].v_R_kms.mean() - g[g.cohort == "young"].v_R_kms.mean()),
        "delta_phi_kms": float(g[g.cohort == "old"].v_phi_kms.mean() - g[g.cohort == "young"].v_phi_kms.mean()),
        "delta_z_kms": float(g[g.cohort == "old"].v_z_kms.mean() - g[g.cohort == "young"].v_z_kms.mean()),
    }


def ad_delta(g: pd.DataFrame, gradient: float, vc: float) -> float:
    pred = {}
    for cohort in ("young", "old"):
        s = g[g.cohort == cohort]
        sr = float(np.std(s.v_R_kms.to_numpy(float), ddof=1))
        sp = float(np.std(s.v_phi_kms.to_numpy(float), ddof=1))
        pred[cohort] = predict_vphi(sr, sp, gradient, vc)
    return float(pred["old"] - pred["young"])


def summarize_units(units: list[pd.DataFrame], gradients: list[float], vc: float) -> dict[str, Any]:
    if not units:
        return {"units": 0}
    rows = []
    for g, grad in zip(units, gradients, strict=True):
        m = moments(g)
        ad = ad_delta(g, grad, vc)
        m["delta_phi_AD_kms"] = ad
        m["delta_phi_residual_kms"] = m["delta_phi_kms"] - ad
        rows.append(m)
    return {
        "units": int(len(rows)),
        "delta_R_equal_unit_kms": float(np.mean([r["delta_R_kms"] for r in rows])),
        "delta_phi_equal_unit_kms": float(np.mean([r["delta_phi_kms"] for r in rows])),
        "delta_z_equal_unit_kms": float(np.mean([r["delta_z_kms"] for r in rows])),
        "delta_phi_AD_equal_unit_kms": float(np.mean([r["delta_phi_AD_kms"] for r in rows])),
        "delta_phi_residual_equal_unit_kms": float(np.mean([r["delta_phi_residual_kms"] for r in rows])),
    }


def gradient_for_group(g: pd.DataFrame, slopes: dict[str, float]) -> float:
    label = z_stratum(float(g.z_kpc.abs().mean()))
    return float(slopes.get(label, np.nan)) if label else float("nan")


def vertical_tests(d: pd.DataFrame, v1: dict[str, Any], slopes: dict[str, float], vc: float) -> dict[str, Any]:
    results = {}
    for name, lo, hi in (("absz_0_020", 0.0, 0.20), ("absz_020_050", 0.20, 0.50)):
        s = d[(d.z_kpc.abs() >= lo) & (d.z_kpc.abs() < hi)].copy()
        s, keep = supported_sample(s, v1)
        units, grads = [], []
        for vid, g in s.groupby("voxel_id", sort=True):
            grad = gradient_for_group(g, slopes)
            if np.isfinite(grad):
                units.append(g.copy()); grads.append(grad)
        summary = summarize_units(units, grads, vc)
        summary["minimum_units"] = 8
        summary["powered"] = bool(summary.get("units", 0) >= 8)
        results[name] = summary
    return results


def add_bins(d: pd.DataFrame, widths: dict[str, float], origins: dict[str, float]) -> pd.DataFrame:
    out = d.copy()
    for col, width in widths.items():
        origin = origins.get(col, 0.0)
        out[f"bin_{col}"] = np.floor((pd.to_numeric(out[col], errors="coerce") - origin) / width).astype("Int64")
    return out


def matched_cells(d: pd.DataFrame, variables: list[str], widths: dict[str, float], origins: dict[str, float], min_each: int) -> list[pd.DataFrame]:
    needed = ["voxel_id", "cohort", *variables]
    s = d.dropna(subset=needed).copy()
    s = add_bins(s, widths, origins)
    keys = ["voxel_id"] + [f"bin_{v}" for v in variables]
    units = []
    for _, g in s.groupby(keys, sort=True, dropna=True):
        counts = g.cohort.value_counts()
        if int(counts.get("young", 0)) >= min_each and int(counts.get("old", 0)) >= min_each:
            units.append(g.copy())
    return units


def selection_test(d: pd.DataFrame, slopes: dict[str, float], vc: float) -> dict[str, Any]:
    work = d.copy()
    work["abs_z"] = work.z_kpc.abs()
    work["parallax_over_error"] = pd.to_numeric(work.parallax, errors="coerce") / pd.to_numeric(work.parallax_error, errors="coerce")
    variables = ["abs_z", "phot_g_mean_mag", "bp_rp", "parallax_over_error", "ruwe"]
    widths = {"abs_z": 0.05, "phot_g_mean_mag": 0.50, "bp_rp": 0.20, "parallax_over_error": 10.0, "ruwe": 0.10}
    units = matched_cells(work, variables, widths, {}, 5)
    valid, grads = [], []
    for g in units:
        grad = gradient_for_group(g, slopes)
        if np.isfinite(grad): valid.append(g); grads.append(grad)
    out = summarize_units(valid, grads, vc)
    out["minimum_cells"] = 8
    out["powered"] = bool(out.get("units", 0) >= 8)
    out["variables"] = variables
    return out


def load_chemistry(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".fits", ".fit", ".fz"}:
        from astropy.table import Table
        c = Table.read(path).to_pandas()
    else:
        c = pd.read_csv(path, low_memory=False)
    lower = {str(x).lower(): str(x) for x in c.columns}
    aliases = {
        "source_id": ["source_id", "gaia_dr3_source_id", "gaiadr3_source_id"],
        "feh": ["fe_h", "feh", "[fe/h]"],
        "alpha_m": ["alpha_m", "alpha_fe", "[alpha/m]", "[alpha/fe]"],
    }
    rename = {}
    for target, names in aliases.items():
        found = next((lower[n.lower()] for n in names if n.lower() in lower), None)
        if found is None: raise ValueError(f"Chemistry table missing {target}; columns={list(c.columns)}")
        rename[found] = target
    c = c.rename(columns=rename)
    c["source_id"] = source_text(c["source_id"])
    c["feh"] = pd.to_numeric(c["feh"], errors="coerce")
    c["alpha_m"] = pd.to_numeric(c["alpha_m"], errors="coerce")
    return c.dropna(subset=["source_id", "feh", "alpha_m"]).drop_duplicates("source_id")


def chemistry_test(d: pd.DataFrame, chemistry: pd.DataFrame, slopes: dict[str, float], vc: float) -> dict[str, Any]:
    work = d.merge(chemistry, on="source_id", how="inner", validate="many_to_one")
    work["abs_z"] = work.z_kpc.abs()
    variables = ["feh", "alpha_m", "abs_z", "phot_g_mean_mag", "bp_rp"]
    widths = {"feh": 0.10, "alpha_m": 0.05, "abs_z": 0.05, "phot_g_mean_mag": 0.50, "bp_rp": 0.20}
    origins = {"feh": -3.0}
    units = matched_cells(work, variables, widths, origins, 5)
    valid, grads = [], []
    for g in units:
        grad = gradient_for_group(g, slopes)
        if np.isfinite(grad): valid.append(g); grads.append(grad)
    out = summarize_units(valid, grads, vc)
    out["chemistry_complete_rows"] = int(len(work))
    out["minimum_cells"] = 8
    out["powered"] = bool(out.get("units", 0) >= 8)
    out["variables"] = variables
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--star-sample", type=Path, default=Path("data/persistence_history/dr20_independent/field_v1/field_star_sample.csv.gz"))
    p.add_argument("--v1-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json"))
    p.add_argument("--v2-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v2_conventional_challenge.json"))
    p.add_argument("--chemistry", type=Path)
    p.add_argument("--output-dir", type=Path, default=Path("data/persistence_history/dr20_independent/conventional_challenge_v2/test_B_population_selection"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    v1, v2 = load_json(args.v1_protocol), load_json(args.v2_protocol)
    if v2.get("status") != "frozen_pre_v2_outcome": raise RuntimeError("v2 protocol is not frozen")
    vc = float(v2["test_A_asymmetric_drift"]["V_c_kms"])
    raw = pd.read_csv(args.star_sample, low_memory=False, dtype={"source_id": "string"})
    d = assign_voxels(select_cohorts(raw), v1)
    # Common gradient population must match Test A: full young+old cohort before supported-voxel reduction.
    slopes, _ = fit_common_radial_gradients(d, v2["test_A_asymmetric_drift"])
    cache = args.output_dir / "gaia_photometry_covariates.csv"
    d, photo_report = get_photometry(d, cache)

    selection = selection_test(d, slopes, vc)
    vertical = vertical_tests(d, v1, slopes, vc)
    if args.chemistry is not None and args.chemistry.exists():
        chemistry = chemistry_test(d, load_chemistry(args.chemistry), slopes, vc)
        chemistry["status"] = "evaluated"
    else:
        chemistry = {
            "status": "unavailable_not_imputed",
            "powered": False,
            "reason": "No source_id-keyed recommended-quality BOSS-CLAM chemistry table supplied; frozen protocol forbids imputation.",
        }

    summary = {
        "protocol_id": v2["protocol_id"],
        "test": "B_population_vertical_selection",
        "young_old_rows": int(len(d)),
        "common_radial_gradient_by_z_stratum": {k: (float(v) if np.isfinite(v) else None) for k, v in slopes.items()},
        "gaia_photometry": photo_report,
        "chemistry_complete_matching": chemistry,
        "vertical_height_stress": vertical,
        "selection_only_matching": selection,
        "interpretation_guardrail": "Test B is a robustness/completeness check. Underpowered or unavailable chemistry cannot be treated as passing, and no Test B result can restore a drift-corrected signal that Test C already found non-significant.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "test_B_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
