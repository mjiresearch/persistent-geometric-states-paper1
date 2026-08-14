#!/usr/bin/env python3
"""Pre-outcome synthetic validation for the frozen DR20 independent block."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from dr20_current_field_v1 import analyze_cluster_control, analyze_current_field, load_protocol


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "data/persistence_history/dr20_independent/protocol_v1.json"
DOCUMENT_PATH = ROOT / "docs/dr20_young_old_current_field_protocol_v1.md"
REPORT_PATH = ROOT / "data/persistence_history/dr20_independent/preoutcome_validation_v1.json"
EXECUTABLES = [
    ROOT / "scripts/dr20_current_field_v1.py",
    ROOT / "scripts/build_dr20_young_old_current_field_v1.py",
    ROOT / "scripts/analyze_dr20_open_cluster_control_v1.py",
    ROOT / "scripts/fetch_dr20_current_field_inputs_v1.py",
]


def synthetic_field(*, injected: bool) -> pd.DataFrame:
    rng = np.random.default_rng(441 if injected else 442)
    rows = []
    widths = np.array([0.25, 0.25, 0.10])
    for cell_index in range(12):
        ix, iy, iz = cell_index % 4, cell_index // 4, 0
        center = (np.array([ix, iy, iz]) + 0.5) * widths
        base = np.array([2.0 * ix, 215.0 + 1.5 * iy, -1.0 + 0.5 * ix])
        paired_noise = rng.normal(0.0, [3.0, 4.0, 2.0], size=(14, 3))
        for cohort_index, cohort in enumerate(("young", "old")):
            for star_index in range(14):
                position = center + rng.uniform(-0.35, 0.35, size=3) * widths
                if injected:
                    velocity = base + rng.normal(0.0, [3.0, 4.0, 2.0], size=3)
                    if cohort == "old":
                        velocity = velocity + np.array([12.0, -20.0, 8.0])
                else:
                    velocity = base + paired_noise[star_index]
                rows.append(
                    {
                        "source_id": f"{cell_index:02d}{cohort_index}{star_index:03d}",
                        "age_gyr": 0.55 if cohort == "young" else 6.0,
                        "age_err_lower_gyr": 0.10 if cohort == "young" else 0.50,
                        "age_err_upper_gyr": 0.10 if cohort == "young" else 0.50,
                        "x_kpc": position[0],
                        "y_kpc": position[1],
                        "z_kpc": position[2],
                        "v_R_kms": velocity[0],
                        "v_phi_kms": velocity[1],
                        "v_z_kms": velocity[2],
                    }
                )
    return pd.DataFrame(rows)


def independence_check() -> tuple[bool, dict]:
    forbidden_patterns = [
        r"data/stationary",
        r"scripts/stationary",
        r"data/sparc",
        r"\bsparc_",
        r"\bL_A\b",
        r"\bC_A\b",
    ]
    findings = []
    imports = []
    for path in EXECUTABLES:
        text = path.read_text()
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        for pattern in forbidden_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE if "sparc" in pattern else 0):
                findings.append({"file": str(path.relative_to(ROOT)), "pattern": pattern})
    return not findings, {"findings": findings, "imports": sorted(set(imports))}


def main() -> None:
    protocol = load_protocol(PROTOCOL_PATH)
    checks = []

    frozen = protocol.get("status") == "frozen_pre_outcome" and protocol.get("outcome_status_at_freeze") == "not_evaluated"
    checks.append({"name": "protocol_frozen_before_outcome", "passed": frozen})

    document = DOCUMENT_PATH.read_text()
    doc_bound = (
        protocol["protocol_id"] in document
        and protocol["documentation"] == str(DOCUMENT_PATH.relative_to(ROOT))
        and "frozen before real-outcome evaluation" in document.lower()
    )
    checks.append({"name": "human_and_machine_protocol_bound", "passed": doc_bound})

    independent, independence_details = independence_check()
    checks.append(
        {
            "name": "no_stationary_sparc_or_locked_parameter_dependency",
            "passed": independent,
            "details": independence_details,
        }
    )

    injected_summary, injected_voxels, _ = analyze_current_field(synthetic_field(injected=True), protocol)
    expected_voxels = int(protocol["field_test"]["grid"]["minimum_powered_voxels"])
    count_check = injected_summary["supported_voxels"] == expected_voxels and len(injected_voxels) == expected_voxels
    checks.append(
        {
            "name": "fixed_grid_has_twelve_synthetic_supported_voxels",
            "passed": count_check,
            "details": {"supported_voxels": injected_summary["supported_voxels"]},
        }
    )

    min_field_p = 1.0 / (protocol["field_test"]["primary_statistic"]["permutations"] + 1)
    injection_check = (
        injected_summary["field_verdict"] == "reject_within_voxel_exchangeability"
        and np.isclose(injected_summary["p_value_greater_equal"], min_field_p)
    )
    checks.append(
        {
            "name": "injected_current_signal_recovered",
            "passed": bool(injection_check),
            "details": {
                "T": injected_summary["primary_statistic_T"],
                "p": injected_summary["p_value_greater_equal"],
            },
        }
    )

    null_summary, _, _ = analyze_current_field(synthetic_field(injected=False), protocol)
    null_check = null_summary["field_verdict"] == "do_not_reject_within_voxel_exchangeability"
    checks.append(
        {
            "name": "paired_null_not_promoted",
            "passed": bool(null_check),
            "details": {"T": null_summary["primary_statistic_T"], "p": null_summary["p_value_greater_equal"]},
        }
    )

    rng = np.random.default_rng(443)
    cluster_age = np.linspace(0.05, 8.0, 60)
    present_radius = 8.0 + rng.normal(0.0, 0.15, size=len(cluster_age))
    signed_offset = 0.04 + 0.22 * cluster_age + rng.normal(0.0, 0.08, size=len(cluster_age))
    guiding_radius = present_radius + signed_offset
    cluster_summary, _ = analyze_cluster_control(cluster_age, present_radius, guiding_radius, protocol)
    min_cluster_p = 1.0 / (protocol["open_cluster_control"]["permutations"] + 1)
    cluster_check = cluster_summary["positive_confound_control"] and np.isclose(
        cluster_summary["p_value_positive_tail"], min_cluster_p
    )
    checks.append(
        {
            "name": "injected_open_cluster_control_recovered",
            "passed": bool(cluster_check),
            "details": {
                "rho": cluster_summary["spearman_rho"],
                "p": cluster_summary["p_value_positive_tail"],
            },
        }
    )

    passed = sum(bool(check["passed"]) for check in checks)
    report = {
        "protocol_id": protocol["protocol_id"],
        "validation_type": "synthetic_pre_outcome_only",
        "real_outcomes_evaluated": False,
        "checks_passed": passed,
        "checks_total": len(checks),
        "all_passed": passed == len(checks),
        "checks": checks,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
