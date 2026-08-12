#!/usr/bin/env python3
"""Audit Spekkens & Giovanelli (2006; SG06) for public radial H I profile assets.

SG06 is the current highest-yield actionable Lelli/SPARC family: five frozen
Paper-I galaxies (4 calibration, 1 blind). The paper reports new aperture-
synthesis H I observations for its fast-rotator sample, so it is treated as a
potential original observing source rather than a downstream mass-model paper.

This audit inventories the arXiv source package for machine-readable data,
vector figures, target-specific assets, H I surface-density/profile language,
public data/archive locators, and explicit statements about the H I observing
setup. It also checks the expected VizieR catalogue endpoint without assuming
that journal pagination implies a CDS catalogue.

Acquisition/provenance only. No raster digitization, profile-value extraction,
helium conversion, distance rescaling, persistence fitting, or blind-outcome
inspection occurs.
"""
from __future__ import annotations

import csv
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ARXIV = "https://export.arxiv.org/e-print/astro-ph/0605542"
CDS_EXPECTED = "https://cdsarc.cds.unistra.fr/ftp/J/AJ/132/1426/ReadMe"
UA = "PersistenceFrameworkPaperI/1.0"
PRIORITY = Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT = Path("validation/stationary/sg06_hi_public_route_audit_v1.json")


def fetch(url: str, timeout: int = 120) -> tuple[bytes, str, str]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urlopen(req, timeout=timeout) as h:
        return h.read(), h.geturl(), h.headers.get("Content-Type", "")


