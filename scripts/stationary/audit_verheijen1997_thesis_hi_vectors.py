#!/usr/bin/env python3
"""Audit Verheijen (1997) Groningen thesis as a public vector H I-profile route.

This is a provenance-consistent fallback for the VS01/SV98 Ursa Major block.
The 1997 thesis documents the same Ursa Major H I synthesis program and is
publicly hosted by the University of Groningen chapter-by-chapter.  We audit
Chapter 4 first, then the complete thesis if needed.

Boundary: route/vector audit only.  No raster digitization, no model fitting,
no helium conversion, and no blind-outcome inspection.
"""
from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pymupdf

PUBLICATION = (
    "https://research.rug.nl/en/publications/"
    "the-ursa-major-cluster-of-galaxies-tf-relations-and-dark-matter/"
)
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0 Safari/537.36"
)
PRIORITY = Path(
    "data/stationary/source_reconstruction/"
    "sparc_hi_reference_family_priority_v1.csv"
)
OUT = Path(
    "validation/stationary/"
    "verheijen1997_thesis_hi_vector_route_audit_v1.json"
)


def fetch(url: str) -> bytes:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/pdf,*/*;q=0.8",
            "Referer": PUBLICATION,
        },
    )
    with urlopen(req, timeout=180) as h:
        return h.read()


def discover_pdf_links(page: bytes) -> dict[str, str]:
    text = page.decode("utf-8", errors="replace")
    candidates = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', text, re.I):
        href = html.unescape(m.group(1))
        low = href.lower()
        if ".pdf" in low:
            candidates.append(urljoin(PUBLICATION, href))
    # Also catch file URLs embedded in JSON/script payloads.
    for m in re.finditer(r'https?[^"\'<> ]+\.pdf(?:\?[^"\'<> ]*)?', text, re.I):
        candidates.append(html.unescape(m.group(0).replace("\\/", "/")))

    out: dict[str, str] = {}
    for u in candidates:
        base = u.split("?", 1)[0].rsplit("/", 1)[-1].lower()
        if base in {"c4.pdf", "thesis.pdf", "c5.pdf", "c6.pdf"}:
            out.setdefault(base, u)
    return out


def compact(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def variants(g: str) -> set[str]:
    if g.startswith("NGC"):
        n = g[3:].lstrip("0")
        return {compact(x) for x in (f"NGC{n}", f"NGC {n}", f"N{n}", f"N {n}")}
    if g.startswith("UGC"):
        n = g[3:].lstrip("0")
        return {compact(x) for x in (f"UGC{n}", f"UGC {n}", f"U{n}", f"U {n}")}
    return {compact(g)}


def page_text_norm(page) -> str:
    return compact(page.get_text("text"))


def find_pages(doc, galaxy: str) -> list[int]:
    vv = variants(galaxy)
    hits = []
    for i, p in enumerate(doc):
        txt = page_text_norm(p)
        if any(v and v in txt for v in vv):
            hits.append(i)
    return hits


def rect_list(r):
    return [round(float(r.x0), 3), round(float(r.y0), 3),
            round(float(r.x1), 3), round(float(r.y1), 3)]


def inspect_page(page, idx: int) -> dict:
    raw_text = page.get_text("text")
    low = raw_text.lower()
    drawings = page.get_drawings()
    images = page.get_images(full=True)
    ranked = []
    for d in drawings:
        r = d.get("rect")
        if r is None:
            continue
        n = len(d.get("items", []))
        ranked.append({
            "n_items": n,
            "rect": rect_list(r),
            "width": round(float(r.x1-r.x0), 3),
            "height": round(float(r.y1-r.y0), 3),
            "color": d.get("color"),
            "fill": d.get("fill"),
        })
    ranked.sort(key=lambda x: x["n_items"], reverse=True)
    long_paths = [
        x for x in ranked
        if x["n_items"] >= 20 and x["width"] >= 20 and x["height"] >= 5
    ]
    return {
        "page_index_0based": idx,
        "page_number_1based": idx + 1,
        "surface_density_text_present": "surface density" in low,
        "hi_text_present": ("h i" in low or "hi" in low),
        "n_drawings": len(drawings),
        "n_images": len(images),
        "n_long_vector_path_candidates": len(long_paths),
        "top_vector_paths": ranked[:25],
        "text_excerpt": " ".join(raw_text.split())[:3000],
    }


def audit_pdf(name: str, url: str, raw: bytes, galaxies: list[str]) -> dict:
    if raw[:5] != b"%PDF-":
        raise RuntimeError(f"{name} returned non-PDF prefix {raw[:20]!r}")
    doc = pymupdf.open(stream=raw, filetype="pdf")
    per = []
    for g in galaxies:
        pages = find_pages(doc, g)
        recs = [inspect_page(doc[p], p) for p in pages]
        per.append({
            "galaxy": g,
            "matching_pages": [p+1 for p in pages],
            "n_matching_pages": len(pages),
            "has_surface_density_page": any(r["surface_density_text_present"] for r in recs),
            "has_long_vector_path_candidate": any(r["n_long_vector_path_candidates"] > 0 for r in recs),
            "pages": recs,
        })
    return {
        "document": name,
        "url": url,
        "bytes": len(raw),
        "pages": len(doc),
        "n_total_drawings": sum(len(p.get_drawings()) for p in doc),
        "n_total_images": sum(len(p.get_images(full=True)) for p in doc),
        "n_priority_galaxies_found": sum(r["n_matching_pages"] > 0 for r in per),
        "n_with_surface_density_text": sum(r["has_surface_density_page"] for r in per),
        "n_with_long_vector_candidate": sum(r["has_long_vector_path_candidate"] for r in per),
        "missing_priority_galaxies": [r["galaxy"] for r in per if r["n_matching_pages"] == 0],
        "galaxies": per,
    }


def main() -> None:
    with PRIORITY.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    target = next((r for r in rows if r["sparc_ref_id"] == "VS01"), None)
    if target is None or int(target["n_untouched_frozen_galaxies"]) != 27:
        raise RuntimeError("Expected VS01 27-galaxy priority block")
    galaxies = target["galaxies"].split(";")

    page = fetch(PUBLICATION)
    links = discover_pdf_links(page)
    attempted = []
    audits = []
    errors = []

    # Chapter 4 is the 15.3 MB H I-heavy chapter listed by the repository.
    # If Pure changes its markup or c4 is insufficient, use the full thesis.
    for name in ("c4.pdf", "thesis.pdf"):
        url = links.get(name)
        if not url:
            errors.append(f"{name}: link not discovered in publication HTML")
            continue
        attempted.append({"document": name, "url": url})
        try:
            raw = fetch(url)
            audits.append(audit_pdf(name, url, raw, galaxies))
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")

    best = None
    if audits:
        best = max(
            audits,
            key=lambda a: (
                a["n_priority_galaxies_found"],
                a["n_with_surface_density_text"],
                a["n_with_long_vector_candidate"],
            ),
        )

    summary = {
        "status": "VERHEIJEN1997_THESIS_HI_VECTOR_ROUTE_AUDIT_COMPLETE",
        "source": "Verheijen 1997 PhD thesis, University of Groningen",
        "publication_page": PUBLICATION,
        "discovered_pdf_links": links,
        "attempted": attempted,
        "errors": errors,
        "n_priority_frozen_galaxies": len(galaxies),
        "priority_role_counts": {
            "calibration": int(target["n_calibration"]),
            "blind": int(target["n_blind"]),
        },
        "audits": audits,
        "best_document": None if best is None else best["document"],
        "best_n_priority_galaxies_found": 0 if best is None else best["n_priority_galaxies_found"],
        "best_n_with_surface_density_text": 0 if best is None else best["n_with_surface_density_text"],
        "best_n_with_long_vector_candidate": 0 if best is None else best["n_with_long_vector_candidate"],
        "route_viable_for_vector_extraction": bool(
            best is not None
            and best["n_priority_galaxies_found"] > 0
            and best["n_with_long_vector_candidate"] > 0
        ),
        "interpretation_rule": (
            "Vector-path presence is only a route-viability signal. It does not promote a profile. "
            "A subsequent extractor must isolate the radial H I surface-density panel, recover axes, "
            "and pass profile-level QC before any source profile is accepted."
        ),
        "boundary": (
            "Public provenance/vector audit only. No raster digitization, helium scaling, "
            "frozen-distance conversion, persistence fitting, or blind-outcome inspection."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "audits"}, indent=2))
    for a in audits:
        print("AUDIT", a["document"], {
            "pages": a["pages"],
            "galaxies_found": a["n_priority_galaxies_found"],
            "surface_density": a["n_with_surface_density_text"],
            "vector_candidate": a["n_with_long_vector_candidate"],
            "total_drawings": a["n_total_drawings"],
            "total_images": a["n_total_images"],
        })


if __name__ == "__main__":
    main()
