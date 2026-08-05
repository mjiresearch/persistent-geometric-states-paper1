#!/usr/bin/env python3
"""Verify the frozen stationary sample against the authoritative SPARC catalog.

This is a data-integrity step only. It does not evaluate any persistence-model
parameter or prediction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

CATALOG_URL = "https://astroweb.case.edu/SPARC/SPARC_Lelli2016c.mrt"
EXPECTED_MASTER_SHA256 = "254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_catalog(path: Path) -> dict[str, dict[str, float | int]]:
    out: dict[str, dict[str, float | int]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        # Official byte ranges (1-indexed): Galaxy 1-11, D 14-19,
        # Inc 27-30, Q 97-99.
        if len(raw) < 99:
            continue
        galaxy = raw[0:11].strip()
        if not galaxy or galaxy in {"Galaxy", "Title:", "Authors:"}:
            continue
        try:
            distance = float(raw[13:19])
            inclination = float(raw[26:30])
            quality = int(raw[96:99])
        except ValueError:
            continue
        out[galaxy] = {
            "distance_mpc": distance,
            "inclination_deg": inclination,
            "quality_flag": quality,
        }
    return out


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--master", type=Path, required=True)
    ap.add_argument("--report-csv", type=Path, required=True)
    ap.add_argument("--report-json", type=Path, required=True)
    ap.add_argument("--freeze-md", type=Path, required=True)
    args = ap.parse_args()

    catalog = parse_catalog(args.catalog)
    manifest = read_csv(args.manifest)
    master = read_csv(args.master)

    master_hash = sha256_file(args.master)
    manifest_hash = sha256_file(args.manifest)
    catalog_hash = sha256_file(args.catalog)

    master_by_gal: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in master:
        master_by_gal[row["galaxy"]].append(row)

    audit_rows: list[dict[str, str | int | float]] = []
    mismatch_count = 0

    for m in manifest:
        g = m["galaxy"]
        c = catalog.get(g)
        rows = master_by_gal.get(g, [])
        reasons: list[str] = []

        if c is None:
            reasons.append("missing_from_official_catalog")
            c = {"distance_mpc": float("nan"), "inclination_deg": float("nan"), "quality_flag": -999}

        md = float(m["distance_mpc"])
        mi = float(m["inclination_deg"])
        mq = int(float(m["quality_flag"]))
        mn = int(m["n_points"])

        if abs(md - float(c["distance_mpc"])) > 1e-12:
            reasons.append("distance_manifest_vs_catalog")
        if abs(mi - float(c["inclination_deg"])) > 1e-12:
            reasons.append("inclination_manifest_vs_catalog")
        if mq != int(c["quality_flag"]):
            reasons.append("quality_manifest_vs_catalog")
        if len(rows) != mn:
            reasons.append("point_count_master_vs_manifest")

        if rows:
            unique_distance = {float(r["distance_mpc"]) for r in rows}
            unique_inc = {float(r["inclination_deg"]) for r in rows}
            unique_q = {int(float(r["quality_flag"])) for r in rows}
            if unique_distance != {md}:
                reasons.append("distance_master_vs_manifest")
            if unique_inc != {mi}:
                reasons.append("inclination_master_vs_manifest")
            if unique_q != {mq}:
                reasons.append("quality_master_vs_manifest")

            radii = [float(r["radius_kpc"]) for r in rows]
            if abs(min(radii) - float(m["r_min_kpc"])) > 1e-12:
                reasons.append("rmin_master_vs_manifest")
            if abs(max(radii) - float(m["r_max_kpc"])) > 1e-12:
                reasons.append("rmax_master_vs_manifest")
            neg = sum(float(r["v_gas_kms"]) < 0 for r in rows)
            if neg != int(m["negative_vgas_points"]):
                reasons.append("negative_vgas_count_master_vs_manifest")
            if any(b <= a for a, b in zip(radii, radii[1:])):
                reasons.append("radial_order_not_strict")
        else:
            reasons.append("missing_from_master")

        if mq > 2:
            reasons.append("selection_quality_fail")
        if mi < 30:
            reasons.append("selection_inclination_fail")
        if mn < 5:
            reasons.append("selection_npoints_fail")

        passed = 0 if reasons else 1
        mismatch_count += 0 if passed else 1
        audit_rows.append({
            "galaxy": g,
            "official_distance_mpc": c["distance_mpc"],
            "manifest_distance_mpc": md,
            "official_inclination_deg": c["inclination_deg"],
            "manifest_inclination_deg": mi,
            "official_quality_flag": c["quality_flag"],
            "manifest_quality_flag": mq,
            "manifest_n_points": mn,
            "master_n_points": len(rows),
            "verification_pass": passed,
            "mismatch_reason": ";".join(reasons),
        })

    manifest_names = [m["galaxy"] for m in manifest]
    master_names = sorted(master_by_gal)
    duplicate_manifest_names = [g for g, n in Counter(manifest_names).items() if n > 1]
    extra_master = sorted(set(master_names) - set(manifest_names))
    missing_master = sorted(set(manifest_names) - set(master_names))

    summary = {
        "catalog_url": CATALOG_URL,
        "catalog_sha256": catalog_hash,
        "catalog_galaxies_parsed": len(catalog),
        "manifest_sha256": manifest_hash,
        "manifest_galaxies": len(manifest),
        "master_sha256": master_hash,
        "expected_master_sha256": EXPECTED_MASTER_SHA256,
        "master_hash_matches_expected": master_hash == EXPECTED_MASTER_SHA256,
        "master_galaxies": len(master_by_gal),
        "master_points": len(master),
        "galaxies_passing_full_metadata_verification": sum(int(r["verification_pass"]) for r in audit_rows),
        "galaxies_with_any_mismatch": mismatch_count,
        "duplicate_manifest_galaxy_names": duplicate_manifest_names,
        "extra_master_galaxies": extra_master,
        "missing_master_galaxies": missing_master,
        "all_checks_pass": (
            len(catalog) == 175
            and len(manifest) == 149
            and len(master_by_gal) == 149
            and len(master) == 3152
            and master_hash == EXPECTED_MASTER_SHA256
            and mismatch_count == 0
            and not duplicate_manifest_names
            and not extra_master
            and not missing_master
        ),
    }

    args.report_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.report_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(audit_rows)

    args.report_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    status = "PASS" if summary["all_checks_pass"] else "FAIL"
    freeze = f"""# Stationary observational freeze record v1\n\nStatus: **{status}**\n\nThis record freezes the observational stationary input before any fitting of `L_A` or `C_A`.\n\n## Authoritative source\n\n- SPARC galaxy catalog: `{CATALOG_URL}`\n- Catalog SHA-256: `{catalog_hash}`\n- Official catalog galaxies parsed: {len(catalog)}\n\n## Frozen products\n\n- `data/stationary/frozen/stationary_master_v1.csv`\n  - SHA-256: `{master_hash}`\n  - Galaxies: {len(master_by_gal)}\n  - Radial measurements: {len(master)}\n- `validation/stationary/stationary_sample_manifest_v1.csv`\n  - SHA-256: `{manifest_hash}`\n  - Galaxies: {len(manifest)}\n\n## Full metadata verification\n\n- Galaxies passing catalog/manifest/master checks: {summary['galaxies_passing_full_metadata_verification']} / {len(manifest)}\n- Galaxies with any mismatch: {mismatch_count}\n- Duplicate manifest names: {len(duplicate_manifest_names)}\n- Extra master galaxies: {len(extra_master)}\n- Missing master galaxies: {len(missing_master)}\n\nThe verified metadata fields are distance, inclination, and SPARC quality flag. The audit also verifies per-galaxy point counts, minimum and maximum radius, signed-gas negative-point counts, radial ordering, and the predeclared stationary selection cuts (`Q <= 2`, `i >= 30 deg`, at least 5 valid radial points).\n\nNo persistence parameter or persistence-model prediction is part of this freeze record.\n"""
    args.freeze_md.write_text(freeze, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    if not summary["all_checks_pass"]:
        raise SystemExit("Stationary metadata verification failed; freeze is not valid.")


if __name__ == "__main__":
    main()
