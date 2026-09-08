#!/usr/bin/env python3
"""Fail-closed intake validation for an author-supplied stationary H I package.

Permission is validated before profile metadata or numerical profile content is
opened. The validator never transforms source values and never evaluates a
velocity, source current, residual, persistence quantity, or blind outcome.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = REPO_ROOT / (
    "validation/stationary/lelli_hi_author_package_intake_schema_v1.json"
)
DEFAULT_REQUEST_MANIFEST = REPO_ROOT / (
    "data/stationary/source_reconstruction/"
    "lelli_hi_profile_request_manifest_v1.csv"
)
EXPECTED_CONTRACT_SHA256 = (
    "584e496f97417f07353adc9cd755c20951841ab70bb7b9518a4a209856ae4a28"
)


@dataclass(frozen=True)
class IntakeOutcome:
    report: dict[str, Any]
    private_errors: dict[str, list[dict[str, str]]]
    exit_code: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def read_csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            return []


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def error(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def clean_csv_row(raw: dict[Any, Any]) -> dict[str, str] | None:
    if None in raw or any(value is not None and not isinstance(value, str) for value in raw.values()):
        return None
    return {str(key): (value or "").strip() for key, value in raw.items()}


def add_gate(
    report: dict[str, Any],
    private_errors: dict[str, list[dict[str, str]]],
    name: str,
    errors: list[dict[str, str]],
    disclose_details: bool,
) -> None:
    private_errors[name] = errors
    gate: dict[str, Any] = {
        "name": name,
        "pass": not errors,
        "n_errors": len(errors),
        "error_codes": sorted({item["code"] for item in errors}),
    }
    if disclose_details and errors:
        gate["errors"] = errors
    report["gates"].append(gate)


def finish(
    report: dict[str, Any],
    private_errors: dict[str, list[dict[str, str]]],
    status: str,
    passed: bool,
) -> IntakeOutcome:
    report["status"] = status
    report["all_intake_gates_pass"] = passed
    report["eligible_for_version_2_staging"] = passed
    return IntakeOutcome(report=report, private_errors=private_errors, exit_code=0 if passed else 2)


def parse_finite_float(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def load_permission(path: Path, contract: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [error("PERMISSION_RECORD_MISSING", "permission record does not exist")]
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [error("PERMISSION_RECORD_UNREADABLE", type(exc).__name__)]

    if not isinstance(payload, dict):
        return {}, [error("PERMISSION_RECORD_NOT_OBJECT", "top-level JSON value must be an object")]

    spec = contract["permission_record"]
    expected_fields = spec["required_exact_fields"]
    if set(payload) != set(expected_fields) or len(payload) != len(expected_fields):
        errors.append(
            error(
                "PERMISSION_FIELDS_MISMATCH",
                f"expected exact fields {expected_fields}; received {list(payload)}",
            )
        )
    if payload.get("schema_version") != spec["schema_version"]:
        errors.append(error("PERMISSION_SCHEMA_VERSION_MISMATCH", "unexpected schema version"))
    if payload.get("template_only") is not False:
        errors.append(error("PERMISSION_TEMPLATE_NOT_USABLE", "template_only must be false"))

    status = payload.get("record_status")
    if status not in spec["allowed_record_statuses"]:
        errors.append(error("PERMISSION_STATUS_INVALID", "record_status is not allowed"))

    boolean_fields = [
        "template_only",
        "data_use_authorized",
        "source_files_redistribution_authorized",
        "derived_profile_redistribution_authorized",
        "public_metadata_authorized",
        "hash_disclosure_authorized",
    ]
    for field in boolean_fields:
        if not isinstance(payload.get(field), bool):
            errors.append(error("PERMISSION_BOOLEAN_INVALID", f"{field} must be boolean"))

    authorized = status in spec["authorized_record_statuses"]
    if authorized:
        for field in [
            "provider",
            "date_received",
            "citation",
            "acknowledgement",
            "conditions",
            "permission_evidence_location",
        ]:
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                errors.append(error("PERMISSION_REQUIRED_TEXT_MISSING", f"{field} is required"))
        evidence_location = payload.get("permission_evidence_location")
        if isinstance(evidence_location, str) and evidence_location.strip() == "OUTSIDE_PUBLIC_REPOSITORY":
            errors.append(
                error(
                    "PERMISSION_EVIDENCE_PLACEHOLDER",
                    "replace the template placeholder with a private evidence reference",
                )
            )
        try:
            date.fromisoformat(str(payload.get("date_received", "")))
        except ValueError:
            errors.append(error("PERMISSION_DATE_INVALID", "date_received must be YYYY-MM-DD"))

    if payload.get("data_use_authorized") is not True:
        errors.append(error("DATA_USE_NOT_AUTHORIZED", "numerical use is not explicitly authorized"))

    source_redistribution = payload.get("source_files_redistribution_authorized")
    if status == "authorized_restricted" and source_redistribution is not False:
        errors.append(error("RESTRICTED_STATUS_INCONSISTENT", "restricted status requires no source redistribution"))
    if status == "authorized_public_redistribution" and source_redistribution is not True:
        errors.append(error("PUBLIC_STATUS_INCONSISTENT", "public status requires source redistribution authorization"))
    if status not in spec["authorized_record_statuses"] and source_redistribution is True:
        errors.append(error("REDISTRIBUTION_WITHOUT_USE_AUTHORITY", "redistribution cannot precede use authorization"))
    return payload, errors


def load_request_manifest(
    path: Path, contract: dict[str, Any]
) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    expected = contract["request_manifest"]
    if not path.is_file():
        return {}, [error("REQUEST_MANIFEST_MISSING", "frozen request manifest is missing")]
    actual_sha = sha256_file(path)
    if actual_sha != expected["sha256"]:
        errors.append(error("REQUEST_MANIFEST_HASH_MISMATCH", "request manifest does not match frozen SHA-256"))
    try:
        header, rows = read_csv_rows(path)
    except (OSError, csv.Error) as exc:
        return {}, errors + [error("REQUEST_MANIFEST_UNREADABLE", type(exc).__name__)]
    required = {
        "galaxy",
        "stationary_role",
        "request_from_lelli",
        "request_reason",
    }
    if not required.issubset(header):
        errors.append(error("REQUEST_MANIFEST_SCHEMA_MISMATCH", "required manifest columns are missing"))
        return {}, errors

    index: dict[str, dict[str, str]] = {}
    for row in rows:
        galaxy = row["galaxy"].strip()
        if galaxy in index:
            errors.append(error("REQUEST_MANIFEST_DUPLICATE_GALAXY", galaxy))
        index[galaxy] = row

    requested = [row for row in rows if row["request_from_lelli"].strip() == "1"]
    role_counts = Counter(row["stationary_role"].strip() for row in requested)
    certified = [
        row
        for row in rows
        if row["request_reason"].strip() == "already_certified_public_profile_no_request"
    ]
    unavailable = [
        row
        for row in rows
        if row["request_reason"].strip().startswith("reported_unavailable_in_169")
    ]
    if len(rows) != expected["n_frozen"] or len(index) != expected["n_frozen"]:
        errors.append(error("REQUEST_MANIFEST_FROZEN_COUNT_MISMATCH", f"rows={len(rows)} unique={len(index)}"))
    if len(requested) != expected["n_request"]:
        errors.append(error("REQUEST_MANIFEST_REQUEST_COUNT_MISMATCH", f"requested={len(requested)}"))
    if role_counts != Counter(expected["request_role_counts"]):
        errors.append(error("REQUEST_MANIFEST_ROLE_COUNT_MISMATCH", str(dict(role_counts))))
    if len(certified) != expected["n_already_certified_no_request"]:
        errors.append(error("REQUEST_MANIFEST_CERTIFIED_COUNT_MISMATCH", f"certified={len(certified)}"))
    if len(unavailable) != expected["n_reported_unavailable_no_request"]:
        errors.append(error("REQUEST_MANIFEST_UNAVAILABLE_COUNT_MISMATCH", f"unavailable={len(unavailable)}"))
    return index, errors


def validate_metadata(
    path: Path,
    contract: dict[str, Any],
    request_index: dict[str, dict[str, str]],
) -> tuple[dict[str, dict[str, str]], list[dict[str, str]], bool, bool]:
    errors: list[dict[str, str]] = []
    try:
        header = read_csv_header(path)
    except FileNotFoundError:
        return {}, [error("METADATA_FILE_MISSING", "metadata CSV does not exist")], False, False
    except (OSError, csv.Error) as exc:
        return {}, [error("METADATA_FILE_UNREADABLE", type(exc).__name__)], False, False

    spec = contract["metadata_csv"]
    expected_header = spec["required_exact_header"]
    if header != expected_header:
        return {}, [
            error(
                "METADATA_HEADER_MISMATCH",
                f"expected exact ordered header {expected_header}; received {header}",
            )
        ], True, False
    try:
        _, rows = read_csv_rows(path)
    except (OSError, csv.Error) as exc:
        return {}, [error("METADATA_FILE_UNREADABLE", type(exc).__name__)], True, False
    if not rows:
        return {}, [error("METADATA_EMPTY", "at least one requested profile is required")], True, True

    metadata: dict[str, dict[str, str]] = {}
    min_rows = int(contract["numerical_rules"]["minimum_rows_per_profile"])
    allowed = spec["allowed_values"]
    helium_factors = spec["helium_multiplier_by_convention"]
    for row_number, raw in enumerate(rows, start=2):
        row = clean_csv_row(raw)
        if row is None:
            errors.append(error("METADATA_ROW_WIDTH_MISMATCH", f"row {row_number}"))
            continue
        galaxy = row["galaxy"]
        for field in spec["required_nonempty_fields"]:
            if not row[field]:
                errors.append(error("METADATA_REQUIRED_VALUE_MISSING", f"row {row_number}: {field}"))
        if not galaxy:
            continue
        if galaxy in metadata:
            errors.append(error("METADATA_DUPLICATE_GALAXY", galaxy))
            continue
        metadata[galaxy] = row

        manifest_row = request_index.get(galaxy)
        if manifest_row is None:
            errors.append(error("GALAXY_OUTSIDE_FROZEN_SAMPLE", galaxy))
        elif manifest_row["request_from_lelli"].strip() != "1":
            reason = manifest_row["request_reason"].strip()
            code = (
                "ALREADY_CERTIFIED_GALAXY_REJECTED"
                if reason == "already_certified_public_profile_no_request"
                else "NO_REQUEST_GALAXY_REJECTED"
            )
            errors.append(error(code, f"{galaxy}: {reason}"))
        elif row["stationary_role"] != manifest_row["stationary_role"].strip():
            errors.append(error("STATIONARY_ROLE_MISMATCH", galaxy))

        for field, values in allowed.items():
            if row[field] not in values:
                errors.append(error("METADATA_ENUM_INVALID", f"{galaxy}: {field}"))

        try:
            expected_rows = int(row["profile_rows_expected"])
            if str(expected_rows) != row["profile_rows_expected"] or expected_rows < min_rows:
                raise ValueError
        except ValueError:
            errors.append(error("PROFILE_ROWS_EXPECTED_INVALID", galaxy))

        distance = parse_finite_float(row["source_distance_mpc"])
        if distance is None or distance <= 0:
            errors.append(error("SOURCE_DISTANCE_INVALID", galaxy))
        inclination = parse_finite_float(row["source_inclination_deg"])
        if inclination is None or not (0 < inclination <= 90):
            errors.append(error("SOURCE_INCLINATION_INVALID", galaxy))

        factor = parse_finite_float(row["helium_multiplier_relative_to_raw_hi"])
        expected_factor = helium_factors.get(row["helium_convention"])
        if factor is None or expected_factor is None or not math.isclose(
            factor, float(expected_factor), rel_tol=0, abs_tol=1e-12
        ):
            errors.append(error("HELIUM_CONVENTION_FACTOR_MISMATCH", galaxy))
    return metadata, errors, True, True


def forbidden_profile_headers(header: list[str], contract: dict[str, Any]) -> list[str]:
    tokens = contract["profiles_csv"]["forbidden_normalized_header_tokens"]
    forbidden: list[str] = []
    for field in header:
        normalized = normalized_header(field)
        if normalized in tokens or any(len(token) >= 4 and token in normalized for token in tokens):
            forbidden.append(field)
    return forbidden


def validate_profiles(
    path: Path,
    contract: dict[str, Any],
    metadata: dict[str, dict[str, str]],
) -> tuple[int, list[dict[str, str]], bool]:
    errors: list[dict[str, str]] = []
    try:
        header = read_csv_header(path)
    except FileNotFoundError:
        return 0, [error("PROFILES_FILE_MISSING", "profiles CSV does not exist")], False
    except (OSError, csv.Error) as exc:
        return 0, [error("PROFILES_FILE_UNREADABLE", type(exc).__name__)], False

    forbidden = forbidden_profile_headers(header, contract)
    if forbidden:
        return 0, [error("FORBIDDEN_OUTCOME_COLUMN", ",".join(forbidden))], False
    expected_header = contract["profiles_csv"]["required_exact_header"]
    if header != expected_header:
        return 0, [
            error(
                "PROFILES_HEADER_MISMATCH",
                f"expected exact ordered header {expected_header}; received {header}",
            )
        ], False

    try:
        _, rows = read_csv_rows(path)
    except (OSError, csv.Error) as exc:
        return 0, [error("PROFILES_FILE_UNREADABLE", type(exc).__name__)], False
    if not rows:
        return 0, [error("PROFILES_EMPTY", "profile table contains no rows")], True

    by_galaxy: dict[str, list[tuple[int, float]]] = defaultdict(list)
    uncertainty_presence: dict[str, list[bool]] = defaultdict(list)
    for row_number, raw in enumerate(rows, start=2):
        row = clean_csv_row(raw)
        if row is None:
            errors.append(error("PROFILE_ROW_WIDTH_MISMATCH", f"row {row_number}"))
            continue
        galaxy = row["galaxy"]
        if galaxy not in metadata:
            errors.append(error("PROFILE_GALAXY_NOT_IN_METADATA", f"row {row_number}: {galaxy}"))
            continue
        try:
            sample_index = int(row["sample_index"])
            if str(sample_index) != row["sample_index"] or sample_index < 0:
                raise ValueError
        except ValueError:
            errors.append(error("SAMPLE_INDEX_INVALID", f"row {row_number}: {galaxy}"))
            continue

        radius = parse_finite_float(row["radius_value"])
        sigma = parse_finite_float(row["sigma_source_msun_pc2"])
        if radius is None or radius < 0:
            errors.append(error("RADIUS_INVALID", f"row {row_number}: {galaxy}"))
        if sigma is None or sigma < 0:
            errors.append(error("SURFACE_DENSITY_INVALID", f"row {row_number}: {galaxy}"))
        if radius is not None:
            by_galaxy[galaxy].append((sample_index, radius))

        minus_text = row["sigma_err_minus_msun_pc2"]
        plus_text = row["sigma_err_plus_msun_pc2"]
        if bool(minus_text) != bool(plus_text):
            errors.append(error("UNCERTAINTY_PAIR_INCOMPLETE", f"row {row_number}: {galaxy}"))
            uncertainty_presence[galaxy].append(False)
        elif not minus_text:
            uncertainty_presence[galaxy].append(False)
        else:
            minus = parse_finite_float(minus_text)
            plus = parse_finite_float(plus_text)
            if minus is None or plus is None or minus < 0 or plus < 0:
                errors.append(error("UNCERTAINTY_INVALID", f"row {row_number}: {galaxy}"))
            elif metadata[galaxy]["uncertainty_convention"] == "symmetric_1sigma" and not math.isclose(
                minus, plus, rel_tol=1e-12, abs_tol=1e-12
            ):
                errors.append(error("SYMMETRIC_UNCERTAINTY_MISMATCH", f"row {row_number}: {galaxy}"))
            uncertainty_presence[galaxy].append(True)

    profile_galaxies = set(by_galaxy)
    metadata_galaxies = set(metadata)
    if profile_galaxies != metadata_galaxies:
        errors.append(
            error(
                "PROFILE_METADATA_MEMBERSHIP_MISMATCH",
                f"profile_only={sorted(profile_galaxies - metadata_galaxies)}; metadata_only={sorted(metadata_galaxies - profile_galaxies)}",
            )
        )

    origin = int(contract["numerical_rules"]["sample_index_origin"])
    for galaxy, samples in by_galaxy.items():
        expected_count = int(metadata[galaxy]["profile_rows_expected"])
        if len(samples) != expected_count:
            errors.append(error("PROFILE_ROW_COUNT_MISMATCH", galaxy))
        indices = [sample_index for sample_index, _ in samples]
        if indices != list(range(origin, origin + len(samples))):
            errors.append(error("SAMPLE_INDEX_SEQUENCE_INVALID", galaxy))
        radii = [radius for _, radius in samples]
        if any(right <= left for left, right in zip(radii, radii[1:])):
            errors.append(error("RADIUS_NOT_STRICTLY_INCREASING", galaxy))

        convention = metadata[galaxy]["uncertainty_convention"]
        presence = uncertainty_presence[galaxy]
        if convention == "not_provided" and any(presence):
            errors.append(error("UNEXPECTED_UNCERTAINTIES", galaxy))
        if convention != "not_provided" and (not presence or not all(presence)):
            errors.append(error("REQUIRED_UNCERTAINTIES_MISSING", galaxy))
    return len(rows), errors, True


def validate_package(
    *,
    package_root: Path,
    permission_record: Path,
    metadata_path: Path,
    profiles_path: Path,
    report_path: Path,
    contract_path: Path = DEFAULT_CONTRACT,
    request_manifest_path: Path = DEFAULT_REQUEST_MANIFEST,
    repo_root: Path = REPO_ROOT,
    allow_repository_contained_public_data: bool = False,
    synthetic_fixture: bool = False,
) -> IntakeOutcome:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract_sha256 = sha256_file(contract_path)
    report: dict[str, Any] = {
        "status": "LELLI_HI_AUTHOR_PACKAGE_INTAKE_NOT_RUN",
        "contract_version": contract["schema_version"],
        "contract_status": contract["status"],
        "contract_sha256": contract_sha256,
        "synthetic_fixture": synthetic_fixture,
        "gates": [],
        "metadata_header_read": False,
        "metadata_rows_read": False,
        "profile_header_read": False,
        "profile_value_rows_read": False,
        "normalization_applied": False,
        "interpolation_or_continuation_applied": False,
        "source_current_evaluated": False,
        "blind_outcome_inspected": False,
        "version_1_rewritten": False,
        "global_source_gate_unlocked": False,
        "membership": None,
        "disclosed_package_sha256": None,
        "boundary": contract["boundary"],
    }
    private_errors: dict[str, list[dict[str, str]]] = {}

    contract_errors: list[dict[str, str]] = []
    if contract_sha256 != EXPECTED_CONTRACT_SHA256:
        contract_errors.append(
            error(
                "INTAKE_CONTRACT_HASH_MISMATCH",
                "machine-readable intake contract does not match the frozen validator",
            )
        )
    add_gate(report, private_errors, "contract_integrity", contract_errors, synthetic_fixture)
    if contract_errors:
        return finish(
            report,
            private_errors,
            "LELLI_HI_AUTHOR_PACKAGE_INTAKE_CONTRACT_BLOCKED",
            False,
        )

    permission, permission_errors = load_permission(permission_record, contract)
    if synthetic_fixture and (
        permission.get("provider") != "Synthetic validator fixture"
        or permission.get("citation") != "SYNTHETIC TEST ONLY"
        or permission.get("conditions") != "synthetic_fixture_only"
    ):
        permission_errors.append(
            error(
                "SYNTHETIC_FIXTURE_MARKERS_MISSING",
                "synthetic mode is reserved for the bundled synthetic test harness",
            )
        )
    disclose_metadata = synthetic_fixture or permission.get("public_metadata_authorized") is True
    disclose_hashes = synthetic_fixture or permission.get("hash_disclosure_authorized") is True
    add_gate(report, private_errors, "permission", permission_errors, synthetic_fixture)
    if permission_errors:
        return finish(
            report,
            private_errors,
            "LELLI_HI_AUTHOR_PACKAGE_INTAKE_PERMISSION_BLOCKED",
            False,
        )

    package_root = package_root.resolve()
    permission_record = permission_record.resolve()
    metadata_path = metadata_path.resolve()
    profiles_path = profiles_path.resolve()
    report_path = report_path.resolve()
    repo_root = repo_root.resolve()
    storage_errors: list[dict[str, str]] = []
    if not package_root.is_dir():
        storage_errors.append(error("PACKAGE_ROOT_MISSING", "package root is not a directory"))
    for label, path in [
        ("permission_record", permission_record),
        ("metadata", metadata_path),
        ("profiles", profiles_path),
    ]:
        if not path_is_within(path, package_root):
            storage_errors.append(error("PACKAGE_MEMBER_OUTSIDE_ROOT", label))
    package_inside_repo = path_is_within(package_root, repo_root)
    public_source_files = permission["source_files_redistribution_authorized"] is True
    if package_inside_repo and not public_source_files:
        storage_errors.append(error("RESTRICTED_PACKAGE_INSIDE_REPOSITORY", "restricted package resolves inside repository"))
    if package_inside_repo and public_source_files and not allow_repository_contained_public_data:
        storage_errors.append(error("PUBLIC_REPOSITORY_OVERRIDE_REQUIRED", "explicit override was not supplied"))
    if (
        path_is_within(report_path, repo_root)
        and not public_source_files
        and not synthetic_fixture
    ):
        storage_errors.append(error("RESTRICTED_REPORT_INSIDE_REPOSITORY", "first restricted report must remain external"))
    add_gate(report, private_errors, "storage_boundary", storage_errors, disclose_metadata)
    if storage_errors:
        return finish(
            report,
            private_errors,
            "LELLI_HI_AUTHOR_PACKAGE_INTAKE_STORAGE_BLOCKED",
            False,
        )

    request_index, manifest_errors = load_request_manifest(request_manifest_path, contract)
    add_gate(report, private_errors, "request_manifest_integrity", manifest_errors, disclose_metadata)
    if manifest_errors:
        return finish(
            report,
            private_errors,
            "LELLI_HI_AUTHOR_PACKAGE_INTAKE_MANIFEST_BLOCKED",
            False,
        )

    metadata, metadata_errors, metadata_header_read, metadata_rows_read = validate_metadata(
        metadata_path, contract, request_index
    )
    report["metadata_header_read"] = metadata_header_read
    report["metadata_rows_read"] = metadata_rows_read
    add_gate(report, private_errors, "metadata_schema_and_membership", metadata_errors, disclose_metadata)
    if metadata_errors:
        return finish(
            report,
            private_errors,
            "LELLI_HI_AUTHOR_PACKAGE_INTAKE_METADATA_BLOCKED",
            False,
        )

    requested_ids = {
        galaxy
        for galaxy, row in request_index.items()
        if row["request_from_lelli"].strip() == "1"
    }
    role_counts = Counter(row["stationary_role"] for row in metadata.values())
    request_complete = set(metadata) == requested_ids
    if disclose_metadata:
        report["membership"] = {
            "n_profiles": len(metadata),
            "role_counts": {
                "calibration": role_counts["calibration"],
                "blind": role_counts["blind"],
            },
            "request_complete": request_complete,
            "n_missing_from_current_request": len(requested_ids - set(metadata)),
            "galaxies": sorted(metadata),
        }
    else:
        report["membership"] = {
            "disclosure": "withheld_by_permission_record",
            "n_profiles": None,
            "role_counts": None,
            "request_complete": None,
            "n_missing_from_current_request": None,
            "galaxies": None,
        }

    try:
        profile_header = read_csv_header(profiles_path)
        report["profile_header_read"] = True
    except (FileNotFoundError, OSError, csv.Error):
        profile_header = []
    row_count, profile_errors, values_read = validate_profiles(
        profiles_path, contract, metadata
    )
    report["profile_value_rows_read"] = values_read
    if profile_header and forbidden_profile_headers(profile_header, contract):
        report["profile_value_rows_read"] = False
    add_gate(report, private_errors, "numerical_schema_and_geometry", profile_errors, disclose_metadata)
    if profile_errors:
        return finish(
            report,
            private_errors,
            "LELLI_HI_AUTHOR_PACKAGE_INTAKE_NUMERICAL_BLOCKED",
            False,
        )

    if disclose_metadata and report["membership"] is not None:
        report["membership"]["n_profile_rows"] = row_count
    if disclose_hashes:
        report["disclosed_package_sha256"] = {
            "permission_record": sha256_file(permission_record),
            "metadata": sha256_file(metadata_path),
            "profiles": sha256_file(profiles_path),
        }
    add_gate(report, private_errors, "no_transform_or_outcome_boundary", [], disclose_metadata)
    return finish(
        report,
        private_errors,
        "LELLI_HI_AUTHOR_PACKAGE_INTAKE_VALID",
        True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--permission-record", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--profiles", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--request-manifest", type=Path, default=DEFAULT_REQUEST_MANIFEST)
    parser.add_argument(
        "--allow-repository-contained-public-data",
        action="store_true",
        help="Allow an in-repository package only when source-file redistribution is authorized.",
    )
    parser.add_argument(
        "--synthetic-fixture",
        action="store_true",
        help="Label an explicitly synthetic validation fixture; never use for an author package.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    outcome = validate_package(
        package_root=args.package_root,
        permission_record=args.permission_record,
        metadata_path=args.metadata,
        profiles_path=args.profiles,
        report_path=args.report,
        request_manifest_path=args.request_manifest,
        allow_repository_contained_public_data=args.allow_repository_contained_public_data,
        synthetic_fixture=args.synthetic_fixture,
    )
    blocked_report_codes = {
        item["code"]
        for item in outcome.private_errors.get("storage_boundary", [])
    }
    if "RESTRICTED_REPORT_INSIDE_REPOSITORY" not in blocked_report_codes:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(outcome.report, indent=2) + "\n", encoding="utf-8")
    else:
        print(
            "Restricted intake report was not written inside the public repository.",
            file=sys.stderr,
        )
    print(json.dumps(outcome.report, indent=2))
    raise SystemExit(outcome.exit_code)


if __name__ == "__main__":
    main()
