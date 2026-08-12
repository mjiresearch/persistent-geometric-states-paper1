#!/usr/bin/env python3
"""Integrate the exact Oosterloo+2007 NGC891 analytic H I profile into the overlay.

Frozen provenance:
Lelli/SPARC NGC0891 -> Fr11 -> Oosterloo, Fraternali & Sancisi 2007.

The source artifact stores the published two-component thin-disk H I radial
surface-density function and parameters exactly.  This integration records that
analytic representation without sampling, helium correction, distance changes,
common-grid normalization, persistence fitting, or blind inspection.
"""
from __future__ import annotations

import csv
from pathlib import Path

OVERLAY=Path("data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv")
PROFILE=Path("data/stationary/source_reconstruction/oosterloo2007_ngc891_hi_analytic_profile_v1.csv")
FIELDS=[
    "galaxy","stationary_role","public_source_family","acquisition_status",
    "numeric_rows_or_model","source_quantity","helium_status",
    "preferred_public_source","source_artifact","notes",
]
STRONGER={"raw_source_profile_ingested"}


def read(path):
    with path.open(newline="",encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main():
    rows=read(OVERLAY)
    if len({r["galaxy"] for r in rows})!=len(rows):
        raise RuntimeError("Duplicate galaxy in overlay")
    overlay={r["galaxy"]:r for r in rows}
    prof=read(PROFILE)
    if len(prof)!=1 or prof[0]["galaxy"]!="NGC0891":
        raise RuntimeError("Expected exactly one NGC0891 analytic profile")
    p=prof[0]; g=p["galaxy"]; role=p["stationary_role"]
    existing=overlay.get(g)
    if existing and existing["stationary_role"]!=role:
        raise RuntimeError(f"Frozen role mismatch for {g}")
    note=(
        "Oosterloo, Fraternali & Sancisi 2007 source-native analytic fit to the observed thin-disk atomic-HI radial surface density of NGC 891. "
        "Published outer tapered exponential plus compact inner exponential ring component retained exactly as parameters; function not sampled. "
        "Fraternali et al. 2011 (SPARC/Lelli Fr11 lineage) uses this H I observation family and derives its gas profile from the H I maps. "
        "No helium factor, distance/inclination change, common-grid normalization, persistence fitting, or blind inspection applied."
    )
    if existing and existing["acquisition_status"] in STRONGER:
        if "Oosterloo" not in existing["notes"]:
            existing["notes"]=existing["notes"].rstrip()+" "+note+" Retained as secondary analytic QC; stronger raw numerical source remains preferred."
        action="retained_stronger_existing"
    else:
        new={
            "galaxy":g,
            "stationary_role":role,
            "public_source_family":"Oosterloo, Fraternali & Sancisi 2007 analytic thin-disk H I",
            "acquisition_status":"analytic_profile_recovered",
            "numeric_rows_or_model":"two-component analytic radial H I surface-density function",
            "source_quantity":"atomic HI surface density",
            "helium_status":"helium not included",
            "preferred_public_source":"1",
            "source_artifact":str(PROFILE),
            "notes":note,
        }
        if existing:
            new["notes"] += f" Replaces weaker overlay status '{existing['acquisition_status']}' while retaining prior provenance: {existing['public_source_family']} — {existing['notes']}"
        overlay[g]=new
        action="integrated_analytic_profile"

    out=[overlay[x] for x in sorted(overlay)]
    with OVERLAY.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=FIELDS);w.writeheader();w.writerows(out)
    print(action,g,"overlay total",len(out))


if __name__=="__main__":main()
