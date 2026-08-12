#!/usr/bin/env python3
"""One-time metadata correction: NGC5033 is blind, not calibration.

This changes no vector coordinates, axis transforms, surface densities, or
provenance. It corrects both the extractor's frozen-role literal and the already
recovered candidate CSV so future reruns remain consistent.
"""
from pathlib import Path
import csv

SCRIPT=Path("scripts/stationary/extract_hoekstra2001_be87_vector_profiles.py")
CSV=Path("data/stationary/source_reconstruction/hoekstra2001_be87_hi_vector_profiles_candidate_v1.csv")

text=SCRIPT.read_text(encoding="utf-8")
old='(1,2):("NGC5033","calibration","Kent 1986 + Begeman 1987"),'
new='(1,2):("NGC5033","blind","Kent 1986 + Begeman 1987"),'
if old not in text and new not in text:
    raise RuntimeError("Expected NGC5033 target literal not found")
SCRIPT.write_text(text.replace(old,new),encoding="utf-8")

with CSV.open(newline="",encoding="utf-8-sig") as fh:
    rows=list(csv.DictReader(fh));fields=list(rows[0])
changed=0
for r in rows:
    if r["galaxy"]=="NGC5033":
        if r["stationary_role"] not in {"calibration","blind"}:raise RuntimeError(r)
        if r["stationary_role"]!="blind":changed+=1
        r["stationary_role"]="blind"
with CSV.open("w",newline="",encoding="utf-8") as fh:
    w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)
print("NGC5033 rows corrected",changed,"of",sum(r["galaxy"]=="NGC5033" for r in rows))
