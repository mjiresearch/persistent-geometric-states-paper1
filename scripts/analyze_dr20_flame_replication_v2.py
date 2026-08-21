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
    # Keep server-side ADQL deliberately simple and re-apply all frozen quality rules
    # locally. Gaia DR3 documents age_flame[_lower/_upper] in Gyr and flags_flame as
    # the FLAME quality/processing flag. Explicit ON syntax is used for TAP portability.
    query = """
    SELECT
      gs.source_id, gs.ra, gs.dec, gs.parallax, gs.parallax_error,
      gs.pmra, gs.pmdec, gs.radial_velocity, gs.ruwe, gs.duplicated_source,
      ap.age_flame, ap.age_flame_lower, ap.age_flame_upper, ap.flags_flame
    FROM gaiadr3.gaia_source AS gs
    JOIN gaiadr3.astrophysical_parameters AS ap
      ON gs.source_id = ap.source_id
    WHERE gs.parallax > 0
      AND gs.parallax_error > 0
      AND gs.parallax/gs.parallax_error >= 10
      AND gs.ruwe <= 1.4
      AND gs.radial_velocity IS NOT NULL
      AND ap.age_flame IS NOT NULL
      AND ap.age_flame_lower IS NOT NULL
      AND ap.age_flame_upper IS NOT NULL
      AND (ap.age_flame_upper <= 1.0 OR ap.age_flame_lower >= 4.0)
    """
    payload = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
    r = requests.post(GAIA_TAP_SYNC, data=payload, timeout=600)
    if r.status_code >= 400:
        raise RuntimeError(f"Gaia TAP HTTP {r.status_code}: {r.text[:2000]}")
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
    fs = v1["field_test"]["galactocentric_frame"]
    frame = Galactocentric(
        galcen_distance=float(fs["galcen_distance_kpc"]) * u.kpc,
        z_sun=float(fs["z_sun_kpc"]) * u.kpc,
        galcen_v_sun=CartesianDifferential(np.asarray(fs["galcen_v_sun_cartesian_kms"], float) * u.km / u.s),
    )
    g = sky.transform_to(frame)
    xx = g.cartesian.x.to_value(u.kpc); yy = g.cartesian.y.to_value(u.kpc); zz = g.cartesian.z.to_value(u.kpc)
    vx = g.velocity.d_x.to_value(u.km/u.s); vy = g.velocity.d_y.to_value(u.km/u.s); vz = g.velocity.d_z.to_value(u.km/u.s)
    R = np.hypot(xx, yy)
    vr = (xx*vx + yy*vy)/R
    vp = (-yy*vx + xx*vy)/R
    sign = -1.0 if float(np.nanmedian(vp)) < 0 else 1.0
    x["x_kpc"], x["y_kpc"], x["z_kpc"], x["R_kpc"] = xx, yy, zz, R
    x["v_R_kms"], x["v_phi_kms"], x["v_z_kms"] = vr, sign*vp, vz
    return x


