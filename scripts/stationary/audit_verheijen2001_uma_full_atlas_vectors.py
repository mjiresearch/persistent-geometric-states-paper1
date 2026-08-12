#!/usr/bin/env python3
"""Audit the complete A&A Verheijen & Sancisi (2001) atlas for vector H I profiles.

The arXiv source bundle contains only the first two Appendix atlas PostScript
assets, so this bounded follow-up inspects the complete publisher atlas. It does
not digitize curves or fit any model. It only determines whether the 27 frozen
VS01/SV98 priority galaxies can be located in the full public atlas and whether
their radial H I surface-density panels retain extractable vector geometry.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

import fitz

PDF_URL = "https://www.aanda.org/articles/aa/pdf/2001/18/aa10469.pdf"
PS_GZ_URL = "https://www.aanda.org/articles/aa/ps/2001/18/aa10469.ps.gz"
UA = "PersistenceFrameworkPaperI/1.0"
PRIORITY = Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT = Path("validation/stationary/verheijen2001_uma_full_atlas_vector_audit_v1.json")


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=180) as h:
        return h.read()


def open_complete_atlas():
    errors = []
    try:
        raw = fetch(PDF_URL)
        if raw[:5] == b"%PDF-":
            return fitz.open(stream=raw, filetype="pdf"), "publisher_pdf", len(raw), errors
        errors.append(f"publisher PDF returned non-PDF prefix {raw[:16]!r}")
    except Exception as exc:
        errors.append(f"publisher PDF fetch failed: {type(exc).__name__}: {exc}")

    raw_gz = fetch(PS_GZ_URL)
    ps = gzip.decompress(raw_gz)
    gs = shutil.which("gs")
    if not gs:
        raise RuntimeError("Publisher PDF unavailable and Ghostscript not installed for PS fallback")
    with tempfile.TemporaryDirectory() as td:
        ps_path = Path(td) / "atlas.ps"
        pdf_path = Path(td) / "atlas.pdf"
        ps_path.write_bytes(ps)
        subprocess.run(
            [gs, "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf_path}", str(ps_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pdf = pdf_path.read_bytes()
    return fitz.open(stream=pdf, filetype="pdf"), "publisher_ps_gz_converted", len(raw_gz), errors


def variants(galaxy: str) -> list[str]:
    if galaxy.startswith("NGC"):
        n = galaxy[3:].lstrip("0")
        return [f"NGC{n}", f"NGC {n}", f"N{n}", f"N {n}"]
    if galaxy.startswith("UGC"):
        n = galaxy[3:].lstrip("0")
        return [f"UGC{n}", f"UGC {n}", f"U{n}", f"U {n}"]
    return [galaxy]


def norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def find_pages(doc, galaxy: str) -> list[int]:
    nv = {norm(v) for v in variants(galaxy)}
    out = []
    for i, page in enumerate(doc):
        t = norm(page.get_text("text"))
        if any(v and v in t for v in nv):
            out.append(i)
    return out


def rect_dict(r):
    if r is None:
        return None
    return [round(float(r.x0), 3), round(float(r.y0), 3), round(float(r.x1), 3), round(float(r.y1), 3)]


def drawing_summary(page):
    drawings = page.get_drawings()
    ranked = []
    for d in drawings:
        items = d.get("items", [])
        r = d.get("rect")
        if r is None:
            continue
        ranked.append({
            "n_items": len(items),
            "rect": rect_dict(r),
            "width": round(float(r.x1 - r.x0), 3),
            "height": round(float(r.y1 - r.y0), 3),
            "fill": d.get("fill") is not None,
            "close_path": bool(d.get("closePath")),
        })
    ranked.sort(key=lambda x: x["n_items"], reverse=True)
    return drawings, ranked[:20]


def page_record(page, page_index: int):
    text = page.get_text("text")
    text_norm = " ".join(text.split())
    surface_rects = []
    for needle in ("Surface density", "surface density", "H I surface density", "HI surface density"):
        for r in page.search_for(needle):
            surface_rects.append(rect_dict(r))
    drawings, ranked = drawing_summary(page)
    images = page.get_images(full=True)
    long_paths = [r for r in ranked if r["n_items"] >= 20 and r["width"] > 20 and r["height"] > 5]
    return {
        "page_index_0based": page_index,
        "page_number_1based": page_index + 1,
        "surface_density_text_present": "surface density" in text.lower(),
        "surface_density_text_rects": surface_rects,
        "n_drawings": len(drawings),
        "n_images": len(images),
        "n_long_vector_path_candidates_top20": len(long_paths),
        "top_vector_paths": ranked,
        "text_excerpt": text_norm[:2500],
    }


def main():
    with PRIORITY.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    target = next((r for r in rows if r["sparc_ref_id"] == "VS01"), None)
    if target is None or int(target["n_untouched_frozen_galaxies"]) != 27:
        raise RuntimeError("Expected VS01 27-galaxy priority block")
    galaxies = target["galaxies"].split(";")

    doc, route, source_bytes, route_errors = open_complete_atlas()
    per = []
    for g in galaxies:
        pages = find_pages(doc, g)
        recs = [page_record(doc[p], p) for p in pages]
        per.append({
            "galaxy": g,
            "matching_pages": [p + 1 for p in pages],
            "n_matching_pages": len(pages),
            "pages": recs,
            "has_surface_density_page": any(r["surface_density_text_present"] for r in recs),
            "has_vector_path_candidate": any(r["n_long_vector_path_candidates_top20"] > 0 for r in recs),
        })

    found = [r for r in per if r["n_matching_pages"] > 0]
    surf = [r for r in per if r["has_surface_density_page"]]
    vec = [r for r in per if r["has_vector_path_candidate"]]
    summary = {
        "status": "VERHEIJEN2001_UMA_FULL_ATLAS_VECTOR_AUDIT_COMPLETE",
        "source_route": route,
        "source_url_primary": PDF_URL,
        "source_url_fallback": PS_GZ_URL,
        "source_download_bytes": source_bytes,
        "route_errors": route_errors,
        "pdf_pages": len(doc),
        "n_priority_frozen_galaxies": len(galaxies),
        "role_counts": {"calibration": int(target["n_calibration"]), "blind": int(target["n_blind"])},
        "n_galaxies_found_in_full_atlas_text": len(found),
        "n_galaxies_with_surface_density_page": len(surf),
        "n_galaxies_with_vector_path_candidate": len(vec),
        "missing_galaxies": [r["galaxy"] for r in per if r["n_matching_pages"] == 0],
        "no_surface_density_text_galaxies": [r["galaxy"] for r in per if not r["has_surface_density_page"]],
        "no_vector_candidate_galaxies": [r["galaxy"] for r in per if not r["has_vector_path_candidate"]],
        "galaxies": per,
        "interpretation_rule": "A positive vector-candidate flag means the publisher atlas page contains nontrivial vector paths; it is a route-viability signal, not yet an extracted H I profile. Final extraction requires isolating the radial surface-density panel and validating its axis mapping.",
        "boundary": "Public-route/vector audit only. No raster digitization, no source normalization, no helium conversion, no persistence fitting, and no blind-outcome inspection.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "galaxies"}, indent=2))


if __name__ == "__main__":
    main()
