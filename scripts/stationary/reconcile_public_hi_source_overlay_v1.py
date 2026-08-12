#!/usr/bin/env python3
"""Reconcile the frozen H I provenance inventory with public-source discoveries.

The original provenance file is retained unchanged for auditability. This script
creates a versioned reconciled view in which the public-source overlay supplies
the current effective acquisition status. It does not alter frozen sample roles,
fit any persistence parameter, or normalize profile data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        default="data/stationary/source_reconstruction/"
        "stationary_hi_profile_provenance_v1.csv",
    )
    ap.add_argument(
        "--overlay",
        default="data/stationary/source_reconstruction/"
        "stationary_public_hi_source_overlay_v1.csv",
    )
    ap.add_argument(
        "--out",
        default="data/stationary/source_reconstruction/"
        "stationary_hi_profile_provenance_reconciled_v1.csv",
    )
    ap.add_argument(
        "--summary",
        default="validation/stationary/"
        "stationary_hi_profile_provenance_reconciled_v1_summary.json",
    )
    args = ap.parse_args()

    base_path = Path(args.base)
    overlay_path = Path(args.overlay)
    out_path = Path(args.out)
    summary_path = Path(args.summary)

    base = read_csv(base_path)
    overlay_rows = read_csv(overlay_path)
    overlay = {r["galaxy"]: r for r in overlay_rows}

    if len(overlay) != len(overlay_rows):
        raise RuntimeError("Duplicate galaxy keys in public-source overlay")

    base_names = {r["galaxy"] for r in base}
    unknown = set(overlay) - base_names
    if unknown:
        raise RuntimeError(f"Overlay contains galaxies outside frozen base: {sorted(unknown)}")

    out: list[dict[str, str]] = []
    for row in base:
        galaxy = row["galaxy"]
        ov = overlay.get(galaxy)
        new = dict(row)
        if ov is None:
            new.update(
                {
                    "public_overlay_present": "0",
                    "effective_public_source_family": "",
                    "effective_acquisition_status": row["primary_profile_acquisition_status"],
                    "effective_numeric_rows_or_model": "",
                    "effective_source_quantity": "",
                    "effective_helium_status": "",
                    "preferred_public_source": "0",
                    "effective_source_artifact": "",
                    "effective_notes": row["notes"],
                }
            )
        else:
            if ov["stationary_role"] != row["stationary_role"]:
                raise RuntimeError(
                    f"Role mismatch for {galaxy}: base={row['stationary_role']} "
                    f"overlay={ov['stationary_role']}"
                )
            new.update(
                {
                    "public_overlay_present": "1",
                    "effective_public_source_family": ov["public_source_family"],
                    "effective_acquisition_status": ov["acquisition_status"],
                    "effective_numeric_rows_or_model": ov["numeric_rows_or_model"],
                    "effective_source_quantity": ov["source_quantity"],
                    "effective_helium_status": ov["helium_status"],
                    "preferred_public_source": ov["preferred_public_source"],
                    "effective_source_artifact": ov["source_artifact"],
                    "effective_notes": ov["notes"],
                }
            )
        out.append(new)

    fields = list(out[0].keys())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out)

    status_counts = Counter(r["effective_acquisition_status"] for r in out)
    overlay_role_counts = Counter(r["stationary_role"] for r in overlay_rows)
    recovered = {
        "raw_source_profile_ingested",
        "analytic_profile_recovered",
    }
    recovered_rows = [r for r in overlay_rows if r["acquisition_status"] in recovered]
    recovered_roles = Counter(r["stationary_role"] for r in recovered_rows)

    summary = {
        "status": "RECONCILED_PUBLIC_SOURCE_VIEW_CREATED",
        "n_frozen_galaxies": len(out),
        "n_public_overlay_galaxies": len(overlay_rows),
        "overlay_role_counts": dict(overlay_role_counts),
        "n_profile_recovered_or_ingested": len(recovered_rows),
        "profile_recovered_or_ingested_role_counts": dict(recovered_roles),
        "effective_status_counts": dict(sorted(status_counts.items())),
        "base_sha256": sha256(base_path),
        "overlay_sha256": sha256(overlay_path),
        "output_sha256": sha256(out_path),
        "boundary": (
            "Original provenance inventory retained unchanged; this reconciled view "
            "changes only acquisition/source-status metadata. Frozen roles and all "
            "persistence-fit locks remain unchanged."
        ),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
