#!/usr/bin/env python3
"""Build a frozen-sample map from SPARC/Lelli 2016 galaxies to their cited H I/Halpha sources.

Authoritative public CDS/VizieR products:
  J/AJ/152/157/table1.dat  -- 175 SPARC galaxies; Ref bytes 117-130
  J/AJ/152/157/refs.dat    -- 56 reference records

Scientific boundary:
- This maps Lelli et al.'s stated H I/Halpha source references only.
- It does NOT claim that every cited source contains a direct radial Sigma_HI profile.
- Lelli et al. 2016 explicitly state that Vgas was either computed from an H I
  surface-density profile or taken from a published mass model. A later source-level
  audit must classify each citation as direct-profile, published-mass-model, map/cube,
  or unresolved.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://cdsarc.cds.unistra.fr/ftp/J/AJ/152/157/"
TABLE1_URL = BASE + "table1.dat"
REFS_URL = BASE + "refs.dat"
UA = "PersistenceFrameworkPaperI/1.0"


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def load_frozen(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return {r["galaxy"].strip(): r["stationary_role"].strip() for r in csv.DictReader(fh)}


def compact_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", s).upper()


def parse_refs(text: str) -> dict[str, dict[str, str]]:
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        ref = line[0:4].strip()
        aut = line[5:29].strip()
        bib = line[30:49].strip()
        com = line[50:91].strip()
        if ref:
            out[ref] = {"ref_code": ref, "author": aut, "bibcode": bib, "comment": com}
    return out


def split_ref_codes(s: str) -> list[str]:
    s = s.strip()
    if not s:
        return []
    # CDS Ref entries may contain comma/semicolon/space separated identifiers.
    toks = [t for t in re.split(r"[;,\s]+", s) if t]
    return toks


def parse_table1(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        name = line[0:11].strip()
        ref = line[116:130].strip() if len(line) >= 117 else ""
        if name:
            rows.append({"name": name, "ref_field": ref})
    return rows


def main() -> None:
    frozen = load_frozen(Path("validation/stationary/stationary_split_v1.csv"))
    frozen_by_compact = {compact_name(k): (k, v) for k, v in frozen.items()}
    refs = parse_refs(fetch(REFS_URL))
    t1 = parse_table1(fetch(TABLE1_URL))

    output_rows = []
    unmatched_frozen = set(frozen)
    unknown_ref_codes = set()

    for row in t1:
        key = compact_name(row["name"])
        if key not in frozen_by_compact:
            continue
        frozen_name, role = frozen_by_compact[key]
        unmatched_frozen.discard(frozen_name)
        codes = split_ref_codes(row["ref_field"])
        if not codes:
            output_rows.append({
                "galaxy": frozen_name,
                "stationary_role": role,
                "lelli2016_name": row["name"],
                "lelli_ref_field": row["ref_field"],
                "ref_code": "",
                "author": "",
                "bibcode": "",
                "comment": "",
                "origin_map_status": "no_reference_code_in_table1",
                "profile_specificity_status": "requires_source_level_audit",
            })
            continue
        for code in codes:
            rr = refs.get(code)
            if rr is None:
                unknown_ref_codes.add(code)
                rr = {"author": "", "bibcode": "", "comment": ""}
                status = "unknown_ref_code"
            else:
                status = "lelli_source_reference_mapped"
            output_rows.append({
                "galaxy": frozen_name,
                "stationary_role": role,
                "lelli2016_name": row["name"],
                "lelli_ref_field": row["ref_field"],
                "ref_code": code,
                "author": rr["author"],
                "bibcode": rr["bibcode"],
                "comment": rr["comment"],
                "origin_map_status": status,
                "profile_specificity_status": "requires_source_level_audit",
            })

    out = Path("data/stationary/source_reconstruction/lelli2016_hi_data_origin_map_v1.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "galaxy", "stationary_role", "lelli2016_name", "lelli_ref_field", "ref_code",
        "author", "bibcode", "comment", "origin_map_status", "profile_specificity_status"
    ]
    output_rows.sort(key=lambda r: (r["galaxy"], r["ref_code"]))
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(output_rows)

    unique_galaxies = {r["galaxy"] for r in output_rows}
    unique_bibcodes = {r["bibcode"] for r in output_rows if r["bibcode"]}
    role_counts = {
        role: len({r["galaxy"] for r in output_rows if r["stationary_role"] == role})
        for role in ("calibration", "blind")
    }
    summary = {
        "status": "LELLI2016_HI_DATA_ORIGIN_MAP_BUILT",
        "source_catalog": "CDS/VizieR J/AJ/152/157",
        "n_sparc_table1_rows": len(t1),
        "n_reference_rows": len(refs),
        "n_frozen_galaxies_mapped": len(unique_galaxies),
        "role_counts": role_counts,
        "n_unique_source_bibcodes_in_frozen_sample": len(unique_bibcodes),
        "n_output_galaxy_reference_rows": len(output_rows),
        "unmatched_frozen_galaxies": sorted(unmatched_frozen),
        "unknown_ref_codes": sorted(unknown_ref_codes),
        "interpretation_boundary": (
            "The Ref field identifies Lelli et al. 2016 H I/Halpha source references. "
            "It is not by itself proof that the cited publication contains a direct radial H I surface-density profile. "
            "Each source must be audited for direct profile vs published mass model vs map/cube vs unresolved provenance."
        ),
    }
    sp = Path("validation/stationary/lelli2016_hi_data_origin_map_v1_summary.json")
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
