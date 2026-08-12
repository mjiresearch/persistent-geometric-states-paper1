#!/usr/bin/env python3
"""Integrate Hoekstra 2001 Begeman-linked vector profile candidates into overlay.

Three calibration galaxies have exact source-vector Sigma_HI profiles in
normalized radius R/R_out. They are candidate-level until R_out is recovered
from the original rotation-curve provenance and converted to physical radius.
Higher-information machine-readable/analytic profiles, if already present, stay
preferred and the Hoekstra route is recorded only as secondary QC.
"""
from __future__ import annotations
import csv
from collections import Counter
from pathlib import Path

OVERLAY=Path("data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv")
CAND=Path("data/stationary/source_reconstruction/hoekstra2001_be87_hi_vector_profiles_candidate_v1.csv")
FIELDS=["galaxy","stationary_role","public_source_family","acquisition_status","numeric_rows_or_model","source_quantity","helium_status","preferred_public_source","source_artifact","notes"]
STRONGER={"raw_source_profile_ingested","analytic_profile_recovered"}

def read(p):
    with p.open(newline="",encoding="utf-8-sig") as fh:return list(csv.DictReader(fh))

def main():
    orows=read(OVERLAY); overlay={r["galaxy"]:r for r in orows}
    if len(overlay)!=len(orows):raise RuntimeError("Duplicate galaxy in overlay")
    rows=read(CAND);counts=Counter(r["galaxy"] for r in rows);roles={r["galaxy"]:r["stationary_role"] for r in rows}
    if set(counts)!={"NGC2903","NGC5033","NGC5371"} or sum(counts.values())!=63:
        raise RuntimeError(f"Unexpected Hoekstra candidate set {counts}")
    added=[];upgraded=[];retained=[]
    for g in sorted(counts):
        existing=overlay.get(g); role=roles[g]
        note=(f"Hoekstra, van Albada & Sancisi 2001 Fig.1 exact red/dashed vector H I profile: {counts[g]} vector vertices; "
              "y-axis calibrated from native printed log10 Sigma_HI labels (+1,0,-1); x-axis is R/R_out with R_out defined as the outermost rotation-curve point. "
              "Begeman 1987 is included in the paper's profile provenance for this galaxy. Raw H I, no helium applied. Candidate only pending exact R_out-to-physical-radius recovery.")
        if existing and existing["stationary_role"]!=role:raise RuntimeError(f"Role mismatch {g}")
        if existing and existing["acquisition_status"] in STRONGER:
            if "Hoekstra, van Albada & Sancisi 2001" not in existing["notes"]:
                existing["notes"]=(existing["notes"].rstrip()+" "+note+" Retained as secondary QC; stronger source stays preferred.")
            retained.append(g);continue
        new={"galaxy":g,"stationary_role":role,"public_source_family":"Begeman 1987 / Hoekstra van Albada & Sancisi 2001 vector republication","acquisition_status":"vector_profile_candidate_recovered","numeric_rows_or_model":str(counts[g]),"source_quantity":"raw HI surface density from exact published vector profile; radius normalized by R_out","helium_status":"helium not applied","preferred_public_source":"1","source_artifact":str(CAND),"notes":note}
        if existing:
            new["notes"]+=f" Supersedes overlay acquisition status '{existing['acquisition_status']}' for numerical availability; prior provenance retained: {existing['public_source_family']} — {existing['notes']}"
            overlay[g]=new;upgraded.append(g)
        else:overlay[g]=new;added.append(g)
    with OVERLAY.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=FIELDS);w.writeheader();w.writerows([overlay[g] for g in sorted(overlay)])
    print("candidates",dict(counts));print("added",added);print("upgraded",upgraded);print("stronger retained",retained);print("overlay total",len(overlay))
if __name__=="__main__":main()
