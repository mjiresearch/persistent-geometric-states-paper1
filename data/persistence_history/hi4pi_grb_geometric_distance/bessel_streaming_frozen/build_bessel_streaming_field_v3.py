#!/usr/bin/env python3
"""Build frozen conventional BeSSeL/maser streaming field V3.

V3 is outcome-blind. It reads only the Reid+2019 maser catalog and the frozen
GRB geometry/arm labels. It must never read H I velocities/residuals, V1/V2
predicted residuals, or Persistence predictions.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord, Galactocentric, CartesianDifferential

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "reid2019_table1.dat"
TARGET_PATH = ROOT / "frozen_grb_geometry_only.csv"
OUTDIR = ROOT / "outputs_v3"
OUTDIR.mkdir(parents=True, exist_ok=True)

# Reid et al. 2019 A5 Galactic constants.
R0 = 8.15
Z_SUN = 0.0055
U_SUN = 10.6
V_SUN = 10.7
W_SUN = 7.6
THETA0 = 236.0
A2 = 0.96
A3 = 1.62

# Exact historical standard solar motion for the catalog V_LSR conversion.
STD_U = 10.3
STD_V = 15.3
STD_W = 7.7

SIGMA_INT = 7.0
MC_DRAWS = 256
MC_SEED = 20260916
BOOT_DRAWS = 2000
BOOT_SEED = 20260917
ARM_BANDWIDTHS = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0])


def urc_theta(R):
    R = np.asarray(R, dtype=float)
    lam = (A3 / 1.5) ** 5
    Ropt = A2 * R0
    rho = R / Ropt
    log_lam = np.log10(lam)
    term1 = 200.0 * lam ** 0.41
    term2 = np.sqrt(
        0.80 + 0.49 * log_lam
        + 0.75 * np.exp(-0.4 * lam) / (0.47 + 2.25 * lam ** 0.4)
    )
    term3 = (0.72 + 0.44 * log_lam) * (
        1.97 * rho ** 1.22 / (rho ** 2 + 0.61) ** 1.43
    )
    term4 = 1.6 * np.exp(-0.4 * lam) * (
        rho ** 2 / (rho ** 2 + 2.25 * lam ** 0.4)
    )
    return (term1 / term2) * np.sqrt(term3 + term4)


def gc_frame():
    # Astropy Galactocentric is right-handed with the Sun at negative x.
    # Thus +v_x at the Sun points toward the Galactic center (= +U).
    return Galactocentric(
        galcen_distance=R0 * u.kpc,
        z_sun=Z_SUN * u.kpc,
        galcen_v_sun=CartesianDifferential(
            [U_SUN, THETA0 + V_SUN, W_SUN] * (u.km / u.s)
        ),
    )


def parse_num(s, cast=float):
    s = s.strip()
    if not s:
        return np.nan
    return cast(s)


def parse_reid_table(path: Path):
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            name = line[0:13].strip()
            oname = line[15:30].strip()
            rah = parse_num(line[31:33], int)
            ram = parse_num(line[34:36], int)
            ras = parse_num(line[37:44])
            desgn = line[46:47].strip() or "+"
            ded = parse_num(line[47:49], int)
            dem = parse_num(line[50:52], int)
            des = parse_num(line[53:59])
            plx = parse_num(line[62:67])
            eplx = parse_num(line[68:73])
            pme = parse_num(line[76:82])
            epme = parse_num(line[83:87])
            pmn = parse_num(line[90:96])
            epmn = parse_num(line[97:101])
            vlsr = parse_num(line[104:108])
            evlsr = parse_num(line[109:111])
            arm = line[113:116].strip()
            if not name or not np.isfinite(plx):
                continue
            ra_deg = 15.0 * (rah + ram / 60.0 + ras / 3600.0)
            dec_abs = ded + dem / 60.0 + des / 3600.0
            dec_deg = (-1 if desgn == "-" else 1) * dec_abs
            rows.append(
                dict(
                    name=name, oname=oname, ra_deg=ra_deg, dec_deg=dec_deg,
                    plx_mas=plx, e_plx_mas=eplx, pmE=pme, e_pmE=epme,
                    pmN=pmn, e_pmN=epmn, VLSR=vlsr, e_VLSR=evlsr,
                    arm=arm,
                )
            )
        except Exception:
            continue
    return pd.DataFrame(rows)


def lsr_to_helio(ra_deg, dec_deg, vlsr):
    c = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs").galactic
    l = c.l.radian
    b = c.b.radian
    proj = (
        STD_U * np.cos(l) * np.cos(b)
        + STD_V * np.sin(l) * np.cos(b)
        + STD_W * np.sin(b)
    )
    return vlsr - proj


def phase_to_peculiar(ra_deg, dec_deg, plx, pme, pmn, vlsr):
    plx = np.asarray(plx, float)
    pme = np.asarray(pme, float)
    pmn = np.asarray(pmn, float)
    vlsr = np.asarray(vlsr, float)
    dist = (1.0 / plx) * u.kpc
    vr = lsr_to_helio(ra_deg, dec_deg, vlsr) * u.km / u.s
    c = SkyCoord(
        ra=np.broadcast_to(ra_deg, plx.shape) * u.deg,
        dec=np.broadcast_to(dec_deg, plx.shape) * u.deg,
        distance=dist,
        pm_ra_cosdec=pme * u.mas / u.yr,
        pm_dec=pmn * u.mas / u.yr,
        radial_velocity=vr,
        frame="icrs",
    )
    g = c.transform_to(gc_frame())
    x = np.asarray(g.x.to_value(u.kpc))
    y = np.asarray(g.y.to_value(u.kpc))
    z = np.asarray(g.z.to_value(u.kpc))
    vx = np.asarray(g.v_x.to_value(u.km / u.s))
    vy = np.asarray(g.v_y.to_value(u.km / u.s))
    vz = np.asarray(g.v_z.to_value(u.km / u.s))
    R = np.sqrt(x * x + y * y)

    # With the Sun at x<0: +U is inward and +V follows Galactic rotation.
    vR_out = (x * vx + y * vy) / R
    vrot = (y * vx - x * vy) / R
    Upec = -vR_out
    Vpec = vrot - urc_theta(R)
    Wpec = vz
    return x, y, z, R, Upec, Vpec, Wpec


def build_maser_sample(df):
    out = []
    for idx, r in df.iterrows():
        vals = [
            r.plx_mas, r.e_plx_mas, r.pmE, r.e_pmE,
            r.pmN, r.e_pmN, r.VLSR, r.e_VLSR,
        ]
        if not all(np.isfinite(vals)) or r.plx_mas <= 0:
            continue
        if r.e_plx_mas / r.plx_mas > 0.20:
            continue

        x, y, z, R, U, V, W = phase_to_peculiar(
            r.ra_deg, r.dec_deg,
            np.array([r.plx_mas]), np.array([r.pmE]),
            np.array([r.pmN]), np.array([r.VLSR]),
        )
        if R[0] < 4.0:
            continue

        rng = np.random.default_rng(MC_SEED + int(idx))
        p = rng.normal(r.plx_mas, r.e_plx_mas, MC_DRAWS)
        pe = rng.normal(r.pmE, r.e_pmE, MC_DRAWS)
        pn = rng.normal(r.pmN, r.e_pmN, MC_DRAWS)
        vv = rng.normal(r.VLSR, r.e_VLSR, MC_DRAWS)
        good = p > 0
        if good.sum() < MC_DRAWS * 0.95:
            continue
        _, _, _, _, Um, Vm, Wm = phase_to_peculiar(
            r.ra_deg, r.dec_deg, p[good], pe[good], pn[good], vv[good]
        )
        sU = float(np.std(Um, ddof=1))
        sV = float(np.std(Vm, ddof=1))
        sW = float(np.std(Wm, ddof=1))
        if max(sU, sV, sW) > 20.0:
            continue

        phi = float(np.arctan2(y[0], x[0]))
        out.append(
            dict(
                name=r["name"], arm=str(r.arm).strip(),
                ra_deg=r.ra_deg, dec_deg=r.dec_deg,
                plx_mas=r.plx_mas, e_plx_mas=r.e_plx_mas,
                x_kpc=x[0], y_kpc=y[0], z_kpc=z[0],
                R_kpc=R[0], phi_rad=phi,
                U_kms=U[0], V_kms=V[0], W_kms=W[0],
                e_U_kms=sU, e_V_kms=sV, e_W_kms=sW,
            )
        )
    return pd.DataFrame(out)


def target_position(l_deg, b_deg, d_kpc):
    c = SkyCoord(
        l=l_deg * u.deg, b=b_deg * u.deg,
        distance=d_kpc * u.kpc, frame="galactic"
    ).transform_to(gc_frame())
    x = float(c.x.to_value(u.kpc))
    y = float(c.y.to_value(u.kpc))
    z = float(c.z.to_value(u.kpc))
    R = float(np.hypot(x, y))
    phi = float(np.arctan2(y, x))
    return x, y, z, R, phi


def los_basis_coeffs(l_deg, b_deg, d_kpc):
    eps = 1e-4
    c0 = SkyCoord(
        l=l_deg * u.deg, b=b_deg * u.deg,
        distance=d_kpc * u.kpc, frame="galactic"
    ).transform_to(gc_frame())
    c1 = SkyCoord(
        l=l_deg * u.deg, b=b_deg * u.deg,
        distance=(d_kpc + eps) * u.kpc, frame="galactic"
    ).transform_to(gc_frame())
    p0 = np.array([
        c0.x.to_value(u.kpc), c0.y.to_value(u.kpc), c0.z.to_value(u.kpc)
    ])
    p1 = np.array([
        c1.x.to_value(u.kpc), c1.y.to_value(u.kpc), c1.z.to_value(u.kpc)
    ])
    n = p1 - p0
    n /= np.linalg.norm(n)
    x, y, _ = p0
    R = np.hypot(x, y)
    eU = np.array([-x / R, -y / R, 0.0])
    eV = np.array([y / R, -x / R, 0.0])
    eW = np.array([0.0, 0.0, 1.0])
    return float(n @ eU), float(n @ eV), float(n @ eW)


def arm_family_mask(arms: pd.Series, target_arm: str):
    a = arms.fillna("").astype(str).str.upper().str.strip()
    t = str(target_arm).upper().strip()
    if t == "OUTER":
        return a.str.startswith("OUT")
    if t == "OSC":
        return a.str.startswith("OSC")
    return a == t


def wrap_about(phi, center):
    return center + ((phi - center + np.pi) % (2 * np.pi) - np.pi)


def fit_log_spiral(arm_df: pd.DataFrame, phi_center: float):
    phi = wrap_about(arm_df.phi_rad.to_numpy(float), phi_center)
    lnR = np.log(arm_df.R_kpc.to_numpy(float))
    X = np.column_stack([np.ones_like(phi), phi])
    coef, *_ = np.linalg.lstsq(X, lnR, rcond=None)
    alpha, beta = map(float, coef)
    Rfit = np.exp(alpha + beta * phi)
    dperp = (arm_df.R_kpc.to_numpy(float) - Rfit) / np.sqrt(1.0 + beta * beta)
    med = np.median(dperp)
    mad = 1.4826 * np.median(np.abs(dperp - med))
    sigma_arm = float(max(mad, 0.25))
    return alpha, beta, sigma_arm


def arm_coordinates(R, phi, alpha, beta, phi_target):
    phi_u = wrap_about(np.asarray(phi, float), phi_target)
    Rfit = np.exp(alpha + beta * phi_u)
    Rfit_t = float(np.exp(alpha + beta * phi_target))
    if abs(beta) > 1e-6:
        s = np.sqrt(1.0 + beta * beta) / beta * (Rfit - Rfit_t)
    else:
        s = Rfit_t * (phi_u - phi_target)
    dperp = (np.asarray(R, float) - Rfit) / np.sqrt(1.0 + beta * beta)
    return np.asarray(s, float), np.asarray(dperp, float), Rfit_t


def arm_kernel_predict(arm_df, target_R, target_phi, h, comp, spiral):
    alpha, beta, sigma_arm = spiral
    s, dperp, Rfit_t = arm_coordinates(
        arm_df.R_kpc.to_numpy(float), arm_df.phi_rad.to_numpy(float),
        alpha, beta, target_phi,
    )
    sig = arm_df[f"e_{comp}_kms"].to_numpy(float)
    val = arm_df[f"{comp}_kms"].to_numpy(float)
    w = (
        np.exp(-0.5 * (s / h) ** 2)
        * np.exp(-0.5 * (dperp / sigma_arm) ** 2)
        / (sig * sig + SIGMA_INT * SIGMA_INT)
    )
    if not np.any(w > 0) or np.sum(w) <= 0:
        return dict(pred=np.nan, neff=0.0, scatter=np.nan, nearest_s=np.nan,
                    target_dperp=np.nan, sigma_arm=sigma_arm)
    pred = float(np.sum(w * val) / np.sum(w))
    neff = float((np.sum(w) ** 2) / np.sum(w * w))
    scatter = float(np.sqrt(np.sum(w * (val - pred) ** 2) / np.sum(w)))
    nearest_s = float(np.min(np.abs(s)))
    target_dperp = float((target_R - Rfit_t) / np.sqrt(1.0 + beta * beta))
    return dict(pred=pred, neff=neff, scatter=scatter, nearest_s=nearest_s,
                target_dperp=target_dperp, sigma_arm=sigma_arm)


def arm_cv_score(arm_df, h, phi_center):
    if len(arm_df) < 4:
        return np.inf, 0
    spiral = fit_log_spiral(arm_df, phi_center)
    total = 0.0
    n = 0
    for i in range(len(arm_df)):
        row = arm_df.iloc[i]
        tr = arm_df.drop(arm_df.index[i]).reset_index(drop=True)
        if len(tr) < 3:
            continue
        # Geometry-only arm fit may use the full arm locus; no velocity outcome
        # enters the spiral fit. Prediction itself excludes the held-out row.
        for comp in ("U", "V"):
            pr = arm_kernel_predict(
                tr, row.R_kpc, row.phi_rad, h, comp, spiral
            )
            if np.isfinite(pr["pred"]):
                denom = row[f"e_{comp}_kms"] ** 2 + SIGMA_INT ** 2
                total += (row[f"{comp}_kms"] - pr["pred"]) ** 2 / denom
                n += 1
    return (float(total / n) if n else np.inf), n


def vertical_design(R, phi):
    dR = np.asarray(R, float) - R0
    phi = np.asarray(phi, float)
    return np.column_stack([
        np.ones_like(dR), dR,
        np.sin(phi), np.cos(phi),
        dR * np.sin(phi), dR * np.cos(phi),
    ])


def fit_vertical(sample):
    X = vertical_design(sample.R_kpc.to_numpy(float), sample.phi_rad.to_numpy(float))
    y = sample.W_kms.to_numpy(float)
    sig = sample.e_W_kms.to_numpy(float)
    w = 1.0 / (sig * sig + SIGMA_INT * SIGMA_INT)
    sw = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    resid = y - X @ coef
    wrms = float(np.sqrt(np.sum(w * resid * resid) / np.sum(w)))
    return np.asarray(coef, float), wrms


def predict_vertical(coef, R, phi):
    X = vertical_design(np.array([R]), np.array([phi]))
    return float((X @ coef)[0])


def choose_arm_bandwidth(arm_df, target_rows):
    if len(arm_df) < 4:
        return None, [], None
    phi_center = float(np.median([
        target_position(t.l_deg, t.b_deg, t.distance_kpc)[4]
        for _, t in target_rows.iterrows()
    ]))
    spiral = fit_log_spiral(arm_df, phi_center)
    records = []
    qualified = []
    for h in ARM_BANDWIDTHS:
        cv, ncv = arm_cv_score(arm_df, float(h), phi_center)
        all_support = True
        support_rows = []
        for _, t in target_rows.iterrows():
            _, _, _, Rt, phit = target_position(t.l_deg, t.b_deg, t.distance_kpc)
            pU = arm_kernel_predict(arm_df, Rt, phit, float(h), "U", spiral)
            pV = arm_kernel_predict(arm_df, Rt, phit, float(h), "V", spiral)
            perp_limit = max(1.0, 2.0 * spiral[2])
            ok = (
                pU["neff"] >= 3.0 and pV["neff"] >= 3.0
                and pU["nearest_s"] <= 2.0 * h
                and abs(pU["target_dperp"]) <= perp_limit
            )
            all_support = all_support and ok
            support_rows.append(dict(target=t.target, ok=bool(ok),
                                     neff_U=pU["neff"], neff_V=pV["neff"],
                                     nearest_s_kpc=pU["nearest_s"],
                                     target_dperp_kpc=pU["target_dperp"],
                                     perp_limit_kpc=perp_limit))
        rec = dict(h_kpc=float(h), cv_mean_standardized_sse=cv,
                   cv_terms=int(ncv), all_targets_supported=bool(all_support),
                   support=support_rows)
        records.append(rec)
        if all_support and np.isfinite(cv):
            qualified.append(rec)
    if not qualified:
        return None, records, spiral
    best = min(qualified, key=lambda r: r["cv_mean_standardized_sse"])
    return float(best["h_kpc"]), records, spiral


def bootstrap_target(arm_df, sample, target, h, spiral, cU, cV, cW):
    rng = np.random.default_rng(BOOT_SEED + abs(hash(str(target.target))) % 100000)
    vals_in = []
    vals_w = []
    vals_tot = []
    na = len(arm_df)
    ng = len(sample)
    for _ in range(BOOT_DRAWS):
        ai = rng.integers(0, na, na)
        gi = rng.integers(0, ng, ng)
        a = arm_df.iloc[ai].reset_index(drop=True)
        g = sample.iloc[gi].reset_index(drop=True)
        _, _, _, Rt, phit = target_position(target.l_deg, target.b_deg, target.distance_kpc)
        pU = arm_kernel_predict(a, Rt, phit, h, "U", spiral)["pred"]
        pV = arm_kernel_predict(a, Rt, phit, h, "V", spiral)["pred"]
        try:
            wc, _ = fit_vertical(g)
            pW = predict_vertical(wc, Rt, phit)
        except Exception:
            continue
        if np.isfinite(pU) and np.isfinite(pV) and np.isfinite(pW):
            vin = cU * pU + cV * pV
            vw = cW * pW
            vals_in.append(vin)
            vals_w.append(vw)
            vals_tot.append(vin + vw)
    def q(x):
        if len(x) < 50:
            return [np.nan, np.nan, np.nan]
        return [float(v) for v in np.percentile(x, [16, 50, 84])]
    return q(vals_in), q(vals_w), q(vals_tot), len(vals_tot)


def main():
    # Hard guardrail: these are the only repo data files opened.
    raw = parse_reid_table(RAW_PATH)
    targets = pd.read_csv(TARGET_PATH)
    sample = build_maser_sample(raw)
    sample.to_csv(OUTDIR / "eligible_masers_peculiar_v3.csv", index=False)

    arm_counts = (
        sample.assign(arm=sample.arm.fillna("").replace("", "UNASSIGNED"))
        .groupby("arm", dropna=False).size().reset_index(name="eligible_count")
        .sort_values(["eligible_count", "arm"], ascending=[False, True])
    )
    arm_counts.to_csv(OUTDIR / "arm_counts_v3.csv", index=False)

    wcoef, w_wrms = fit_vertical(sample)
    vertical_summary = {
        "basis": ["1", "dR", "sin_phi", "cos_phi", "dR_sin_phi", "dR_cos_phi"],
        "coefficients_kms": [float(x) for x in wcoef],
        "weighted_rms_kms": w_wrms,
    }

    outputs = []
    arm_models = {}

    for target_arm, tg in targets.groupby("arm", sort=False):
        mask = arm_family_mask(sample.arm, target_arm)
        arm_df = sample.loc[mask].reset_index(drop=True)
        h, support_grid, spiral = choose_arm_bandwidth(arm_df, tg)
        model_key = str(target_arm)
        arm_models[model_key] = {
            "eligible_same_arm_masers": int(len(arm_df)),
            "catalog_designators": sorted(set(arm_df.arm.astype(str))) if len(arm_df) else [],
            "selected_h_kpc": h,
            "support_grid": support_grid,
            "spiral": None if spiral is None else {
                "alpha": float(spiral[0]), "beta": float(spiral[1]),
                "sigma_arm_kpc": float(spiral[2]),
            },
            "status": "SUPPORTED" if h is not None else "NO_INPLANE_PREDICTION",
        }

        for _, t in tg.iterrows():
            x, y, z, Rt, phit = target_position(t.l_deg, t.b_deg, t.distance_kpc)
            cU, cV, cW = los_basis_coeffs(t.l_deg, t.b_deg, t.distance_kpc)
            Wpred = predict_vertical(wcoef, Rt, phit)
            row = {
                "target": t.target, "arm": t.arm,
                "l_deg": float(t.l_deg), "b_deg": float(t.b_deg),
                "distance_kpc": float(t.distance_kpc),
                "x_kpc": x, "y_kpc": y, "z_kpc": z,
                "R_kpc": Rt, "phi_rad": phit,
                "cU": cU, "cV": cV, "cW": cW,
                "same_arm_masers": int(len(arm_df)),
                "selected_h_kpc": h,
                "W_pred_kms": Wpred,
                "delta_v_los_vertical_kms": cW * Wpred,
            }

            if h is None or spiral is None:
                row.update({
                    "status": "NO_INPLANE_PREDICTION",
                    "U_pred_kms": np.nan, "V_pred_kms": np.nan,
                    "Neff_U": np.nan, "Neff_V": np.nan,
                    "nearest_same_arm_s_kpc": np.nan,
                    "target_arm_dperp_kpc": np.nan,
                    "delta_v_los_inplane_kms": np.nan,
                    "delta_v_los_total_kms": np.nan,
                    "bootstrap_total_p16_kms": np.nan,
                    "bootstrap_total_p50_kms": np.nan,
                    "bootstrap_total_p84_kms": np.nan,
                    "bootstrap_draws_valid": 0,
                })
            else:
                pU = arm_kernel_predict(arm_df, Rt, phit, h, "U", spiral)
                pV = arm_kernel_predict(arm_df, Rt, phit, h, "V", spiral)
                inplane = cU * pU["pred"] + cV * pV["pred"]
                total = inplane + cW * Wpred
                _, _, qt, nb = bootstrap_target(
                    arm_df, sample, t, h, spiral, cU, cV, cW
                )
                row.update({
                    "status": "SUPPORTED",
                    "U_pred_kms": pU["pred"], "V_pred_kms": pV["pred"],
                    "Neff_U": pU["neff"], "Neff_V": pV["neff"],
                    "nearest_same_arm_s_kpc": pU["nearest_s"],
                    "target_arm_dperp_kpc": pU["target_dperp"],
                    "delta_v_los_inplane_kms": inplane,
                    "delta_v_los_total_kms": total,
                    "bootstrap_total_p16_kms": qt[0],
                    "bootstrap_total_p50_kms": qt[1],
                    "bootstrap_total_p84_kms": qt[2],
                    "bootstrap_draws_valid": nb,
                })
            outputs.append(row)

    outdf = pd.DataFrame(outputs)
    outdf.to_csv(OUTDIR / "frozen_bessel_streaming_predictions_v3.csv", index=False)

    summary = {
        "protocol": "CONVENTIONAL_BESSEL_STREAMING_FREEZE_V3",
        "status": "FROZEN_BEFORE_HI_COMPARISON",
        "raw_catalog_rows": int(len(raw)),
        "eligible_rows": int(len(sample)),
        "standard_lsr_solar_motion_kms": [STD_U, STD_V, STD_W],
        "A5_solar_peculiar_motion_kms": [U_SUN, V_SUN, W_SUN],
        "arm_bandwidth_candidates_kpc": [float(x) for x in ARM_BANDWIDTHS],
        "sigma_intrinsic_kms": SIGMA_INT,
        "mc_draws_per_source": MC_DRAWS,
        "bootstrap_draws": BOOT_DRAWS,
        "vertical_model": vertical_summary,
        "arm_models": arm_models,
        "guardrail": (
            "Builder read only Reid2019 table1 and frozen geometry/arm labels; "
            "no GRB H I velocity/residual, V1/V2 predicted residual, or "
            "Persistence prediction was read or used."
        ),
        "predictions": outdf.replace({np.nan: None}).to_dict(orient="records"),
    }
    (OUTDIR / "freeze_summary_v3.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "eligible_rows": len(sample),
        "arm_counts": arm_counts.to_dict(orient="records"),
        "predictions": summary["predictions"],
    }, indent=2))


if __name__ == "__main__":
    main()
