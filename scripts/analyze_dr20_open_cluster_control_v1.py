#!/usr/bin/env python3
"""Run the frozen DR20 BOSS OCCAM open-cluster control."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from dr20_current_field_v1 import analyze_cluster_control, load_protocol


def read_catalog(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".fits", ".fit", ".fz"}:
        from astropy.table import Table

        return Table.read(path).to_pandas()
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, low_memory=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clusters",
        type=Path,
        default=Path("data/external/sdss/dr20_boss_occam/BOSS_occam_cluster-DR20-v1.fits"),
    )
    parser.add_argument(
        "--protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/persistence_history/dr20_independent/open_cluster_control_v1")
    )
    parser.add_argument(
        "--field-summary",
        type=Path,
        default=Path("data/persistence_history/dr20_independent/field_v1/field_summary.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = load_protocol(args.protocol)
    raw = read_catalog(args.clusters)
    required = ["Cav_logAge", "R_GC_Cav", "R_Guide"]
    missing = sorted(set(required) - set(raw.columns))
    if missing:
        raise ValueError(f"BOSS OCCAM cluster schema is missing {missing}; columns={list(raw.columns)}")
    d = raw.copy()
    d["age_gyr"] = np.power(10.0, pd.to_numeric(d["Cav_logAge"], errors="coerce")) / 1.0e9
    d["R_now_kpc"] = pd.to_numeric(d["R_GC_Cav"], errors="coerce")
    d["R_guide_kpc"] = pd.to_numeric(d["R_Guide"], errors="coerce")
    finite = np.isfinite(d[["age_gyr", "R_now_kpc", "R_guide_kpc"]].to_numpy(dtype=float)).all(axis=1)
    member_cut_applied = "Num_Full_Members" in d.columns
    if member_cut_applied:
        members = pd.to_numeric(d["Num_Full_Members"], errors="coerce")
        finite &= np.isfinite(members) & (members >= 3)
    d = d.loc[finite].copy()
    d["abs_Rguide_minus_Rnow_kpc"] = np.abs(d["R_guide_kpc"] - d["R_now_kpc"])
    summary, permutations = analyze_cluster_control(
        d["age_gyr"].to_numpy(),
        d["R_now_kpc"].to_numpy(),
        d["R_guide_kpc"].to_numpy(),
        protocol,
    )
    summary["raw_catalog_rows"] = int(len(raw))
    summary["member_count_cut_applied"] = member_cut_applied
    args.output_dir.mkdir(parents=True, exist_ok=True)
    keep = [
        column
        for column in [
            "Name",
            "age_gyr",
            "R_now_kpc",
            "R_guide_kpc",
            "abs_Rguide_minus_Rnow_kpc",
            "Num_Full_Members",
            "OCCAM_Qual",
            "Eccentricity",
            "Z_Max",
            "Fe_H",
        ]
        if column in d.columns
    ]
    d[keep].to_csv(args.output_dir / "open_cluster_control_sample.csv", index=False)
    pd.DataFrame({"rho_permuted": permutations}).to_csv(
        args.output_dir / "open_cluster_permutation_distribution.csv.gz", index=False, compression="gzip"
    )
    (args.output_dir / "open_cluster_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    combined = None
    if args.field_summary.exists():
        field = json.loads(args.field_summary.read_text())
        rejected = field.get("field_verdict") == "reject_within_voxel_exchangeability"
        if not field.get("powered", False):
            classification = "underpowered_field_block"
        elif not rejected:
            classification = "no_support_from_field_block"
        elif summary["positive_confound_control"]:
            classification = "field_difference_conventionally_confounded_not_persistence_evidence"
        else:
            classification = "persistence_compatible_not_a_detection"
        combined = {
            "protocol_id": protocol["protocol_id"],
            "field": field,
            "open_cluster_control": summary,
            "classification": classification,
            "claim_guardrail": protocol["interpretation"]["prohibited_claim"],
        }
        (args.output_dir.parent / "block_verdict_v1.json").write_text(json.dumps(combined, indent=2) + "\n")
    print(json.dumps(combined or summary, indent=2))


if __name__ == "__main__":
    main()
