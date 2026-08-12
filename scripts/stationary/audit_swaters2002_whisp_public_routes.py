#!/usr/bin/env python3
"""Audit Swaters et al. (2002) WHISP Paper I for public radial H I profile assets.

Lelli/SPARC ref Sw02 is the next untouched source family after VS01/SV98:
13 frozen Paper-I galaxies (7 calibration, 6 blind).  Swaters et al. explicitly
publish radial H I surface-density profiles.  This audit inventories the arXiv
source bundle for machine-readable tables or reusable vector profile assets.

Boundary: acquisition audit only. No raster digitization, helium conversion,
persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations

import csv
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV = "https://export.arxiv.org/e-print/astro-ph/0204525"
UA = "PersistenceFrameworkPaperI/1.0"
PRIORITY = Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT = Path("validation/stationary/swaters2002_whisp_public_route_audit_v1.json")


def fetch(url: str) -> bytes:
    return urlopen(Request(url, headers={"User-Agent": UA}), timeout=120).read()


def compact(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def variants(g: str) -> set[str]:
    out = {compact(g)}
    if g.startswith("UGC"):
        n = g[3:].lstrip("0")
        out |= {compact(f"UGC {n}"), compact(f"U{n}"), compact(f"U {n}")}
    if g.startswith("DDO"):
        n = g[3:].lstrip("0")
        out |= {compact(f"DDO {n}")}
    return out


def main() -> None:
    with PRIORITY.open(newline="", encoding="utf-8-sig") as fh:
        priority = list(csv.DictReader(fh))
    target = next((r for r in priority if r["sparc_ref_id"] == "Sw02"), None)
    if target is None or int(target["n_untouched_frozen_galaxies"]) != 13:
        raise RuntimeError("Expected Sw02 13-galaxy priority block")
    galaxies = target["galaxies"].split(";")

    raw = fetch(ARXIV)
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    members = [m for m in tf.getmembers() if m.isfile()]

    vector_ext = {".eps", ".ps", ".pdf"}
    raster_ext = {".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff"}
    data_ext = {".dat", ".tab", ".csv", ".txt", ".tbl"}
    files = []
    text_hits = []
    galaxy_hits = {g: [] for g in galaxies}
    profile_re = re.compile(
        r"surface\s*density|radial\s*(?:h\s*i|hi).*profile|h\s*i.*surface|"
        r"appendix|atlas|includegraphics|epsfig",
        re.I,
    )

    for m in members:
        suffix = Path(m.name).suffix.lower()
        rec = {
            "name": m.name,
            "bytes": m.size,
            "suffix": suffix,
            "vector": suffix in vector_ext,
            "raster": suffix in raster_ext,
            "data_like": suffix in data_ext,
        }
        files.append(rec)
        if suffix in {".tex", ".txt", ".dat", ".tab", ".csv", ".tbl"}:
            try:
                text = tf.extractfile(m).read().decode("latin-1", "ignore")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if profile_re.search(line):
                    text_hits.append({"file": m.name, "line": i, "text": line[:800]})
                cl = compact(line)
                for g in galaxies:
                    if any(v and v in cl for v in variants(g)):
                        galaxy_hits[g].append({"file": m.name, "line": i, "text": line[:800]})

    vector = [f for f in files if f["vector"]]
    raster = [f for f in files if f["raster"]]
    data_like = [f for f in files if f["data_like"]]
    candidate = [
        f for f in files
        if re.search(r"prof|dens|surf|atlas|append|fig|hi|ugc|ddo", f["name"], re.I)
    ]

    result = {
        "status": "SWATERS2002_WHISP_PUBLIC_ROUTE_AUDIT_COMPLETE",
        "source": "Swaters et al. 2002 A&A 390 829; arXiv astro-ph/0204525",
        "n_priority_frozen_galaxies": len(galaxies),
        "priority_role_counts": {
            "calibration": int(target["n_calibration"]),
            "blind": int(target["n_blind"]),
        },
        "priority_galaxies": galaxies,
        "arxiv_bytes": len(raw),
        "n_arxiv_files": len(files),
        "n_vector_files": len(vector),
        "n_raster_files": len(raster),
        "n_data_like_files": len(data_like),
        "vector_files": vector,
        "raster_files": raster,
        "data_like_files": data_like,
        "candidate_named_assets": candidate,
        "text_hits": text_hits[:500],
        "galaxy_text_hits": galaxy_hits,
        "n_priority_galaxies_named_in_source_text": sum(bool(v) for v in galaxy_hits.values()),
        "interpretation": (
            "Swaters et al. explicitly publish radial H I surface-density profiles. "
            "This audit determines whether their arXiv source package contains numeric tables "
            "or vector assets suitable for reproducible recovery for the 13 Lelli/Sw02 frozen galaxies."
        ),
        "boundary": (
            "Acquisition-route audit only. No raster digitization, source normalization, helium conversion, "
            "persistence fitting, or blind-outcome inspection."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "n_priority_frozen_galaxies": result["n_priority_frozen_galaxies"],
        "priority_role_counts": result["priority_role_counts"],
        "arxiv_bytes": result["arxiv_bytes"],
        "n_arxiv_files": result["n_arxiv_files"],
        "n_vector_files": result["n_vector_files"],
        "n_raster_files": result["n_raster_files"],
        "n_data_like_files": result["n_data_like_files"],
        "n_priority_galaxies_named_in_source_text": result["n_priority_galaxies_named_in_source_text"],
    }, indent=2))
    print("VECTOR_FILES", [f["name"] for f in vector])
    print("DATA_FILES", [f["name"] for f in data_like])
    print("CANDIDATE_ASSETS", [f["name"] for f in candidate])


if __name__ == "__main__":
    main()