def compact(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def variants(g: str) -> set[str]:
    c = compact(g)
    out = {c}
    m = re.match(r"(NGC|UGC|IC|ESO)0*(\d+)(.*)$", c)
    if m:
        p, n, rest = m.groups()
        n2 = str(int(n))
        out |= {p+n2+rest, p+n2.zfill(5)+rest}
    # Common typography in paper source.
    if c.startswith("ESO") and "G" in c:
        out.add(c.replace("G", "-G"))
    return {compact(x) for x in out}


def main() -> None:
    with PRIORITY.open(newline="", encoding="utf-8-sig") as fh:
        priority = list(csv.DictReader(fh))
    target = next((r for r in priority if r["sparc_ref_id"] == "SG06"), None)
    if target is None or int(target["n_untouched_frozen_galaxies"]) != 5:
        raise RuntimeError("Expected SG06 five-galaxy actionable block")
    galaxies = target["galaxies"].split(";")

    raw, arxiv_final, arxiv_ct = fetch(ARXIV)
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    members = [m for m in tf.getmembers() if m.isfile()]

    files = []
    texts = []
    for m in members:
        suffix = Path(m.name).suffix.lower()
        rec = {
            "name": m.name,
            "bytes": m.size,
            "suffix": suffix,
            "data_like": suffix in {".dat", ".tab", ".csv", ".txt", ".tbl", ".fits", ".fit", ".fts"},
            "vector": suffix in {".eps", ".ps", ".pdf"},
            "raster": suffix in {".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff"},
        }
        files.append(rec)
        if suffix in {".tex", ".txt", ".dat", ".tab", ".csv", ".tbl"}:
            try:
                txt = tf.extractfile(m).read().decode("latin-1", "ignore")
                texts.append((m.name, txt))
            except Exception:
                pass

    pattern = re.compile(
        r"surface\s*density|column\s*density|radial\s+(?:H\s*I|HI)|"
        r"H\s*I\s+(?:surface|distribution|profile|map|observ)|moment\s*0|"
        r"aperture\s+synthesis|VLA|WSRT|Arecibo|archive|data\s+available|"
        r"electronic|online|Table|Appendix|rotation\s+curve",
        re.I,
    )
    text_hits = []
    urls = []
    target_hits = {g: [] for g in galaxies}
    for fname, txt in texts:
        for i, line in enumerate(txt.splitlines(), 1):
            if pattern.search(line):
                text_hits.append({"file": fname, "line": i, "text": line[:1200]})
            cl = compact(line)
            for g in galaxies:
                if any(v and v in cl for v in variants(g)):
                    target_hits[g].append({"file": fname, "line": i, "text": line[:1200]})
        for u in re.findall(r"https?://[^\s{}\\]+|www\.[^\s{}\\]+", txt, flags=re.I):
            u = u.rstrip(".,;)")
            if u.startswith("www."):
                u = "http://" + u
            if u not in urls:
                urls.append(u)

    combined = "\n".join(t for _, t in texts)
    data_like = [f for f in files if f["data_like"]]
    vector = [f for f in files if f["vector"]]
    raster = [f for f in files if f["raster"]]
    candidate_assets = [
        f for f in files
        if re.search(r"hi|moment|dens|prof|map|rot|vel|fig|gal", f["name"], re.I)
    ]

    cds = {"url": CDS_EXPECTED}
    try:
        cbytes, cfinal, cct = fetch(CDS_EXPECTED, 30)
        cds.update({
            "status": "fetched", "final_url": cfinal, "content_type": cct,
            "bytes": len(cbytes), "prefix": cbytes[:120].decode("latin-1", "replace")
        })
    except HTTPError as exc:
        cds.update({"status": "http_error", "code": exc.code, "error": str(exc)})
    except Exception as exc:
        cds.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})

    # Inspect vector candidates as inert source bytes for signs of true paths vs raster images.
    vector_structure = []
    for f in vector:
        try:
            b = tf.extractfile(f["name"]).read()
        except Exception:
            continue
        vector_structure.append({
            "name": f["name"], "bytes": len(b),
            "image_ops": len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])", b)),
            "colorimage_ops": b.count(b"colorimage"),
            "imagemask_ops": b.count(b"imagemask"),
            "moveto_tokens": b.count(b"moveto"),
            "lineto_tokens": b.count(b"lineto"),
            "curveto_tokens": b.count(b"curveto"),
            "stroke_tokens": b.count(b"stroke"),
            "surface_density_literal": bool(re.search(rb"surface\s*density|column\s*density|sigma", b, re.I)),
        })

    result = {
        "status": "SG06_HI_PUBLIC_ROUTE_AUDIT_COMPLETE",
        "source": "Spekkens & Giovanelli 2006 AJ 132 1426-1444; arXiv astro-ph/0605542",
        "n_priority_frozen_galaxies": len(galaxies),
        "priority_role_counts": {
            "calibration": int(target["n_calibration"]),
            "blind": int(target["n_blind"]),
        },
        "priority_galaxies": galaxies,
        "arxiv_url": arxiv_final,
        "arxiv_content_type": arxiv_ct,
        "arxiv_bytes": len(raw),
        "n_arxiv_files": len(files),
        "n_data_like_files": len(data_like),
        "data_like_files": data_like,
        "n_vector_files": len(vector),
        "vector_files": vector,
        "n_raster_files": len(raster),
        "raster_files": raster,
        "candidate_named_assets": candidate_assets,
        "vector_structure": vector_structure,
        "target_text_hits": target_hits,
        "n_targets_named_in_source_text": sum(bool(v) for v in target_hits.values()),
        "text_hits": text_hits[:1000],
        "embedded_urls": urls,
        "cds_expected_catalog_probe": cds,
        "surface_density_mentions": len(re.findall(r"surface\s*density", combined, re.I)),
        "column_density_mentions": len(re.findall(r"column\s*density", combined, re.I)),
        "hi_profile_mentions": len(re.findall(r"H\s*I\s+(?:surface|distribution|profile)", combined, re.I)),
        "aperture_synthesis_mentions": len(re.findall(r"aperture\s+synthesis", combined, re.I)),
        "interpretation_rule": (
            "SG06 is treated as a potential direct observing source because it reports new resolved H I observations. "
            "It is promoted to a radial-profile source only if the public package or a directly linked archive exposes a defensible "
            "radial H I surface-density product, analytic representation, or exact recoverable vector geometry."
        ),
        "boundary": (
            "Acquisition/provenance only. No raster digitization, profile-value extraction, helium conversion, "
            "distance rescaling, persistence fitting, or blind-outcome inspection."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "targets": galaxies,
        "n_arxiv_files": result["n_arxiv_files"],
        "n_data_like_files": result["n_data_like_files"],
        "n_vector_files": result["n_vector_files"],
        "n_raster_files": result["n_raster_files"],
        "n_targets_named_in_source_text": result["n_targets_named_in_source_text"],
        "surface_density_mentions": result["surface_density_mentions"],
        "column_density_mentions": result["column_density_mentions"],
        "hi_profile_mentions": result["hi_profile_mentions"],
        "cds_probe": cds,
        "urls": urls,
    }, indent=2))
    print("DATA", [f["name"] for f in data_like])
    print("VECTOR", [f["name"] for f in vector])


if __name__ == "__main__":
    main()
