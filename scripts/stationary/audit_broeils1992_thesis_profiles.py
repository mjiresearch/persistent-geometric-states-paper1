#!/usr/bin/env python3
"""Audit the official Broeils (1992) Groningen thesis for radial H I profiles.

Lelli/SPARC Br92 -> Broeils 1992 PhD thesis, University of Groningen.
This is acquisition/provenance only. The thesis PDF is downloaded to a temporary
workspace, inspected, and discarded; it is not redistributed in this repo.

The audit is deliberately bounded:
- official University of Groningen Research Portal/Pure routes first;
- one Wayback availability lookup per exact public URL if live transport fails;
- no OCR and no raster digitization;
- no persistence parameters or blind-outcome inspection.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

TARGETS = ["NGC0801", "NGC1003", "NGC2683", "NGC2998", "NGC5985", "NGC6674"]
URLS = [
    "https://research.rug.nl/files/3332246/broeils.PDF",
    "https://pure.rug.nl/ws/portalfiles/portal/3332246/broeils.PDF",
]
UA = "PersistenceFrameworkPaperI/1.0"
OUT = Path("validation/stationary/broeils1992_thesis_profile_audit_v1.json")


def fetch(url: str, timeout: int = 120) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), {"final_url": r.geturl(), "content_type": r.headers.get("Content-Type", "")}


def wayback_available(url: str) -> dict:
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    try:
        raw, meta = fetch(api, 60)
        return json.loads(raw.decode("utf-8", "replace"))
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def valid_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF-") and len(data) > 100_000


def compact(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def variants(g: str) -> list[str]:
    n = str(int(re.sub(r"\D", "", g)))
    return [f"NGC {n}", f"NGC{n}", f"NGC {n.zfill(4)}", f"NGC{n.zfill(4)}"]


def page_texts(pdf: Path) -> tuple[list[str], dict]:
    pdftotext = shutil.which("pdftotext")
    pdfinfo = shutil.which("pdfinfo")
    if not pdftotext:
        raise RuntimeError("pdftotext unavailable")
    meta = {}
    if pdfinfo:
        p = subprocess.run([pdfinfo, str(pdf)], capture_output=True, text=True, timeout=60)
        meta["pdfinfo"] = p.stdout[:12000]
    # Determine page count from pdfinfo; fall back to a generous bounded loop.
    m = re.search(r"(?mi)^Pages:\s*(\d+)", meta.get("pdfinfo", ""))
    n_pages = int(m.group(1)) if m else 300
    texts = []
    for pageno in range(1, n_pages + 1):
        cp = subprocess.run(
            [pdftotext, "-f", str(pageno), "-l", str(pageno), "-layout", str(pdf), "-"],
            capture_output=True, text=True, timeout=30,
        )
        if cp.returncode != 0:
            texts.append("")
        else:
            texts.append(cp.stdout)
    meta["n_pages_extracted"] = len(texts)
    return texts, meta


def page_graphics(pdf: Path, page_indices: list[int]) -> dict:
    """Non-raster geometry audit with PyMuPDF, installed by workflow."""
    import fitz  # PyMuPDF
    doc = fitz.open(pdf)
    out = {}
    for idx in sorted(set(page_indices)):
        if idx < 0 or idx >= len(doc):
            continue
        page = doc[idx]
        drawings = page.get_drawings()
        images = page.get_images(full=True)
        item_counts = []
        for d in drawings:
            items = d.get("items", [])
            item_counts.append(len(items))
        out[str(idx + 1)] = {
            "page_number_1based": idx + 1,
            "n_drawings": len(drawings),
            "drawing_items_total": sum(item_counts),
            "drawing_items_max_single_object": max(item_counts) if item_counts else 0,
            "n_images": len(images),
            "text_chars": len(page.get_text("text")),
        }
    return out


def contexts(text: str, pats: list[str], radius: int = 6) -> list[dict]:
    lines = text.splitlines()
    regs = [re.compile(re.escape(p), re.I) for p in pats]
    hits = []
    for i, line in enumerate(lines):
        if any(r.search(line) for r in regs):
            lo, hi = max(0, i-radius), min(len(lines), i+radius+1)
            hits.append({"line": i+1, "context": "\n".join(lines[lo:hi])[:5000]})
    return hits[:40]


def main() -> None:
    attempts = []
    pdf_data = None
    recovered_url = None
    recovered_route = None

    for url in URLS:
        try:
            data, meta = fetch(url)
            rec = {"route": "live", "url": url, "bytes": len(data), **meta, "valid_pdf": valid_pdf(data)}
            attempts.append(rec)
            if valid_pdf(data):
                pdf_data, recovered_url, recovered_route = data, meta.get("final_url", url), "live"
                break
        except Exception as exc:
            attempts.append({"route": "live", "url": url, "status": "error", "error": f"{type(exc).__name__}: {exc}"})

    wayback = []
    if pdf_data is None:
        for url in URLS:
            av = wayback_available(url)
            wayback.append({"url": url, "availability": av})
            snap = ((av.get("archived_snapshots") or {}).get("closest") or {}) if isinstance(av, dict) else {}
            snap_url = snap.get("url") if snap.get("available") else None
            if not snap_url:
                continue
            # Prefer raw snapshot payload, but keep exact archived provenance.
            raw_url = re.sub(r"/web/(\d+)/", r"/web/\1id_/", snap_url, count=1)
            try:
                data, meta = fetch(raw_url, 180)
                rec = {"route": "wayback", "url": raw_url, "bytes": len(data), **meta, "valid_pdf": valid_pdf(data)}
                attempts.append(rec)
                if valid_pdf(data):
                    pdf_data, recovered_url, recovered_route = data, raw_url, "wayback"
                    break
            except Exception as exc:
                attempts.append({"route": "wayback", "url": raw_url, "status": "error", "error": f"{type(exc).__name__}: {exc}"})

    result = {
        "status": "BROEILS1992_THESIS_PROFILE_AUDIT_COMPLETE",
        "source": "A.H. Broeils 1992, Dark and visible matter in spiral galaxies, PhD thesis, University of Groningen",
        "official_portal_page": "https://research.rug.nl/en/publications/dark-and-visible-matter-in-spiral-galaxies/",
        "target_galaxies": TARGETS,
        "transport_attempts": attempts,
        "wayback_availability": wayback,
        "recovered": pdf_data is not None,
        "recovered_route": recovered_route,
        "recovered_url": recovered_url,
        "boundary": "Acquisition/provenance only; no OCR, raster digitization, profile normalization, persistence fitting, or blind-outcome inspection.",
    }

    if pdf_data is not None:
        result["pdf_bytes"] = len(pdf_data)
        result["pdf_sha256"] = hashlib.sha256(pdf_data).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "broeils1992.pdf"
            pdf.write_bytes(pdf_data)
            texts, meta = page_texts(pdf)
            result["pdf_metadata"] = meta
            target_results = []
            graphics_pages = []
            science_terms = [
                "surface density", "surface-density", "H I distribution", "HI distribution",
                "radial distribution", "radial surface", "gas surface", "hydrogen surface",
                "mass surface density", "strip integral", "deproject",
            ]
            for g in TARGETS:
                vv = variants(g)
                hit_pages = [i for i,t in enumerate(texts) if any(v.lower() in t.lower() for v in vv)]
                # Include immediate neighboring pages because captions/figures often split across scans.
                inspect_pages = sorted({j for i in hit_pages for j in (i-1,i,i+1) if 0 <= j < len(texts)})
                graphics_pages.extend(inspect_pages)
                contexts_by_page = []
                for i in hit_pages:
                    contexts_by_page.append({
                        "page_number_1based": i+1,
                        "galaxy_contexts": contexts(texts[i], vv, 8),
                        "science_term_contexts": contexts(texts[i], science_terms, 5),
                        "page_text_excerpt": " ".join(texts[i].split())[:6000],
                    })
                target_results.append({
                    "galaxy": g,
                    "text_hit_pages_1based": [i+1 for i in hit_pages],
                    "n_text_hit_pages": len(hit_pages),
                    "contexts": contexts_by_page,
                })
            result["target_results"] = target_results
            result["target_neighbor_page_graphics"] = page_graphics(pdf, graphics_pages)

            # Global profile-language index for locating likely tables/figures even when a galaxy label is graphical.
            global_hits = []
            for i,t in enumerate(texts):
                if any(term.lower() in t.lower() for term in science_terms):
                    global_hits.append({
                        "page_number_1based": i+1,
                        "matched_terms": [term for term in science_terms if term.lower() in t.lower()],
                        "excerpt": " ".join(t.split())[:3500],
                    })
            result["global_profile_language_pages"] = global_hits[:120]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    compact_out = {
        "status": result["status"],
        "recovered": result["recovered"],
        "recovered_route": result.get("recovered_route"),
        "pdf_bytes": result.get("pdf_bytes"),
        "targets_found": {
            r["galaxy"]: r["text_hit_pages_1based"]
            for r in result.get("target_results", [])
        },
    }
    print(json.dumps(compact_out, indent=2))


if __name__ == "__main__":
    main()
