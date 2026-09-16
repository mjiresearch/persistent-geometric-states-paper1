#!/usr/bin/env python3
"""Build the halo-blind Stage 9A historical Phi_b and D_H Phi_b source product.

This is the canonical 0-degree orientation baseline.  It uses only the public
Ratcliffe Table A.1 minimum-information disk history and the ordinary Newtonian
potential of each historical baryonic disk.  It does not read halo, pulsar,
or orbit-weight targets.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.milky_way.historical_baryonic_potential import (
    DEFAULT_RMAX_KPC,
    potential_history,
    snapshots_from_table_a1,
    state_frame_time_derivative,
)
from analysis.milky_way.orientation_history import OrientationHistory
from analysis.milky_way.provisional_source_history import DEFAULT_SOURCE, load_table_a1

OUT = Path("data/persistence_history/milky_way_stage9a_historical_potential")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    table = load_table_a1(DEFAULT_SOURCE)
    snapshots = snapshots_from_table_a1(table, append_present_hold=True)

    # Cell-centred evaluation coordinates avoid R=0 and deliberately do not
    # coincide with the Gauss-Legendre source-ring nodes.
    R = np.linspace(0.25, 25.25, 51)
    z = np.linspace(-10.25, 10.25, 42)
    RR, ZZ = np.meshgrid(R, z, indexing="ij")
    xyz = np.stack([RR, np.zeros_like(RR), ZZ], axis=-1)

    orientation = OrientationHistory(total_angle_deg=0.0)
    lookback, phi = potential_history(
        xyz,
        snapshots,
        orientation=orientation,
        n_ring=192,
        rmax_kpc=DEFAULT_RMAX_KPC,
    )
    dphi = state_frame_time_derivative(lookback, phi)

    np.savez_compressed(
        OUT / "stage9a_phi_b_history.npz",
        lookback_gyr=lookback,
        R_kpc=R,
        z_kpc=z,
        phi_b_kms2=phi,
        dH_phi_b_kms2_per_gyr=dphi,
    )

    # Small text audit product for repository inspection without loading NPZ.
    rows = []
    for i, t in enumerate(lookback):
        rows.append(
            {
                "lookback_gyr": float(t),
                "phi_min_kms2": float(np.nanmin(phi[i])),
                "phi_max_kms2": float(np.nanmax(phi[i])),
                "dH_phi_min_kms2_per_gyr": float(np.nanmin(dphi[i])),
                "dH_phi_max_kms2_per_gyr": float(np.nanmax(dphi[i])),
                "dH_phi_rms_kms2_per_gyr": float(np.sqrt(np.mean(dphi[i] ** 2))),
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "stage9a_phi_b_epoch_audit.csv", index=False)

    report = {
        "analysis_name": "Milky Way Stage 9A halo-blind historical baryonic potential source build",
        "orientation_deg": 0.0,
        "source": str(DEFAULT_SOURCE),
        "source_history_status": "PROVISIONAL_TABLE_A1_MINIMUM_INFORMATION",
        "ordinary_baryonic_potential_only": True,
        "halo_or_force_target_used": False,
        "disk_model": "razor_thin_exponential_birth_radius_disk",
        "potential_method": "exact_circular_ring_kernel_with_Gauss_Legendre_radial_quadrature",
        "softening_kpc": None,
        "vertical_scale_height_kpc": None,
        "source_radial_boundary_kpc": DEFAULT_RMAX_KPC,
        "n_published_epochs": int(len(table)),
        "n_epochs_with_present_hold": int(len(lookback)),
        "youngest_published_lookback_gyr": float(table.lookback_time_gyr.min()),
        "present_endpoint_rule": "hold youngest published Mstar and Reff_birth fixed to 0 Gyr; no invented deposition in final interval",
        "present_dH_phi_max_abs_kms2_per_gyr": float(np.max(np.abs(dphi[-1]))),
        "grid": {
            "n_R": int(R.size),
            "n_z": int(z.size),
            "R_min_kpc": float(R.min()),
            "R_max_kpc": float(R.max()),
            "z_min_kpc": float(z.min()),
            "z_max_kpc": float(z.max()),
        },
        "next_step": "feed raw D_H Phi_b history to Candidate L1 free-space causal solver; do not apply external exp(-t/tau) weighting",
    }
    (OUT / "stage9a_phi_b_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