def statistic(groups: list[pd.DataFrame], grads: list[float], ridge: float, vc: float, corrected: bool) -> dict[str, float]:
    rows = [voxel_stats(g, ridge, grad, vc) if corrected else voxel_stats(g, ridge) for g, grad in zip(groups, grads, strict=True)]
    return aggregate(rows, corrected=corrected)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--v1-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json"))
    p.add_argument("--v2-protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v2_conventional_challenge.json"))
    p.add_argument("--gyro-path", type=Path, default=Path("data/external/sdss/dr20_independent_current_field_v1/gyro_age_dwarf-1.0.0.fits"))
    p.add_argument("--output-dir", type=Path, default=Path("data/persistence_history/dr20_independent/conventional_challenge_v2/test_D_flame_replication"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    v1 = load_json(args.v1_protocol); v2 = load_json(args.v2_protocol)
    spec = v2["test_D_replication"]; ad = v2["test_A_asymmetric_drift"]
    gyro_url = v1["sources"]["gyro"]["url"]
    download_gyro(gyro_url, args.gyro_path)
    excluded = gyro_ids(args.gyro_path)
    raw = query_flame()
    cohort = flame_cohorts(raw, excluded)
    phase = build_phase_space(cohort, v1)
    phase = assign_voxels(phase, v1)
    supported, voxel_ids = supported_sample(phase, v1)
    minimum = int(spec["minimum_powered_voxels"])
    powered = len(voxel_ids) >= minimum

    # Common gradients are fit from the full quality FLAME young+old sample, not only supported voxels.
    slopes, gradient_audit = fit_common_radial_gradients(phase, ad)
    groups = []; grads = []
    for vid in voxel_ids:
        g = supported[supported["voxel_id"] == vid].copy()
        zs = z_stratum(float(g["z_kpc"].abs().mean()))
        grad = slopes.get(zs, float("nan")) if zs else float("nan")
        if np.isfinite(grad):
            groups.append(g); grads.append(float(grad))

    ridge = float(v1["field_test"]["primary_statistic"]["covariance_ridge_fraction"])
    vc = float(ad["V_c_kms"])
    raw_obs = statistic(groups, grads, ridge, vc, False) if groups else {}
    corr_obs = statistic(groups, grads, ridge, vc, True) if groups else {}
    nperm = int(spec["permutation"]["permutations"]); seed = int(spec["permutation"]["seed"]); alpha = float(spec["permutation"]["alpha"])
    rng = np.random.default_rng(seed)
    raw_perm = np.full(nperm, np.nan); corr_perm = np.full(nperm, np.nan)
    if groups:
        for i in range(nperm):
            pgroups = []
            for g in groups:
                gp = g.copy(); gp["cohort"] = rng.permutation(gp["cohort"].to_numpy()); pgroups.append(gp)
            raw_perm[i] = statistic(pgroups, grads, ridge, vc, False)["T_3D"]
            corr_perm[i] = statistic(pgroups, grads, ridge, vc, True)["T_3D"]
    p_raw = float((1 + np.sum(raw_perm >= raw_obs.get("T_3D", np.inf))) / (nperm + 1)) if groups else None
    p_corr = float((1 + np.sum(corr_perm >= corr_obs.get("T_3D", np.inf))) / (nperm + 1)) if groups else None
    success = bool(powered and len(groups) >= minimum and p_corr is not None and p_corr <= alpha)

    summary = {
        "protocol_id": v2["protocol_id"], "test": "D_disjoint_Gaia_FLAME_replication",
        "gyro_source_ids_excluded": len(excluded), "gaia_rows_returned_before_disjointness": len(raw),
        "flame_young_old_rows_after_disjointness_and_quality": len(phase),
        "supported_voxels": len(voxel_ids), "valid_gradient_voxels": len(groups), "minimum_powered_voxels": minimum,
        "powered": powered and len(groups) >= minimum,
        "common_radial_gradient_by_z_stratum": {k: (float(v) if np.isfinite(v) else None) for k,v in slopes.items()},
        "raw": ({**raw_obs, "p_T_3D": p_raw} if groups else None),
        "drift_corrected": ({**corr_obs, "p_T_3D": p_corr} if groups else None),
        "permutations": nperm, "seed": seed, "alpha": alpha,
        "replication_success": success,
        "interpretation": "disjoint_FLAME_replication_succeeds" if success else ("disjoint_FLAME_replication_underpowered" if not (powered and len(groups) >= minimum) else "disjoint_FLAME_replication_fails_drift_corrected_threshold"),
        "guardrail": "A raw uncorrected FLAME difference does not count as replication; the frozen criterion is the drift-corrected 3-D result."
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"test_D_summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    phase.to_csv(args.output_dir/"test_D_flame_star_sample.csv.gz", index=False, compression="gzip")
    gradient_audit.to_csv(args.output_dir/"test_D_gradient_audit.csv", index=False)
    pd.DataFrame({"raw_T3D": raw_perm, "corrected_T3D": corr_perm}).to_csv(args.output_dir/"test_D_permutations.csv.gz", index=False, compression="gzip")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
