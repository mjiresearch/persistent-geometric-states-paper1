#!/usr/bin/env python3
"""Frozen Gaia-Cepheid V3 support audit.

Geometry-only. This script MUST NOT read H I velocities/residuals or any
streaming/Persistence prediction. See GAIA_CEPHEID_V3_SUPPORT_FREEZE.md.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

HERE = Path(__file__).resolve().parent
BESSEL = HERE.parent / "bessel_streaming_frozen"
TARGETS = BESSEL / "frozen_grb_geometry_only.csv"
REID = BESSEL / "reid2019_table1.dat"
RAW_CEPHEIDS = HERE / "gaia_dr3_classical_cepheids_table2.dat"
OUTDIR = HERE / "outputs_v1"
OUTDIR.mkdir(parents=True, exist_ok=True)

CEPHEID_URL = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/674/A37/table2.dat"
R0 = 8.15
H_GRID = [1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0]

# Exact frozen V3 Outer-arm locus.
OUTER_ALPHA = 2.0373888808067595
OUTER_BETA = 0.15578848229141543
OUTER_SIGMA = 0.8489392303918806

# Frozen OSC geometry rule.
OSC_PITCH_DEG = 13.1
OSC_BETA = math.tan(math.radians(OSC_PITCH_DEG))


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 1000:
        return
    req = Request(url, headers={"User-Agent": "PGS-Gaia-Cepheid-support-audit/1.0"})
    with urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def galcen_xy(l_deg: float, b_deg: float, d_kpc: float):
    l = math.radians(l_deg)
    b = math.radians(b_deg)
    cb = math.cos(b)
    x = -R0 + d_kpc * cb * math.cos(l)
    y = d_kpc * cb * math.sin(l)
    z = d_kpc * math.sin(b)
    R = math.hypot(x, y)
    phi = math.atan2(y, x)
    return x, y, z, R, phi


def wrap_about(phi, center):
    return center + ((np.asarray(phi, float) - center + np.pi) % (2 * np.pi) - np.pi)


def spiral_coords(R, phi, alpha, beta, target_phi):
    phi_u = wrap_about(phi, target_phi)
    Rfit = np.exp(alpha + beta * phi_u)
    Rfit_t = float(math.exp(alpha + beta * target_phi))
    if abs(beta) > 1e-9:
        s = math.sqrt(1.0 + beta * beta) / beta * (Rfit - Rfit_t)
    else:
        s = Rfit_t * (phi_u - target_phi)
    dperp = (np.asarray(R, float) - Rfit) / math.sqrt(1.0 + beta * beta)
    target_dperp = (float(Rfit_t) - float(Rfit_t))  # explicit zero on locus
    return np.asarray(s, float), np.asarray(dperp, float), Rfit_t, target_dperp


def target_spiral_offset(Rt, phit, alpha, beta):
    Rfit_t = math.exp(alpha + beta * phit)
    return (Rt - Rfit_t) / math.sqrt(1.0 + beta * beta)


def parse_cepheids(path: Path):
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            gaia = line[0:19].strip()
            glon = float(line[20:29])
            glat = float(line[30:39])
            dist = float(line[42:47])
            emu_s = line[56:61].strip()
            e_mu = float(emu_s) if emu_s else float("nan")
            if not gaia or not np.isfinite(dist) or dist <= 0:
                continue
            x, y, z, R, phi = galcen_xy(glon, glat, dist)
            rows.append({
                "GaiaDR3": gaia,
                "GLON": glon,
                "GLAT": glat,
                "Dist": dist,
                "e_mu": e_mu,
                "x": x,
                "y": y,
                "z": z,
                "R": R,
                "phi": phi,
            })
        except Exception:
            continue
    return rows


def read_targets(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def osc_anchor_alpha(reid_path: Path):
    # The source name itself encodes l=7.47, b=+0.05 degrees.
    for line in reid_path.read_text(errors="replace").splitlines():
        if line.startswith("G007.47+00.05"):
            plx = float(line[62:67])
            if plx <= 0:
                raise RuntimeError("Invalid G007.47+00.05 parallax")
            d = 1.0 / plx
            _, _, _, R, phi = galcen_xy(7.47, 0.05, d)
            alpha = math.log(R) - OSC_BETA * phi
            return {
                "source": "G007.47+00.05",
                "parallax_mas": plx,
                "distance_kpc": d,
                "R_kpc": R,
                "phi_rad": phi,
                "pitch_deg": OSC_PITCH_DEG,
                "alpha": alpha,
                "beta": OSC_BETA,
            }
    raise RuntimeError("G007.47+00.05 not found in frozen Reid table")


def robust_sigma(offsets):
    a = np.asarray(offsets, float)
    med = float(np.median(a))
    mad = 1.4826 * float(np.median(np.abs(a - med)))
    return float(np.clip(mad, 0.25, 1.00))


def audit_one(cepheids, target, osc_anchor):
    name = target["target"]
    arm = target["arm"]
    l = float(target["l_deg"])
    b = float(target["b_deg"])
    d = float(target["distance_kpc"])
    _, _, _, Rt, phit = galcen_xy(l, b, d)

    if arm == "Outer":
        alpha, beta, sigma = OUTER_ALPHA, OUTER_BETA, OUTER_SIGMA
        geometry_source = "frozen_V3_Outer"
    elif arm == "OSC":
        alpha, beta = osc_anchor["alpha"], osc_anchor["beta"]
        geometry_source = "Reid2019_SC_to_OSC_anchor_G007.47"
        # Sigma determined below from geometry-only provisional Cepheid members.
        sigma = None
    else:
        raise RuntimeError(f"Unsupported arm label {arm}")

    R = np.array([r["R"] for r in cepheids], float)
    phi = np.array([r["phi"] for r in cepheids], float)
    s, dperp, _, _ = spiral_coords(R, phi, alpha, beta, phit)

    if sigma is None:
        provisional = np.abs(dperp) <= 1.5
        if provisional.sum() < 3:
            sigma = 0.25
        else:
            sigma = robust_sigma(dperp[provisional])

    perp_limit = max(1.0, 2.0 * sigma)
    member = np.abs(dperp) <= perp_limit
    N_arm = int(member.sum())
    nearest_phase = float(np.min(np.abs(s[member]))) if N_arm else float("nan")
    target_dperp = float(target_spiral_offset(Rt, phit, alpha, beta))

    grid = []
    selected_h = None
    selected_neff = None
    for h in H_GRID:
        if N_arm:
            sm = s[member]
            dm = dperp[member]
            w = np.exp(-0.5 * (sm / h) ** 2) * np.exp(-0.5 * (dm / sigma) ** 2)
            sw = float(w.sum())
            neff = float(sw * sw / np.sum(w * w)) if sw > 0 else 0.0
        else:
            neff = 0.0
        ok = bool(
            neff >= 3.0
            and np.isfinite(nearest_phase)
            and nearest_phase <= 2.0 * h
            and abs(target_dperp) <= perp_limit
        )
        grid.append({"h_kpc": h, "N_eff": neff, "support_qualified": ok})
        if selected_h is None and ok:
            selected_h = h
            selected_neff = neff

    return {
        "target": name,
        "arm": arm,
        "geometry_source": geometry_source,
        "R_target_kpc": Rt,
        "phi_target_rad": phit,
        "N_arm": N_arm,
        "sigma_arm_kpc": sigma,
        "perp_limit_kpc": perp_limit,
        "d_nearest_phase_kpc": nearest_phase,
        "d_perp_target_kpc": target_dperp,
        "selected_support_h_kpc": selected_h,
        "N_eff": selected_neff,
        "status": "CEPHEID_SUPPORT" if selected_h is not None else "NO_CEPHEID_SUPPORT",
        "support_grid": grid,
    }


def main():
    download(CEPHEID_URL, RAW_CEPHEIDS)
    cepheids = parse_cepheids(RAW_CEPHEIDS)
    targets = read_targets(TARGETS)
    osc_anchor = osc_anchor_alpha(REID)

    results = [audit_one(cepheids, t, osc_anchor) for t in targets]
    summary = {
        "protocol": "GAIA_CEPHEID_V3_SUPPORT_AUDIT_V1",
        "status": "FROZEN_GEOMETRY_ONLY_BEFORE_HI_COMPARISON",
        "catalog": "CDS/VizieR J/A+A/674/A37/table2",
        "catalog_expected_rows": 3306,
        "catalog_parsed_rows": len(cepheids),
        "R0_kpc": R0,
        "h_grid_kpc": H_GRID,
        "outer_geometry": {
            "alpha": OUTER_ALPHA,
            "beta": OUTER_BETA,
            "sigma_arm_kpc": OUTER_SIGMA,
            "source": "frozen V3 Outer locus",
        },
        "osc_geometry": osc_anchor,
        "guardrail": "No H I spectrum, velocity, residual, V1/V2/V3 prediction, or Persistence prediction was read.",
        "results": results,
    }
    (OUTDIR / "gaia_cepheid_v3_support_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    fields = [
        "target", "arm", "geometry_source", "R_target_kpc", "phi_target_rad",
        "N_arm", "sigma_arm_kpc", "perp_limit_kpc", "d_nearest_phase_kpc",
        "d_perp_target_kpc", "selected_support_h_kpc", "N_eff", "status",
    ]
    with open(OUTDIR / "gaia_cepheid_v3_support_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow({k: r[k] for k in fields})

    with open(OUTDIR / "gaia_cepheid_v3_support_grid.csv", "w", newline="") as f:
        fields2 = ["target", "arm", "h_kpc", "N_eff", "support_qualified"]
        w = csv.DictWriter(f, fieldnames=fields2)
        w.writeheader()
        for r in results:
            for g in r["support_grid"]:
                w.writerow({"target": r["target"], "arm": r["arm"], **g})

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
