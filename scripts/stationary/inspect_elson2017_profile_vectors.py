#!/usr/bin/env python3
"""Inspect vector drawing structure of Elson (2017) Appendix profile PDFs.

The arXiv source package for 1709.03288 contains profiles1_V2.pdf through
profiles4_V2.pdf.  This script does NOT digitize any scientific values.  It
records text positions and vector stroke/fill metadata so a subsequent
extractor can recover the published red Sigma_HI(R) series deterministically
from vector geometry rather than raster pixels.
"""
from __future__ import annotations

import collections
import io
import json
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

import fitz  # PyMuPDF

ARXIV_URL = "https://export.arxiv.org/e-print/1709.03288"
PROFILE_FILES = [f"profiles{i}_V2.pdf" for i in range(1, 5)]


def download() -> bytes:
    req = Request(ARXIV_URL, headers={"User-Agent": "PersistenceFrameworkPaperI/1.0"})
    with urlopen(req, timeout=90) as resp:
        return resp.read()


def norm_color(c):
    if c is None:
        return None
    return tuple(round(float(x), 4) for x in c)


def main() -> None:
    raw = download()
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    out = {"status": "ELSON2017_VECTOR_STRUCTURE_INSPECTED", "files": {}}

    for name in PROFILE_FILES:
        data = tf.extractfile(name).read()
        doc = fitz.open(stream=data, filetype="pdf")
        finfo = {"pdf_bytes": len(data), "pages": []}
        for pno, page in enumerate(doc):
            words = page.get_text("words")
            ugc_words = []
            for w in words:
                text = str(w[4])
                if "UGC" in text.upper() or text.isdigit() and len(text) >= 3:
                    ugc_words.append({
                        "text": text,
                        "bbox": [round(float(v), 3) for v in w[:4]],
                    })

            drawings = page.get_drawings()
            color_counts = collections.Counter()
            fill_counts = collections.Counter()
            colored = []
            for d in drawings:
                color = norm_color(d.get("color"))
                fill = norm_color(d.get("fill"))
                color_counts[str(color)] += 1
                fill_counts[str(fill)] += 1
                if color is not None and (
                    color[0] > 0.5 and color[1] < 0.6 and color[2] < 0.6
                ):
                    rect = d.get("rect")
                    colored.append({
                        "color": color,
                        "fill": fill,
                        "width": d.get("width"),
                        "closePath": d.get("closePath"),
                        "n_items": len(d.get("items", [])),
                        "rect": [round(float(rect.x0),3), round(float(rect.y0),3), round(float(rect.x1),3), round(float(rect.y1),3)] if rect else None,
                        "items_preview": [str(x)[:300] for x in d.get("items", [])[:8]],
                    })

            finfo["pages"].append({
                "page": pno,
                "page_rect": [round(float(v), 3) for v in (page.rect.x0,page.rect.y0,page.rect.x1,page.rect.y1)],
                "n_words": len(words),
                "ugc_or_numeric_words": ugc_words[:500],
                "n_drawings": len(drawings),
                "stroke_color_counts": dict(color_counts),
                "fill_color_counts": dict(fill_counts),
                "red_candidate_drawings": colored[:1000],
            })
        out["files"][name] = finfo

    path = Path("validation/stationary/elson2017_profile_vector_structure_v1.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    # Compact stdout for the Actions log.
    for name, finfo in out["files"].items():
        for p in finfo["pages"]:
            print(name, "page", p["page"], "drawings", p["n_drawings"], "red_candidates", len(p["red_candidate_drawings"]))
            print("UGC_NUMERIC_WORDS", p["ugc_or_numeric_words"][:80])
            print("STROKE_COLORS", p["stroke_color_counts"])
            for r in p["red_candidate_drawings"][:20]:
                print("RED", r)


if __name__ == "__main__":
    main()
