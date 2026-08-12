#!/usr/bin/env python3
"""Bounded raster text audit of Elson (2017) Appendix axis labels.

The scientific H I curves remain vector-exact.  This script is used only to
recover the printed numeric axis labels from the four public Appendix pages,
because those labels are outline paths rather than PDF text objects.

Exactly four Tesseract calls are made (one per Appendix page).  Recognized
numeric tokens are converted back to PDF-point coordinates and associated with
black plot-frame boxes.  No curve values are raster-digitized.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

import fitz

BASE = Path(__file__).with_name("calibrate_elson2017_whisp_vector_axes.py")
spec = importlib.util.spec_from_file_location("whisp_cal", BASE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

ARXIV = "https://export.arxiv.org/e-print/1709.03288"
ZOOM = 6.0
NUMERIC_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


def download() -> bytes:
    req = Request(ARXIV, headers={"User-Agent": "PersistenceFrameworkPaperI/1.0"})
    with urlopen(req, timeout=90) as resp:
        return resp.read()


def tesseract_tokens(png: Path) -> list[dict]:
    proc = subprocess.run(
        ["tesseract", str(png), "stdout", "--psm", "11", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = list(csv.DictReader(io.StringIO(proc.stdout), delimiter="\t"))
    out = []
    for r in rows:
        text = (r.get("text") or "").strip()
        if not text:
            continue
        try:
            conf = float(r.get("conf", "-1"))
            left = float(r["left"]) / ZOOM
            top = float(r["top"]) / ZOOM
            width = float(r["width"]) / ZOOM
            height = float(r["height"]) / ZOOM
        except Exception:
            continue
        out.append({
            "text": text,
            "conf": conf,
            "bbox_pdf": [left, top, left + width, top + height],
            "numeric": bool(NUMERIC_RE.match(text.replace("−", "-"))),
        })
    return out


def near_panel_tokens(tokens, box):
    x0, ytop, x1, ybase = box
    x_axis = []
    y_axis = []
    inside = []
    for t in tokens:
        a,b,c,d = t["bbox_pdf"]
        cx=(a+c)/2; cy=(b+d)/2
        if x0-5 <= cx <= x1+5 and ybase-2 <= cy <= ybase+28:
            x_axis.append(t)
        if x0-32 <= cx <= x0+2 and ytop-5 <= cy <= ybase+5:
            y_axis.append(t)
        if x0 <= cx <= x1 and ytop <= cy <= ybase:
            inside.append(t)
    return x_axis, y_axis, inside


def main() -> None:
    raw = download()
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    result = {
        "status": "ELSON2017_APPENDIX_AXIS_LABEL_AUDIT",
        "method": "four_page_raster_text_audit_axis_labels_only_curves_remain_vector_exact",
        "zoom": ZOOM,
        "files": [],
    }
    ugc_offset = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for pi, name in enumerate(mod.PDFS):
            pdf = tf.extractfile(name).read()
            doc = fitz.open(stream=pdf, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
            png = td / f"p{pi+1}.png"
            pix.save(str(png))
            tokens = tesseract_tokens(png)
            boxes = mod.plot_boxes(page)
            expected = 12 if pi < 3 else 1
            if len(boxes) != expected:
                raise RuntimeError(f"{name}: expected {expected} boxes, got {len(boxes)}")
            panels=[]
            for j, box in enumerate(boxes):
                ugc=mod.UGCS[ugc_offset+j]
                xa,ya,inside=near_panel_tokens(tokens,box)
                panels.append({
                    "ugc": f"UGC{ugc:05d}",
                    "panel_index": j,
                    "box_pdf": [float(v) for v in box],
                    "x_axis_tokens": xa,
                    "y_axis_tokens": ya,
                    "inside_panel_tokens": inside,
                })
            result["files"].append({
                "source_pdf": name,
                "n_tokens": len(tokens),
                "all_tokens": tokens,
                "panels": panels,
            })
            ugc_offset += expected
    result["boundary"] = (
        "Raster recognition is used only for printed axis/annotation labels. "
        "H I profile geometry is never raster-digitized. No helium, distance replacement, "
        "interpolation, persistence fitting, or blind-outcome inspection is performed."
    )
    out=Path("validation/stationary/elson2017_appendix_axis_label_audit_v1.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print('FILES',len(result['files']))
    for f in result['files']:
        print('\n',f['source_pdf'],'TOKENS',f['n_tokens'])
        for p in f['panels']:
            print(p['ugc'],'X',[t['text'] for t in p['x_axis_tokens']], 'Y',[t['text'] for t in p['y_axis_tokens']], 'IN',[t['text'] for t in p['inside_panel_tokens']])


if __name__ == "__main__":
    main()
