#!/usr/bin/env python3
"""Create the frozen stationary calibration/blind split without model residuals.

The split uses only pre-fit observational covariates. The RNG seed is derived
from the frozen master SHA-256 so it cannot be chosen after inspecting any
persistence-model result.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

MASTER_EXPECTED_SHA256 = "254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f"
N_CANDIDATES = 50000
BLIND_FRACTION = 0.30


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_sparc_catalog(path: Path) -> dict[str, dict[str, float | int | str]]:
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        p = raw.split()
        if len(p) < 18:
            continue
        try:
            galaxy = p[0]
            T = int(p[1]); D = float(p[2]); inc = float(p[5])
            lum = float(p[7]); reff = float(p[9]); sbeff = float(p[10])
            rdisk = float(p[11]); mhi = float(p[13]); vflat = float(p[15]); q = int(p[17])
        except ValueError:
            continue
        out[galaxy] = {
            "T": T, "distance_mpc": D, "inclination_deg": inc,
            "lum36_1e9_lsun": lum, "reff_kpc": reff,
            "sbeff_lsun_pc2": sbeff, "rdisk_kpc": rdisk,
            "mhi_1e9_msun": mhi, "vflat_kms": vflat, "quality_flag": q,
        }
    if len(out) != 175:
        raise ValueError(f"Expected 175 SPARC catalog galaxies; found {len(out)}")
    return out


def mean(xs):
    return sum(xs) / len(xs)


def sd(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x-m)**2 for x in xs) / (len(xs)-1))


def z_standardize(records, fields):
    centers = {}; scales = {}
    for f in fields:
        vals = [r[f] for r in records]
        centers[f] = mean(vals)
        scales[f] = sd(vals) or 1.0
    return centers, scales


def morphology_bin(T: int) -> str:
    if T <= 4:
        return "early_spiral"
    if T <= 7:
        return "intermediate_disk"
    return "late_dwarf_irregular"


def objective(records, blind_idx, numeric_fields):
    blind_set = set(blind_idx)
    b = [r for i,r in enumerate(records) if i in blind_set]
    c = [r for i,r in enumerate(records) if i not in blind_set]
    score = 0.0
    # Match both first and second moments for continuous pre-fit covariates.
    for f in numeric_fields:
        vb = [r[f] for r in b]; vc = [r[f] for r in c]
        score += (mean(vb)-mean(vc))**2
        score += 0.25 * (sd(vb)-sd(vc))**2
    # Match broad morphology and quality proportions.
    for field, cats in [("morphology_bin", ["early_spiral","intermediate_disk","late_dwarf_irregular"]),
                        ("quality_flag", [1,2])]:
        for cat in cats:
            pb = sum(r[field] == cat for r in b)/len(b)
            pc = sum(r[field] == cat for r in c)/len(c)
            score += (pb-pc)**2
    return score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--master", type=Path, required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--split-csv", type=Path, required=True)
    ap.add_argument("--summary-json", type=Path, required=True)
    ap.add_argument("--freeze-md", type=Path, required=True)
    args = ap.parse_args()

    master_hash = sha256_file(args.master)
    if master_hash != MASTER_EXPECTED_SHA256:
        raise SystemExit(f"Frozen master hash mismatch: {master_hash}")
    seed = int(master_hash[:8], 16)

    manifest = load_csv(args.manifest)
    master = load_csv(args.master)
    catalog = parse_sparc_catalog(args.catalog)
    by_g = defaultdict(list)
    for row in master:
        by_g[row["galaxy"]].append(row)

    records = []
    for m in sorted(manifest, key=lambda x: x["galaxy"]):
        g = m["galaxy"]; c = catalog[g]; rows = by_g[g]
        vmaxobs = max(float(r["v_obs_kms"]) for r in rows)
        rmax = max(float(r["radius_kpc"]) for r in rows)
        lum = float(c["lum36_1e9_lsun"])
        mhi = float(c["mhi_1e9_msun"])
        sbeff = float(c["sbeff_lsun_pc2"])
        rdisk = float(c["rdisk_kpc"])
        reff = float(c["reff_kpc"])
        vchar = float(c["vflat_kms"]) if float(c["vflat_kms"]) > 0 else vmaxobs
        size = rdisk if rdisk > 0 else reff
        records.append({
            "galaxy": g,
            "T": int(c["T"]),
            "morphology_bin": morphology_bin(int(c["T"])),
            "quality_flag": int(c["quality_flag"]),
            "log_lum36": math.log10(max(lum, 1e-6)),
            "log_sbeff": math.log10(max(sbeff, 1e-6)),
            "log_gas_richness": math.log10((mhi + 1e-4)/(lum + 1e-4)),
            "log_vchar": math.log10(max(vchar, 1e-6)),
            "log_size": math.log10(max(size, 1e-6)),
            "radial_coverage_size": rmax/max(size, 1e-6),
            "n_points": int(float(m["n_points"])),
            "inclination_deg": float(m["inclination_deg"]),
        })

    numeric = ["log_lum36","log_sbeff","log_gas_richness","log_vchar","log_size","radial_coverage_size","n_points","inclination_deg"]
    centers, scales = z_standardize(records, numeric)
    for r in records:
        for f in numeric:
            r[f] = (r[f]-centers[f])/scales[f]

    n = len(records)
    n_blind = round(n*BLIND_FRACTION)
    rng = random.Random(seed)
    best = None; best_score = float("inf")
    universe = list(range(n))
    for _ in range(N_CANDIDATES):
        blind = tuple(sorted(rng.sample(universe, n_blind)))
        s = objective(records, blind, numeric)
        if s < best_score:
            best_score = s; best = blind
    assert best is not None
    blind_set = set(best)

    # Recreate unstandardized reporting covariates.
    output_rows = []
    for i,r in enumerate(records):
        raw = {f: r[f]*scales[f] + centers[f] for f in numeric}
        output_rows.append({
            "galaxy": r["galaxy"],
            "stationary_role": "blind" if i in blind_set else "calibration",
            "seed": seed,
            "master_sha256": master_hash,
            "T": r["T"],
            "morphology_bin": r["morphology_bin"],
            "quality_flag": r["quality_flag"],
            "log10_lum36_1e9_lsun": f"{raw['log_lum36']:.12g}",
            "log10_sbeff_lsun_pc2": f"{raw['log_sbeff']:.12g}",
            "log10_mhi_to_lum36": f"{raw['log_gas_richness']:.12g}",
            "log10_vchar_kms": f"{raw['log_vchar']:.12g}",
            "log10_size_kpc": f"{raw['log_size']:.12g}",
            "radial_coverage_over_size": f"{raw['radial_coverage_size']:.12g}",
            "n_points": int(round(raw["n_points"])),
            "inclination_deg": f"{raw['inclination_deg']:.12g}",
        })

    args.split_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.split_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
        w.writeheader(); w.writerows(output_rows)

    summary = {
        "status": "FROZEN",
        "n_total": n,
        "n_calibration": n-n_blind,
        "n_blind": n_blind,
        "blind_fraction": n_blind/n,
        "rng_seed": seed,
        "seed_derivation": "integer value of first 8 hex characters of stationary_master_v1.csv SHA-256",
        "master_sha256": master_hash,
        "manifest_sha256": sha256_file(args.manifest),
        "catalog_sha256": sha256_file(args.catalog),
        "candidate_splits_evaluated": N_CANDIDATES,
        "balance_objective": best_score,
        "selection_uses_model_results": False,
        "numeric_balance_covariates": numeric,
        "categorical_balance_covariates": ["morphology_bin","quality_flag"],
    }
    args.summary_json.write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")

    freeze = f"""# Stationary calibration/blind split freeze v1

