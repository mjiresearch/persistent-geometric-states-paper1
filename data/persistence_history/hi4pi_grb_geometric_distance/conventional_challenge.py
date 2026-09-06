#!/usr/bin/env python3
"""Conventional streaming/warp challenge for the GRB geometric-distance test.

This script intentionally separates two questions:
1) arm/component association, frozen without using the Reid-predicted velocity;
2) whether conventional non-circular motions can reproduce the observed LOS residual.

Conventions:
- Galactocentric radial perturbation U_R > 0 is outward.
- Tangential perturbation dV_phi > 0 is in the direction of Galactic rotation.
- W > 0 is toward the north Galactic pole.
- Residual is v_HI - v_Reid at the X-ray geometric distance.

Empirical nuisance scales used for the screening challenge:
- sigma_R = 10 km/s
- sigma_phi = 5 km/s
- sigma_z = 5 km/s
These are deliberately broad, zero-centered scales consistent with observed Milky Way
streaming fields; a second broad-envelope check uses radial amplitudes up to 15 km/s.

This is a screening challenge, not a full hydrodynamical likelihood.
"""

from pathlib import Path
import math
import json
import pandas as pd

R0 = 8.15
BASE = Path(__file__).resolve().parent
INFILE = BASE / "bonn_results" / "geometric_kinematic_residuals.csv"
OUTDIR = BASE / "conventional_challenge"
OUTDIR.mkdir(exist_ok=True)

# Frozen external association rules. These rules are set without consulting
# v_Reid_geometric_kms.
ASSOCIATION = {
    ("GRB_221009A", "Outer"): {
        "status": "retained_medium_confidence",
        "rule": "Koo2017 bright Outer-arm first-quadrant ridge (l~20-80 deg), separated from the more-negative OSC locus; retain the major less-negative outer-Galaxy HI component.",
        "independent_of_reid": True,
    },
    ("GRB_221009A", "OSC"): {
        "status": "retained_high_confidence",
        "rule": "Dame2011/Wenger2018 OSC longitude-velocity locus v_LSR=-1.6*l +/-15 km/s.",
        "independent_of_reid": True,
    },
    ("GRB_160623A", "Outer"): {
        "status": "retained_medium_high_confidence",
        "rule": "Local parallax-anchored Outer-arm velocity bracket from G075.29+01.32 (-58 km/s) and G097.53+03.18 (-73 km/s), with a conservative +/-15 km/s arm/streaming window; retain the dominant outer-arm HI complex.",
        "independent_of_reid": True,
    },
    ("GRB_031203", "Outer"): {
        "status": "retained_with_arm_label_caveat",
        "rule": "Koo2017 outermost coherent southern HI ridge (l~210-300 deg), supported by CO clouds to l~255 deg; retain the outermost high-positive-velocity component. Arm nomenclature is controversial in this quadrant.",
        "independent_of_reid": True,
    },
}


def los_coefficients(l_deg, b_deg, d_kpc):
    l = math.radians(l_deg)
    b = math.radians(b_deg)
    cb, sb = math.cos(b), math.sin(b)
    cl, sl = math.cos(l), math.sin(l)

    # GC Cartesian: Sun=(R0,0,0), l=0 points toward GC.
    x = R0 - d_kpc * cb * cl
    y = d_kpc * cb * sl
    z = d_kpc * sb
    R = math.hypot(x, y)

    # LOS unit vector from Sun to source.
    nx, ny, nz = -cb * cl, cb * sl, sb
    # Cylindrical basis at source.
    erx, ery = x / R, y / R
    epx, epy = -y / R, x / R

    cR = nx * erx + ny * ery
    cphi = nx * epx + ny * epy
    cz = nz
    return R, z, cR, cphi, cz


