#!/usr/bin/env python3
"""Acquire Hunter et al. (2021) LITTLE THINGS H I Sersic-fit parameters.

Public source:
  VizieR J/AJ/161/71/table1 and table2

This is a pre-fit source-acquisition step. It preserves the published fit
parameters and performs only catalogue-name reconciliation against the frozen
Paper I stationary split. It does NOT instantiate an H I profile from the
parameters until the exact Hunter et al. functional convention is separately
verified and frozen.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VIZIER = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
CAT1 = "J/AJ/161/71/table1"
CAT2 = "J/AJ/161/71/table2"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compact_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def url_for(source: str, columns: list[str]) -> str:
    return VIZIER + "?" + urlencode({
        "-source": source,
        "-out": ",".join(columns),
        "-out.max": "1000",
    })


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "PersistenceFrameworkPaperI/1.0"})
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_asu_tsv(text: str, required: list[str]) -> list[dict[str, str]]:
    lines = text.splitlines()
    header = None
    start = None
    for i, line in enumerate(lines):
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if all(c in cols for c in required):
            header = cols
            start = i + 1
            break
    if header is None or start is None:
        raise RuntimeError(f"Could not find VizieR header containing {required}")
    out = []
    for line in lines[start:]:
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != len(header):
            continue
        if all((not x) or set(x) <= {"-"} for x in cols):
            continue
        row = {k: v.strip() for k, v in zip(header, cols)}
        if row.get(required[0], ""):
            out.append(row)
    return out


def load_split(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    role = {}
    by_compact = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            g = row["galaxy"]
            role[g] = row["stationary_role"]
            key = compact_name(g)
            if key in by_compact:
                raise RuntimeError(f"Frozen compact-name collision: {g} / {by_compact[key]}")
            by_compact[key] = g
    return role, by_compact


def maybe_float(s: str):
    s = (s or "").strip()
    if not s or s in {"--", "---"}:
        return ""
    return f"{float(s):g}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="validation/stationary/stationary_split_v1.csv")
    ap.add_argument("--out", default="data/stationary/source_reconstruction/hunter2021_littlethings_hi_sersic_parameters_v1.csv")
    ap.add_argument("--summary", default="validation/stationary/hunter2021_littlethings_hi_sersic_parameters_v1_summary.json")
    args = ap.parse_args()

    split = Path(args.split)
    roles, frozen_by_compact = load_split(split)

    cols1 = ["Galaxy", "NED", "Dist"]
    cols2 = ["Galaxy", "logS0", "e_logS0", "R0", "e_R0", "nHI", "e_nHI", "R50", "e_R50"]
    rows1 = parse_asu_tsv(fetch(url_for(CAT1, cols1)), cols1)
    rows2 = parse_asu_tsv(fetch(url_for(CAT2, cols2)), cols2)

    if len(rows1) != 40 or len(rows2) != 40:
        raise RuntimeError(f"Expected 40 rows in each Hunter table, got {len(rows1)} and {len(rows2)}")

    meta = {r["Galaxy"]: r for r in rows1}
    output = []
    unmatched = []
    for p in rows2:
        source_name = p["Galaxy"]
        m = meta.get(source_name, {})
        candidates = [source_name, m.get("NED", "")]
        frozen = None
        matched_via = None
        for candidate in candidates:
            key = compact_name(candidate)
            if key and key in frozen_by_compact:
                frozen = frozen_by_compact[key]
                matched_via = "source_name" if candidate == source_name else "NED_name"
                break
        if frozen is None:
            unmatched.append(source_name)
            continue

        output.append({
            "galaxy": frozen,
            "stationary_role": roles[frozen],
            "source_galaxy_name": source_name,
            "source_ned_name": m.get("NED", ""),
            "match_method": matched_via,
            "source_distance_mpc": maybe_float(m.get("Dist", "")),
            "log10_sigma0_msun_pc2": maybe_float(p.get("logS0", "")),
            "e_log10_sigma0_msun_pc2": maybe_float(p.get("e_logS0", "")),
            "r0_kpc": maybe_float(p.get("R0", "")),
            "e_r0_kpc": maybe_float(p.get("e_R0", "")),
            "n_hi": maybe_float(p.get("nHI", "")),
            "e_n_hi": maybe_float(p.get("e_nHI", "")),
            "r50_hi_kpc": maybe_float(p.get("R50", "")),
            "e_r50_hi_kpc": maybe_float(p.get("e_R50", "")),
            "profile_formula_status": "pending_exact_primary_equation_verification",
            "source_values_transformed": "0",
            "source_catalog": "J/AJ/161/71",
            "source_table": "table2",
            "source_bibcode": "2021AJ....161...71H",
            "source_doi": "10.3847/1538-3881/abd089",
        })

    output.sort(key=lambda r: r["galaxy"])
    if not output:
        raise RuntimeError("No Hunter 2021 LITTLE THINGS galaxies matched the frozen 149 sample")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(output[0].keys()))
        w.writeheader(); w.writerows(output)

    summary = {
        "status": "PUBLIC_HI_SERSIC_PARAMETERS_ACQUIRED",
        "source_catalog": "J/AJ/161/71",
        "source_rows": 40,
        "n_frozen_matches": len(output),
        "n_calibration": sum(r["stationary_role"] == "calibration" for r in output),
        "n_blind": sum(r["stationary_role"] == "blind" for r in output),
        "matched_galaxies": [r["galaxy"] for r in output],
        "unmatched_source_names": unmatched,
        "formula_boundary": "Fit parameters are source data, but no analytic Sigma_HI(R) is instantiated until Hunter et al.'s exact Sersic functional convention is verified from the primary paper.",
        "split_sha256": sha256(split),
        "output_sha256": sha256(out),
    }
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
