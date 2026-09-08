#!/usr/bin/env python3
"""Synthetic-only tests for the frozen Lelli H I author-package intake validator."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
from typing import Any, Callable

from validate_lelli_hi_author_package_v1 import (
    EXPECTED_CONTRACT_SHA256,
    validate_package,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / (
    "validation/stationary/lelli_hi_author_package_intake_schema_v1.json"
)
REQUEST_MANIFEST = REPO_ROOT / (
    "data/stationary/source_reconstruction/"
    "lelli_hi_profile_request_manifest_v1.csv"
)
OUTPUT = REPO_ROOT / (
    "validation/stationary/"
    "lelli_hi_author_package_validator_v1_synthetic_validation.json"
)
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
PERMISSION_FIELDS = CONTRACT["permission_record"]["required_exact_fields"]
METADATA_HEADER = CONTRACT["metadata_csv"]["required_exact_header"]
PROFILES_HEADER = CONTRACT["profiles_csv"]["required_exact_header"]


def request_rows() -> list[dict[str, str]]:
    with REQUEST_MANIFEST.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


REQUEST_ROWS = request_rows()
REQUESTED = [row for row in REQUEST_ROWS if row["request_from_lelli"] == "1"]
CERTIFIED = [
    row
    for row in REQUEST_ROWS
    if row["request_reason"] == "already_certified_public_profile_no_request"
]


def permission(status: str = "authorized_restricted") -> dict[str, Any]:
    public = status == "authorized_public_redistribution"
    authorized = status in {"authorized_restricted", "authorized_public_redistribution"}
    values: dict[str, Any] = {
        "schema_version": "lelli_hi_author_package_permission_v1",
        "template_only": False,
        "record_status": status,
        "provider": "Synthetic validator fixture",
        "date_received": "2026-08-14" if authorized else "",
        "data_use_authorized": authorized,
        "source_files_redistribution_authorized": public,
        "derived_profile_redistribution_authorized": False,
        "public_metadata_authorized": False,
        "hash_disclosure_authorized": False,
        "citation": "SYNTHETIC TEST ONLY" if authorized else "",
        "acknowledgement": "none_requested" if authorized else "",
        "conditions": "synthetic_fixture_only" if authorized else "",
        "permission_evidence_location": "private://synthetic-permission-evidence",
    }
    return {field: values[field] for field in PERMISSION_FIELDS}


def metadata_row(source: dict[str, str], **changes: str) -> dict[str, str]:
    row = {
        "galaxy": source["galaxy"],
        "stationary_role": source["stationary_role"],
        "source_galaxy_id": f"SYNTHETIC_{source['galaxy']}",
        "profile_rows_expected": "2",
        "radius_unit": "arcsec",
        "surface_density_unit": "Msun_pc^-2",
        "helium_convention": "raw_hi",
        "helium_multiplier_relative_to_raw_hi": "1.0",
        "source_distance_mpc": "10.0",
        "source_inclination_deg": "60.0",
        "inclination_treatment": "source_profile_deprojected",
        "beam_description": "synthetic beam; no observational meaning",
        "radial_sampling_description": "two synthetic samples",
        "uncertainty_convention": "not_provided",
        "uncertainty_description": "not provided in synthetic fixture",
        "source_citation": "SYNTHETIC TEST ONLY",
        "source_profile_reference": "synthetic in-memory fixture",
        "numerical_value_state": "source_values_unmodified",
    }
    row.update(changes)
    return row


def profile_rows(galaxy: str, **changes: str) -> list[dict[str, str]]:
    rows = [
        {
            "galaxy": galaxy,
            "sample_index": "0",
            "radius_value": "12345.678901",
            "sigma_source_msun_pc2": "8.25",
            "sigma_err_minus_msun_pc2": "",
            "sigma_err_plus_msun_pc2": "",
        },
        {
            "galaxy": galaxy,
            "sample_index": "1",
            "radius_value": "23456.789012",
            "sigma_source_msun_pc2": "4.125",
            "sigma_err_minus_msun_pc2": "",
            "sigma_err_plus_msun_pc2": "",
        },
    ]
    for row in rows:
        row.update(changes)
    return rows


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_package(
    root: Path,
    *,
    metadata_rows: list[dict[str, str]] | None,
    profiles: list[dict[str, str]] | None,
    permission_record: dict[str, Any] | None = None,
    metadata_header: list[str] = METADATA_HEADER,
    profiles_header: list[str] = PROFILES_HEADER,
) -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    permission_path = root / "permission_record.json"
    metadata_path = root / "metadata.csv"
    profiles_path = root / "profiles.csv"
    permission_path.write_text(
        json.dumps(permission_record or permission(), indent=2) + "\n",
        encoding="utf-8",
    )
    if metadata_rows is not None:
        write_csv(metadata_path, metadata_header, metadata_rows)
    if profiles is not None:
        write_csv(profiles_path, profiles_header, profiles)
    return permission_path, metadata_path, profiles_path


def run_validation(
    root: Path,
    paths: tuple[Path, Path, Path],
    *,
    request_manifest: Path = REQUEST_MANIFEST,
    repo_root: Path = REPO_ROOT,
    allow_repository_contained_public_data: bool = False,
):
    permission_path, metadata_path, profiles_path = paths
    return validate_package(
        package_root=root,
        permission_record=permission_path,
        metadata_path=metadata_path,
        profiles_path=profiles_path,
        report_path=root / "intake_report.json",
        contract_path=CONTRACT_PATH,
        request_manifest_path=request_manifest,
        repo_root=repo_root,
        allow_repository_contained_public_data=allow_repository_contained_public_data,
        synthetic_fixture=True,
    )


def has_error(outcome, gate: str, code: str) -> bool:
    return code in {item["code"] for item in outcome.private_errors.get(gate, [])}


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def test_valid_partial_restricted(base: Path) -> str:
    selected = [
        next(row for row in REQUESTED if row["stationary_role"] == "calibration"),
        next(row for row in REQUESTED if row["stationary_role"] == "blind"),
    ]
    root = base / "valid_partial"
    metadata = [metadata_row(row) for row in selected]
    profiles = [item for row in selected for item in profile_rows(row["galaxy"])]
    outcome = run_validation(root, write_package(root, metadata_rows=metadata, profiles=profiles))
    require(outcome.exit_code == 0, outcome.report["status"])
    require(outcome.report["membership"]["n_profiles"] == 2, "partial membership count")
    require(outcome.report["membership"]["request_complete"] is False, "partial marked complete")
    rendered = json.dumps(outcome.report)
    require("12345.678901" not in rendered and "23456.789012" not in rendered, "numeric value leaked")
    return outcome.report["status"]


def test_valid_full_request(base: Path) -> str:
    root = base / "valid_full"
    metadata = [metadata_row(row) for row in REQUESTED]
    profiles = [item for row in REQUESTED for item in profile_rows(row["galaxy"])]
    outcome = run_validation(root, write_package(root, metadata_rows=metadata, profiles=profiles))
    require(outcome.exit_code == 0, outcome.report["status"])
    require(outcome.report["membership"]["n_profiles"] == 112, "full membership count")
    require(outcome.report["membership"]["request_complete"] is True, "full package not complete")
    require(
        outcome.report["membership"]["role_counts"] == {"calibration": 77, "blind": 35},
        "role counts changed",
    )
    require(outcome.report["global_source_gate_unlocked"] is False, "global gate unlocked")
    return outcome.report["status"]


def test_permission_blocks_before_content(base: Path) -> str:
    root = base / "permission_block"
    paths = write_package(
        root,
        metadata_rows=None,
        profiles=None,
        permission_record=permission("permission_pending"),
    )
    outcome = run_validation(root, paths)
    require(has_error(outcome, "permission", "DATA_USE_NOT_AUTHORIZED"), "authorization gate absent")
    require(not outcome.report["metadata_header_read"], "metadata header read before permission")
    require(not outcome.report["metadata_rows_read"], "metadata read before permission")
    require(not outcome.report["profile_header_read"], "profile header read before permission")
    require(not outcome.report["profile_value_rows_read"], "profile values read before permission")
    return outcome.report["status"]


def test_restricted_package_rejected_in_repo(base: Path) -> str:
    fake_repo = base / "fake_repo"
    root = fake_repo / "restricted_package"
    paths = write_package(root, metadata_rows=None, profiles=None)
    outcome = run_validation(root, paths, repo_root=fake_repo)
    require(
        has_error(outcome, "storage_boundary", "RESTRICTED_PACKAGE_INSIDE_REPOSITORY"),
        "restricted repository boundary absent",
    )
    require(not outcome.report["metadata_rows_read"], "metadata read after storage failure")
    return outcome.report["status"]


def test_public_package_requires_explicit_override(base: Path) -> str:
    fake_repo = base / "fake_public_repo"
    root = fake_repo / "authorized_public_package"
    selected = REQUESTED[0]
    paths = write_package(
        root,
        metadata_rows=[metadata_row(selected)],
        profiles=profile_rows(selected["galaxy"]),
        permission_record=permission("authorized_public_redistribution"),
    )
    blocked = run_validation(root, paths, repo_root=fake_repo)
    require(
        has_error(blocked, "storage_boundary", "PUBLIC_REPOSITORY_OVERRIDE_REQUIRED"),
        "public override gate absent",
    )
    allowed = run_validation(
        root,
        paths,
        repo_root=fake_repo,
        allow_repository_contained_public_data=True,
    )
    require(allowed.exit_code == 0, allowed.report["status"])
    return "override_required_then_valid"


def test_tampered_manifest_blocks_before_metadata(base: Path) -> str:
    root = base / "tampered_manifest_package"
    selected = REQUESTED[0]
    paths = write_package(root, metadata_rows=[metadata_row(selected)], profiles=None)
    tampered = base / "tampered_request_manifest.csv"
    tampered.write_bytes(REQUEST_MANIFEST.read_bytes() + b"\n")
    outcome = run_validation(root, paths, request_manifest=tampered)
    require(
        has_error(outcome, "request_manifest_integrity", "REQUEST_MANIFEST_HASH_MISMATCH"),
        "manifest hash gate absent",
    )
    require(not outcome.report["metadata_rows_read"], "metadata read after manifest failure")
    return outcome.report["status"]


def test_unknown_galaxy_blocks_metadata(base: Path) -> str:
    root = base / "unknown_galaxy"
    row = metadata_row(REQUESTED[0], galaxy="SYNTHETIC-NOT-IN-FROZEN-SAMPLE")
    outcome = run_validation(root, write_package(root, metadata_rows=[row], profiles=None))
    require(
        has_error(outcome, "metadata_schema_and_membership", "GALAXY_OUTSIDE_FROZEN_SAMPLE"),
        "unknown galaxy accepted",
    )
    require(not outcome.report["profile_header_read"], "profile opened after metadata failure")
    return outcome.report["status"]


def test_already_certified_galaxy_rejected(base: Path) -> str:
    root = base / "already_certified"
    outcome = run_validation(
        root,
        write_package(root, metadata_rows=[metadata_row(CERTIFIED[0])], profiles=None),
    )
    require(
        has_error(outcome, "metadata_schema_and_membership", "ALREADY_CERTIFIED_GALAXY_REJECTED"),
        "already-certified profile accepted",
    )
    return outcome.report["status"]


def test_role_mismatch_rejected(base: Path) -> str:
    root = base / "role_mismatch"
    selected = REQUESTED[0]
    wrong_role = "blind" if selected["stationary_role"] == "calibration" else "calibration"
    outcome = run_validation(
        root,
        write_package(
            root,
            metadata_rows=[metadata_row(selected, stationary_role=wrong_role)],
            profiles=None,
        ),
    )
    require(
        has_error(outcome, "metadata_schema_and_membership", "STATIONARY_ROLE_MISMATCH"),
        "role mismatch accepted",
    )
    return outcome.report["status"]


def test_missing_metadata_column_rejected(base: Path) -> str:
    root = base / "missing_metadata_column"
    outcome = run_validation(
        root,
        write_package(
            root,
            metadata_rows=[metadata_row(REQUESTED[0])],
            profiles=None,
            metadata_header=METADATA_HEADER[:-1],
        ),
    )
    require(
        has_error(outcome, "metadata_schema_and_membership", "METADATA_HEADER_MISMATCH"),
        "metadata schema mismatch accepted",
    )
    require(not outcome.report["metadata_rows_read"], "metadata values read after invalid header")
    return outcome.report["status"]


def test_duplicate_radius_rejected(base: Path) -> str:
    root = base / "duplicate_radius"
    selected = REQUESTED[0]
    profiles = profile_rows(selected["galaxy"])
    profiles[1]["radius_value"] = profiles[0]["radius_value"]
    outcome = run_validation(
        root,
        write_package(root, metadata_rows=[metadata_row(selected)], profiles=profiles),
    )
    require(
        has_error(outcome, "numerical_schema_and_geometry", "RADIUS_NOT_STRICTLY_INCREASING"),
        "duplicate radius accepted",
    )
    return outcome.report["status"]


def test_negative_surface_density_rejected(base: Path) -> str:
    root = base / "negative_sigma"
    selected = REQUESTED[0]
    profiles = profile_rows(selected["galaxy"])
    profiles[1]["sigma_source_msun_pc2"] = "-0.01"
    outcome = run_validation(
        root,
        write_package(root, metadata_rows=[metadata_row(selected)], profiles=profiles),
    )
    require(
        has_error(outcome, "numerical_schema_and_geometry", "SURFACE_DENSITY_INVALID"),
        "negative surface density accepted",
    )
    return outcome.report["status"]


def test_forbidden_outcome_column_rejected_before_values(base: Path) -> str:
    root = base / "forbidden_outcome_column"
    selected = REQUESTED[0]
    rows = profile_rows(selected["galaxy"])
    for row in rows:
        row["blind_residual"] = "DO_NOT_READ_THIS_VALUE"
    outcome = run_validation(
        root,
        write_package(
            root,
            metadata_rows=[metadata_row(selected)],
            profiles=rows,
            profiles_header=PROFILES_HEADER + ["blind_residual"],
        ),
    )
    require(
        has_error(outcome, "numerical_schema_and_geometry", "FORBIDDEN_OUTCOME_COLUMN"),
        "outcome column accepted",
    )
    require(not outcome.report["profile_value_rows_read"], "values read after forbidden header")
    return outcome.report["status"]


def test_uncertainty_convention_enforced(base: Path) -> str:
    root = base / "uncertainty_mismatch"
    selected = REQUESTED[0]
    metadata = metadata_row(
        selected,
        uncertainty_convention="symmetric_1sigma",
        uncertainty_description="synthetic symmetric errors",
    )
    outcome = run_validation(
        root,
        write_package(root, metadata_rows=[metadata], profiles=profile_rows(selected["galaxy"])),
    )
    require(
        has_error(outcome, "numerical_schema_and_geometry", "REQUIRED_UNCERTAINTIES_MISSING"),
        "missing declared uncertainties accepted",
    )
    return outcome.report["status"]


TESTS: list[tuple[str, Callable[[Path], str]]] = [
    ("valid_partial_restricted_package", test_valid_partial_restricted),
    ("valid_complete_112_profile_package", test_valid_full_request),
    ("permission_blocks_before_content", test_permission_blocks_before_content),
    ("restricted_package_rejected_in_repository", test_restricted_package_rejected_in_repo),
    ("public_package_requires_explicit_override", test_public_package_requires_explicit_override),
    ("frozen_manifest_hash_enforced", test_tampered_manifest_blocks_before_metadata),
    ("unknown_galaxy_rejected", test_unknown_galaxy_blocks_metadata),
    ("already_certified_galaxy_rejected", test_already_certified_galaxy_rejected),
    ("stationary_role_mismatch_rejected", test_role_mismatch_rejected),
    ("metadata_header_enforced", test_missing_metadata_column_rejected),
    ("duplicate_radius_rejected", test_duplicate_radius_rejected),
    ("negative_surface_density_rejected", test_negative_surface_density_rejected),
    ("forbidden_outcome_header_blocks_value_read", test_forbidden_outcome_column_rejected_before_values),
    ("uncertainty_convention_enforced", test_uncertainty_convention_enforced),
]


def main() -> None:
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="lelli-hi-intake-v1-") as directory:
        base = Path(directory)
        for name, test in TESTS:
            try:
                detail = test(base)
            except Exception as exc:  # synthetic validation artifact must record every case
                checks.append(
                    {
                        "name": name,
                        "pass": False,
                        "detail": type(exc).__name__,
                    }
                )
            else:
                checks.append({"name": name, "pass": True, "detail": detail})

    all_pass = all(item["pass"] for item in checks)
    result = {
        "status": (
            "LELLI_HI_AUTHOR_PACKAGE_VALIDATOR_V1_SYNTHETIC_PASS"
            if all_pass
            else "LELLI_HI_AUTHOR_PACKAGE_VALIDATOR_V1_SYNTHETIC_FAIL_CLOSED"
        ),
        "synthetic_only": True,
        "n_cases": len(checks),
        "n_pass": sum(bool(item["pass"]) for item in checks),
        "all_pass": all_pass,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "request_manifest_sha256": CONTRACT["request_manifest"]["sha256"],
        "request_boundary": {
            "n_request": 112,
            "role_counts": {"calibration": 77, "blind": 35},
        },
        "checks": checks,
        "boundary": (
            "Synthetic schema and control-flow validation only. No author-supplied data, "
            "velocity, residual, persistence prediction, model preference, L_A, C_A, "
            "tau_A, or blind outcome was read or evaluated."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
