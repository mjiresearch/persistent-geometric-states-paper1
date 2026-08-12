#!/usr/bin/env python3
"""Audit exact embedded Swaters+2002 atlas figure blocks for vector recoverability.

Inputs are publication-traceable only:
  Lelli/SPARC -> Sw02 -> Swaters+2002 Appendix-B figure -> recovered author atlas.

For each of the 13 frozen Sw02 targets, locate the exact embedded h3074fNN.ps
subdocument in the recovered monolithic PostScript and inspect its native text
and graphics operators *without executing PostScript*.  This decides whether
there is evidence for an exact vector radial-HI profile route.  It does not
extract raster pixels or numerical profile values.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

ATLAS = (
    "http://web.archive.org/web/20070824112627id_/"
    "http://www.robswork.net/publications/WHISPI.ps.gz"
)
UA = "PersistenceFrameworkPaperI/1.0"
MAP = Path("data/stationary/source_reconstruction/sw02_recovered_atlas_page_map_v1.csv")
OUT = Path("validation/stationary/sw02_recovered_figure_block_audit_v1.json")


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urlopen(req, timeout=240) as h:
        return h.read()


def count_token(block: bytes, token: bytes) -> int:
    return len(re.findall(rb"(?<![A-Za-z])" + re.escape(token) + rb"(?![A-Za-z])", block))


def ascii_comment_lines(block: bytes, limit: int = 120) -> list[str]:
    out=[]
    for raw in block.splitlines()[:limit]:
        if raw.startswith(b"%"):
            out.append(raw.decode("latin-1", "replace")[:500])
    return out


def literal_strings(block: bytes) -> list[str]:
    vals=[]
    for raw in re.findall(rb"\(((?:\\.|[^\\)])*)\)", block):
        s=raw.decode("latin-1","replace")
        s=re.sub(r"\\([0-7]{1,3})",lambda m:chr(int(m.group(1),8)),s)
        s=s.replace(r"\(","(").replace(r"\)",")").replace(r"\\","\\")
        if s.strip(): vals.append(s[:300])
    return vals


def locate_block(ps: bytes, fig: int) -> tuple[int,int,bytes,str]:
    name=f"h3074f{fig}.ps".encode()
    pos=ps.find(name)
    if pos < 0:
        raise RuntimeError(f"embedded figure marker not found: {name!r}")

    # Prefer a DSC BeginDocument wrapper if retained.
    begin=ps.rfind(b"%%BeginDocument", max(0,pos-5000), pos+1)
    if begin < 0:
        begin=pos
    end=ps.find(b"%%EndDocument", pos)
    method="dsc_begin_end"
    if end >= 0:
        eol=ps.find(b"\n",end)
        end=len(ps) if eol < 0 else eol+1
    else:
        # Fall back to the next embedded Appendix filename marker.
        nexts=[]
        for n in range(fig+1,86):
            p=ps.find(f"h3074f{n}.ps".encode(),pos+1)
            if p >= 0:
                nexts.append(p); break
        end=nexts[0] if nexts else min(len(ps),pos+5_000_000)
        method="next_figure_marker_fallback"
    return begin,end,ps[begin:end],method


def classify(rec: dict) -> str:
    # Conservative decision rule. A typical plotted polyline should leave
    # substantial native geometry unless the figure is rasterized/encoded.
    raster_ops=rec["image_ops"]+rec["colorimage_ops"]+rec["imagemask_ops"]
    path_ops=rec["lineto_ops"]+rec["curveto_ops"]
    creator=" ".join(rec["creator_lines"]).lower()
    if raster_ops > 0 and path_ops < 150:
        return "raster_dominant_no_exact_vector_profile_evidence"
    if raster_ops > 0 and ("image" in creator or "xv" in creator or "convert" in creator):
        return "raster_dominant_no_exact_vector_profile_evidence"
    if raster_ops == 0 and path_ops >= 150:
        return "native_vector_candidate_requires_panel_axis_isolation"
    if raster_ops > 0 and path_ops >= 150:
        return "mixed_graphics_requires_bottom_left_panel_isolation"
    return "insufficient_native_geometry_evidence"


def main() -> None:
    with MAP.open(newline="",encoding="utf-8-sig") as fh:
        rows=list(csv.DictReader(fh))
    if len(rows)!=13:
        raise RuntimeError(f"Expected 13 Sw02 mapped targets, got {len(rows)}")

    raw=fetch(ATLAS)
    ps=gzip.decompress(raw)
    results=[]
    for r in rows:
        fig=int(r["appendix_figure_number"])
        begin,end,block,method=locate_block(ps,fig)
        comments=ascii_comment_lines(block)
        strings=literal_strings(block)
        creators=[x for x in comments if re.search(r"Creator|Producer|Title|For:|CreationDate",x,re.I)]
        rec={
            "galaxy":r["galaxy"],
            "stationary_role":r["stationary_role"],
            "ugc":int(r["ugc"]),
            "appendix_figure_number":fig,
            "block_locator_method":method,
            "block_start":begin,
            "block_end":end,
            "block_bytes":len(block),
            "block_sha256":hashlib.sha256(block).hexdigest(),
            "creator_lines":creators[:30],
            "bounding_box_lines":[x for x in comments if "BoundingBox" in x][:20],
            "image_ops":count_token(block,b"image"),
            "colorimage_ops":count_token(block,b"colorimage"),
            "imagemask_ops":count_token(block,b"imagemask"),
            "moveto_ops":count_token(block,b"moveto"),
            "lineto_ops":count_token(block,b"lineto"),
            "curveto_ops":count_token(block,b"curveto"),
            "stroke_ops":count_token(block,b"stroke"),
            "show_ops":count_token(block,b"show"),
            "literal_string_count":len(strings),
            "useful_strings":[s for s in strings if re.search(r"UGC|DDO|HI|H I|M.?sun|pc|kpc|arcsec|Sigma|surface|density|radius",s,re.I)][:100],
            "header_comments":comments[:80],
        }
        rec["recoverability_classification"]=classify(rec)
        results.append(rec)

    counts={}
    for r in results:
        counts[r["recoverability_classification"]]=counts.get(r["recoverability_classification"],0)+1
    out={
        "status":"SW02_RECOVERED_FIGURE_BLOCK_AUDIT_COMPLETE",
        "source":"Swaters et al. 2002 Appendix-B figures from exact author WHISPI atlas recovered via Wayback",
        "n_targets":len(results),
        "classification_counts":counts,
        "targets":results,
        "promotion_rule":(
            "Only a native-vector candidate may proceed to bottom-left radial-profile panel isolation and axis calibration. "
            "Raster-dominant figures are not digitized under the current exact-public-data freeze."
        ),
        "boundary":(
            "Acquisition/provenance audit only. PostScript is parsed as bytes and never executed. "
            "No raster digitization, profile values, helium factor, distance rescaling, persistence fitting, or blind-outcome inspection."
        )
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"classification_counts":counts},indent=2))
    for r in results:
        print(r["galaxy"],r["appendix_figure_number"],r["block_bytes"],r["image_ops"],r["lineto_ops"],r["curveto_ops"],r["recoverability_classification"])


if __name__=="__main__":
    main()
