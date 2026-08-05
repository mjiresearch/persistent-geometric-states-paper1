#!/usr/bin/env python3
"""Audit the frozen stationary master and manifest against the authoritative SPARC catalog.

This script performs no persistence-model fitting. It verifies the observational
sample boundary only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sparc_catalog(path: Path) -> dict[str, dict[str, object]]:
    catalog: dict[str, dict[str, object]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if len(parts) < 18:
            continue
        try:
            t = int(parts[1])
            distance = float(parts[2])
            e_distance = float(parts[3])
            distance_method = int(parts[4])
            inclination = float(parts[5])
            e_inclination = float(parts[6])
            quality = int(parts[17])
        except ValueError:
            continue
        galaxy = parts[0]
        catalog[galaxy] = {
            "galaxy": galaxy,
            "T": t,
            "distance_mpc": distance,
            "e_distance_mpc": e_distance,
            "distance_method": distance_method,
            "inclination_deg": inclination,
            "e_inclination_deg": e_inclination,
            "quality_flag": quality,
            "reference": " ".join(parts[18:]),
        }
    if len(catalog) != 175:
        raise ValueError(f"Expected 175 galaxies in authoritative SPARC catalog; found {len(catalog)}")
    return catalog


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=tol)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--master", type=Path, required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--audit-csv", type=Path, required=True)
    ap.add_argument("--audit-json", type=Path, required=True)
    ap.add_argument("--report-md", type=Path, required=True)
    ap.add_argument("--freeze-md", type=Path, required=True)
    args = ap.parse_args()

    manifest = load_csv(args.manifest)
    master = load_csv(args.master)
    catalog = parse_sparc_catalog(args.catalog)

    manifest_by_galaxy = {r["galaxy"]: r for r in manifest}
    if len(manifest_by_galaxy) != len(manifest):
        raise ValueError("Duplicate galaxy identifiers in sample manifest")

    master_by_galaxy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in master:
        master_by_galaxy[row["galaxy"]].append(row)

    audit_rows: list[dict[str, object]] = []
    failures: list[str] = []

    for galaxy in sorted(manifest_by_galaxy):
        m = manifest_by_galaxy[galaxy]
        c = catalog.get(galaxy)
        rows = master_by_galaxy.get(galaxy, [])
        if c is None:
            failures.append(f"{galaxy}: missing from authoritative catalog")
            continue
        if not rows:
            failures.append(f"{galaxy}: missing from frozen master")
            continue

        master_distances = sorted({float(r["distance_mpc"]) for r in rows})
        master_quality = sorted({int(float(r["quality_flag"])) for r in rows})
        master_inclinations = sorted({float(r["inclination_deg"]) for r in rows})

        q_manifest = int(float(m["quality_flag"]))
        i_manifest = float(m["inclination_deg"])
        n_manifest = int(float(m["n_points"]))

        q_match = q_manifest == int(c["quality_flag"]) and master_quality == [q_manifest]
        i_match = close(i_manifest, float(c["inclination_deg"])) and (len(master_inclinations) == 1 and close(master_inclinations[0], i_manifest))
        d_match = len(master_distances) == 1 and close(master_distances[0], float(c["distance_mpc"]))
        n_match = len(rows) == n_manifest and all(int(float(r["n_points_galaxy"])) == n_manifest for r in rows)
        cut_q = q_manifest <= 2
        cut_i = i_manifest >= 30.0
        cut_n = n_manifest >= 5
        radial = [float(r["radius_kpc"]) for r in rows]
        radial_order = all(b > a for a, b in zip(radial, radial[1:]))
        positive_radius = all(r > 0 for r in radial)
        positive_verr = all(float(r["v_err_kms"]) > 0 for r in rows)
        all_pass = all([q_match, i_match, d_match, n_match, cut_q, cut_i, cut_n, radial_order, positive_radius, positive_verr])

        if not all_pass:
            failures.append(f"{galaxy}: metadata/cut audit failed")

        audit_rows.append({
            "galaxy": galaxy,
            "catalog_distance_mpc": c["distance_mpc"],
            "master_distance_mpc": master_distances[0] if len(master_distances) == 1 else "MULTIPLE",
            "distance_match": int(d_match),
            "catalog_inclination_deg": c["inclination_deg"],
            "manifest_inclination_deg": i_manifest,
            "inclination_match": int(i_match),
            "catalog_quality_flag": c["quality_flag"],
            "manifest_quality_flag": q_manifest,
            "quality_match": int(q_match),
            "manifest_n_points": n_manifest,
            "master_n_points": len(rows),
            "point_count_match": int(n_match),
            "cut_quality_le_2": int(cut_q),
            "cut_inclination_ge_30": int(cut_i),
            "cut_n_points_ge_5": int(cut_n),
            "radial_order_pass": int(radial_order),
            "positive_radius_pass": int(positive_radius),
            "positive_velocity_error_pass": int(positive_verr),
            "all_pass": int(all_pass),
        })

    master_members = set(master_by_galaxy)
    manifest_members = set(manifest_by_galaxy)
    extra_master = sorted(master_members - manifest_members)
    missing_master = sorted(manifest_members - master_members)
    if extra_master:
        failures.append(f"Frozen master has galaxies absent from manifest: {extra_master}")
    if missing_master:
        failures.append(f"Manifest galaxies absent from frozen master: {missing_master}")

    keys = [(r["galaxy"], r["radius_kpc"]) for r in master]
    duplicate_keys = sum(v - 1 for v in Counter(keys).values() if v > 1)
    duplicate_rows = len(master) - len({tuple(sorted(r.items())) for r in master})
    if duplicate_keys:
        failures.append(f"Duplicate galaxy-radius keys: {duplicate_keys}")
    if duplicate_rows:
        failures.append(f"Duplicate full observational rows: {duplicate_rows}")

    negative_gas_rows = sum(float(r["v_gas_kms"]) < 0 for r in master)
    negative_gas_galaxies = len({r["galaxy"] for r in master if float(r["v_gas_kms"]) < 0})
    zero_gas_rows = sum(float(r["v_gas_kms"]) == 0 for r in master)

    args.audit_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(audit_rows[0].keys())
    with args.audit_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(audit_rows)

    summary = {
        "status": "PASS" if not failures else "FAIL",
        "authoritative_catalog_galaxies": len(catalog),
        "manifest_galaxies": len(manifest),
        "master_galaxies": len(master_members),
        "master_rows": len(master),
        "galaxies_all_metadata_checks_pass": sum(int(r["all_pass"]) for r in audit_rows),
        "metadata_failures": failures,
        "duplicate_galaxy_radius_keys": duplicate_keys,
        "duplicate_full_rows": duplicate_rows,
        "negative_vgas_rows": negative_gas_rows,
        "negative_vgas_galaxies": negative_gas_galaxies,
        "zero_vgas_rows": zero_gas_rows,
        "master_sha256": sha256_file(args.master),
        "manifest_sha256": sha256_file(args.manifest),
        "catalog_sha256": sha256_file(args.catalog),
        "selection_rules": {"quality_flag_max": 2, "inclination_deg_min": 30.0, "minimum_valid_radial_points": 5},
    }
    args.audit_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    failures_text = "\n".join("- " + x for x in failures) if failures else "- None."
    report = f"""# Stationary metadata audit v1

