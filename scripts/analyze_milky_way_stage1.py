#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold

ROOT = Path("data/persistence_history/milky_way_stage1")
ROOT.mkdir(parents=True, exist_ok=True)
MS_PATH = Path("data/external/sdss/dr20_minesweeper/minesweeper_v1.2.2.parquet")
BOSS_MEM_PATH = Path("data/external/sdss/dr20_boss_occam/BOSS_occam_member-DR20-v1.parquet")
BOSS_CL_PATH = Path("data/external/sdss/dr20_boss_occam/BOSS_occam_cluster-DR20-v1.parquet")

RNG = np.random.default_rng(20260807)


def finite_fractional_error(v, e, max_frac=0.5):
    return np.isfinite(v) & np.isfinite(e) & (v > 0) & (e >= 0) & (e / v <= max_frac)


def clean_minesweeper(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    n0 = len(df)
    d = df.copy()
    required = ["Age", "Age_err", "R_gal", "Z_gal", "Vphi_gal", "Vr_gal", "Vz_gal",
                "FeH", "aFe", "ecc_mw22", "R_apo_mw22", "R_peri_mw22", "z_max_mw22"]
    mask = np.ones(len(d), dtype=bool)
    for c in required:
        mask &= np.isfinite(pd.to_numeric(d[c], errors="coerce"))
    mask &= finite_fractional_error(pd.to_numeric(d["Age"], errors="coerce"),
                                    pd.to_numeric(d["Age_err"], errors="coerce"), 0.5)
    mask &= d["Age"].between(0.05, 14.5)
    mask &= d["R_gal"].between(3.0, 20.0)
    mask &= d["Z_gal"].abs().le(8.0)
    if "snr" in d.columns:
        mask &= pd.to_numeric(d["snr"], errors="coerce").fillna(0).ge(20)
    d = d.loc[mask].copy()
    d["absZ_gal"] = d["Z_gal"].abs()
    d["radial_excursion"] = d["R_apo_mw22"] - d["R_peri_mw22"]
    d["orbit_mid_radius"] = 0.5 * (d["R_apo_mw22"] + d["R_peri_mw22"])
    d["present_minus_orbit_mid"] = d["R_gal"] - d["orbit_mid_radius"]
    d["age_frac_err"] = d["Age_err"] / d["Age"]
    d["R_bin"] = np.floor(d["R_gal"] / 0.5) * 0.5
    d["Z_bin"] = np.floor(d["absZ_gal"] / 0.25) * 0.25
    d["spatial_cell"] = d["R_bin"].round(2).astype(str) + "_" + d["Z_bin"].round(2).astype(str)
    summary = {
        "raw_rows": int(n0),
        "quality_rows": int(len(d)),
        "quality_fraction": float(len(d) / n0 if n0 else np.nan),
        "cuts": {
            "age_range_gyr": [0.05, 14.5],
            "age_fractional_error_max": 0.5,
            "R_gal_kpc": [3.0, 20.0],
            "abs_Z_gal_kpc_max": 8.0,
            "snr_min_if_present": 20,
        },
    }
    return d, summary


def age_orbit_bins(d: pd.DataFrame) -> pd.DataFrame:
    q = pd.qcut(d["Age"], 10, duplicates="drop")
    rows = []
    for label, g in d.groupby(q, observed=True):
        rows.append({
            "age_bin": str(label), "n": len(g),
            "age_median_gyr": g["Age"].median(),
            "R_median_kpc": g["R_gal"].median(),
            "absZ_median_kpc": g["absZ_gal"].median(),
            "FeH_median": g["FeH"].median(), "aFe_median": g["aFe"].median(),
            "Vphi_median_kms": g["Vphi_gal"].median(),
            "Vr_sigma_kms": g["Vr_gal"].std(ddof=1),
            "Vz_sigma_kms": g["Vz_gal"].std(ddof=1),
            "ecc_median": g["ecc_mw22"].median(),
            "zmax_median_kpc": g["z_max_mw22"].median(),
            "radial_excursion_median_kpc": g["radial_excursion"].median(),
            "present_minus_orbit_mid_median_kpc": g["present_minus_orbit_mid"].median(),
        })
    return pd.DataFrame(rows)


def spatial_history_map(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (rb, zb), g in d.groupby(["R_bin", "Z_bin"], observed=True):
        if len(g) < 30:
            continue
        rows.append({
            "R_bin_kpc": rb, "absZ_bin_kpc": zb, "n": len(g),
            "age_median_gyr": g["Age"].median(),
            "age_q25_gyr": g["Age"].quantile(0.25), "age_q75_gyr": g["Age"].quantile(0.75),
            "old_fraction_age_gt_8gyr": (g["Age"] > 8).mean(),
            "FeH_median": g["FeH"].median(), "aFe_median": g["aFe"].median(),
            "Vphi_median_kms": g["Vphi_gal"].median(),
            "Vr_sigma_kms": g["Vr_gal"].std(ddof=1), "Vz_sigma_kms": g["Vz_gal"].std(ddof=1),
            "ecc_median": g["ecc_mw22"].median(), "zmax_median_kpc": g["z_max_mw22"].median(),
            "radial_excursion_median_kpc": g["radial_excursion"].median(),
            "present_minus_orbit_mid_median_kpc": g["present_minus_orbit_mid"].median(),
        })
    return pd.DataFrame(rows).sort_values(["R_bin_kpc", "absZ_bin_kpc"])


def cv_incremental_age(d: pd.DataFrame) -> dict:
    # Strict screen: chemistry is already in the baseline, so Age must add information beyond R, |Z|, [Fe/H], [alpha/Fe].
    base_features = ["R_gal", "absZ_gal", "FeH", "aFe"]
    plus_features = base_features + ["Age"]
    outcomes = ["Vphi_gal", "ecc_mw22", "z_max_mw22", "radial_excursion"]
    dd = d[base_features + ["Age", "spatial_cell"] + outcomes].replace([np.inf, -np.inf], np.nan).dropna().copy()
    # Require enough stars per spatial group to make grouped CV meaningful.
    counts = dd["spatial_cell"].value_counts()
    dd = dd[dd["spatial_cell"].isin(counts[counts >= 20].index)].copy()
    groups = dd["spatial_cell"].to_numpy()
    n_groups = pd.Series(groups).nunique()
    n_splits = min(5, int(n_groups))
    if n_splits < 3:
        return {"error": "Too few populated spatial cells for grouped cross-validation", "rows": int(len(dd)), "groups": int(n_groups)}

    out = {"rows": int(len(dd)), "groups": int(n_groups), "n_splits": n_splits, "outcomes": {}}
    gkf = GroupKFold(n_splits=n_splits)
    for target in outcomes:
        y = dd[target].to_numpy()
        fold_rows = []
        for fold, (tr, te) in enumerate(gkf.split(dd, y, groups), start=1):
            m0 = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, max_leaf_nodes=31,
                                               l2_regularization=1.0, random_state=1000 + fold)
            m1 = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, max_leaf_nodes=31,
                                               l2_regularization=1.0, random_state=2000 + fold)
            X0tr = dd.iloc[tr][base_features]
            X0te = dd.iloc[te][base_features]
            X1tr = dd.iloc[tr][plus_features]
            X1te = dd.iloc[te][plus_features]
            m0.fit(X0tr, y[tr]); m1.fit(X1tr, y[tr])
            p0 = m0.predict(X0te); p1 = m1.predict(X1te)
            fold_rows.append({
                "fold": fold,
                "baseline_mae": float(mean_absolute_error(y[te], p0)),
                "plus_age_mae": float(mean_absolute_error(y[te], p1)),
                "baseline_r2": float(r2_score(y[te], p0)),
                "plus_age_r2": float(r2_score(y[te], p1)),
            })
        fr = pd.DataFrame(fold_rows)
        out["outcomes"][target] = {
            "folds": fold_rows,
            "mean_baseline_mae": float(fr["baseline_mae"].mean()),
            "mean_plus_age_mae": float(fr["plus_age_mae"].mean()),
            "fractional_mae_improvement": float((fr["baseline_mae"].mean() - fr["plus_age_mae"].mean()) / fr["baseline_mae"].mean()),
            "mean_baseline_r2": float(fr["baseline_r2"].mean()),
            "mean_plus_age_r2": float(fr["plus_age_r2"].mean()),
            "delta_r2": float(fr["plus_age_r2"].mean() - fr["baseline_r2"].mean()),
        }
    return out


