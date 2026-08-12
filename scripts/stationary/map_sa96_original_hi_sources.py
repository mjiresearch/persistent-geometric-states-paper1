#!/usr/bin/env python3
"""Map the 13 frozen Sa96 galaxies to Sanders (1996) original data references.

Sanders 1996 Table 1 gives each rotation-curve galaxy one or more reference
numbers.  This script parses the target rows and the corresponding \tablerefs
block directly from the public arXiv TeX, producing an auditable galaxy ->
reference-number -> cited-source map.

Provenance only.  A cited paper is not labeled as containing radial Sigma_HI
until a source-level audit establishes that fact.
"""
from __future__ import annotations

import csv
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV = "https://export.arxiv.org/e-print/astro-ph/9606089"
UA = "PersistenceFrameworkPaperI/1.0"
PRIORITY = Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUTCSV = Path("data/stationary/source_reconstruction/sa96_original_hi_source_map_v1.csv")
OUTJSON = Path("validation/stationary/sa96_original_hi_source_map_v1_summary.json")


def fetch() -> str:
    req = Request(ARXIV, headers={"User-Agent": UA})
    raw = urlopen(req, timeout=90).read()
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    tex = next(m for m in tf.getmembers() if m.isfile() and m.name.endswith(".tex"))
    return tf.extractfile(tex).read().decode("latin-1", "replace")


def compact(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def normalize_name(field: str) -> str:
    s = re.sub(r"\$[^$]*\$", "", field)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\\[A-Za-z]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return compact(s)


def parse_tablerefs(tex: str) -> dict[int, str]:
    blocks = re.findall(r"\\tablerefs\{(.*?)\}", tex, flags=re.S)
    refs: dict[int, str] = {}
    for block in blocks:
        clean = re.sub(r"\s+", " ", block).strip()
        # Split only where a new numeric reference begins after ; or start.
        for m in re.finditer(r"(?:^|;)\s*(\d+)\s*,\s*(.*?)(?=(?:;\s*\d+\s*,)|$)", clean):
            n = int(m.group(1))
            citation = m.group(2).strip().rstrip(";")
            # Keep first occurrence for Table 1; later tables may reuse numbers.
            refs.setdefault(n, citation)
    return refs


def parse_target_rows(tex: str, targets: set[str]) -> list[dict]:
    rows = []
    for line_no, line in enumerate(tex.splitlines(), 1):
        if "&" not in line or "\\\\" not in line:
            continue
        fields = [x.strip() for x in line.split("&")]
        if len(fields) < 8:
            continue
        gnorm = normalize_name(fields[0])
        match = None
        for g in targets:
            if compact(g).lstrip("0") == gnorm.lstrip("0") or compact(g) == gnorm:
                match = g
                break
            # Explicit NGC/UGC numeric match, tolerant of leading zeroes.
            mg = re.match(r"(NGC|UGC)0*(\d+)$", compact(g))
            mr = re.match(r"(NGC|UGC)0*(\d+)$", gnorm)
            if mg and mr and mg.group(1) == mr.group(1) and int(mg.group(2)) == int(mr.group(2)):
                match = g
                break
        if not match:
            continue
        last = fields[-1]
        last = re.sub(r"\\\\.*$", "", last).strip()
        nums = [int(x) for x in re.findall(r"\d+", last)]
        rows.append({
            "galaxy": match,
            "line": line_no,
            "raw_row": line.strip(),
            "reference_numbers": nums,
        })
    # Prefer rows near Sanders Table 1 (~990-1021); avoid later model-fit tables.
    by_g = {}
    for r in rows:
        score = 0 if 980 <= r["line"] <= 1035 else abs(r["line"] - 1010) + 1000
        if r["galaxy"] not in by_g or score < by_g[r["galaxy"]][0]:
            by_g[r["galaxy"]] = (score, r)
    return [by_g[g][1] for g in sorted(by_g)]


def main() -> None:
    with PRIORITY.open(newline="", encoding="utf-8-sig") as fh:
        pr = list(csv.DictReader(fh))
    target = next((r for r in pr if r["sparc_ref_id"] == "Sa96"), None)
    if target is None or int(target["n_untouched_frozen_galaxies"]) != 13:
        raise RuntimeError("Expected Sa96 13-galaxy untouched block")
    galaxies = target["galaxies"].split(";")

    tex = fetch()
    refs = parse_tablerefs(tex)
    rows = parse_target_rows(tex, set(galaxies))

    output = []
    missing_ref_numbers = set()
    for r in rows:
        if not r["reference_numbers"]:
            output.append({
                "galaxy": r["galaxy"], "sand1996_table_line": r["line"],
                "sand1996_reference_number": "", "cited_source": "",
                "mapping_status": "target_row_found_no_reference_number",
                "profile_specificity_status": "requires_source_level_audit",
            })
            continue
        for n in r["reference_numbers"]:
            citation = refs.get(n, "")
            if not citation:
                missing_ref_numbers.add(n)
            output.append({
                "galaxy": r["galaxy"],
                "sand1996_table_line": r["line"],
                "sand1996_reference_number": n,
                "cited_source": citation,
                "mapping_status": "mapped_to_sanders_cited_source" if citation else "reference_number_unresolved",
                "profile_specificity_status": "requires_source_level_audit",
            })

    OUTCSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "galaxy", "sand1996_table_line", "sand1996_reference_number", "cited_source",
        "mapping_status", "profile_specificity_status"
    ]
    with OUTCSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(output)

    mapped_galaxies = {r["galaxy"] for r in output}
    citations = sorted({r["cited_source"] for r in output if r["cited_source"]})
    summary = {
        "status": "SA96_ORIGINAL_HI_SOURCE_MAP_BUILT",
        "source": "Sanders 1996 ApJ 473 117-129; arXiv astro-ph/9606089",
        "n_priority_galaxies": len(galaxies),
        "n_target_rows_found": len(rows),
        "n_galaxies_mapped": len(mapped_galaxies),
        "unmapped_galaxies": sorted(set(galaxies) - mapped_galaxies),
        "n_output_galaxy_source_rows": len(output),
        "n_unique_cited_sources": len(citations),
        "unique_cited_sources": citations,
        "missing_reference_numbers": sorted(missing_ref_numbers),
        "target_rows": rows,
        "interpretation_boundary": (
            "This file resolves Sanders 1996's per-galaxy reference numbers to cited earlier papers. "
            "It does not assert that those papers expose radial H I surface-density profiles; source-level audits remain required."
        ),
    }
    OUTJSON.parent.mkdir(parents=True, exist_ok=True)
    OUTJSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("MAP")
    for r in output:
        print(r["galaxy"], r["sand1996_reference_number"], r["cited_source"])


if __name__ == "__main__":
    main()
