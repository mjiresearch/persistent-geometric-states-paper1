#!/usr/bin/env python3
"""Build harmonized public radial-HI and source-profile tables for the stationary sample.

This is a data-construction utility, not a fit. It enforces the current freeze rules:
- only direct public radial HI measurements or direct public map extractions;
- radii are converted to the frozen SPARC distance convention;
- no inward or outward HI extrapolation;
- HI remains hydrogen-only in the profile table;
- the source table applies one declared helium factor (1.33);
- stellar surface density uses the predeclared 3.6um M/L values 0.5 disk, 0.7 bulge;
- v_obs is never used as the source-current velocity.

Inputs are expected to be locally acquired public products:
1. direct_hi_annular_profiles.csv (THINGS/LITTLE THINGS map extraction)
2. feasts_hi_profiles_long.csv (public FEASTS direct radial profiles)
3. stationary_master_v1.csv (frozen stationary SPARC master)

Outputs:
- stationary_hi_profiles_public_harmonized_v1.csv
- stationary_source_profiles_public_seed_v1.csv
- stationary_public_harmonized_summary_v1.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

DIRECT_FROZEN = ("DDO154", "DDO168")
FEASTS_FROZEN = (
    "NGC2841", "NGC2903", "NGC3198", "NGC3521",
    "NGC4559", "NGC5033", "NGC5055",
)
HELIUM_FACTOR = 1.33
ML_DISK = 0.5
ML_BULGE = 0.7


def build(direct_path: Path, feasts_path: Path, master_path: Path, outdir: Path) -> None:
    hi = pd.read_csv(direct_path)
    fe = pd.read_csv(feasts_path)
    master = pd.read_csv(master_path)
    frozen = set(master["galaxy"].unique())

    rows: list[dict] = []

    for galaxy in DIRECT_FROZEN:
        if galaxy not in frozen:
            raise ValueError(f"{galaxy} is not in the frozen stationary master")
        d = hi[
            (hi["name"] == galaxy)
            & (~hi["beam_smeared_mask"].astype(bool))
            & np.isfinite(hi["Sigma_HI_Msun_pc2"])
        ].copy().sort_values("r_kpc")
        frozen_distance = float(master.loc[master.galaxy == galaxy, "distance_mpc"].iloc[0])
        for _, row in d.iterrows():
            err = np.nan
            if np.isfinite(row["Sigma_HI_p16"]) and np.isfinite(row["Sigma_HI_p84"]):
                err = 0.5 * (row["Sigma_HI_p84"] - row["Sigma_HI_p16"])
            rows.append({
                "galaxy": galaxy,
                "radius_kpc": float(row["r_kpc"]),
                "sigma_hi_msun_pc2": float(row["Sigma_HI_Msun_pc2"]),
                "sigma_hi_err_msun_pc2": err,
                "source_family": "THINGS/LITTLE_THINGS",
                "source_product": "public moment-0 annular extraction",
                "source_distance_mpc": frozen_distance,
                "radius_scale_to_frozen": 1.0,
                "helium_included": False,
                "profile_method": "direct_public_map_extraction",
                "qc_flag": "clean_non_beam_smeared",
            })

    for galaxy in FEASTS_FROZEN:
        if galaxy not in frozen:
            raise ValueError(f"{galaxy} is not in the frozen stationary master")
        d = fe[fe["name_key"] == galaxy].copy().sort_values("radius_hi_kpc")
        if d.empty:
            raise ValueError(f"No FEASTS profile found for {galaxy}")
        frozen_distance = float(master.loc[master.galaxy == galaxy, "distance_mpc"].iloc[0])
        source_distance = float(d["dist_feasts_mpc"].iloc[0])
        scale = frozen_distance / source_distance
        for _, row in d.iterrows():
            if not np.isfinite(row["sigma_hi_msun_pc2"]):
                continue
            rows.append({
                "galaxy": galaxy,
                "radius_kpc": float(row["radius_hi_kpc"] * scale),
                "sigma_hi_msun_pc2": float(row["sigma_hi_msun_pc2"]),
                "sigma_hi_err_msun_pc2": np.nan,
                "source_family": "FEASTS",
                "source_product": "public direct radial HI profile",
                "source_distance_mpc": source_distance,
                "radius_scale_to_frozen": scale,
                "helium_included": False,
                "profile_method": "direct_public_radial_profile",
                "qc_flag": "distance_rescaled_to_frozen_SPARC",
            })

    profiles = pd.DataFrame(rows).sort_values(["galaxy", "radius_kpc"]).reset_index(drop=True)

    source_rows: list[dict] = []
    for galaxy, profile in profiles.groupby("galaxy"):
        profile = profile.sort_values("radius_kpc")
        rp = profile["radius_kpc"].to_numpy(float)
        yp = profile["sigma_hi_msun_pc2"].to_numpy(float)
        galaxy_master = master[master.galaxy == galaxy].sort_values("radius_kpc")
        for _, row in galaxy_master.iterrows():
            radius = float(row["radius_kpc"])
            if radius < rp.min() or radius > rp.max():
                continue  # no extrapolation
            sigma_hi = float(np.interp(radius, rp, yp))
            sigma_atomic = HELIUM_FACTOR * sigma_hi
            sigma_star = ML_DISK * float(row["sb_disk_lsun_pc2"]) + ML_BULGE * float(row["sb_bulge_lsun_pc2"])
            source_rows.append({
                "galaxy": galaxy,
                "radius_kpc": radius,
                "sigma_hi_msun_pc2": sigma_hi,
                "helium_factor": HELIUM_FACTOR,
                "sigma_atomic_gas_msun_pc2": sigma_atomic,
                "sigma_star_msun_pc2": sigma_star,
                "sigma_baryon_msun_pc2": sigma_atomic + sigma_star,
                "hi_interpolation": "linear_inside_measured_range_only",
                "stellar_ml_disk": ML_DISK,
                "stellar_ml_bulge": ML_BULGE,
                "source_current_velocity_policy": "self_consistent_model_velocity_not_vobs",
                "qc_flag": "no_HI_extrapolation",
            })

    source = pd.DataFrame(source_rows).sort_values(["galaxy", "radius_kpc"]).reset_index(drop=True)

    summary_rows = []
    for galaxy, profile in profiles.groupby("galaxy"):
        s = source[source.galaxy == galaxy]
        summary_rows.append({
            "galaxy": galaxy,
            "n_hi_bins": len(profile),
            "hi_rmin_kpc": profile.radius_kpc.min(),
            "hi_rmax_kpc": profile.radius_kpc.max(),
            "n_source_rows": len(s),
            "source_rmin_kpc": s.radius_kpc.min() if len(s) else np.nan,
            "source_rmax_kpc": s.radius_kpc.max() if len(s) else np.nan,
            "source_family": profile.source_family.iloc[0],
            "profile_method": profile.profile_method.iloc[0],
        })
    summary = pd.DataFrame(summary_rows)

    outdir.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(outdir / "stationary_hi_profiles_public_harmonized_v1.csv", index=False)
    source.to_csv(outdir / "stationary_source_profiles_public_seed_v1.csv", index=False)
    summary.to_csv(outdir / "stationary_public_harmonized_summary_v1.csv", index=False)

    print(f"HI profile rows: {len(profiles)} across {profiles.galaxy.nunique()} galaxies")
    print(f"Source rows: {len(source)} across {source.galaxy.nunique()} galaxies")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct", type=Path, required=True)
    parser.add_argument("--feasts", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    build(args.direct, args.feasts, args.master, args.outdir)


if __name__ == "__main__":
    main()
