#!/usr/bin/env python3
"""Inspect the recovered Swaters 2002 full atlas without executing PostScript.

The author-advertised WHISPI.ps.gz was recovered from Wayback. This parser only
reads DSC page boundaries, literal PostScript strings, and operator frequencies.
It never sends the historical PostScript to an interpreter. The goal is to map
our 13 Sw02 galaxies to atlas pages and determine whether those page payloads
contain meaningful native path geometry in addition to raster image operators.

Acquisition audit only: no raster digitization, no profile-value extraction,
no helium conversion, no distance rescaling, no persistence/blind analysis.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

ATLAS = (
    "http://web.archive.org/web/20070824112627id_/"
    "http://www.robswork.net/publications/WHISPI.ps.gz"
)
UA = "PersistenceFrameworkPaperI/1.0"
PRIORITY = Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
SPLIT = Path("validation/stationary/stationary_split_v1.csv")
OUT = Path("validation/stationary/sw02_recovered_atlas_native_ps_audit_v1.json")

# DDO 64 is UGC 5272 in the Swaters source table.
ALIASES = {"DDO064": ["DDO64", "UGC5272"]}


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urlopen(req, timeout=180) as h:
        return h.read()


def compact(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def variants(g: str) -> set[str]:
    c = compact(g)
    out = {c}
    m = re.match(r"(UGC|DDO)0*(\d+)$", c)
    if m:
        p, n = m.groups(); n = str(int(n))
        out |= {p+n, p+n.zfill(3), p+n.zfill(5)}
    out |= {compact(x) for x in ALIASES.get(g, [])}
    return out


def ps_strings(chunk: bytes) -> list[str]:
    raw = re.findall(rb"\(((?:\\.|[^\\)])*)\)", chunk)
    out = []
    for b in raw:
        s = b.decode("latin-1", "replace")
        s = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), s)
        s = s.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
        out.append(s)
    return out


def split_pages(ps: bytes) -> list[dict]:
    starts = list(re.finditer(rb"(?m)^%%Page:\s*([^\r\n]*)", ps))
    pages = []
    for i, m in enumerate(starts):
        lo = m.start(); hi = starts[i+1].start() if i+1 < len(starts) else len(ps)
        chunk = ps[lo:hi]
        strings = ps_strings(chunk)
        text = compact(" ".join(strings))
        operators = {
            "image": len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])", chunk)),
            "colorimage": chunk.count(b"colorimage"),
            "imagemask": chunk.count(b"imagemask"),
            "moveto": chunk.count(b"moveto"),
            "lineto": chunk.count(b"lineto"),
            "curveto": chunk.count(b"curveto"),
            "stroke": chunk.count(b"stroke"),
            "show": chunk.count(b"show"),
            "setlinewidth": chunk.count(b"setlinewidth"),
        }
        pages.append({
            "index_0based": i,
            "page_number_1based": i+1,
            "dsc_header": m.group(1).decode("latin-1", "replace"),
            "bytes": len(chunk),
            "n_strings": len(strings),
            "strings": strings,
            "text_compact": text,
            "operators": operators,
            "native_path_signal": (operators["lineto"] + operators["curveto"] >= 15),
            "raster_signal": (operators["image"] + operators["colorimage"] + operators["imagemask"] > 0),
        })
    return pages


def main() -> None:
    with PRIORITY.open(newline="", encoding="utf-8-sig") as fh:
        priority = list(csv.DictReader(fh))
    target = next((r for r in priority if r["sparc_ref_id"] == "Sw02"), None)
    if target is None or int(target["n_untouched_frozen_galaxies"]) != 13:
        raise RuntimeError("Expected Sw02 13-galaxy priority block")
    galaxies = target["galaxies"].split(";")

    roles = {}
    with SPLIT.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            roles[r["galaxy"].strip()] = r["stationary_role"].strip()

    raw = fetch(ATLAS)
    ps = gzip.decompress(raw)
    pages = split_pages(ps)

    per = []
    for g in galaxies:
        vv = variants(g)
        hits = []
        for p in pages:
            if any(v and v in p["text_compact"] for v in vv):
                hits.append({
                    "page_number_1based": p["page_number_1based"],
                    "dsc_header": p["dsc_header"],
                    "bytes": p["bytes"],
                    "operators": p["operators"],
                    "native_path_signal": p["native_path_signal"],
                    "raster_signal": p["raster_signal"],
                    "matching_strings": [s for s in p["strings"] if any(v and v in compact(s) for v in vv)][:50],
                    "all_short_strings": [s for s in p["strings"] if 0 < len(s) <= 120][:250],
                })
        per.append({
            "galaxy": g,
            "stationary_role": roles.get(g, ""),
            "search_variants": sorted(vv),
            "n_matching_pages": len(hits),
            "matching_pages": hits,
            "has_native_path_signal": any(h["native_path_signal"] for h in hits),
            "has_raster_signal": any(h["raster_signal"] for h in hits),
        })

    result = {
        "status": "SW02_RECOVERED_ATLAS_NATIVE_PS_AUDIT_COMPLETE",
        "source": "Swaters et al. 2002 WHISP-I full atlas; Wayback capture 2007-08-24",
        "archive_url": ATLAS,
        "gzip_bytes": len(raw),
        "postscript_bytes": len(ps),
        "n_dsc_pages": len(pages),
        "n_priority_galaxies": len(galaxies),
        "priority_role_counts": {"calibration": int(target["n_calibration"]), "blind": int(target["n_blind"])},
        "n_located": sum(r["n_matching_pages"] > 0 for r in per),
        "n_with_native_path_signal": sum(r["has_native_path_signal"] for r in per),
        "n_with_raster_signal": sum(r["has_raster_signal"] for r in per),
        "unlocated": [r["galaxy"] for r in per if not r["n_matching_pages"]],
        "galaxies": per,
        "page_operator_summary": [
            {
                "page": p["page_number_1based"],
                "dsc_header": p["dsc_header"],
                "bytes": p["bytes"],
                "operators": p["operators"],
                "native_path_signal": p["native_path_signal"],
                "raster_signal": p["raster_signal"],
            }
            for p in pages
        ],
        "interpretation_rule": (
            "Native-path signal is a page-level viability flag only; it does not prove the radial H I curve itself is vector. "
            "A second parser must isolate the bottom-left profile-panel path and establish axes before any numerical profile is accepted."
        ),
        "boundary": (
            "PostScript is parsed as bytes/text only and is never executed. No raster digitization, profile-value extraction, "
            "helium factor, frozen-distance conversion, persistence fitting, or blind-outcome inspection."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"galaxies","page_operator_summary"}}, indent=2))
    for r in per:
        print("TARGET", r["galaxy"], [h["page_number_1based"] for h in r["matching_pages"]], "path", r["has_native_path_signal"], "raster", r["has_raster_signal"])


if __name__ == "__main__":
    main()