def within_cell_old_young(d: pd.DataFrame) -> pd.DataFrame:
    # Matched-present-location screen: compare age quartiles only inside the same narrow (R, |Z|) cells.
    rows = []
    for cell, g in d.groupby("spatial_cell", observed=True):
        if len(g) < 80:
            continue
        q1, q3 = g["Age"].quantile([0.25, 0.75])
        young = g[g["Age"] <= q1]
        old = g[g["Age"] >= q3]
        if min(len(young), len(old)) < 15:
            continue
        rb = g["R_bin"].iloc[0]; zb = g["Z_bin"].iloc[0]
        rows.append({
            "spatial_cell": cell, "R_bin_kpc": rb, "absZ_bin_kpc": zb, "n": len(g),
            "young_age_median": young["Age"].median(), "old_age_median": old["Age"].median(),
            "delta_Vphi_old_minus_young_kms": old["Vphi_gal"].median() - young["Vphi_gal"].median(),
            "delta_ecc_old_minus_young": old["ecc_mw22"].median() - young["ecc_mw22"].median(),
            "delta_zmax_old_minus_young_kpc": old["z_max_mw22"].median() - young["z_max_mw22"].median(),
            "delta_radial_excursion_old_minus_young_kpc": old["radial_excursion"].median() - young["radial_excursion"].median(),
            "delta_FeH_old_minus_young": old["FeH"].median() - young["FeH"].median(),
            "delta_aFe_old_minus_young": old["aFe"].median() - young["aFe"].median(),
        })
    return pd.DataFrame(rows)


