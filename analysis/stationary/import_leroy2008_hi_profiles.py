#!/usr/bin/env python3
"""Import the public Leroy et al. (2008) radial HI table into the stationary schema.

Primary source: CDS/VizieR J/AJ/136/2782/table7 (table7.dat).
The catalogue explicitly states that SigmaHI includes helium. Leroy et al. (2008)
use a factor 1.36; this importer divides both SigmaHI and its rms uncertainty by
1.36 to restore hydrogen-only Sigma_HI before the common stationary gas
correction is applied downstream.

Only the six still-unrecovered frozen THINGS systems are selected here:
IC2574, NGC2403, NGC2976, NGC6946, NGC7331, NGC7793.
Radii are rescaled from Leroy's adopted distance to the frozen SPARC distance.
No interpolation or extrapolation occurs in this importer.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

TARGETS = ("IC2574", "NGC2403", "NGC2976", "NGC6946", "NGC7331", "NGC7793")
HELIUM_LEROY = 1.36

# Leroy et al. 2008 Table 4 / sample distances (Mpc), matching the CDS catalogue.
LEROY_DISTANCE_MPC = {
    "IC2574": 4.0,
    "NGC2403": 3.2,
    "NGC2976": 3.6,
    "NGC6946": 5.9,
    "NGC7331": 14.7,
    "NGC7793": 3.9,
}


def parse_table7(path: Path) -> pd.DataFrame:
    """Parse CDS fixed-width table7.dat using its documented byte layout."""
    # Bytes are 1-indexed in the CDS ReadMe; pandas colspec endpoints are 0-based,
    # half-open. Only the fields needed for this project are parsed.
    colspecs = [(0, 8), (9, 13), (19, 24), (25, 28)]
    names = ["raw_name", "r_leroy_kpc", "sigma_hi_with_he_msun_pc2", "e_sigma_hi_with_he_msun_pc2"]
    df = pd.read_fwf(path, colspecs=colspecs, names=names, na_values=["", "-", "--"])
    df["raw_name"] = df["raw_name"].astype(str).str.strip()
    return df


def normalize_name(name: str) -> str:
    return name.replace(" ", "").upper()


def build(table7: Path, master: Path, output: Path) -> None:
    raw = parse_table7(table7)
    raw["galaxy"] = raw.raw_name.map(normalize_name)
    master_df = pd.read_csv(master)
    frozen = set(master_df.galaxy.unique())

    out_rows = []
    for galaxy in TARGETS:
        if galaxy not in frozen:
            raise ValueError(f"{galaxy} missing from frozen stationary master")
        rows = raw[raw.galaxy == galaxy].copy()
        if rows.empty:
            raise ValueError(f"No Leroy table7 rows found for {galaxy}")
        d_sparc = float(master_df.loc[master_df.galaxy == galaxy, "distance_mpc"].iloc[0])
        d_leroy = LEROY_DISTANCE_MPC[galaxy]
        scale = d_sparc / d_leroy
        for _, row in rows.iterrows():
            if not np.isfinite(row.r_leroy_kpc) or not np.isfinite(row.sigma_hi_with_he_msun_pc2):
                continue
            err_raw = row.e_sigma_hi_with_he_msun_pc2
            upper_limit = bool(np.isfinite(err_raw) and float(err_raw) == 1.0)
            err_hi = np.nan if not np.isfinite(err_raw) or upper_limit else float(err_raw) / HELIUM_LEROY
            out_rows.append({
                "galaxy": galaxy,
                "radius_kpc": float(row.r_leroy_kpc) * scale,
                "sigma_hi_msun_pc2": float(row.sigma_hi_with_he_msun_pc2) / HELIUM_LEROY,
                "sigma_hi_err_msun_pc2": err_hi,
                "source_family": "Leroy_et_al_2008_THINGS",
                "source_product": "CDS J/AJ/136/2782/table7",
                "source_distance_mpc": d_leroy,
                "frozen_sparc_distance_mpc": d_sparc,
                "radius_scale_to_frozen": scale,
                "catalog_helium_factor_removed": HELIUM_LEROY,
                "helium_included": False,
                "upper_limit_flag": upper_limit,
                "profile_method": "direct_public_machine_readable_radial_profile",
                "qc_flag": "distance_rescaled_helium_removed",
            })

    out = pd.DataFrame(out_rows).sort_values(["galaxy", "radius_kpc"]).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)
    print(out.groupby("galaxy").size().to_string())
    print(f"Wrote {len(out)} rows to {output}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--table7", required=True, type=Path)
    p.add_argument("--master", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    build(a.table7, a.master, a.output)


if __name__ == "__main__":
    main()