**Status:** FROZEN BEFORE PERSISTENCE FITTING

The 149-galaxy stationary sample is divided into **{n-n_blind} calibration** and
**{n_blind} blind-validation** galaxies ({n_blind/n:.3%} blind).

The split uses no rotation-curve residuals and no values or trial fits of
`L_A`, `C_A`, or `tau_A`.

## Deterministic seed

The random seed is `{seed}`, obtained from the first eight hexadecimal
characters of the already-frozen stationary-master SHA-256
`{master_hash}`. This prevents discretionary seed selection after model results
are known.

## Balance procedure

Exactly {N_CANDIDATES:,} candidate 70/30 random splits are generated from that
fixed pseudo-random sequence. The retained split minimizes a predeclared
covariate-balance objective using only independent observational/sample
quantities: luminosity, effective surface brightness, HI-to-3.6um luminosity
ratio, characteristic rotation speed, characteristic disk size, radial
coverage relative to size, radial-point count, inclination, broad morphology,
and SPARC quality flag.

The objective matches calibration and blind first moments, partially matches
second moments, and matches broad categorical proportions. It never evaluates
a persistence prediction.

## Frozen file

`validation/stationary/stationary_split_v1.csv`

Any later change to membership requires a new versioned split and cannot replace
this file silently. The original blind result must remain reportable.
"""
    args.freeze_md.write_text(freeze, encoding="utf-8")


if __name__ == "__main__":
    main()
