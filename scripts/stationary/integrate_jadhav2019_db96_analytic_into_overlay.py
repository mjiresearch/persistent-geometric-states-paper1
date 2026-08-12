#!/usr/bin/env python3
"""Integrate five public dB96-family analytic H I profiles into the overlay.

These are Jadhav & Banerjee (2019) analytic republications of literature H I
surface-density profiles for the same LSB systems. Provenance explicitly retains
that this is a later analytic representation, not numerical recovery of the
1996 graphics themselves.

No normalization, helium correction, persistence fitting, or blind inspection.
"""
from __future__ import annotations

import csv
from pathlib import Path

OVERLAY=Path("data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv")
PROFILES=Path("data/stationary/source_reconstruction/jadhav_banerjee2019_lsb_hi_analytic_profiles_v1.csv")
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
    prof=read(PROFILES)
    if len(prof)!=5 or len({r["galaxy"] for r in prof})!=5:
        raise RuntimeError(f"Expected five unique Jadhav dB96 profiles, got {len(prof)}")

    added=[]; retained=[]
    for p in prof:
        g=p["galaxy"]; role=p["stationary_role"]
        existing=overlay.get(g)
        if existing and existing["stationary_role"]!=role:
            raise RuntimeError(f"Frozen role mismatch for {g}")
        note=(
            "Jadhav & Banerjee 2019 Table 7 public analytic representation of literature atomic-HI surface-density profile; "
            "paper identifies de Blok et al. 2001 as the LSB profile source. SPARC/Lelli also assigns this system to the earlier dB96 H I family. "
            "This is a later analytic republication route, not proof that dB96 graphics are numerically recoverable. "
            "Parameters retained exactly; no helium, distance, inclination or common-grid normalization applied."
        )
        if existing and existing["acquisition_status"] in STRONGER:
            if "Jadhav & Banerjee 2019" not in existing["notes"]:
                existing["notes"]=existing["notes"].rstrip()+" "+note+" Retained as secondary analytic QC; stronger raw numerical source remains preferred."
            retained.append(g)
            continue
        model="single off-centred Gaussian" if not p["sigma02_msun_pc2"].strip() else "two-component off-centred Gaussian"
        new={
            "galaxy":g,
            "stationary_role":role,
            "public_source_family":"Jadhav & Banerjee 2019 analytic republication / de Blok LSB H I",
            "acquisition_status":"analytic_profile_recovered",
            "numeric_rows_or_model":model,
            "source_quantity":"atomic HI surface density",
            "helium_status":"helium not included",
            "preferred_public_source":"1",
            "source_artifact":str(PROFILES),
            "notes":note,
        }
        if existing:
            new["notes"] += f" Replaces weaker overlay status '{existing['acquisition_status']}' while retaining prior provenance: {existing['public_source_family']} — {existing['notes']}"
        overlay[g]=new; added.append(g)

    out=[overlay[g] for g in sorted(overlay)]
    with OVERLAY.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=FIELDS); w.writeheader(); w.writerows(out)
    print("Jadhav dB96 analytic profiles integrated",len(added),added)
    print("stronger source retained",len(retained),retained)
    print("overlay total",len(out))


if __name__=="__main__":
    main()
