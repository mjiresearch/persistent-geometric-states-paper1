#!/usr/bin/env python3
"""Run the Elson 2017 WHISP axis calibration with frame-containment mapping.

The v1 calibration logic is retained, but panel identity is assigned by the
red curve's centre lying inside one and only one recovered black plot frame.
This is robust to published profiles whose red vector does not extend all the
way to the right-hand plot boundary.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

BASE = Path(__file__).with_name("calibrate_elson2017_whisp_vector_axes.py")
spec = importlib.util.spec_from_file_location("whisp_cal", BASE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def panel_paths_containment(tf):
    ans = []
    offset = 0
    for pi, name in enumerate(mod.PDFS):
        doc = mod.fitz.open(stream=tf.extractfile(name).read(), filetype="pdf")
        page = doc[0]
        reds = []
        for d in page.get_drawings():
            if mod.col(d.get("color")) == (1.0, 0.0, 0.0):
                seg = mod.lines(d)
                if len(seg) >= 20:
                    reds.append((d, seg))

        boxes = mod.plot_boxes(page)
        expected = 12 if pi < 3 else 1
        if len(boxes) != expected:
            raise RuntimeError(f"{name}: expected {expected} plot boxes, got {len(boxes)}")
        if len(reds) != expected:
            raise RuntimeError(f"{name}: expected {expected} red paths, got {len(reds)}")

        assignments = []
        used = set()
        for box in boxes:
            x0, y0, x1, y1 = box
            matches = []
            for ri, (d, seg) in enumerate(reds):
                r = d["rect"]
                cx = (r.x0 + r.x1) / 2.0
                cy = (r.y0 + r.y1) / 2.0
                if x0 - 1.0 <= cx <= x1 + 1.0 and y0 - 1.0 <= cy <= y1 + 1.0:
                    matches.append((ri, d, seg))
            if len(matches) != 1:
                raise RuntimeError(
                    f"{name}: frame {box} has {len(matches)} centre-contained red paths; "
                    f"centres={[(round((d['rect'].x0+d['rect'].x1)/2,2), round((d['rect'].y0+d['rect'].y1)/2,2)) for d,_ in reds]}"
                )
            ri, d, seg = matches[0]
            if ri in used:
                raise RuntimeError(f"{name}: red path {ri} assigned twice")
            used.add(ri)
            assignments.append((box, d, seg))

        if len(used) != expected:
            raise RuntimeError(f"{name}: only {len(used)}/{expected} red paths assigned")
        for j, (box, d, seg) in enumerate(assignments):
            ugc = mod.UGCS[offset + j]
            ans.append((ugc, name, j, page, box, d, seg))
        offset += expected

    if offset != 37:
        raise RuntimeError(offset)
    return ans


mod.panel_paths = panel_paths_containment
mod.main()
