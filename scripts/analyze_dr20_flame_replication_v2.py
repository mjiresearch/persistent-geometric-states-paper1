#!/usr/bin/env python3
"""Run Test D of the frozen DR20-v2 conventional-dynamics challenge.

Independent replication with Gaia DR3 FLAME ages. Every Gaia source_id present anywhere
in the original SDSS DR20 gyrochronology VAC is excluded before FLAME cohort assignment.
The script then applies the frozen v1 6-D quality/frame/grid rules, reruns the asymmetric-
drift correction, and evaluates the raw and drift-corrected 3-D permutation statistics.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from analyze_dr20_asymmetric_drift_v2 import (
    assign_voxels,
    fit_common_radial_gradients,
    supported_sample,
    z_stratum,
)
from analyze_dr20_component_decomposition_v2 import voxel_stats, aggregate

GAIA_TAP_SYNC = "https://gea.esac.esa.int/tap-server/tap/sync"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def download_gyro(url: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    return path


def gyro_ids(path: Path) -> set[str]:
    from astropy.table import Table
    t = Table.read(path)
    lower = {str(c).lower(): str(c) for c in t.colnames}
    candidates = ["gaia_dr3_source_id", "gaiadr3_source_id", "gaia_source_id", "source_id", "gaiadr3_id"]
    col = next((lower[c] for c in candidates if c in lower), None)
    if col is None:
        raise ValueError(f"No Gaia source_id column in gyro VAC: {t.colnames}")
    s = pd.Series(t[col]).astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    return set(s[s.str.fullmatch(r"[0-9]+", na=False)].tolist())


def query_flame() -> pd.DataFrame:
    # Quality and age cuts are pushed into TAP only to reduce transport. The full frozen
    # rules are rechecked locally after download.
    query = """
    SELECT
      gs.source_id, gs.ra, gs.dec, gs.parallax, gs.parallax_error,
      gs.pmra, gs.pmdec, gs.radial_velocity, gs.ruwe, gs.duplicated_source,
      ap.age_flame, ap.age_flame_lower, ap.age_flame_upper, ap.flags_flame
    FROM gaiadr3.gaia_source AS gs
    JOIN gaiadr3.astrophysical_parameters AS ap USING (source_id)
    WHERE gs.parallax > 0
      AND gs.parallax_error > 0
      AND gs.parallax/gs.parallax_error >= 10
      AND gs.ruwe <= 1.4
      AND gs.duplicated_source = 'false'
      AND gs.radial_velocity IS NOT NULL
      AND ap.age_flame IS NOT NULL
      AND ap.age_flame_lower IS NOT NULL
      AND ap.age_flame_upper IS NOT NULL
      AND SUBSTRING(ap.flags_flame,1,1) = '0'
      AND (ap.age_flame_upper <= 1.0 OR ap.age_flame_lower >= 4.0)
    """
    payload = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
    r = requests.post(GAIA_TAP_SYNC, data=payload, timeout=600)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text), dtype={"source_id": "string"})


def flame_cohorts(d: pd.DataFrame, excluded: set[str]) -> pd.DataFrame:
    x = d.copy()
    x["source_id"] = x["source_id"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    x = x[~x["source_id"].isin(excluded)].copy()
    for c in ["age_flame", "age_flame_lower", "age_flame_upper"]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    flags = x["flags_flame"].astype("string")
    finite = np.isfinite(x[["age_flame", "age_flame_lower", "age_flame_upper"]].to_numpy(float)).all(axis=1)
    quality = finite & flags.str.startswith("0", na=False)
    young = quality & (x["age_flame_upper"] <= 1.0)
    old = quality & (x["age_flame_lower"] >= 4.0)
    if np.any(young & old):
        raise AssertionError("FLAME young/old bounds overlap")
    x = x.loc[young | old].copy()
    x["cohort"] = np.where(young[young | old], "young", "old")
    return x


def build_phase_space(d: pd.DataFrame, v1: dict[str, Any]) -> pd.DataFrame:
    from astropy import units as u
    from astropy.coordinates import CartesianDifferential, Galactocentric, SkyCoord

    numeric = ["ra", "dec", "parallax", "parallax_error", "pmra", "pmdec", "radial_velocity", "ruwe"]
    for c in numeric:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    finite = np.isfinite(d[numeric].to_numpy(float)).all(axis=1)
    dup = d["duplicated_source"].astype("string").str.lower().isin(["true", "1", "t", "yes"])
    q = finite & (d["parallax"] > 0) & (d["parallax_error"] > 0) & ((d["parallax"] / d["parallax_error"]) >= 10) & (d["ruwe"] <= 1.4) & (~dup)
    x = d.loc[q].copy()
    x["distance_kpc"] = 1.0 / x["parallax"]
    sky = SkyCoord(
        ra=x["ra"].to_numpy(float) * u.deg,
        dec=x["dec"].to_numpy(float) * u.deg,
        distance=x["distance_kpc"].to_numpy(float) * u.kpc,
        pm_ra_cosdec=x["pmra"].to_numpy(float) * u.mas / u.yr,
        pm_dec=x["pmdec"].to_numpy(float) * u.mas / u.yr,
        radial_velocity=x["radial_velocity"].to_numpy(float) * u.km / u.s,
        frame="icrs",
    )
    f = v1["field_test"]["galactocentric_frame"]
    frame = Galactocentric(
        galcen_distance=float(f["galcen_distance_kpc"]) * u.kpc,
        z_sun=float(f["z_sun_kpc"]) * u.kpc,
        galcen_v_sun=CartesianDifferential(np.asarray(f["galcen_v_sun_cartesian_kms"], float) * u.km / u.s),
    )
    tr = sky.transform_to(frame)
    xx = tr.cartesian.x.to_value(u.kpc); yy = tr.cartesian.y.to_value(u.kpc); zz = tr.cartesian.z.to_value(u.kpc)
    vx = tr.velocity.d_x.to_value(u.km/u.s); vy = tr.velocity.d_y.to_value(u.km/u.s); vz = tr.velocity.d_z.to_value(u.km/u.s)
    R = np.hypot(xx, yy)
    vR = (xx*vx + yy*vy)/R
    vp = (-yy*vx + xx*vy)/R
    sign = -1.0 if float(np.nanmedian(vp)) < 0 else 1.0
    x["x_kpc"], x["y_kpc"], x["z_kpc"], x["R_kpc"] = xx, yy, zz, R
    x["v_R_kms"], x["v_phi_kms"], x["v_z_kms"] = vR, sign*vp, vz
    return x


def permutation_test(groups: list[pd.DataFrame], gradients: list[float], ridge: float, vc: float, nperm: int, seed: int, corrected: bool) -> tuple[dict[str, float], float]:
    rows = [voxel_stats(g, ridge, grad, vc) if corrected else voxel_stats(g, ridge) for g, grad in zip(groups, gradients, strict=True)]
    obs = aggregate(rows, corrected=corrected)
    rng = np.random.default_rng(seed)
    vals = np.full(nperm, np.nan)
    for i in range(nperm):
        prow = []
        for g, grad in zip(groups, gradients, strict=True):
            gp = g.copy(); gp["cohort"] = rng.permutation(gp["cohort"].to_numpy())
            prow.append(voxel_stats(gp, ridge, grad, vc) if corrected else voxel_stats(gp, ridge))
        vals[i] = aggregate(prow, corrected=corrected)["T_3D"]
    p = float((1 + np.sum(vals >= obs["T_3D"])) / (nperm + 1))
    return obs, p


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--v1-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json"))
    p.add_argument("--v2-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v2_conventional_challenge.json"))
    p.add_argument("--output-dir", type=Path, default=Path("data/persistence_history/dr20_independent/conventional_challenge_v2/test_D_flame_replication"))
    return p.parse_args()


def main() -> None:
    args = parse_args(); v1 = load_json(args.v1_protocol); v2 = load_json(args.v2_protocol)
    if v2.get("status") != "frozen_pre_v2_outcome":
        raise RuntimeError("Refusing to run: v2 protocol is not frozen")
    spec = v2["test_D_replication"]; drift = v2["test_A_asymmetric_drift"]
    nperm = int(spec["permutation"]["permutations"]); seed = int(spec["permutation"]["seed"]); alpha = float(spec["permutation"]["alpha"])
    ridge = float(v1["field_test"]["primary_statistic"]["covariance_ridge_fraction"]); vc = float(drift["V_c_kms"])

    gyro_url = v1["sources"]["gyro"]["url"]
    gyro_path = Path("data/external/sdss/dr20_independent_current_field_v1/gyro_age_dwarf-1.0.0.fits")
    excluded = gyro_ids(download_gyro(gyro_url, gyro_path))

    raw = query_flame()
    cohorts = flame_cohorts(raw, excluded)
    phase = build_phase_space(cohorts, v1)
    phase = assign_voxels(phase, v1)
    supported, voxel_ids = supported_sample(phase, v1)

    # Common radial gradient is fit on the full disjoint FLAME young+old replication cohort,
    # matching Test A's implementation lock; supported voxels are used only for inference.
    slopes, gradient_audit = fit_common_radial_gradients(phase, drift)
    groups: list[pd.DataFrame] = []; gradients: list[float] = []
    for vid in voxel_ids:
        g = supported[supported["voxel_id"] == vid].copy()
        zs = z_stratum(float(g["z_kpc"].abs().mean()))
        grad = slopes.get(zs, float("nan")) if zs else float("nan")
        if np.isfinite(grad):
            groups.append(g); gradients.append(float(grad))

    powered = len(groups) >= int(spec["minimum_powered_voxels"])
    raw_obs = corr_obs = {}; raw_p = corr_p = None
    if groups:
        raw_obs, raw_p = permutation_test(groups, gradients, ridge, vc, nperm, seed, corrected=False)
        corr_obs, corr_p = permutation_test(groups, gradients, ridge, vc, nperm, seed, corrected=True)

    # Frozen direction rule is evaluated against the primary Test-C residual vector when available.
    primary_path = Path("data/persistence_history/dr20_independent/conventional_challenge_v2/test_C_component_decomposition/test_C_summary.json")
    direction_ok = None; tested_components: list[str] = []
    if primary_path.exists() and corr_obs:
        primary = load_json(primary_path)["drift_corrected"]
        for name, key in (("R", "delta_R_equal_voxel_kms"), ("phi", "delta_phi_equal_voxel_kms"), ("z", "delta_z_equal_voxel_kms")):
            pv = float(primary[key])
            if abs(pv) > 2.0:
                tested_components.append(name)
                rv = float(corr_obs[key])
                if np.sign(rv) != np.sign(pv):
                    direction_ok = False
        if direction_ok is None:
            direction_ok = True
    success = bool(powered and corr_p is not None and corr_p <= alpha and direction_ok is True)

    summary = {
        "protocol_id": v2["protocol_id"],
        "test": "D_disjoint_Gaia_FLAME_replication",
        "gyro_source_ids_excluded": len(excluded),
        "gaia_flame_rows_from_tap_before_disjoint_exclusion": int(len(raw)),
        "disjoint_flame_young_old_rows": int(len(cohorts)),
        "quality_phase_space_rows": int(len(phase)),
        "supported_voxels": int(len(groups)),
        "minimum_powered_voxels": int(spec["minimum_powered_voxels"]),
        "powered": powered,
        "common_radial_gradient_by_z_stratum": {k: (float(v) if np.isfinite(v) else None) for k,v in slopes.items()},
        "raw": ({**raw_obs, "p_T_3D": raw_p} if raw_obs else None),
        "drift_corrected": ({**corr_obs, "p_T_3D": corr_p} if corr_obs else None),
        "permutations": nperm,
        "seed": seed,
        "alpha": alpha,
        "direction_rule_components_with_primary_abs_residual_gt_2_kms": tested_components,
        "direction_rule_pass": direction_ok,
        "replication_success": success,
        "interpretation": (
            "independent_drift_corrected_replication_success" if success else
            ("underpowered_disjoint_FLAME_replication" if not powered else "independent_drift_corrected_replication_failed")
        ),
        "guardrail": "A raw FLAME age difference does not count as replication; only the frozen drift-corrected criterion can pass Test D."
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "test_D_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    phase.to_csv(args.output_dir / "test_D_disjoint_flame_phase_space.csv.gz", index=False, compression="gzip")
    gradient_audit.to_csv(args.output_dir / "test_D_gradient_audit.csv", index=False)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
