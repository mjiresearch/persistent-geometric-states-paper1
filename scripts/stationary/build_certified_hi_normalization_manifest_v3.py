#!/usr/bin/env python3
"""Build the normalization manifest for the current certified H I set.

Version 3 preserves the 33-profile v2 artifact and records the promoted blind
NGC5033 profile in a new 34-profile manifest. This is source metadata only; no
interpolation, rotation velocity, persistence quantity, or blind outcome is
evaluated.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


PROV = Path("data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv")
SCHEMA = Path("validation/stationary/certified_hi_profile_schema_audit_v1.json")
SCALE = Path("data/stationary/source_reconstruction/certified_hi_source_scale_metadata_v2.csv")
MASTER = Path("data/stationary/frozen/stationary_master_v1.csv")
OUT = Path("data/stationary/source_reconstruction/certified_hi_normalization_manifest_v3.csv")
SUMMARY = Path("validation/stationary/certified_hi_normalization_manifest_v3_summary.json")
CERTIFIED = {"raw_source_profile_ingested", "analytic_profile_recovered"}
LEROY = "data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv"
NGC300 = "data/stationary/source_reconstruction/westmeier2011_ngc300_gas_profile_v1.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    provenance = [
        row
        for row in read_csv(PROV)
        if row["effective_acquisition_status"] in CERTIFIED
    ]
    if not provenance:
        raise RuntimeError("no certified profiles in reconciled provenance")
    schema = json.loads(SCHEMA.read_text())
    artifact_map = {artifact["artifact"]: artifact for artifact in schema["artifacts"]}
    missing_artifacts = {
        row["effective_source_artifact"] for row in provenance
    } - set(artifact_map)
    if missing_artifacts:
        raise RuntimeError(f"schema audit is stale: {sorted(missing_artifacts)}")

    scale = {row["galaxy"]: row for row in read_csv(SCALE)}
    frozen_distance: dict[str, float] = {}
    for row in read_csv(MASTER):
        frozen_distance.setdefault(row["galaxy"], float(row["distance_mpc"]))

    rows = []
    unresolved = []
    for source in provenance:
        galaxy = source["galaxy"]
        artifact = source["effective_source_artifact"]
        columns = set(artifact_map[artifact].get("columns", []))
        if galaxy in scale:
            radius_method = "source_kpc_times_frozen_over_source_distance"
            radius_factor: str | float = float(scale[galaxy]["radius_scale_frozen_over_source"])
            source_distance = scale[galaxy]["source_distance_mpc"]
        elif columns & {
            "radius_kpc_frozen",
            "frozen_radius_kpc",
            "radius_kpc_frozen_distance",
        }:
            radius_method = "explicit_frozen_radius"
            radius_factor = 1.0
            source_distance = ""
        elif columns & {
            "radius_arcsec",
            "radius_arcsec_vector",
            "radius_arcsec_native_grid",
            "source_radius_arcsec",
            "r_arcsec",
        }:
            radius_method = "angular_radius_times_frozen_distance"
            radius_factor = ""
            source_distance = ""
        elif (
            source["effective_acquisition_status"] == "analytic_profile_recovered"
            and any(column.endswith("_arcsec") for column in columns)
        ):
            radius_method = "analytic_angular_scale_times_frozen_distance"
            radius_factor = ""
            source_distance = ""
        else:
            unresolved.append((galaxy, "radius", artifact, sorted(columns)))
            radius_method = "UNRESOLVED"
            radius_factor = ""
            source_distance = ""

        if artifact == LEROY:
            helium_method = "source_includes_1p36_to_common_1p33"
            helium_multiplier = 1.33 / 1.36
            source_helium_factor = "1.36"
        elif artifact == NGC300:
            helium_method = "source_includes_1p4_to_common_1p33"
            helium_multiplier = 1.33 / 1.4
            source_helium_factor = "1.4"
        else:
            helium_method = "raw_HI_to_common_1p33"
            helium_multiplier = 1.33
            source_helium_factor = "1.0"

        rows.append(
            {
                "galaxy": galaxy,
                "stationary_role": source["stationary_role"],
                "acquisition_status": source["effective_acquisition_status"],
                "source_artifact": artifact,
                "source_quantity": source["effective_source_quantity"],
                "source_helium_status": source["effective_helium_status"],
                "frozen_distance_mpc": f"{frozen_distance[galaxy]:.12g}",
                "source_distance_mpc": source_distance,
                "radius_mapping_method": radius_method,
                "radius_multiplicative_factor_if_source_kpc": (
                    "" if radius_factor == "" else f"{radius_factor:.12g}"
                ),
                "source_helium_factor_relative_to_raw_HI": source_helium_factor,
                "helium_mapping_method": helium_method,
                "surface_density_multiplier_to_common_1p33": f"{helium_multiplier:.12g}",
                "common_surface_density_convention": "Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw",
                "inclination_amplitude_rescale": "0",
                "normalization_ready": "1" if radius_method != "UNRESOLVED" else "0",
            }
        )
    if unresolved:
        raise RuntimeError(f"unresolved normalization metadata: {unresolved!r}")

    rows.sort(key=lambda row: row["galaxy"])
    role_counts = {
        "calibration": sum(row["stationary_role"] == "calibration" for row in rows),
        "blind": sum(row["stationary_role"] == "blind" for row in rows),
    }
    if len(rows) != 34 or role_counts != {"calibration": 25, "blind": 9}:
        raise RuntimeError(f"unexpected certified manifest: n={len(rows)} roles={role_counts}")
    ngc5033 = next(row for row in rows if row["galaxy"] == "NGC5033")
    if (
        ngc5033["stationary_role"] != "blind"
        or ngc5033["radius_mapping_method"] != "explicit_frozen_radius"
        or ngc5033["helium_mapping_method"] != "raw_HI_to_common_1p33"
        or ngc5033["normalization_ready"] != "1"
    ):
        raise RuntimeError(f"unexpected NGC5033 manifest row: {ngc5033}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "status": "CERTIFIED_HI_NORMALIZATION_MANIFEST_V3_COMPLETE",
        "v2_baseline_certified": 33,
        "new_galaxies": ["NGC5033"],
        "n_certified": len(rows),
        "n_ready": sum(row["normalization_ready"] == "1" for row in rows),
        "role_counts": role_counts,
        "helium_mapping_counts": {
            method: sum(row["helium_mapping_method"] == method for row in rows)
            for method in sorted({row["helium_mapping_method"] for row in rows})
        },
        "radius_mapping_counts": {
            method: sum(row["radius_mapping_method"] == method for row in rows)
            for method in sorted({row["radius_mapping_method"] for row in rows})
        },
        "policy": "validation/stationary/STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md",
        "blind_source_protocol": "validation/stationary/FEASTS2025_BLIND_HI_SOURCE_ACQUISITION_PROTOCOL_V1.md",
        "boundary": (
            "Normalization metadata only. No profile interpolation, rotation velocity, L_A, C_A, "
            "tau_A, persistence prediction, or blind outcome evaluated."
        ),
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
