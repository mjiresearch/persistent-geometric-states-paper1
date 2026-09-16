#!/usr/bin/env python3
"""Independently validate stationary certified source-profile freeze v1."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path


MASTER = Path("data/stationary/frozen/stationary_master_v1.csv")
MANIFEST = Path(
    "data/stationary/source_reconstruction/certified_hi_normalization_manifest_v3.csv"
)
TABULATED = Path(
    "data/stationary/source_reconstruction/certified_hi_common_tabulated_v5.csv"
)
ANALYTIC = Path(
    "data/stationary/source_reconstruction/certified_hi_common_analytic_v5.csv"
)
COVERAGE = Path("validation/stationary/certified_hi_full_radial_coverage_v3.csv")
HI = Path("data/stationary/processed/stationary_hi_profiles_v1.csv")
SOURCE = Path("data/stationary/processed/stationary_source_profiles_v1.csv")
SUMMARY = Path(
    "validation/stationary/stationary_source_profile_freeze_v1_summary.json"
)
FREEZE = Path("validation/stationary/STATIONARY_SOURCE_PROFILE_FREEZE_V1.md")
OUT = Path(
    "validation/stationary/stationary_source_profile_freeze_v1_validation.json"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analytic_value(row: dict[str, str], radius: float) -> float:
    total = 0.0
    for component in range(1, int(row["n_components"]) + 1):
        sigma0 = float(row[f"sigma0{component}_neutral_1p33_msun_pc2"])
        center = float(row[f"a{component}_kpc_frozen"])
        scale = float(row[f"r0{component}_kpc_frozen"])
        total += sigma0 * math.exp(-((radius - center) ** 2) / (2 * scale**2))
    return total


def main() -> None:
    required = [MASTER, MANIFEST, TABULATED, ANALYTIC, COVERAGE, HI, SOURCE, SUMMARY, FREEZE]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing validation inputs: {missing}")

    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "pass": bool(passed), "detail": detail})

    manifest_rows = read_csv(MANIFEST)
    manifest = {row["galaxy"]: row for row in manifest_rows}
    hi_rows = read_csv(HI)
    source_rows = read_csv(SOURCE)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    coverage = {row["galaxy"]: row for row in read_csv(COVERAGE)}
    analytic = {row["galaxy"]: row for row in read_csv(ANALYTIC)}

    master_keys: set[tuple[str, str, str]] = set()
    master_basis: dict[tuple[str, str], tuple[float, float]] = {}
    master_counts: Counter[str] = Counter()
    for row in read_csv(MASTER):
        if row["galaxy"] not in manifest:
            continue
        key = (row["galaxy"], row["galaxy_point_index"], row["radius_kpc"])
        master_keys.add(key)
        master_basis[(row["galaxy"], row["galaxy_point_index"])] = (
            float(row["sb_disk_lsun_pc2"]),
            float(row["sb_bulge_lsun_pc2"]),
        )
        master_counts[row["galaxy"]] += 1

    hi_keys = {
        (row["galaxy"], row["galaxy_point_index"], row["radius_kpc"])
        for row in hi_rows
    }
    source_keys = {
        (row["galaxy"], row["galaxy_point_index"], row["radius_kpc"])
        for row in source_rows
    }
    check(
        "exact_frozen_grid_keys",
        hi_keys == source_keys == master_keys and len(hi_keys) == len(hi_rows) == len(source_rows),
        f"master={len(master_keys)} hi={len(hi_rows)} source={len(source_rows)}",
    )

    profile_roles = Counter(row["stationary_role"] for row in manifest_rows)
    check(
        "exact_profile_membership_and_roles",
        len(manifest) == 34
        and profile_roles == Counter({"calibration": 25, "blind": 9})
        and {row["galaxy"] for row in hi_rows} == set(manifest),
        f"profiles={len(manifest)} roles={dict(profile_roles)}",
    )
    check(
        "frozen_grid_row_counts_match_master",
        all(
            sum(row["galaxy"] == galaxy for row in hi_rows) == count
            for galaxy, count in master_counts.items()
        ),
    )
    check(
        "finite_nonnegative_hi",
        all(
            math.isfinite(float(row["sigma_neutral_1p33_msun_pc2"]))
            and float(row["sigma_neutral_1p33_msun_pc2"]) >= 0
            for row in hi_rows
        ),
    )

    hi_by_key = {
        (row["galaxy"], row["galaxy_point_index"]): row for row in hi_rows
    }
    source_matches = True
    source_basis_matches = True
    for row in source_rows:
        key = (row["galaxy"], row["galaxy_point_index"])
        hi_row = hi_by_key[key]
        source_matches &= math.isclose(
            float(row["sigma_neutral_gas_1p33_msun_pc2"]),
            float(hi_row["sigma_neutral_1p33_msun_pc2"]),
            rel_tol=0,
            abs_tol=1e-11,
        )
        disk, bulge = master_basis[key]
        source_basis_matches &= math.isclose(
            float(row["sigma_disk_per_unit_upsilon_msun_pc2"]),
            disk,
            rel_tol=0,
            abs_tol=1e-11,
        ) and math.isclose(
            float(row["sigma_bulge_per_unit_upsilon_msun_pc2"]),
            bulge,
            rel_tol=0,
            abs_tol=1e-11,
        )
    check("source_gas_matches_hi_freeze", source_matches)
    check("stellar_unit_ml_basis_matches_master", source_basis_matches)
    check(
        "vobs_guard",
        all(row["vobs_used_as_source_current"] == "0" for row in source_rows)
        and "v_obs_kms" not in source_rows[0]
        and "v_obs_kms" not in hi_rows[0],
    )

    tabulated_by_galaxy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(TABULATED):
        tabulated_by_galaxy[row["galaxy"]].append(row)
    for rows in tabulated_by_galaxy.values():
        rows.sort(key=lambda row: int(row["sample_index"]))

    numerical_values_match = True
    method_semantics_match = True
    for row in hi_rows:
        galaxy = row["galaxy"]
        radius = float(row["radius_kpc"])
        value = float(row["sigma_neutral_1p33_msun_pc2"])
        method = row["evaluation_method"]
        if galaxy in analytic:
            expected = analytic_value(analytic[galaxy], radius)
            numerical_values_match &= math.isclose(value, expected, rel_tol=2e-11, abs_tol=1e-12)
            method_semantics_match &= method == "analytic_offcentered_gaussian_sum"
            continue
        source = tabulated_by_galaxy[galaxy]
        radii = [float(item["radius_kpc_frozen"]) for item in source]
        sigma = [float(item["sigma_neutral_1p33_msun_pc2"]) for item in source]
        lower = int(row["source_bracket_lower_index"])
        upper = int(row["source_bracket_upper_index"])
        if method == "inner_constant":
            expected = sigma[0]
            semantics = radius < radii[0] and lower == upper == 0
        elif method == "outer_zero":
            expected = 0.0
            semantics = radius > radii[-1] and lower == upper == len(radii) - 1
        elif method == "measured_node":
            expected = sigma[lower]
            semantics = lower == upper and radius == radii[lower]
        elif method == "piecewise_linear":
            fraction = (radius - radii[lower]) / (radii[upper] - radii[lower])
            expected = sigma[lower] + fraction * (sigma[upper] - sigma[lower])
            semantics = upper == lower + 1 and radii[lower] < radius < radii[upper]
        else:
            expected = math.nan
            semantics = False
        numerical_values_match &= math.isclose(value, expected, rel_tol=2e-11, abs_tol=1e-12)
        method_semantics_match &= semantics
    check("independent_profile_value_recalculation", numerical_values_match)
    check("evaluation_method_semantics", method_semantics_match)

    methods_by_galaxy: dict[str, set[str]] = defaultdict(set)
    for row in hi_rows:
        methods_by_galaxy[row["galaxy"]].add(row["evaluation_method"])
    coverage_matches = True
    for galaxy, row in coverage.items():
        methods = methods_by_galaxy[galaxy]
        if row["profile_kind"] == "analytic":
            coverage_matches &= methods == {"analytic_offcentered_gaussian_sum"}
        else:
            coverage_matches &= (
                ("inner_constant" in methods)
                == (row["inner_continuation_required"] == "1")
            ) and (
                ("outer_zero" in methods)
                == (row["outer_continuation_required"] == "1")
            )
    check("coverage_audit_matches_applied_methods", coverage_matches)

    method_counts = Counter(row["evaluation_method"] for row in hi_rows)
    check(
        "summary_counts_match_products",
        summary["n_profiles"] == 34
        and summary["n_grid_rows"] == len(hi_rows)
        and summary["profile_role_counts"] == {"calibration": 25, "blind": 9}
        and summary["evaluation_method_counts"]
        == {method: method_counts[method] for method in sorted(method_counts)},
    )
    output_hashes = summary["output_sha256"]
    check(
        "summary_output_hashes_match",
        output_hashes[str(HI)] == sha256_file(HI)
        and output_hashes[str(SOURCE)] == sha256_file(SOURCE),
    )
    freeze_text = FREEZE.read_text(encoding="utf-8")
    check(
        "freeze_record_binds_output_hashes",
        output_hashes[str(HI)] in freeze_text and output_hashes[str(SOURCE)] in freeze_text,
    )
    check(
        "global_gate_remains_locked",
        summary["global_fit_gate_unlocked"] is False
        and summary["source_current_evaluated"] is False
        and summary["blind_outcome_inspected"] is False
        and "GLOBAL 149-GALAXY SOURCE GATE REMAINS LOCKED" in freeze_text,
    )

    result = {
        "status": (
            "STATIONARY_SOURCE_PROFILE_FREEZE_V1_VALIDATION_PASS"
            if all(bool(item["pass"]) for item in checks)
            else "STATIONARY_SOURCE_PROFILE_FREEZE_V1_VALIDATION_FAIL_CLOSED"
        ),
        "n_checks": len(checks),
        "n_pass": sum(bool(item["pass"]) for item in checks),
        "all_pass": all(bool(item["pass"]) for item in checks),
        "n_profiles": len(manifest),
        "n_grid_rows": len(hi_rows),
        "profile_role_counts": {
            "calibration": profile_roles["calibration"],
            "blind": profile_roles["blind"],
        },
        "evaluation_method_counts": {
            method: method_counts[method] for method in sorted(method_counts)
        },
        "checks": checks,
        "boundary": (
            "Independent source-construction validation only. No velocity value, residual, "
            "persistence prediction, model preference, L_A, C_A, tau_A, or blind outcome "
            "evaluated."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
