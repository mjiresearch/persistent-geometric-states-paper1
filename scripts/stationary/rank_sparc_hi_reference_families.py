#!/usr/bin/env python3
"""Rank remaining frozen galaxies by Lelli/SPARC H I-Halpha reference family.

Uses the authoritative per-galaxy SPARC Ref map together with the reconciled
public-source acquisition view and an audited family-disposition ledger.

Important distinction:
- `n_untouched_no_public_overlay` describes database coverage.
- the live acquisition queue must also honor completed anti-loop audits.
  Families whose currently known public routes are exhausted are retained in
  the output for auditability but ranked after actionable families.

No profile normalization, persistence fitting, or blind-outcome inspection is
performed here.
"""
from __future__ import annotations

import csv, json
from collections import defaultdict
from pathlib import Path

REFMAP=Path("data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv")
RECON=Path("data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv")
DISPOSITION=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv")
OUT=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
SUMMARY=Path("validation/stationary/sparc_hi_reference_family_priority_v1_summary.json")


def read(path):
    with path.open(newline="",encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main():
    recon=read(RECON)
    if len(recon)!=149:
        raise RuntimeError(f"Expected 149 reconciled galaxies, got {len(recon)}")
    untouched={r["galaxy"]:r for r in recon if r.get("public_overlay_present")=="0"}
    refrows=read(REFMAP)

    disp_rows=read(DISPOSITION) if DISPOSITION.exists() else []
    dispositions={r["sparc_ref_id"]:r for r in disp_rows}
    if len(dispositions)!=len(disp_rows):
        raise RuntimeError("Duplicate SPARC reference ID in family-disposition ledger")

    groups=defaultdict(lambda:{"galaxies":set(),"calibration":set(),"blind":set(),"authors":set(),"bibcodes":set(),"comments":set(),"resolved":set()})
    for r in refrows:
        g=r["galaxy"]
        if g not in untouched:
            continue
        rid=r["sparc_ref_id"] or "UNRESOLVED_EMPTY"
        z=groups[rid]
        z["galaxies"].add(g)
        z[r["stationary_role"]].add(g)
        if r.get("author"): z["authors"].add(r["author"])
        if r.get("bibcode"): z["bibcodes"].add(r["bibcode"])
        if r.get("comment"): z["comments"].add(r["comment"])
        z["resolved"].add(r.get("reference_resolved_in_cds_refs", "0"))

    rows=[]
    for rid,z in groups.items():
        d=dispositions.get(rid,{})
        queue_status=d.get("queue_status","") or "actionable_unreviewed"
        actionable="1" if queue_status=="actionable_unreviewed" else "0"
        rows.append({
            "sparc_ref_id":rid,
            "n_untouched_frozen_galaxies":len(z["galaxies"]),
            "n_calibration":len(z["calibration"]),
            "n_blind":len(z["blind"]),
            "queue_actionable_now":actionable,
            "queue_status":queue_status,
            "disposition":d.get("disposition",""),
            "disposition_artifact":d.get("validation_artifact",""),
            "reopen_rule":d.get("reopen_rule",""),
            "reference_resolved_in_cds_refs":"1" if z["resolved"]=={"1"} else "0",
            "author":" | ".join(sorted(z["authors"])),
            "bibcode":" | ".join(sorted(z["bibcodes"])),
            "comment":" | ".join(sorted(z["comments"])),
            "galaxies":";".join(sorted(z["galaxies"])),
        })

    # Live queue first: actionable families by yield. Audited deferred/redirected
    # families remain below them so their coverage is never silently discarded.
    rows.sort(key=lambda r:(
        -int(r["queue_actionable_now"]),
        -int(r["n_untouched_frozen_galaxies"]),
        -int(r["n_calibration"]),
        r["sparc_ref_id"],
    ))

    fields=[
        "sparc_ref_id","n_untouched_frozen_galaxies","n_calibration","n_blind",
        "queue_actionable_now","queue_status","disposition","disposition_artifact","reopen_rule",
        "reference_resolved_in_cds_refs","author","bibcode","comment","galaxies"
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)

    actionable=[r for r in rows if r["queue_actionable_now"]=="1"]
    deferred=[r for r in rows if r["queue_actionable_now"]=="0"]
    summary={
        "status":"SPARC_HI_REFERENCE_FAMILY_PRIORITY_COMPLETE",
        "n_frozen_galaxies":149,
        "n_untouched_no_public_overlay":len(untouched),
        "n_reference_families_covering_untouched":len(rows),
        "n_actionable_reference_families":len(actionable),
        "n_deferred_or_redirected_reference_families":len(deferred),
        "top_15_actionable_reference_families":actionable[:15],
        "deferred_or_redirected_families":deferred,
        "interpretation":(
            "Coverage and actionability are separated. Families with no public overlay remain visible, "
            "but audited anti-loop dispositions prevent exhausted or redirected source families from "
            "reappearing at the head of the live acquisition queue."
        ),
        "boundary":"Acquisition priority only; no profile normalization, persistence fitting, or blind-outcome inspection.",
    }
    SUMMARY.parent.mkdir(parents=True,exist_ok=True)
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
