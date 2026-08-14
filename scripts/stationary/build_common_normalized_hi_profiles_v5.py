#!/usr/bin/env python3
"""Extend the validated v4 common-normalized profiles with blind NGC5033.

The v4 products remain the immutable 33-galaxy baseline. This version verifies
that the only newly certified profile absent from v4 is NGC5033, then appends
its exact FEASTS source rows under the already-frozen blind source-acquisition
protocol. The deterministic common convention is
Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw.

No interpolation, continuation, rotation velocity, persistence quantity, or
blind outcome is evaluated.
"""
from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import shutil


MAN = Path("data/stationary/source_reconstruction/certified_hi_normalization_manifest_v3.csv")
BASE_TAB = Path("data/stationary/source_reconstruction/certified_hi_common_tabulated_v4.csv")
BASE_ANA = Path("data/stationary/source_reconstruction/certified_hi_common_analytic_v4.csv")
OUT_TAB = Path("data/stationary/source_reconstruction/certified_hi_common_tabulated_v5.csv")
OUT_ANA = Path("data/stationary/source_reconstruction/certified_hi_common_analytic_v5.csv")
SUMMARY = Path("validation/stationary/certified_hi_common_normalized_v5_summary.json")
NEW = {"NGC5033": "blind"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fmt(value: str | float) -> str:
    return f"{float(value):.12g}"


def main() -> None:
    manifest = read_csv(MAN)
    manifest_by_galaxy = {row["galaxy"]: row for row in manifest}
    if len(manifest_by_galaxy) != len(manifest):
        raise RuntimeError("duplicate normalization-manifest galaxy")

    base_tabulated = read_csv(BASE_TAB)
    base_analytic = read_csv(BASE_ANA)
    base_galaxies = {row["galaxy"] for row in base_tabulated} | {
        row["galaxy"] for row in base_analytic
    }
    current_galaxies = set(manifest_by_galaxy)
    additions = current_galaxies - base_galaxies
    removed = base_galaxies - current_galaxies
    if additions != set(NEW) or removed:
        raise RuntimeError(
            f"unexpected delta from v4 baseline: additions={sorted(additions)} "
            f"removed={sorted(removed)}"
        )
    if len(base_galaxies) != 33:
        raise RuntimeError(f"v4 baseline changed: expected 33 galaxies, got {len(base_galaxies)}")

    fields = list(base_tabulated[0])
    output_rows = list(base_tabulated)
    added_rows: dict[str, int] = {}
    for galaxy, expected_role in NEW.items():
        metadata = manifest_by_galaxy[galaxy]
        if (
            metadata["stationary_role"] != expected_role
            or metadata["acquisition_status"] != "raw_source_profile_ingested"
        ):
            raise RuntimeError(f"{galaxy}: unexpected manifest state")
        if metadata["helium_mapping_method"] != "raw_HI_to_common_1p33":
            raise RuntimeError(f"{galaxy}: unexpected helium mapping")
        if metadata["radius_mapping_method"] != "explicit_frozen_radius":
            raise RuntimeError(f"{galaxy}: unexpected radius mapping")

        artifact = Path(metadata["source_artifact"])
        source_rows = read_csv(artifact)
        if not source_rows or any(
            row["galaxy"] != galaxy or row["stationary_role"] != expected_role
            for row in source_rows
        ):
            raise RuntimeError(f"{galaxy}: source artifact content mismatch")
        if len(source_rows) != 50:
            raise RuntimeError(f"{galaxy}: expected 50 locked-QC rows, got {len(source_rows)}")

        previous_radius = None
        for sample_index, source in enumerate(source_rows):
            radius = float(source["radius_kpc_frozen_distance"])
            sigma = float(source["sigma_hi_raw_msun_pc2"])
            radius_arcsec = float(source["radius_arcsec"])
            if radius <= 0 or sigma < 0:
                raise RuntimeError(f"{galaxy}: invalid radius/sigma row {sample_index}")
            if previous_radius is not None and radius <= previous_radius:
                raise RuntimeError(f"{galaxy}: non-increasing radius")
            previous_radius = radius
            multiplier = float(metadata["surface_density_multiplier_to_common_1p33"])
            row = {
                "galaxy": galaxy,
                "stationary_role": expected_role,
                "sample_index": str(sample_index),
                "source_artifact": str(artifact),
                "source_radius_value": fmt(radius_arcsec),
                "source_radius_unit": "arcsec",
                "radius_kpc_frozen": fmt(radius),
                "sigma_source_msun_pc2": fmt(sigma),
                "sigma_source_err_minus_msun_pc2": "",
                "sigma_source_err_plus_msun_pc2": "",
                "surface_density_multiplier_to_common_1p33": metadata[
                    "surface_density_multiplier_to_common_1p33"
                ],
                "sigma_neutral_1p33_msun_pc2": fmt(sigma * multiplier),
                "sigma_neutral_1p33_err_minus_msun_pc2": "",
                "sigma_neutral_1p33_err_plus_msun_pc2": "",
                "radius_mapping_method": metadata["radius_mapping_method"],
                "helium_mapping_method": metadata["helium_mapping_method"],
                "inclination_amplitude_rescale": "0",
                "source_note": (
                    "Official FEASTS 2025 machine-readable raw-HI profile; "
                    "promoted under the locked blind source-acquisition protocol; "
                    "angular radius mapped to frozen distance during acquisition; "
                    "no interpolation or continuation."
                ),
            }
            if set(row) != set(fields):
                raise RuntimeError("v5 row schema mismatch")
            output_rows.append(row)
        added_rows[galaxy] = len(source_rows)

    output_rows.sort(key=lambda row: (row["galaxy"], int(row["sample_index"])))
    OUT_TAB.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TAB.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    shutil.copyfile(BASE_ANA, OUT_ANA)

    all_galaxies = {row["galaxy"] for row in output_rows} | {
        row["galaxy"] for row in base_analytic
    }
    roles = Counter(manifest_by_galaxy[galaxy]["stationary_role"] for galaxy in all_galaxies)
    if len(all_galaxies) != 34 or roles != Counter({"calibration": 25, "blind": 9}):
        raise RuntimeError(f"unexpected certified set: n={len(all_galaxies)} roles={dict(roles)}")
    if len(all_galaxies) != len(manifest_by_galaxy):
        raise RuntimeError(
            f"normalized galaxy count {len(all_galaxies)} != manifest {len(manifest_by_galaxy)}"
        )

    result = {
        "status": "CERTIFIED_HI_COMMON_NORMALIZED_V5_BUILT",
        "v4_baseline_galaxies": len(base_galaxies),
        "new_galaxies": sorted(NEW),
        "new_rows": added_rows,
        "n_certified_galaxies": len(all_galaxies),
        "n_tabulated_galaxies": len({row["galaxy"] for row in output_rows}),
        "n_analytic_galaxies": len({row["galaxy"] for row in base_analytic}),
        "role_counts": dict(roles),
        "n_tabulated_rows": len(output_rows),
        "outputs": [str(OUT_TAB), str(OUT_ANA)],
        "normalization_policy": "validation/stationary/STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md",
        "blind_source_protocol": "validation/stationary/FEASTS2025_BLIND_HI_SOURCE_ACQUISITION_PROTOCOL_V1.md",
        "boundary": (
            "Common source normalization only. No interpolation, continuation, rotation velocity, "
            "source-current evaluation, persistence parameter, or blind outcome."
        ),
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
