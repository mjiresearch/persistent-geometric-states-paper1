#!/usr/bin/env python3
"""Build the provisional halo-blind Stage 9 baryonic-memory source suite.

This script deliberately stops at the hereditary SOURCE field. It does not turn
that source into an acceleration by inventing a Poisson kernel, vertical scale
height, softening length, or normalization not already frozen by the theory.
It also never reads Portail17/Hunter24 halo targets, Delta a(R), pulsar
residuals, or orbit weights.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.milky_way.orientation_history import OrientationHistory
from analysis.milky_way.provisional_source_history import (
    build_memory_source_cloud,
    build_radial_increments,
    load_table_a1,
    source_cloud_moments,
)

OUT = Path("data/persistence_history/milky_way_stage9_provisional_source_suite")
ANGLES_DEG = (0, 30, 60, 90, 120, 150, 180)
TAU_GYR = (1.0, 2.0, 4.0, 8.0, 16.0)
ENVELOPES = ("signed_mininfo", "nonnegative_clipped")
ROTATION_AXIS = (1.0, 0.0, 0.0)
TRANSITION_LOOKBACK_GYR = 8.0
TRANSITION_DURATION_GYR = 2.0
RADIUS_KPC = np.linspace(0.001, 25.0, 300)
N_PHI = 24


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    table = load_table_a1()

    interval_rows = []
    result_rows = []
    increments_by_envelope = {}

    for envelope in ENVELOPES:
        increments = build_radial_increments(table, radius_kpc=RADIUS_KPC, envelope=envelope)
        increments_by_envelope[envelope] = increments
        for i, inc in enumerate(increments):
            r = inc.radius_kpc
            sigma = inc.delta_sigma_msun_kpc2
            shell = 2.0 * np.pi * r * sigma
            mass = float(np.trapezoid(shell, r))
            neg = float(np.trapezoid(2.0 * np.pi * r * np.clip(-sigma, 0.0, None), r))
            abs_mass = float(np.trapezoid(2.0 * np.pi * r * np.abs(sigma), r))
            interval_rows.append(
                {
                    "envelope": envelope,
                    "interval_index": i,
                    "older_lookback_gyr": inc.older_lookback_gyr,
                    "younger_lookback_gyr": inc.younger_lookback_gyr,
                    "representative_lookback_gyr": inc.representative_lookback_gyr,
                    "integrated_increment_mass_msun": mass,
                    "negative_abs_mass_msun": neg,
                    "negative_fraction_of_abs_mass": neg / abs_mass if abs_mass > 0 else 0.0,
                }
            )

    for envelope, increments in increments_by_envelope.items():
        for angle in ANGLES_DEG:
            stage_case = f"9{chr(ord('A') + ANGLES_DEG.index(angle))}"
            orientation = OrientationHistory(
                total_angle_deg=angle,
                axis=ROTATION_AXIS,
                transition_lookback_gyr=TRANSITION_LOOKBACK_GYR,
                transition_duration_gyr=TRANSITION_DURATION_GYR,
            )
            for tau in TAU_GYR:
                points, weights, times = build_memory_source_cloud(
                    increments,
                    orientation=orientation,
                    tau_gyr=tau,
                    n_phi=N_PHI,
                )
                moments = source_cloud_moments(points, weights)
                result_rows.append(
                    {
                        "stage_case": stage_case,
                        "primary_baseline": angle == 0,
                        "source_envelope": envelope,
                        "orientation_angle_deg": angle,
                        "memory_tau_gyr": tau,
                        "n_source_quadrature_points": int(points.shape[0]),
                        "min_source_lookback_gyr": float(times.min()),
                        "max_source_lookback_gyr": float(times.max()),
                        **moments,
                    }
                )

    intervals = pd.DataFrame(interval_rows)
    results = pd.DataFrame(result_rows)
    intervals.to_csv(OUT / "provisional_source_interval_audit.csv", index=False)
    results.to_csv(OUT / "provisional_source_geometry_grid.csv", index=False)

    signed = intervals[intervals.envelope == "signed_mininfo"]
    manifest = {
        "analysis_name": "Milky Way Stage 9 provisional halo-blind hereditary source construction",
        "status": "PROVISIONAL_SOURCE_SHAPE_ONLY_SOURCE_HISTORY_LIMITED",
        "input": "Ratcliffe et al. 2026 A&A 706 A103 Table A.1 global disc history",
        "n_epochs": int(len(table)),
        "n_intervals": int(len(table) - 1),
        "orientation_angles_deg": list(ANGLES_DEG),
        "memory_tau_gyr": list(TAU_GYR),
        "source_envelopes": list(ENVELOPES),
        "canonical_case": {
            "stage_case": "9A",
            "orientation_angle_deg": 0,
            "source_envelope": "signed_mininfo",
            "reason": "preserves the original non-flipped construction and exposes rather than hides the Table A.1 compression failure",
        },
        "source_history_warning": (
            "Stage 7 established that Mstar(t)+Reff_birth(t) do not uniquely determine a physical spatial SFH. "
            "The signed branch is a diagnostic minimum-information reconstruction; the clipped branch is a conservative envelope. "
            "Neither is the decisive source history required by the theory."
        ),
        "signed_intervals_with_any_negative_mass": int((signed.negative_abs_mass_msun > 0).sum()),
        "maximum_signed_negative_fraction_of_abs_mass": float(signed.negative_fraction_of_abs_mass.max()),
        "force_mapping_status": "NOT_APPLIED",
        "force_mapping_reason": (
            "No acceleration field is generated here because doing so would require a separately frozen persistence response law and, "
            "for this compressed source, unsupported assumptions about vertical structure/regularization. Those choices must not be "
            "back-solved from halo targets."
        ),
        "forbidden_inputs": [
            "Portail17+halo",
            "Hunter24+halo",
            "Delta a(R)",
            "pulsar residual catalog",
            "orbit-weight targets",
        ],
        "next_reopening_condition": (
            "Insert a resolved R_birth-by-lookback-time mass/SFR grid (preferred minimum) or stronger orbit/secular-history product, "
            "then apply the already-frozen orientation operator before any force comparison."
        ),
    }
    (OUT / "stage9_provisional_source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