df = pd.read_csv(INFILE)
out = []
for _, r in df.iterrows():
    R, z, cR, cphi, cz = los_coefficients(r.l_deg, r.b_deg, r.distance_kpc)
    dv = r.delta_v_obs_minus_reid_kms
    sigR, sigP, sigZ = 10.0, 5.0, 5.0
    sig_los = math.sqrt((cR*sigR)**2 + (cphi*sigP)**2 + (cz*sigZ)**2)

    key = (r.target, r.arm)
    assoc = ASSOCIATION[key]

    # Independent OSC check, where an explicit empirical locus exists.
    osc_center = -1.6*r.l_deg if r.arm == "OSC" else float("nan")
    osc_delta = r.v_hi_peak_kms - osc_center if r.arm == "OSC" else float("nan")

    out.append({
        "target": r.target,
        "arm": r.arm,
        "distance_kpc": r.distance_kpc,
        "R_gal_kpc": R,
        "z_kpc": z,
        "v_hi_peak_kms": r.v_hi_peak_kms,
        "v_reid_geometric_kms": r.v_reid_geometric_kms,
        "delta_v_kms": dv,
        "c_radial_out": cR,
        "c_tangential": cphi,
        "c_vertical": cz,
        "required_radial_out_kms": dv/cR,
        "required_tangential_kms": dv/cphi,
        "required_vertical_kms": dv/cz,
        "generic_streaming_sigma_los_kms": sig_los,
        "generic_streaming_zscore": dv/sig_los,
        "within_15_kms_radial_envelope": abs(dv/cR) <= 15.0,
        "osc_external_center_kms": osc_center,
        "osc_peak_minus_external_center_kms": osc_delta,
        "association_status": assoc["status"],
        "association_rule": assoc["rule"],
        "association_independent_of_reid": assoc["independent_of_reid"],
    })

res = pd.DataFrame(out)
res.to_csv(OUTDIR / "streaming_warp_challenge.csv", index=False)

# A specific empirical Outer-arm mean peculiar-motion vector from Hachisuka et al.
# U_s=+11.7 km/s toward the Galactic center => U_R(outward)=-11.7.
# V_s=-3.3 km/s, W_s=+1.8 km/s.
outer_mean = {"U_R_out": -11.7, "dV_phi": -3.3, "W": 1.8}
for i, row in res.iterrows():
    if row.arm == "Outer":
        pred = (row.c_radial_out*outer_mean["U_R_out"] +
                row.c_tangential*outer_mean["dV_phi"] +
                row.c_vertical*outer_mean["W"])
        res.loc[i, "outer_arm_empirical_mean_pred_kms"] = pred
        res.loc[i, "residual_after_outer_mean_kms"] = row.delta_v_kms - pred

res.to_csv(OUTDIR / "streaming_warp_challenge.csv", index=False)

verdict = {
    "test": "independently frozen arm association + conventional streaming/warp challenge",
    "association_result": {
        "GRB_221009A_OSC": "retained at high confidence; observed -82.82 km/s lies near independent OSC locus center -84.74 km/s and within the +/-15 km/s window",
        "GRB_160623A_Outer": "same dominant outer HI complex retained using external parallax-arm bracket",
        "GRB_221009A_Outer": "retained at medium confidence from independent first-quadrant arm-ridge ordering",
        "GRB_031203_Outer": "outermost component retained, but Outer-vs-Perseus nomenclature remains model-dependent in this quadrant",
    },
    "kinematic_result": {
        "warp_alone": "fails for the two largest residuals because low |b| makes the vertical projection tiny; required |W| is ~136-143 km/s",
        "radial_streaming": "can reproduce every residual with |U_R| <= 11.4 km/s",
        "generic_streaming_prior": "all four residuals are <=1.11 sigma under zero-centered (sigma_R,sigma_phi,sigma_z)=(10,5,5) km/s nuisance scales",
        "outer_arm_specific_mean": "the Hachisuka Outer-arm mean inward motion has the wrong sign for the positive first-quadrant residuals, so that single mean vector does not explain them; however arm/phase-dependent streaming can change sign",
    },
    "persistence_status": "not supported by this test after conventional streaming is admitted; the residual pattern remains a target only if a predictive conventional streaming model fails and a precomputed persistence field succeeds",
    "next_discriminator": "replace broad nuisance envelopes with a spatially predictive gas-flow/spiral-arm streaming model at the four (R,phi,z) points and compare out-of-sample likelihood against the frozen persistence prediction",
}
(OUTDIR / "verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")

print(res.to_string(index=False))
print(json.dumps(verdict, indent=2))
