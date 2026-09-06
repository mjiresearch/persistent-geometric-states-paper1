#!/usr/bin/env python3
"""Build frozen Gaia-Cepheid arm-conditioned U,V streaming field V2.

Outcome-blind. Uses Cepheid-specific Gaia DR3 modeled average RVs, with VELOCE
DR1 vgamma as a fallback. Geometry/support rules are inherited unchanged from
V1/V3. This script MUST NOT read H I outcomes or Persistence predictions.
"""
from __future__ import annotations

import importlib.util
import io
import json
import math
import time
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs_v2"
OUT.mkdir(parents=True, exist_ok=True)
GAIA_CACHE = HERE / "gaia_dr3_cepheid_specific_rv_join_v2.csv"
VELOCE_A1 = HERE / "veloce_dr1_tablea1.dat"
VELOCE_A2 = HERE / "veloce_dr1_tablea2.dat"
VELOCE_URL_A1 = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/686/A177/tablea1.dat"
VELOCE_URL_A2 = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/686/A177/tablea2.dat"
TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
VELOCE_RV_ERROR_FLOOR = 1.0
MC = 256
MCSEED = 20260920
BOOT = 2000
BOOTSEED = 20260921

# Import the frozen V1 implementation for the unchanged geometry, transform,
# support, kernel, CV, and LOS-projection rules.
spec = importlib.util.spec_from_file_location("v1", HERE / "build_gaia_cepheid_streaming_v1.py")
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 100:
        return
    req = Request(url, headers={"User-Agent": "PGS-Cepheid-stream-v2/1.0"})
    with urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def gaia_cepheid_join(ids):
    if GAIA_CACHE.exists() and GAIA_CACHE.stat().st_size > 1000:
        return pd.read_csv(GAIA_CACHE)
    cols = (
        "gs.source_id,gs.ra,gs.dec,gs.pmra,gs.pmra_error,gs.pmdec,gs.pmdec_error,gs.ruwe,"
        "vc.average_rv,vc.average_rv_error,vc.num_clean_epochs_rv"
    )
    parts = []
    for j in range(0, len(ids), 100):
        chunk = ids[j:j+100]
        q = (
            f"SELECT {cols} FROM gaiadr3.gaia_source AS gs "
            "LEFT OUTER JOIN gaiadr3.vari_cepheid AS vc ON gs.source_id=vc.source_id "
            f"WHERE gs.source_id IN ({','.join(str(int(x)) for x in chunk)})"
        )
        last = None
        for attempt in range(4):
            try:
                r = requests.post(
                    TAP,
                    data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q},
                    timeout=180,
                )
                r.raise_for_status()
                d = pd.read_csv(io.StringIO(r.text))
                parts.append(d)
                last = None
                break
            except Exception as exc:
                last = exc
                time.sleep(3 * (attempt + 1))
        if last is not None:
            raise RuntimeError(f"Gaia TAP failed chunk {j}: {last}")
    out = pd.concat(parts, ignore_index=True).drop_duplicates("source_id")
    out.to_csv(GAIA_CACHE, index=False)
    return out


def parse_veloce():
    download(VELOCE_URL_A1, VELOCE_A1)
    download(VELOCE_URL_A2, VELOCE_A2)
    a1 = {}
    for line in VELOCE_A1.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            name = line[0:19].strip()
            sid_s = line[39:58].strip()
            binflag = line[73:74].strip()
            nrv_s = line[75:78].strip()
            if not sid_s:
                continue
            a1[name] = {
                "source_id": int(sid_s),
                "binflag": binflag,
                "nrv": int(nrv_s) if nrv_s else 0,
            }
        except Exception:
            continue
    out = {}
    for line in VELOCE_A2.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            name = line[0:19].strip()
            vg = float(line[37:45].strip())
            if name not in a1:
                continue
            r = a1[name]
            out[r["source_id"]] = {
                "name": name,
                "vgamma": vg,
                "binflag": r["binflag"],
                "nrv": r["nrv"],
            }
        except Exception:
            continue
    return out


def build_sample(df, veloce):
    out = []
    for i, r in df.iterrows():
        basics = [r.pmra, r.pmra_error, r.pmdec, r.pmdec_error, r.ruwe, r.e_mu]
        if not all(np.isfinite(basics)):
            continue
        if r.ruwe >= 1.4:
            continue
        frac = math.log(10.0) / 5.0 * r.e_mu
        if frac > 0.20:
            continue

        rv = None
        erv = None
        rv_source = None
        rv_epochs = None
        if (
            np.isfinite(r.average_rv)
            and np.isfinite(r.average_rv_error)
            and np.isfinite(r.num_clean_epochs_rv)
            and r.num_clean_epochs_rv >= 8
            and r.average_rv_error <= 5.0
        ):
            rv = float(r.average_rv)
            erv = float(r.average_rv_error)
            rv_source = "gaia_vari_cepheid"
            rv_epochs = int(r.num_clean_epochs_rv)
        else:
            vr = veloce.get(int(r.source_id))
            if vr is not None and vr["binflag"] == "F" and vr["nrv"] >= 8:
                rv = float(vr["vgamma"])
                erv = VELOCE_RV_ERROR_FLOOR
                rv_source = "veloce_dr1_vgamma"
                rv_epochs = int(vr["nrv"])
        if rv is None:
            continue

        x, y, z, R, U, V, W = v1.phase(
            [r.ra], [r.dec], [r.Dist], [r.pmra], [r.pmdec], [rv]
        )
        if R[0] < 4.0:
            continue

        rng = np.random.default_rng(MCSEED + int(i))
        dm = rng.normal(0.0, r.e_mu, MC)
        dd = r.Dist * 10 ** (dm / 5.0)
        pra = rng.normal(r.pmra, r.pmra_error, MC)
        pde = rng.normal(r.pmdec, r.pmdec_error, MC)
        vrr = rng.normal(rv, erv, MC)
        _, _, _, _, Um, Vm, _ = v1.phase(
            np.repeat(r.ra, MC), np.repeat(r.dec, MC), dd, pra, pde, vrr
        )
        eU = float(np.std(Um, ddof=1))
        eV = float(np.std(Vm, ddof=1))
        if max(eU, eV) > 20.0:
            continue

        out.append(
            dict(
                source_id=int(r.source_id),
                x=x[0], y=y[0], z=z[0], R=R[0],
                phi=float(np.arctan2(y[0], x[0])),
                U=U[0], V=V[0], eU=eU, eV=eV,
                Dist=r.Dist, e_mu=r.e_mu, ruwe=r.ruwe,
                rv_kms=rv, rv_error_kms=erv, rv_epochs=rv_epochs,
                rv_source=rv_source,
            )
        )
    return pd.DataFrame(out)


