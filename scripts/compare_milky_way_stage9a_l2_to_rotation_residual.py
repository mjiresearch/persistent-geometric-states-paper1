#!/usr/bin/env python3
"""Compare frozen Stage 9A Candidate L2 fields to the existing Stage 3 residual.

This script is intentionally downstream of field generation.  It does not tune,
renormalize, or select tau.  Every predeclared tau case is reported unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

FIELD = Path("data/persistence_history/milky_way_stage9a_candidate_l2/stage9a_candidate_l2_midplane_fields.npz")
TARGET = Path("data/persistence_history/milky_way_stage3/milky_way_rotation_residual_history.csv")
OUT = Path("data/persistence_history/milky_way_stage9a_candidate_l2")
TAU_GYR = (1.0, 2.0, 4.0, 8.0, 16.0)


def main() -> None:
    f = np.load(FIELD)
    R_field = f["R_kpc"]
    target = pd.read_csv(TARGET)
    target = target[target.R_kpc.between(5.0, 20.0)].copy()
    R = target.R_kpc.to_numpy(float)
    required = target.gres_kms2_per_kpc.to_numpy(float)

    rows = []
    for tau in TAU_GYR:
        key = str(int(tau)).replace(".", "p")
        pred_full = f[f"aR_tau_{key}_kms2_per_kpc"]
        pred = np.interp(R, R_field, pred_full)
        ratio = np.divide(np.abs(pred), np.abs(required), out=np.full_like(pred, np.nan), where=required != 0)
        pr, pp = pearsonr(pred, required)
        sr, sp = spearmanr(pred, required)
        i8 = int(np.argmin(np.abs(R - 8.0)))
        rows.append(
            {
                "tau_gyr": tau,
                "pearson_r_shape": float(pr),
                "pearson_p": float(pp),
                "spearman_rho_shape": float(sr),
                "spearman_p": float(sp),
                "median_abs_acceleration_ratio_L2_over_required": float(np.nanmedian(ratio)),
                "max_abs_acceleration_ratio_L2_over_required": float(np.nanmax(ratio)),
                "R_near_8_kpc": float(R[i8]),
                "L2_aR_at_8_kpc_kms2_per_kpc": float(pred[i8]),
                "required_gres_at_8_kpc_kms2_per_kpc": float(required[i8]),
                "ratio_at_8_kpc": float(ratio[i8]),
            }
        )

    result = pd.DataFrame(rows)
    result.to_csv(OUT / "stage9a_l2_vs_stage3_rotation_residual.csv", index=False)

    report = {
        "analysis_name": "Milky Way Stage 9A Candidate L2 frozen direct-acceleration screen",
        "field_was_frozen_before_target_comparison": True,
        "field_normalization_changed_after_comparison": False,
        "tau_selection_performed": False,
        "target": str(TARGET),
        "target_definition": "Eilers rotation residual relative to McMillan17 baryons from frozen Stage 3",
        "rows": rows,
        "falsification_rule": "A candidate that is orders of magnitude too small and/or has the wrong radial shape is not rescued by post-hoc amplitude fitting; it remains a failed preregistered candidate unless an independently motivated theory change defines a new candidate before re-comparison.",
    }
    (OUT / "stage9a_l2_vs_stage3_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
