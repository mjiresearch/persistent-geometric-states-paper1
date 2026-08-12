#!/usr/bin/env python3
"""Integrate Elson 2017 WHISP vector-profile candidates into public-source overlay.

Rules:
- The 19 calibrated WHISP candidate curves are public numerical reconstructions.
- Existing higher-information machine-readable source profiles remain preferred.
- UGC05918 and UGC07559 retain Iorio 2017 as preferred, with WHISP noted as QC.
- UGC05829 is upgraded from Taylor-map-only to the WHISP numerical candidate,
  retaining Taylor 1994 as independent source provenance.
- Candidate status is never equated with final source-profile freeze.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

OVERLAY = Path("data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv")
WHISP = Path("data/stationary/source_reconstruction/elson2017_whisp_vector_profiles_candidate_v1.csv")

FIELDS = [
    "galaxy","stationary_role","public_source_family","acquisition_status",
    "numeric_rows_or_model","source_quantity","helium_status",
    "preferred_public_source","source_artifact","notes",
]

STRONGER_STATUSES = {"raw_source_profile_ingested", "analytic_profile_recovered"}


def read(path):
    with path.open(newline="",encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main():
    overlay_rows=read(OVERLAY)
    if len({r["galaxy"] for r in overlay_rows}) != len(overlay_rows):
        raise RuntimeError("Duplicate galaxy in overlay before integration")
    overlay={r["galaxy"]:r for r in overlay_rows}

    wrows=read(WHISP)
    counts=Counter(r["galaxy"] for r in wrows)
    roles={}
    for r in wrows:
        g=r["galaxy"]
        if g in roles and roles[g] != r["stationary_role"]:
            raise RuntimeError(f"Role mismatch within WHISP candidate rows for {g}")
        roles[g]=r["stationary_role"]
    if len(counts) != 19 or sum(counts.values()) != 947:
        raise RuntimeError(f"Expected WHISP 19 galaxies / 947 rows, got {len(counts)} / {sum(counts.values())}")

    added=[]; upgraded=[]; retained=[]
    for g in sorted(counts):
        role=roles[g]
        existing=overlay.get(g)
        whisp_note=(
            f"Elson 2017 WHISP Appendix vector profile candidate: {counts[g]} exact vector vertices; "
            "physical axes reconstructed from audited source R_HI and mean-Sigma anchors; raw HI; "
            "no helium or frozen-distance normalization applied. Candidate only until final source-profile freeze."
        )
        if existing and existing["stationary_role"] != role:
            raise RuntimeError(f"Frozen role mismatch for {g}")

        if existing and existing["acquisition_status"] in STRONGER_STATUSES:
            # Preserve the higher-information source as preferred; append WHISP as independent QC.
            if "Elson 2017 WHISP" not in existing["notes"]:
                existing["notes"] = existing["notes"].rstrip() + " " + whisp_note + " Retained as secondary QC; existing machine-readable/analytic source remains preferred."
            retained.append(g)
            continue

        new={
            "galaxy":g,
            "stationary_role":role,
            "public_source_family":"Elson 2017 / WHISP (Butler et al. 2017 reconstruction sample)",
            "acquisition_status":"vector_profile_candidate_recovered",
            "numeric_rows_or_model":str(counts[g]),
            "source_quantity":"raw HI surface density candidate from published vector curve",
            "helium_status":"helium not applied; Elson mass accounting applies helium downstream",
            "preferred_public_source":"1",
            "source_artifact":"data/stationary/source_reconstruction/elson2017_whisp_vector_profiles_candidate_v1.csv",
            "notes":whisp_note,
        }
        if existing:
            # Preserve pre-existing provenance in notes, e.g. Taylor 1994 for UGC05829.
            new["notes"] += (
                f" Supersedes overlay acquisition status '{existing['acquisition_status']}' for numerical availability; "
                f"prior source family retained in provenance: {existing['public_source_family']} — {existing['notes']}"
            )
            overlay[g]=new; upgraded.append(g)
        else:
            overlay[g]=new; added.append(g)

    rows=[overlay[g] for g in sorted(overlay)]
    with OVERLAY.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)

    print("WHISP galaxies",len(counts),"rows",sum(counts.values()))
    print("added",len(added),added)
    print("upgraded",len(upgraded),upgraded)
    print("stronger source retained",len(retained),retained)
    print("overlay total",len(rows))

if __name__=="__main__":
    main()
