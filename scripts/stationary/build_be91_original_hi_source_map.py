#!/usr/bin/env python3
"""Build the five-target Be91 -> original H I observing-source map.

The mapping is supported by native text already preserved in
validation/stationary/be91_original_hi_source_audit_v1.json. This script fails
closed if the required source phrases are absent; it does not infer profiles or
inspect persistence outcomes.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

AUDIT=Path("validation/stationary/be91_original_hi_source_audit_v1.json")
OUT=Path("data/stationary/source_reconstruction/be91_original_hi_source_map_v1.csv")
SUMMARY=Path("validation/stationary/be91_original_hi_source_map_v1_summary.json")

ROWS=[
    ("DDO170","Lake, Schommer & van Gorkom 1990","explicit Be91 text: DDO 170 observed by Lake et al. (1990) at the VLA"),
    ("NGC2903","Begeman 1987 PhD thesis","Be91 primary six-galaxy Begeman (1987) WSRT subset"),
    ("NGC3109","Jobin & Carignan 1990","explicit Be91 Addendum: new NGC 3109 curve from VLA observations by Jobin & Carignan (1990)"),
    ("NGC6503","Begeman 1987 PhD thesis","Be91 primary six-galaxy Begeman (1987) WSRT subset"),
    ("UGC02259","Carignan, Sancisi & van Albada 1988","Be91 four-added-source branch plus 21-cm source legend for the UGC 2259 Westerbork study"),
]

REQUIRED_PHRASES=[
    "DDO 170 is a",
    "Lake et al (1990)",
    "Six out of the 10 galaxies are from the sample of Begeman",
    "All of these galaxies were observed at the Wester-",
    "ADDENDUM: NGC 3109",
    "Jobin & Carignan (1990)",
    "UGC 2259 is a very small but regular spiral galaxy",
    "Carignan, Sancisi & van Albada (1988)",
]


def flatten(obj):
    if isinstance(obj,dict):
        return "\n".join(flatten(v) for v in obj.values())
    if isinstance(obj,list):
        return "\n".join(flatten(v) for v in obj)
    return str(obj)


def main():
    audit=json.loads(AUDIT.read_text(encoding="utf-8"))
    text=flatten(audit)
    missing=[p for p in REQUIRED_PHRASES if p not in text]
    if missing:
        raise RuntimeError("Required Be91 source evidence missing: "+repr(missing))

    OUT.parent.mkdir(parents=True,exist_ok=True)
    fields=["galaxy","original_hi_source","mapping_status","be91_evidence"]
    with OUT.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader()
        for galaxy,source,evidence in ROWS:
            w.writerow({
                "galaxy":galaxy,
                "original_hi_source":source,
                "mapping_status":"mapped_to_original_observing_source",
                "be91_evidence":evidence,
            })

    summary={
        "status":"BE91_ORIGINAL_HI_SOURCE_MAP_BUILT",
        "source":"Begeman, Broeils & Sanders 1991 MNRAS 249 523-537",
        "n_targets":len(ROWS),
        "n_mapped":len(ROWS),
        "targets":[{"galaxy":g,"original_hi_source":s} for g,s,_ in ROWS],
        "next_high_yield_original_source":"Begeman 1987 PhD thesis",
        "begeman1987_targets":["NGC2903","NGC5033","NGC5371","NGC6503"],
        "boundary":"Provenance mapping only; each original source must still pass radial H I public-recoverability and QC gates before ingestion."
    }
    SUMMARY.parent.mkdir(parents=True,exist_ok=True)
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
