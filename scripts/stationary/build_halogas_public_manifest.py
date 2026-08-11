#!/usr/bin/env python3
"""Crossmatch HALOGAS DR1 public HI column-density maps to the frozen stationary sample.

This is acquisition/provenance plumbing only. It queries the Zenodo record API,
selects high-resolution column-density FITS products, canonicalizes galaxy names,
and intersects them with validation/stationary/stationary_split_v1.csv.
"""
from __future__ import annotations
import csv, json, re, urllib.request
from pathlib import Path

ZENODO_RECORD = "3715549"  # HALOGAS DR1 v2
ZENODO_API = f"https://zenodo.org/api/records/{ZENODO_RECORD}"
SPLIT = Path("validation/stationary/stationary_split_v1.csv")
OUT = Path("data/stationary/source_reconstruction/halogas_stationary_overlap_v1.csv")


def canon(s: str) -> str:
    x = re.sub(r"[^A-Z0-9]", "", s.upper())
    m = re.fullmatch(r"NGC0*(\d+)", x)
    if m:
        return f"NGC{int(m.group(1)):04d}"
    m = re.fullmatch(r"UGC0*(\d+)", x)
    if m:
        return f"UGC{int(m.group(1)):05d}"
    return x


def main():
    with urllib.request.urlopen(ZENODO_API, timeout=60) as r:
        rec = json.load(r)
    with SPLIT.open(newline="", encoding="utf-8") as f:
        split = list(csv.DictReader(f))
    frozen = {canon(r["galaxy"]): r for r in split}
    rows = []
    for f in rec.get("files", []):
        key = f.get("key", "")
        if not key.endswith("-HR_coldens.fits"):
            continue
        raw_gal = key[: -len("-HR_coldens.fits")]
        g = canon(raw_gal)
        if g not in frozen:
            continue
        s = frozen[g]
        links = f.get("links", {})
        rows.append({
            "galaxy": s["galaxy"],
            "stationary_role": s["stationary_role"],
            "zenodo_record": ZENODO_RECORD,
            "doi": "10.5281/zenodo.3715549",
            "source_family": "HALOGAS_DR1_v2",
            "product": "high_resolution_HI_column_density_map",
            "filename": key,
            "download_url": links.get("content", links.get("self", "")),
            "checksum": f.get("checksum", ""),
            "size_bytes": f.get("size", ""),
            "profile_method": "direct_public_column_density_map_annular_extraction",
            "notes": "Use frozen common annular extractor; preserve beam/WCS and no-extrapolation policy.",
        })
    rows.sort(key=lambda r: r["galaxy"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["galaxy","stationary_role","zenodo_record","doi","source_family","product","filename","download_url","checksum","size_bytes","profile_method","notes"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"HALOGAS HR column-density products overlapping frozen sample: {len(rows)}")
    for r in rows:
        print(r["galaxy"], r["stationary_role"], r["filename"])

if __name__ == "__main__":
    main()
