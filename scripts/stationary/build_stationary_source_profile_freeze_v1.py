#!/usr/bin/env python3
"""Build the frozen 34-galaxy stationary H I/source-profile subset v1.

The build uses only frozen radii, stellar surface-density bases, certified H I
profiles, and predeclared source-construction rules. It never accesses an
observed velocity value and does not evaluate a persistence quantity or blind
outcome.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

from stationary_hi_profile_rule_v1 import evaluate_tabulated_profile


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
NORMALIZATION_POLICY = Path(
    "validation/stationary/STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md"
)
MISSING_VALUE_POLICY = Path(
    "validation/stationary/STATIONARY_HI_MISSING_VALUE_POLICY_V1.md"
)
INTERPOLATION_POLICY = Path(
    "validation/stationary/STATIONARY_HI_INTERPOLATION_CONTINUATION_POLICY_V1.md"
)
MOCK_VALIDATION = Path(
    "validation/stationary/hi_interpolation_rule_v1_mock_validation.json"
)

HI_OUT = Path("data/stationary/processed/stationary_hi_profiles_v1.csv")
SOURCE_OUT = Path("data/stationary/processed/stationary_source_profiles_v1.csv")
SUMMARY_OUT = Path(
    "validation/stationary/stationary_source_profile_freeze_v1_summary.json"
)
FREEZE_OUT = Path("validation/stationary/STATIONARY_SOURCE_PROFILE_FREEZE_V1.md")

EXPECTED_PROFILE_ROLES = {"calibration": 25, "blind": 9}
COMMON_CONVENTION = "Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw"
INTERPOLATION_RULE_ID = "stationary_hi_interpolation_continuation_policy_v1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty product: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fmt(value: float | str) -> str:
    return f"{float(value):.12g}"


def evaluate_analytic_profile(row: dict[str, str], radius_kpc: float) -> float:
    if row["profile_family"] != "offcentered_gaussian_sum":
        raise RuntimeError(f"unsupported analytic family: {row['profile_family']}")
    n_components = int(row["n_components"])
    if n_components not in {1, 2}:
        raise RuntimeError(f"invalid analytic component count: {n_components}")
    total = 0.0
    for component in range(1, n_components + 1):
        sigma0 = float(row[f"sigma0{component}_neutral_1p33_msun_pc2"])
        center = float(row[f"a{component}_kpc_frozen"])
        scale = float(row[f"r0{component}_kpc_frozen"])
        if not all(math.isfinite(value) for value in (sigma0, center, scale)):
            raise RuntimeError("nonfinite analytic parameter")
        if sigma0 < 0 or scale <= 0:
            raise RuntimeError("invalid analytic amplitude or scale")
        total += sigma0 * math.exp(-((radius_kpc - center) ** 2) / (2 * scale**2))
    if not math.isfinite(total) or total < 0:
        raise RuntimeError("analytic profile produced invalid surface density")
    return total


def render_freeze(summary: dict[str, object]) -> str:
    calibration = ", ".join(summary["membership"]["calibration"])
    blind = ", ".join(summary["membership"]["blind"])
    methods = summary["evaluation_method_counts"]
    hashes = summary["output_sha256"]
    return f"""# Stationary source-profile freeze v1 — certified 34-profile subset

**Status: FROZEN CERTIFIED SUBSET; GLOBAL 149-GALAXY SOURCE GATE REMAINS LOCKED.**

- **Freeze date:** 2026-08-14
- **Scope:** 34 galaxies = 25 calibration + 9 blind
- **Grid rows:** {summary['n_grid_rows']} frozen rotation radii
- **Common gas convention:** `{COMMON_CONVENTION}`

## Frozen numerical rule

- measured tabulated nodes are retained exactly;
- interior samples use piecewise-linear `Sigma(R)` interpolation;
- radii inside the first measured node use the first measured value;
- radii beyond the last measured node use zero, without an inferred taper;
- analytic profiles are evaluated directly from their frozen source functions;
- invalid, negative, nonfinite, duplicate-radius, or interior-gap inputs fail closed.

The authoritative rule is `validation/stationary/STATIONARY_HI_INTERPOLATION_CONTINUATION_POLICY_V1.md`. It was promoted from the predeclared candidate only after the complete 34-profile support audit showed that no galaxy-specific numerical rule was required.

