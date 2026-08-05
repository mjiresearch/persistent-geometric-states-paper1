#!/usr/bin/env python3
"""Build the pre-fit stationary baryonic source basis for Appendix I.

Uses only frozen observational inputs. Does not fit or evaluate L_A, C_A,
tau_A, or any persistence-model prediction.

SPARC 2016 supplies inclination-corrected stellar surface brightnesses and the
Newtonian gas velocity contribution Vgas, but not radial HI surface-density
profiles. Vgas is therefore never treated as Sigma_gas in this build.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

HI_PROFILE_UNAVAILABLE_HUA2025 = {
    "D512-2", "D564-8", "D631-7", "NGC5907", "NGC4138", "UGC06818"
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fmt(x: float) -> str:
    return f"{x:.12g}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", type=Path, required=True)
    ap.add_argument("--split", type=Path, required=True)
    ap.add_argument("--basis-out", type=Path, required=True)
    ap.add_argument("--availability-out", type=Path, required=True)
    ap.add_argument("--summary-out", type=Path, required=True)
    args = ap.parse_args()

    master = read_csv(args.master)
    split = read_csv(args.split)
    split_by_galaxy = {r["galaxy"]: r for r in split}
    role_col = "stationary_role" if "stationary_role" in split[0] else "sample_role"

    if len(master) != 3152:
        raise ValueError(f"Expected 3152 master rows, found {len(master)}")
    galaxies = sorted({r["galaxy"] for r in master})
    if len(galaxies) != 149:
        raise ValueError(f"Expected 149 galaxies, found {len(galaxies)}")
    if set(galaxies) != set(split_by_galaxy):
        raise ValueError("Galaxy membership differs between master and frozen split")

    basis_fields = [
        "galaxy", "stationary_role", "radius_kpc", "v_obs_kms", "v_err_kms",
        "v_gas_kms", "v_gas2_signed_km2_s2", "v_disk_ml1_kms",
        "v_disk2_per_unit_upsilon_km2_s2", "v_bulge_ml1_kms",
        "v_bulge2_per_unit_upsilon_km2_s2", "sb_disk_lsun_pc2",
        "sb_bulge_lsun_pc2", "sigma_disk_per_unit_upsilon_msun_pc2",
        "sigma_bulge_per_unit_upsilon_msun_pc2", "sigma_gas_msun_pc2",
        "sigma_gas_status", "source_current_velocity_status",
        "vobs_used_as_source_current",
    ]

    basis_rows = []
    for r in master:
        g = r["galaxy"]
        vgas = float(r["v_gas_kms"])
        vdisk = float(r["v_disk_ml1_kms"])
        vbul = float(r["v_bulge_ml1_kms"])
        sbd = float(r["sb_disk_lsun_pc2"])
        sbb = float(r["sb_bulge_lsun_pc2"])
        basis_rows.append({
            "galaxy": g,
            "stationary_role": split_by_galaxy[g][role_col],
            "radius_kpc": r["radius_kpc"],
            "v_obs_kms": r["v_obs_kms"],
            "v_err_kms": r["v_err_kms"],
            "v_gas_kms": r["v_gas_kms"],
            "v_gas2_signed_km2_s2": fmt(vgas * abs(vgas)),
            "v_disk_ml1_kms": r["v_disk_ml1_kms"],
            "v_disk2_per_unit_upsilon_km2_s2": fmt(vdisk * vdisk),
            "v_bulge_ml1_kms": r["v_bulge_ml1_kms"],
            "v_bulge2_per_unit_upsilon_km2_s2": fmt(vbul * vbul),
            "sb_disk_lsun_pc2": r["sb_disk_lsun_pc2"],
            "sb_bulge_lsun_pc2": r["sb_bulge_lsun_pc2"],
            "sigma_disk_per_unit_upsilon_msun_pc2": fmt(sbd),
            "sigma_bulge_per_unit_upsilon_msun_pc2": fmt(sbb),
            "sigma_gas_msun_pc2": "",
            "sigma_gas_status": (
                "HI_profile_unavailable_in_Hua2025_compilation"
                if g in HI_PROFILE_UNAVAILABLE_HUA2025
                else "HI_profile_reported_available_in_literature_not_yet_ingested"
            ),
            "source_current_velocity_status": "self_consistent_model_velocity_required_at_fit_stage",
            "vobs_used_as_source_current": "0",
        })

    args.basis_out.parent.mkdir(parents=True, exist_ok=True)
    with args.basis_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=basis_fields, lineterminator="\r\n")
        w.writeheader(); w.writerows(basis_rows)

    by_galaxy_master = {}
    for r in master:
        by_galaxy_master.setdefault(r["galaxy"], []).append(r)

    availability_fields = [
        "galaxy", "stationary_role", "n_rotation_points",
        "hi_profile_in_sparc_2016_public_massmodel_release",
        "hi_profile_reported_available_hua2025",
        "hi_profile_acquired_in_repository",
        "primary_source_reconstruction_status", "note",
    ]
    availability_rows = []
    for g in galaxies:
        reported = g not in HI_PROFILE_UNAVAILABLE_HUA2025
        availability_rows.append({
            "galaxy": g,
            "stationary_role": split_by_galaxy[g][role_col],
            "n_rotation_points": str(len(by_galaxy_master[g])),
            "hi_profile_in_sparc_2016_public_massmodel_release": "0",
            "hi_profile_reported_available_hua2025": "1" if reported else "0",
            "hi_profile_acquired_in_repository": "0",
            "primary_source_reconstruction_status": (
                "await_external_HI_profile_ingestion" if reported
                else "requires_predeclared_missing_profile_policy"
            ),
            "note": (
                "Hua et al. 2025 identify this galaxy among six SPARC systems whose rotation-curve references lack radial HI profiles."
                if not reported else
                "Radial HI profile reported available in the literature compilation; exact source/provenance must be ingested before use."
            ),
        })

    args.availability_out.parent.mkdir(parents=True, exist_ok=True)
    with args.availability_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=availability_fields, lineterminator="\r\n")
        w.writeheader(); w.writerows(availability_rows)

    unavailable = [r["galaxy"] for r in availability_rows if r["hi_profile_reported_available_hua2025"] == "0"]
    unavailable_roles = {g: split_by_galaxy[g][role_col] for g in unavailable}
    summary = {
        "status": "SOURCE_BASIS_BUILT_GAS_PROFILES_NOT_YET_INGESTED",
        "n_galaxies": len(galaxies),
        "n_rows": len(basis_rows),
        "n_hi_profiles_reported_available_hua2025": len(galaxies) - len(unavailable),
        "n_hi_profiles_reported_unavailable_hua2025": len(unavailable),
        "hi_profile_unavailable_galaxies_in_frozen_149": unavailable,
        "hi_profile_unavailable_roles": unavailable_roles,
        "master_sha256": sha256_file(args.master),
        "split_sha256": sha256_file(args.split),
        "basis_sha256": sha256_file(args.basis_out),
        "availability_sha256": sha256_file(args.availability_out),
        "signed_gas_rule": "v_gas2_signed = Vgas * abs(Vgas)",
        "stellar_surface_density_rule": "Sigma_disk = Upsilon_d * SBdisk; Sigma_bulge = Upsilon_b * SBbulge",
        "gas_surface_density_rule": "Do not substitute Vgas for Sigma_gas. Ingest independently sourced radial HI profiles; any missing-profile reconstruction requires separate pre-fit validation.",
        "source_current_velocity_rule": "Use self-consistent model velocity V(R); Vobs is target data and is not used as source current.",
        "contains_persistence_parameters": False,
    }
    args.summary_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