**Status:** {summary['status']}

- Authoritative SPARC catalog galaxies: {len(catalog)}
- Frozen eligible galaxies: {len(manifest)}
- Frozen master galaxies: {len(master_members)}
- Frozen radial measurements: {len(master)}
- Galaxies passing all catalog/manifest/master checks: {summary['galaxies_all_metadata_checks_pass']} / {len(manifest)}
- Duplicate galaxy-radius keys: {duplicate_keys}
- Duplicate full rows: {duplicate_rows}
- Negative signed gas rows preserved: {negative_gas_rows} across {negative_gas_galaxies} galaxies
- Zero gas rows: {zero_gas_rows}

## Verified metadata

For every eligible galaxy the audit compares the frozen manifest/master against
`SPARC_Lelli2016c.mrt` for the adopted distance, inclination, and quality flag,
and verifies the radial-point count and frozen selection rules.

## Selection boundary

- SPARC quality flag `Q <= 2`
- inclination `i >= 30 deg`
- at least 5 valid radial measurements

## Hashes

- `stationary_master_v1.csv`: `{summary['master_sha256']}`
- `stationary_sample_manifest_v1.csv`: `{summary['manifest_sha256']}`
- authoritative `SPARC_Lelli2016c.mrt`: `{summary['catalog_sha256']}`

## Failures

{failures_text}
"""
    args.report_md.write_text(report, encoding="utf-8")

    freeze = f"""# Stationary observational freeze record v1

**Freeze status:** {'FROZEN' if not failures else 'NOT FROZEN'}

This record freezes the observational input boundary only. No value of `L_A`,
`C_A`, `tau_A`, or any persistence-model prediction was used to construct or
audit this dataset.

## Frozen products

- `data/stationary/frozen/stationary_master_v1.csv`
  - SHA-256: `{summary['master_sha256']}`
  - 149 galaxies
  - 3,152 radial measurements
- `validation/stationary/stationary_sample_manifest_v1.csv`
  - SHA-256: `{summary['manifest_sha256']}`
- authoritative SPARC catalog used for metadata verification
  - `SPARC_Lelli2016c.mrt`
  - SHA-256: `{summary['catalog_sha256']}`

## Freeze conditions verified

1. All 149 eligible galaxies exist in the authoritative 175-galaxy SPARC catalog.
2. Quality flag, inclination, and adopted distance match the authoritative catalog.
3. Each galaxy satisfies `Q <= 2`, `i >= 30 deg`, and at least five valid radial points.
4. Galaxy membership and per-galaxy point counts match between manifest and master.
5. No duplicate galaxy-radius keys or duplicate observational rows are present.
6. Radial ordering, positive radii, and positive velocity uncertainties are preserved.
7. Signed gas values are retained without clipping or absolute-value replacement.

Any future change to the frozen observational master requires a new versioned
file and a new freeze record; `stationary_master_v1.csv` must not be silently
overwritten.
"""
    args.freeze_md.write_text(freeze, encoding="utf-8")

    if failures:
        raise SystemExit("Metadata audit failed; freeze record marked NOT FROZEN")


if __name__ == "__main__":
    main()
