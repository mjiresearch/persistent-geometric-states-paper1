#!/usr/bin/env python3
"""Audit public radial H I profiles against frozen SPARC total H I masses.

This script is a pre-fit standardization diagnostic. It does not alter profile
shape and it does not evaluate any persistence-model parameter.

For an axisymmetric face-on hydrogen-only profile Sigma_HI(R),

    M_HI,profile = 2 pi int R Sigma_HI(R) dR.

The script compares that integral with the SPARC catalog M_HI and reports the
single multiplicative surface-density normalization that would make the
integrated observed profile equal the SPARC H I mass. This is NOT by itself a
replacement for Hua et al.'s GIPSY Rotmod standardization; it is a transparent
QC quantity to be compared with Rotmod when that executable/reference output is
available.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

KPC2_TO_PC2 = 1.0e6


def parse_sparc_catalog(path: Path) -> dict[str, dict[str, float]]:
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        p = raw.split()
        if len(p) < 14:
            continue
        try:
            g = p[0]
            distance = float(p[2])
            mhi_1e9 = float(p[13])
        except ValueError:
            continue
        out[g] = {"distance_mpc": distance, "mhi_1e9_msun": mhi_1e9}
    if not out:
        raise ValueError("No SPARC catalog rows parsed")
    return out


def integrate_profile(r_kpc: np.ndarray, sigma_hi: np.ndarray) -> float:
    order = np.argsort(r_kpc)
    r = np.asarray(r_kpc, float)[order]
    s = np.asarray(sigma_hi, float)[order]
    good = np.isfinite(r) & np.isfinite(s) & (r >= 0) & (s >= 0)
    r = r[good]; s = s[good]
    if len(r) < 2:
        return np.nan
    # Observed radial profiles typically begin at a finite ring center. For the
    # diagnostic only, close the integral to R=0 with the innermost measured
    # surface density. Flag this assumption in the output.
    if r[0] > 0:
        r = np.r_[0.0, r]
        s = np.r_[s[0], s]
    return float(2.0 * np.pi * KPC2_TO_PC2 * np.trapz(r * s, r))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--profiles", required=True, type=Path)
    p.add_argument("--sparc-catalog", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()

    profiles = pd.read_csv(a.profiles)
    cat = parse_sparc_catalog(a.sparc_catalog)
    rows = []
    for galaxy, d in profiles.groupby("galaxy"):
        if galaxy not in cat:
            continue
        m_profile = integrate_profile(d.radius_kpc.to_numpy(), d.sigma_hi_msun_pc2.to_numpy())
        m_sparc = 1e9 * cat[galaxy]["mhi_1e9_msun"]
        factor = m_sparc / m_profile if np.isfinite(m_profile) and m_profile > 0 else np.nan
        rows.append({
            "galaxy": galaxy,
            "n_profile_bins": len(d),
            "profile_rmin_kpc": d.radius_kpc.min(),
            "profile_rmax_kpc": d.radius_kpc.max(),
            "mhi_profile_integrated_msun": m_profile,
            "mhi_sparc_msun": m_sparc,
            "mass_ratio_profile_to_sparc": m_profile / m_sparc if m_sparc > 0 else np.nan,
            "shape_preserving_scale_to_sparc_mhi": factor,
            "central_closure_assumption": "SigmaHI(R<first_ring)=SigmaHI(first_ring)",
            "outer_missing_flux_warning": "profile integral excludes HI outside last measured ring",
            "status": "QC_ONLY_NOT_ROTMOD_REPLACEMENT",
        })

    out = pd.DataFrame(rows).sort_values("galaxy")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.output, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