def boss_occam_links(ms: pd.DataFrame) -> dict:
    report = {}
    if BOSS_MEM_PATH.exists():
        b = pd.read_parquet(BOSS_MEM_PATH)
        a = pd.to_numeric(ms["source_id"], errors="coerce").dropna().astype("int64")
        c = pd.to_numeric(b["GaiaDR3_ID"], errors="coerce").dropna().astype("int64")
        overlap = np.intersect1d(a.unique(), c.unique())
        report["minesweeper_to_boss_occam_gaia_dr3"] = {
            "minesweeper_unique_source_ids": int(a.nunique()),
            "boss_occam_unique_gaia_dr3_ids": int(c.nunique()),
            "overlap_unique_gaia_dr3_ids": int(len(overlap)),
        }
    if BOSS_CL_PATH.exists():
        cl = pd.read_parquet(BOSS_CL_PATH).copy()
        age_col = "Cav_logAge" if "Cav_logAge" in cl.columns else "EH_logAge"
        cl["age_gyr"] = 10 ** pd.to_numeric(cl[age_col], errors="coerce") / 1e9
        cl["delta_R_current_minus_guide_kpc"] = pd.to_numeric(cl["R_GC_Cav"], errors="coerce") - pd.to_numeric(cl["R_Guide"], errors="coerce")
        keep = ["Name", "age_gyr", "R_GC_Cav", "R_Guide", "delta_R_current_minus_guide_kpc", "Z_Height", "Z_Max", "Eccentricity", "Fe_H", "alpha_M", "Num_Full_Members", "OCCAM_Qual"]
        cl[keep].to_csv(ROOT / "boss_occam_cluster_history_screen.csv", index=False)
        report["boss_occam_cluster_screen"] = {
            "rows": int(len(cl)),
            "finite_age_rows": int(np.isfinite(cl["age_gyr"]).sum()),
            "finite_current_minus_guide_rows": int(np.isfinite(cl["delta_R_current_minus_guide_kpc"]).sum()),
            "output": str(ROOT / "boss_occam_cluster_history_screen.csv"),
        }
    return report


def main():
    ms_raw = pd.read_parquet(MS_PATH)
    d, quality = clean_minesweeper(ms_raw)

    age_bins = age_orbit_bins(d)
    age_bins.to_csv(ROOT / "age_orbit_deciles.csv", index=False)

    spatial = spatial_history_map(d)
    spatial.to_csv(ROOT / "spatial_history_cells.csv", index=False)

    matched = within_cell_old_young(d)
    matched.to_csv(ROOT / "within_cell_old_young.csv", index=False)

    metrics = cv_incremental_age(d)
    boss = boss_occam_links(ms_raw)

    summary = {
        "analysis_name": "Milky Way persistence framework Stage 1 history-signal screen",
        "interpretation_guardrail": (
            "This stage tests whether age/history proxies add reproducible dynamical information after narrow present-location and chemistry controls. "
            "It is not by itself evidence for gravitational persistence: standard disk heating, formation history, selection effects, and non-equilibrium dynamics can produce age-orbit correlations. "
            "A persistence test requires a present-baryonic force model and a gravitational/Jeans residual that can be tested against reconstructed source history."
        ),
        "quality": quality,
        "age_orbit_deciles_rows": int(len(age_bins)),
        "spatial_history_cells_rows": int(len(spatial)),
        "within_cell_old_young_rows": int(len(matched)),
        "incremental_age_cv": metrics,
        "boss_occam_crosswalk": boss,
    }
    (ROOT / "stage1_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