## Exact membership

**Calibration (25):** {calibration}

**Blind (9):** {blind}

## Frozen products

| Product | SHA-256 |
|---|---|
| `data/stationary/processed/stationary_hi_profiles_v1.csv` | `{hashes[str(HI_OUT)]}` |
| `data/stationary/processed/stationary_source_profiles_v1.csv` | `{hashes[str(SOURCE_OUT)]}` |

The H I product contains one common-normalized central surface density at every frozen rotation radius for each certified galaxy. The source product adds the unit-`Upsilon` disk and bulge bases and retains the symbolic rules `Sigma_b = Sigma_gas + Upsilon_d Sigma_disk,1 + Upsilon_b Sigma_bulge,1` and `J = Sigma_b V_model`.

No observed velocity is present in either frozen product. The self-consistent source-current velocity is deliberately unevaluated.

## Evaluation accounting

- analytic evaluations: **{methods.get('analytic_offcentered_gaussian_sum', 0)}**
- exact measured nodes: **{methods.get('measured_node', 0)}**
- piecewise-linear samples: **{methods.get('piecewise_linear', 0)}**
- constant-inner continuation samples: **{methods.get('inner_constant', 0)}**
- zero-outer continuation samples: **{methods.get('outer_zero', 0)}**
- tabulated galaxies requiring inner continuation: **11**
- tabulated galaxies requiring outer continuation: **11**

## Scientific and versioning boundary

This is an immutable freeze of the currently certified public 34-profile subset. It is **not** the final 149-galaxy source package and does not unlock `L_A`, `C_A`, `tau_A`, source-current evaluation, calibration fitting, or blind evaluation. The current 112-galaxy author request remains pending.