def bootstrap(d, h, arm, cU, cV):
    rng = np.random.default_rng(BOOTSEED)
    vals = []
    n = len(d)
    for _ in range(BOOT):
        b = d.iloc[rng.integers(0, n, n)].copy()
        b.attrs["arm"] = arm
        U, _, _, _ = v1.pred(b, h, "U")
        V, _, _, _ = v1.pred(b, h, "V")
        vals.append(cU * U + cV * V)
    return [float(x) for x in np.percentile(vals, [16, 50, 84])]


def native(o):
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    raise TypeError(type(o).__name__)


def main():
    v1.download()
    ceps = v1.parse_ceps()
    gaia = gaia_cepheid_join(ceps.source_id.tolist())
    veloce = parse_veloce()
    df = ceps.merge(gaia, on="source_id", how="inner")
    sample = build_sample(df, veloce)
    sample.to_csv(OUT / "eligible_6d_cepheids_v2.csv", index=False)

    results = []
    choices = {}
    for arm in ["Outer", "OSC"]:
        ts = [t for t in v1.TARGETS if t["arm"] == arm]
        h, grid = v1.choose(sample, arm, ts)
        choices[arm] = {"selected_h_kpc": h, "grid": grid}
        for t in ts:
            _, _, _, R, pt = v1.target_pos(t)
            d, _ = v1.members(sample, arm, pt)
            d.attrs["arm"] = arm
            cU, cV = v1.los_coeff(t)
            pars = v1.armpars(arm)
            _, _, rft = v1.armcoords(np.array([R]), np.array([pt]), pars, pt)
            dp = (R - rft) / np.sqrt(1 + pars[1] ** 2)
            source_counts = d.rv_source.value_counts().to_dict() if len(d) else {}
            row = dict(
                target=t["target"], arm=arm,
                eligible_same_arm_6d=len(d), rv_source_counts=source_counts,
                selected_h_kpc=h, R_kpc=R, phi_rad=pt,
                d_perp_kpc=dp, cU=cU, cV=cV,
            )
            if h is None:
                row.update(
                    status="NO_PREDICTION", U_pred_kms=None, V_pred_kms=None,
                    Neff_U=None, Neff_V=None, nearest_phase_kpc=None,
                    delta_v_los_inplane_kms=None,
                    bootstrap_p16=None, bootstrap_p50=None, bootstrap_p84=None,
                )
            else:
                U, nU, sU, near = v1.pred(d, h, "U")
                V, nV, sV, _ = v1.pred(d, h, "V")
                q = bootstrap(d, h, arm, cU, cV)
                row.update(
                    status="FROZEN_PREDICTION", U_pred_kms=U, V_pred_kms=V,
                    U_scatter_kms=sU, V_scatter_kms=sV,
                    Neff_U=nU, Neff_V=nV, nearest_phase_kpc=near,
                    delta_v_los_inplane_kms=cU * U + cV * V,
                    bootstrap_p16=q[0], bootstrap_p50=q[1], bootstrap_p84=q[2],
                )
            results.append(row)

    flat = []
    for r in results:
        q = dict(r)
        q["rv_source_counts"] = json.dumps(q["rv_source_counts"], sort_keys=True)
        flat.append(q)
    pd.DataFrame(flat).to_csv(OUT / "frozen_gaia_cepheid_streaming_predictions_v2.csv", index=False)

    summary = dict(
        protocol="GAIA_CEPHEID_STREAMING_AUGMENT_V2",
        status="FROZEN_BEFORE_HI_COMPARISON",
        catalog_rows=len(ceps), gaia_join_rows=len(gaia), veloce_modeled_rows=len(veloce),
        eligible_6d_rows=len(sample),
        rv_source_counts=sample.rv_source.value_counts().to_dict(),
        quality=dict(
            ruwe_lt=1.4,
            gaia_cepheid_rv_epochs_ge=8,
            gaia_cepheid_rv_error_le_kms=5.0,
            veloce_nonbinary_only=True,
            veloce_nrv_ge=8,
            veloce_rv_error_floor_kms=VELOCE_RV_ERROR_FLOOR,
            frac_distance_error_le=0.20,
            R_ge_kpc=4.0,
            propagated_UV_error_le_kms=20.0,
        ),
        choices=choices,
        guardrail=(
            "No H I spectrum, H I velocity, H I residual, GRB conventional outcome, "
            "or Persistence prediction was read."
        ),
        predictions=results,
    )
    txt = json.dumps(summary, indent=2, default=native) + "\n"
    (OUT / "freeze_summary_v2.json").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
