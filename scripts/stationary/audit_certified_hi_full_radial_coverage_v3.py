#!/usr/bin/env python3
"""Audit radial support of the 34-profile common-normalized H I set.

Geometry/support audit only. No rotation velocity, residual, persistence
quantity, or blind outcome is evaluated.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


MASTER = Path("data/stationary/frozen/stationary_master_v1.csv")
MAN = Path("data/stationary/source_reconstruction/certified_hi_normalization_manifest_v3.csv")
TAB = Path("data/stationary/source_reconstruction/certified_hi_common_tabulated_v5.csv")
ANA = Path("data/stationary/source_reconstruction/certified_hi_common_analytic_v5.csv")
OUTCSV = Path("validation/stationary/certified_hi_full_radial_coverage_v3.csv")
OUTJSON = Path("validation/stationary/certified_hi_full_radial_coverage_v3_summary.json")
CHECKPOINT = Path("validation/stationary/CHECKPOINT_CERTIFIED_HI_34_NORMALIZATION_V1.md")
FEASTS_PROFILES = ("NGC2903", "NGC4559", "NGC5033")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    master = read_csv(MASTER)
    manifest = {row["galaxy"]: row for row in read_csv(MAN)}
    rotation_radii: dict[str, list[float]] = defaultdict(list)
    for row in master:
        rotation_radii[row["galaxy"]].append(float(row["radius_kpc"]))
    tabulated: dict[str, list[float]] = defaultdict(list)
    for row in read_csv(TAB):
        tabulated[row["galaxy"]].append(float(row["radius_kpc_frozen"]))
    analytic = {row["galaxy"]: row for row in read_csv(ANA)}
    galaxies = sorted(set(tabulated) | set(analytic))
    if set(galaxies) != set(manifest):
        raise RuntimeError(
            f"normalized/manifest galaxy mismatch: normalized={len(galaxies)} "
            f"manifest={len(manifest)}"
        )
    if len(galaxies) != 34:
        raise RuntimeError(f"expected 34 certified galaxies, got {len(galaxies)}")

    rows = []
    for galaxy in galaxies:
        radii = sorted(rotation_radii[galaxy])
        rotation_min, rotation_max = min(radii), max(radii)
        role = manifest[galaxy]["stationary_role"]
        if galaxy in analytic:
            rows.append(
                {
                    "galaxy": galaxy,
                    "stationary_role": role,
                    "profile_kind": "analytic",
                    "n_rotation_points": len(radii),
                    "rotation_rmin_kpc": f"{rotation_min:.12g}",
                    "rotation_rmax_kpc": f"{rotation_max:.12g}",
                    "profile_rmin_kpc": "0",
                    "profile_rmax_kpc": "analytic",
                    "inner_gap_kpc": "0",
                    "outer_gap_kpc": "0",
                    "inner_continuation_required": "0",
                    "outer_continuation_required": "0",
                    "coverage_class": "analytic_defined_on_rotation_grid",
                }
            )
            continue
        profile_radii = sorted(tabulated[galaxy])
        profile_min, profile_max = min(profile_radii), max(profile_radii)
        inner_gap = max(0, profile_min - rotation_min)
        outer_gap = max(0, rotation_max - profile_max)
        needs_inner = inner_gap > 1e-12
        needs_outer = outer_gap > 1e-12
        coverage_class = (
            "inner_and_outer_continuation"
            if needs_inner and needs_outer
            else "inner_continuation_only"
            if needs_inner
            else "outer_continuation_only"
            if needs_outer
            else "full_measured_support"
        )
        rows.append(
            {
                "galaxy": galaxy,
                "stationary_role": role,
                "profile_kind": "tabulated",
                "n_rotation_points": len(radii),
                "rotation_rmin_kpc": f"{rotation_min:.12g}",
                "rotation_rmax_kpc": f"{rotation_max:.12g}",
                "profile_rmin_kpc": f"{profile_min:.12g}",
                "profile_rmax_kpc": f"{profile_max:.12g}",
                "inner_gap_kpc": f"{inner_gap:.12g}",
                "outer_gap_kpc": f"{outer_gap:.12g}",
                "inner_continuation_required": "1" if needs_inner else "0",
                "outer_continuation_required": "1" if needs_outer else "0",
                "coverage_class": coverage_class,
            }
        )

    OUTCSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTCSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    tabulated_rows = [row for row in rows if row["profile_kind"] == "tabulated"]
    inner = [row for row in tabulated_rows if row["inner_continuation_required"] == "1"]
    outer = [row for row in tabulated_rows if row["outer_continuation_required"] == "1"]
    classes = sorted({row["coverage_class"] for row in rows})
    role_counts = {
        "calibration": sum(row["stationary_role"] == "calibration" for row in rows),
        "blind": sum(row["stationary_role"] == "blind" for row in rows),
    }
    if role_counts != {"calibration": 25, "blind": 9}:
        raise RuntimeError(f"unexpected role counts: {role_counts}")
    feasts_rows = [next(row for row in rows if row["galaxy"] == galaxy) for galaxy in FEASTS_PROFILES]
    ngc5033 = next(row for row in feasts_rows if row["galaxy"] == "NGC5033")
    if ngc5033["coverage_class"] != "inner_continuation_only":
        raise RuntimeError(f"unexpected NGC5033 coverage: {ngc5033}")

    summary = {
        "status": "CERTIFIED_HI_FULL_RADIAL_COVERAGE_V3_AUDITED",
        "n_profiles": len(rows),
        "n_tabulated": len(tabulated_rows),
        "n_analytic": len(analytic),
        "role_counts": role_counts,
        "coverage_class_counts": {
            coverage_class: sum(row["coverage_class"] == coverage_class for row in rows)
            for coverage_class in classes
        },
        "n_tabulated_requiring_inner_continuation": len(inner),
        "n_tabulated_requiring_outer_continuation": len(outer),
        "inner_continuation_galaxies": [row["galaxy"] for row in inner],
        "outer_continuation_galaxies": [row["galaxy"] for row in outer],
        "feasts_profiles": feasts_rows,
        "new_v3_profile": ngc5033,
        "max_inner_gap_kpc": max([float(row["inner_gap_kpc"]) for row in tabulated_rows] or [0]),
        "max_outer_gap_kpc": max([float(row["outer_gap_kpc"]) for row in tabulated_rows] or [0]),
        "boundary": (
            "Radial-support geometry only. No rotation velocity, residual, L_A, C_A, tau_A, "
            "persistence prediction, or blind outcome evaluated."
        ),
    }
    OUTJSON.write_text(json.dumps(summary, indent=2) + "\n")
    CHECKPOINT.write_text(
        "# Certified stationary H I normalization checkpoint — 34 profiles v1\n\n"
        "- Certified common-normalized set: **34 galaxies = 25 calibration + 9 blind**.\n"
        "- NGC5033 entered only after the locked FEASTS 2025 blind source-acquisition protocol "
        "passed all source-only QC checks.\n"
        "- NGC5033 contributes **50** exact machine-readable raw-H I radial rows.\n"
        "- Deterministic normalization: `Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw`; angular "
        "radii were already mapped to the frozen distance; no inclination/amplitude rescale.\n"
        f"- NGC5033 radial support: {ngc5033['profile_rmin_kpc']}–{ngc5033['profile_rmax_kpc']} "
        f"kpc versus the frozen rotation grid {ngc5033['rotation_rmin_kpc']}–"
        f"{ngc5033['rotation_rmax_kpc']} kpc; **inner continuation only** remains required.\n"
        "- No continuation has been applied at this stage.\n"
        "- Blind firewall preserved: no rotation residual, persistence prediction, model "
        "preference, `L_A`, `C_A`, or `tau_A` was inspected.\n"
        "- `L_A` and `C_A` remain locked.\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