Later profiles must pass provenance, schema, normalization, missing-value, and support QC and enter a new version under the same source-independent numerical rule. Version 1 is not rewritten to improve a fit or accommodate a blind result.
"""


def main() -> None:
    required = [
        MASTER,
        MANIFEST,
        TABULATED,
        ANALYTIC,
        COVERAGE,
        NORMALIZATION_POLICY,
        MISSING_VALUE_POLICY,
        INTERPOLATION_POLICY,
        MOCK_VALIDATION,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing required freeze inputs: {missing}")

    mock = json.loads(MOCK_VALIDATION.read_text(encoding="utf-8"))
    if mock.get("status") != "HI_INTERPOLATION_RULE_V1_MOCK_VALIDATED" or not mock.get(
        "all_pass"
    ):
        raise RuntimeError("interpolation rule mock validation is not passing")

    manifest_rows = read_csv(MANIFEST)
    manifest = {row["galaxy"]: row for row in manifest_rows}
    if len(manifest) != len(manifest_rows):
        raise RuntimeError("duplicate galaxy in certified normalization manifest")
    profile_roles = Counter(row["stationary_role"] for row in manifest_rows)
    if len(manifest) != 34 or dict(profile_roles) != EXPECTED_PROFILE_ROLES:
        raise RuntimeError(
            f"unexpected certified membership: n={len(manifest)} roles={dict(profile_roles)}"
        )
    if any(row["normalization_ready"] != "1" for row in manifest_rows):
        raise RuntimeError("normalization manifest contains a non-ready profile")

    master_by_galaxy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(MASTER):
        if row["galaxy"] in manifest:
            master_by_galaxy[row["galaxy"]].append(row)
    if set(master_by_galaxy) != set(manifest):
        raise RuntimeError("certified galaxy missing from frozen observational master")
    for galaxy, rows in master_by_galaxy.items():
        rows.sort(key=lambda row: int(row["galaxy_point_index"]))
        expected_indices = list(range(len(rows)))
        actual_indices = [int(row["galaxy_point_index"]) for row in rows]
        if actual_indices != expected_indices:
            raise RuntimeError(f"{galaxy}: non-contiguous frozen grid indices")
        radii = [float(row["radius_kpc"]) for row in rows]
        if any(radii[index + 1] <= radii[index] for index in range(len(radii) - 1)):
            raise RuntimeError(f"{galaxy}: non-increasing frozen rotation grid")

    tabulated_by_galaxy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(TABULATED):
        tabulated_by_galaxy[row["galaxy"]].append(row)
    for rows in tabulated_by_galaxy.values():
        rows.sort(key=lambda row: int(row["sample_index"]))
    analytic = {row["galaxy"]: row for row in read_csv(ANALYTIC)}
    if set(tabulated_by_galaxy) & set(analytic):
        raise RuntimeError("galaxy appears in both tabulated and analytic products")
    if set(tabulated_by_galaxy) | set(analytic) != set(manifest):
        raise RuntimeError("common-normalized profile membership differs from manifest")
    if len(tabulated_by_galaxy) != 27 or len(analytic) != 7:
        raise RuntimeError("expected 27 tabulated and 7 analytic profiles")

    coverage = {row["galaxy"]: row for row in read_csv(COVERAGE)}
    if set(coverage) != set(manifest):
        raise RuntimeError("coverage audit membership differs from manifest")

    hi_rows: list[dict[str, str]] = []
    source_rows: list[dict[str, str]] = []
    method_counts: Counter[str] = Counter()

    for galaxy in sorted(manifest):
        metadata = manifest[galaxy]
        role = metadata["stationary_role"]
        common_artifact = ANALYTIC if galaxy in analytic else TABULATED
        if galaxy in tabulated_by_galaxy:
            common_rows = tabulated_by_galaxy[galaxy]
            source_radii = [float(row["radius_kpc_frozen"]) for row in common_rows]
            source_sigma = [
                float(row["sigma_neutral_1p33_msun_pc2"]) for row in common_rows
            ]
            support_min = fmt(source_radii[0])
            support_max = fmt(source_radii[-1])
            source_artifact = metadata["source_artifact"]
            profile_kind = "tabulated"
        else:
            analytic_row = analytic[galaxy]
            source_radii = []
            source_sigma = []
            support_min = "0"
            support_max = "analytic"
            source_artifact = analytic_row["source_artifact"]
            profile_kind = "analytic"
        if source_artifact != metadata["source_artifact"]:
            raise RuntimeError(f"{galaxy}: source artifact mismatch")

        for master_row in master_by_galaxy[galaxy]:
            point_index = master_row["galaxy_point_index"]
            radius = float(master_row["radius_kpc"])
            if profile_kind == "tabulated":
                evaluation = evaluate_tabulated_profile(source_radii, source_sigma, radius)
                sigma = evaluation.sigma
                method = evaluation.method
                lower_index = str(evaluation.lower_index)
                upper_index = str(evaluation.upper_index)
                continuation_side = (
                    "inner"
                    if method == "inner_constant"
                    else "outer"
                    if method == "outer_zero"
                    else "none"
                )
            else:
                sigma = evaluate_analytic_profile(analytic[galaxy], radius)
                method = "analytic_offcentered_gaussian_sum"
                lower_index = ""
                upper_index = ""
                continuation_side = "none"
            method_counts[method] += 1

            hi_row = {
                "galaxy": galaxy,
                "stationary_role": role,
                "galaxy_point_index": point_index,
                "radius_kpc": master_row["radius_kpc"],
                "sigma_neutral_1p33_msun_pc2": fmt(sigma),
                "common_surface_density_convention": COMMON_CONVENTION,
                "profile_kind": profile_kind,
                "evaluation_method": method,
                "continuation_side": continuation_side,
                "coverage_class": coverage[galaxy]["coverage_class"],
                "measured_support_rmin_kpc": support_min,
                "measured_support_rmax_kpc": support_max,
                "source_bracket_lower_index": lower_index,
                "source_bracket_upper_index": upper_index,
                "source_artifact": source_artifact,
                "common_profile_artifact": str(common_artifact),
                "radius_mapping_method": metadata["radius_mapping_method"],
                "helium_mapping_method": metadata["helium_mapping_method"],
                "surface_density_multiplier_to_common_1p33": metadata[
                    "surface_density_multiplier_to_common_1p33"
                ],
                "inclination_amplitude_rescale": metadata[
                    "inclination_amplitude_rescale"
                ],
                "uncertainty_treatment": (
                    "central_value_frozen; source_uncertainties_retained_upstream"
                ),
                "interpolation_policy": str(INTERPOLATION_POLICY),
            }
            hi_rows.append(hi_row)

            source_rows.append(
                {
                    "galaxy": galaxy,
                    "stationary_role": role,
                    "galaxy_point_index": point_index,
                    "radius_kpc": master_row["radius_kpc"],
                    "sigma_neutral_gas_1p33_msun_pc2": fmt(sigma),
                    "sigma_disk_per_unit_upsilon_msun_pc2": fmt(
                        master_row["sb_disk_lsun_pc2"]
                    ),
                    "sigma_bulge_per_unit_upsilon_msun_pc2": fmt(
                        master_row["sb_bulge_lsun_pc2"]
                    ),
                    "sigma_baryon_rule": (
                        "Sigma_b = Sigma_gas + Upsilon_d*Sigma_disk_ml1 + "
                        "Upsilon_b*Sigma_bulge_ml1"
                    ),
                    "sigma_baryon_status": (
                        "basis_only; stellar_mass_to_light_nuisance_not_applied"
                    ),
                    "source_current_rule": "J = Sigma_b * V_model",
                    "source_current_velocity_status": (
                        "self_consistent_model_velocity_required; not_evaluated"
                    ),
                    "vobs_used_as_source_current": "0",
                    "hi_profile_kind": profile_kind,
                    "hi_profile_evaluation_method": method,
                    "hi_source_artifact": source_artifact,
                    "hi_freeze_row_key": f"{galaxy}:{point_index}",
                }
            )

    expected_rows = sum(len(rows) for rows in master_by_galaxy.values())
    if len(hi_rows) != expected_rows or len(source_rows) != expected_rows:
        raise RuntimeError("frozen source-grid row count mismatch")
    if any(float(row["sigma_neutral_1p33_msun_pc2"]) < 0 for row in hi_rows):
        raise RuntimeError("negative frozen H I surface density")
    if any(row["vobs_used_as_source_current"] != "0" for row in source_rows):
        raise RuntimeError("Vobs source-current guard failed")

    write_csv(HI_OUT, hi_rows)
    write_csv(SOURCE_OUT, source_rows)

    membership = {
        role: sorted(
            row["galaxy"] for row in manifest_rows if row["stationary_role"] == role
        )
        for role in ("calibration", "blind")
    }
    row_roles = Counter(row["stationary_role"] for row in hi_rows)
    input_paths = required
    output_paths = [HI_OUT, SOURCE_OUT]
    summary: dict[str, object] = {
        "status": "STATIONARY_SOURCE_PROFILE_CERTIFIED_SUBSET_V1_FROZEN",
        "scope": "certified_34_profile_subset_not_global_149_galaxy_unlock",
        "n_profiles": len(manifest),
        "n_tabulated_profiles": len(tabulated_by_galaxy),
        "n_analytic_profiles": len(analytic),
        "profile_role_counts": EXPECTED_PROFILE_ROLES,
        "membership": membership,
        "n_grid_rows": len(hi_rows),
        "grid_row_role_counts": {
            "calibration": row_roles["calibration"],
            "blind": row_roles["blind"],
        },
        "evaluation_method_counts": {
            method: method_counts[method] for method in sorted(method_counts)
        },
        "n_tabulated_requiring_inner_continuation": sum(
            row["inner_continuation_required"] == "1" for row in coverage.values()
        ),
        "n_tabulated_requiring_outer_continuation": sum(
            row["outer_continuation_required"] == "1" for row in coverage.values()
        ),
        "common_surface_density_convention": COMMON_CONVENTION,
        "interpolation_rule_id": INTERPOLATION_RULE_ID,
        "interpolation_policy": str(INTERPOLATION_POLICY),
        "input_sha256": {str(path): sha256_file(path) for path in input_paths},
        "output_sha256": {str(path): sha256_file(path) for path in output_paths},
        "source_current_evaluated": False,
        "vobs_used_as_source_current": False,
        "global_fit_gate_unlocked": False,
        "blind_outcome_inspected": False,
        "boundary": (
            "Observational source construction only. Certified 34-profile subset freeze; "
            "no velocity value, residual, persistence prediction, model preference, L_A, C_A, "
            "or tau_A evaluated."
        ),
    }
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    FREEZE_OUT.write_text(render_freeze(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
