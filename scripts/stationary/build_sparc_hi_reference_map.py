#!/usr/bin/env python3
"""Build a frozen-149 source-reference map from Lelli et al. (2016) SPARC.

The SPARC catalog explicitly provides a per-galaxy Ref field for HI/Halpha data
and a 56-row reference table. This script joins those published records to the
frozen Paper I calibration/blind split. It is provenance only: it does not
claim that Lelli's later 169-galaxy azimuthally averaged HI profile compilation
is itself public, nor that every cited source publishes a machine-readable
radial Sigma_HI profile.
"""
from __future__ import annotations

import csv, json, re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
TABLE1 = "J/AJ/152/157/table1"
REFS = "J/AJ/152/157/refs"
UA = "PersistenceFrameworkPaperI/1.0"


def fetch_tsv(source: str, columns: str) -> str:
    q = urlencode({"-source": source, "-out": columns, "-out.max": "1000"})
    req = Request(VIZIER + "?" + q, headers={"User-Agent": UA})
    return urlopen(req, timeout=60).read().decode("utf-8")


def parse_asu(text: str, required: set[str]) -> list[dict[str, str]]:
    lines = text.splitlines(); header = None; start = None
    for i, line in enumerate(lines):
        if not line or line.startswith("#"): continue
        cols = line.split("\t")
        if required.issubset(set(cols)):
            header, start = cols, i + 1; break
    if header is None:
        raise RuntimeError(f"VizieR header not found; required={sorted(required)}")
    out = []
    for line in lines[start:]:
        if not line or line.startswith("#"): continue
        cols = line.split("\t")
        if len(cols) != len(header): continue
        if all((not c) or set(c) <= {"-"} for c in cols): continue
        out.append({k: v.strip() for k, v in zip(header, cols)})
    return out


def ref_tokens(s: str) -> list[str]:
    return [x for x in re.split(r"[,;\s]+", s.strip()) if x]


def main() -> None:
    with open("validation/stationary/stationary_split_v1.csv", newline="", encoding="utf-8-sig") as fh:
        frozen = {r["galaxy"]: r["stationary_role"] for r in csv.DictReader(fh)}
    if len(frozen) != 149:
        raise RuntimeError(f"Expected 149 frozen galaxies, got {len(frozen)}")

    galaxies = parse_asu(fetch_tsv(TABLE1, "Name,Ref"), {"Name", "Ref"})
    refs = parse_asu(fetch_tsv(REFS, "Ref,Aut,BibCode,Com"), {"Ref", "Aut", "BibCode", "Com"})
    ref_lookup = {r["Ref"]: r for r in refs}

    rows = []; unresolved = set(); frozen_seen = set()
    for g in galaxies:
        name = g["Name"]; role = frozen.get(name)
        if role not in {"calibration", "blind"}: continue
        frozen_seen.add(name)
        toks = ref_tokens(g["Ref"])
        if not toks: toks = [""]
        for tok in toks:
            rr = ref_lookup.get(tok)
            resolved = rr is not None if tok else False
            if tok and rr is None:
                unresolved.add(tok)
                rr = {"Aut": "", "BibCode": "", "Com": ""}
            elif rr is None:
                rr = {"Aut": "", "BibCode": "", "Com": ""}
            rows.append({
                "galaxy": name,
                "stationary_role": role,
                "sparc_ref_id": tok,
                "reference_resolved_in_cds_refs": "1" if resolved else "0",
                "author": rr["Aut"],
                "bibcode": rr["BibCode"],
                "comment": rr["Com"],
                "provenance_scope": "SPARC_Table1_column15_HI_Halpha_reference",
            })

    missing_galaxies = sorted(set(frozen) - frozen_seen)
    if missing_galaxies:
        raise RuntimeError(f"Frozen galaxies missing from SPARC table1 join: {missing_galaxies}")

    out = Path("data/stationary/source_reconstruction/sparc_hi_reference_map_v1.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["galaxy", "stationary_role", "sparc_ref_id", "reference_resolved_in_cds_refs", "author", "bibcode", "comment", "provenance_scope"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)

    unique_refs = sorted({r["sparc_ref_id"] for r in rows if r["sparc_ref_id"]})
    summary = {
        "status": "SPARC_FROZEN149_HI_REFERENCE_MAP_COMPLETE",
        "n_frozen_galaxies": len(frozen_seen),
        "n_long_reference_rows": len(rows),
        "n_unique_sparc_reference_ids": len(unique_refs),
        "n_reference_catalog_rows": len(refs),
        "unresolved_reference_ids": sorted(unresolved),
        "source": "Lelli et al. 2016 AJ 152 157 / CDS J/AJ/152/157",
        "interpretation": "Per-galaxy references identify the underlying HI/Halpha data used by SPARC. They are an authoritative acquisition map to original observations, not proof that Lelli's later 169-galaxy azimuthally averaged HI profile compilation is public or identical to a profile printed in each source paper.",
        "boundary": "Provenance only. No source-profile normalization, interpolation, helium correction, persistence fitting, or blind-outcome inspection.",
    }
    sp = Path("validation/stationary/sparc_hi_reference_map_v1_summary.json")
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
