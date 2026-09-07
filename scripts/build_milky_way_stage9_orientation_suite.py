#!/usr/bin/env python3
"""Freeze the Stage 9 Milky Way orientation/memory sensitivity grid.

No halo, force residual, orbit-weight target, or acceleration target is read by
this script. Its only job is to serialize the predeclared cases that subsequent
Stage 9 integrations must execute unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


OUT = Path("data/persistence_history/milky_way_stage9_orientation_suite")
ANGLES_DEG = (0, 30, 60, 90, 120, 150, 180)
TAU_GYR = (1.0, 2.0, 4.0, 8.0, 16.0)
DEFAULT_AXIS = (1.0, 0.0, 0.0)
DEFAULT_TRANSITION_LOOKBACK_GYR = 8.0
DEFAULT_TRANSITION_DURATION_GYR = 2.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for angle in ANGLES_DEG:
        label = chr(ord("A") + ANGLES_DEG.index(angle))
        for tau in TAU_GYR:
            rows.append(
                {
                    "stage_case": f"9{label}",
                    "primary_baseline": angle == 0,
                    "orientation_angle_deg": angle,
                    "rotation_axis_x": DEFAULT_AXIS[0],
                    "rotation_axis_y": DEFAULT_AXIS[1],
                    "rotation_axis_z": DEFAULT_AXIS[2],
                    "transition_lookback_gyr": DEFAULT_TRANSITION_LOOKBACK_GYR,
                    "transition_duration_gyr": DEFAULT_TRANSITION_DURATION_GYR,
                    "memory_tau_gyr": tau,
                    "selection_rule": "predeclared_sensitivity_only_not_halo_optimized",
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "stage9_orientation_memory_grid.csv", index=False)

    manifest = {
        "analysis_name": "Milky Way Stage 9 halo-blind orientation-history sensitivity suite",
        "status": "PREDECLARED_ARCHITECTURE_ONLY",
        "canonical_primary_case": "9A",
        "canonical_primary_orientation_deg": 0,
        "orientation_angles_deg": list(ANGLES_DEG),
        "memory_tau_gyr": list(TAU_GYR),
        "rotation_axis_present_frame": list(DEFAULT_AXIS),
        "transition_lookback_gyr": DEFAULT_TRANSITION_LOOKBACK_GYR,
        "transition_duration_gyr": DEFAULT_TRANSITION_DURATION_GYR,
        "guardrails": [
            "Do not choose orientation angle by maximizing agreement with Portail17+halo, Hunter24+halo, Delta a(R), or any other force target.",
            "Do not choose memory tau by maximizing agreement with halo orbit weights or the existing pulsar residual catalog.",
            "Run the 0-degree case first and retain it as the canonical Stage 9A prediction.",
            "Treat 30-180 degree cases as predeclared sensitivity tests unless independent Galactic-archaeology evidence is used to define a separate prior before force comparison.",
            "Keep density geometry and vector/current rotation distinct in diagnostics; 0 and 180 degrees may be degenerate for scalar geometry while remaining distinguishable for current direction.",
        ],
        "planned_outputs": [
            "orbit_weight_pearson_r_by_theta_tau",
            "orbit_weight_spearman_r_by_theta_tau",
            "orbit_weight_cosine_similarity_by_theta_tau",
            "weighted_rms_weight_difference_by_theta_tau",
            "delta_a_profile_error_by_theta_tau",
            "three_dimensional_acceleration_residual_map",
        ],
    }
    (OUT / "stage9_orientation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
