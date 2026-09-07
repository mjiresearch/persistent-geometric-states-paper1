#!/usr/bin/env python3
"""Generate the first halo-blind Stage 9A Candidate L2 persistence field.

This run is intentionally limited to the canonical 0-degree orientation case.
It uses the provisional Ratcliffe Table A.1 cumulative disk history, the local
curvature-change deposition law, and the predeclared tau grid.  No halo or
rotation-curve residual target is read.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.milky_way.candidate_l2 import (
    CandidateL2Parameters,
    acceleration_from_regular_grid,
    interval_integrated_density_change_clouds,
    present_psi_from_interval_clouds,
)
from analysis.milky_way.historical_baryonic_potential import snapshots_from_table_a1
from analysis.milky_way.orientation_history import OrientationHistory
from analysis.milky_way.provisional_source_history import DEFAULT_SOURCE, load_table_a1

OUT = Path("data/persistence_history/milky_way_stage9a_candidate_l2")
TAU_GYR = (1.0, 2.0, 4.0, 8.0, 16.0)
ACCEL_KMS2_PER_KPC_TO_M_S2 = 3.2407792896664e-14


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    table = load_table_a1(DEFAULT_SOURCE)
    snapshots = snapshots_from_table_a1(table, append_present_hold=True)
    orientation = OrientationHistory(total_angle_deg=0.0)

    clouds = interval_integrated_density_change_clouds(
        snapshots,
        orientation,
        n_ring=64,
        n_phi=32,
    )

    # Canonical midplane diagnostic grid.  The L2 tail kernel is finite at zero
    # separation, so no force softening is required.
    R = np.linspace(0.5, 25.0, 99)
    xyz = np.stack([R, np.zeros_like(R), np.zeros_like(R)], axis=-1)

    rows = []
    fields = {"R_kpc": R}
    for tau in TAU_GYR:
        params = CandidateL2Parameters(tau_gyr=tau)
        psi = present_psi_from_interval_clouds(xyz, clouds, params, chunk_size=64)
        (a_R,) = acceleration_from_regular_grid(psi, (R,))
        a_m_s2 = a_R * ACCEL_KMS2_PER_KPC_TO_M_S2

        key = str(int(tau)).replace(".", "p")
        fields[f"psi_tau_{key}_kms2"] = psi
        fields[f"aR_tau_{key}_kms2_per_kpc"] = a_R
        fields[f"aR_tau_{key}_m_s2"] = a_m_s2

        rows.append(
            {
                "tau_gyr": tau,
                "correlation_length_kpc": params.correlation_length_kpc,
                "psi_min_kms2": float(np.min(psi)),
                "psi_max_kms2": float(np.max(psi)),
                "aR_min_kms2_per_kpc": float(np.min(a_R)),
                "aR_max_kms2_per_kpc": float(np.max(a_R)),
                "aR_rms_m_s2": float(np.sqrt(np.mean(a_m_s2**2))),
                "aR_at_8kpc_m_s2": float(np.interp(8.0, R, a_m_s2)),
                "aR_at_15kpc_m_s2": float(np.interp(15.0, R, a_m_s2)),
                "aR_at_20kpc_m_s2": float(np.interp(20.0, R, a_m_s2)),
            }
        )

    np.savez_compressed(OUT / "stage9a_candidate_l2_midplane_fields.npz", **fields)
    pd.DataFrame(rows).to_csv(OUT / "stage9a_candidate_l2_tau_audit.csv", index=False)

    report = {
        "analysis_name": "Milky Way Stage 9A Candidate L2 first halo-blind persistence field",
        "status": "PROVISIONAL_SOURCE_HISTORY_FIRST_FIELD",
        "orientation_deg": 0.0,
        "tau_gyr": list(TAU_GYR),
        "response_law": "[(D+1/tau)(D+2/tau)-c^2 Laplacian] Psi = 4pi G c^2 tau D rho_b",
        "kappa": 1.0,
        "c_H": "c",
        "interaction_acceleration": "zero_at_strict_linear_order",
        "source_history": str(DEFAULT_SOURCE),
        "source_history_limitation": "Ratcliffe Table A.1 minimum-information cumulative exponential disks; not the missing full R_birth-by-time array",
        "present_endpoint_rule": "youngest 0.70-Gyr disk held fixed to present, giving zero final-interval deposition",
        "solver": "free_space_retarded_interior_cone_Green_function_interval_impulse_quadrature",
        "numerical_domain_boundary": None,
        "force_softening": None,
        "halo_or_force_target_used": False,
        "n_intervals": len(clouds),
        "source_quadrature": {"n_ring": 64, "n_phi": 32},
        "evaluation_grid": {"R_min_kpc": float(R.min()), "R_max_kpc": float(R.max()), "n_R": int(R.size), "z_kpc": 0.0},
        "interpretation_rule": "Do not select tau from these amplitudes. All five predeclared tau cases remain sensitivity outputs until external comparison is opened.",
        "next_step": "after numerical validation, freeze these fields and compare all predeclared tau cases with Delta-a and orbit-weight benchmarks without retuning",
    }
    (OUT / "stage9a_candidate_l2_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
