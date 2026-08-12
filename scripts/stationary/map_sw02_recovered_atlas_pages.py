#!/usr/bin/env python3
"""Deterministically map Swaters+2002 sample galaxies to recovered atlas pages.

The arXiv TeX lists the 73-galaxy WHISP sample and Appendix-B figure assets
h3074f13.ps ... h3074f85.ps (73 consecutive galaxy figures). The exact full
WHISPI.ps.gz recovered from Wayback contains 89 rendered `showpage` outputs.
This audit tests the one-to-one ordering hypothesis:

    16 paper pages + 73 galaxy atlas pages = 89 showpages

and maps each frozen Sw02 target by its position in the published sample table,
without executing PostScript and without depending on rasterized galaxy labels.

No profile coordinates are extracted. No raster digitization or persistence
quantities are used.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV = "https://export.arxiv.org/e-print/astro-ph/0204525"
ATLAS = (
    "http://web.archive.org/web/20070824112627id_/"
    "http://www.robswork.net/publications/WHISPI.ps.gz"
)
UA = "PersistenceFrameworkPaperI/1.0"
PRIORITY = Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
SPLIT = Path("validation/stationary/stationary_split_v1.csv")
OUTCSV = Path("data/stationary/source_reconstruction/sw02_recovered_atlas_page_map_v1.csv")
OUTJSON = Path("validation/stationary/sw02_recovered_atlas_page_map_v1_summary.json")


def fetch(url: str, timeout=180) -> bytes:
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urlopen(req, timeout=timeout) as h:
        return h.read()


def compact_name(s: str) -> str:
    s = re.sub(r"\\[A-Za-z]+", "", s)
    s = s.replace("~", " ").replace("{", "").replace("}", "")
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def parse_sample_order(tex: str) -> list[dict]:
    """Parse Table A.1 rows: first field is UGC number, second optional other name."""
    rows = []
    for line_no, line in enumerate(tex.splitlines(), 1):
        if "&" not in line or "\\\\" not in line:
            continue
        fields = [f.strip() for f in line.split("&")]
        if len(fields) < 8:
            continue
        first = re.sub(r"[^0-9]", "", fields[0])
        if not first:
            continue
        ugc = int(first)
        # Table A.1 is the long sample table around lines 1170+; reject unrelated tables
        # by requiring a plausible UGC and the second field to look like an alternate name or blank.
        if ugc <= 0 or ugc > 13000:
            continue
        other = compact_name(fields[1]) if len(fields) > 1 else ""
        # Candidate rows are retained only from the contiguous Table A.1 block.
        if not (1150 <= line_no <= 1260):
            continue
        rows.append({"line": line_no, "ugc": ugc, "other": other, "raw": line.strip()})
    # Deduplicate while preserving order.
    out=[]; seen=set()
    for r in rows:
        if r["ugc"] in seen:
            continue
        seen.add(r["ugc"]); out.append(r)
    return out


def appendix_figure_numbers(tex: str) -> list[int]:
    nums=[]
    for m in re.finditer(r"includegraphics\{h3074f(\d+)\.ps\}", tex, re.I):
        n=int(m.group(1))
        if 13 <= n <= 85 and n not in nums:
            nums.append(n)
    return nums


def split_dsc_pages(ps: bytes) -> list[dict]:
    starts=list(re.finditer(rb"(?m)^%%Page:\s*([^\r\n]*)", ps))
    chunks=[]
    show_ord=0
    for i,m in enumerate(starts):
        lo=m.start(); hi=starts[i+1].start() if i+1<len(starts) else len(ps)
        chunk=ps[lo:hi]
        has_show=bool(re.search(rb"(?<![A-Za-z])showpage(?![A-Za-z])", chunk))
        if has_show:
            show_ord += 1
        chunks.append({
            "dsc_index_0based":i,
            "dsc_header":m.group(1).decode("latin-1","replace"),
            "bytes":len(chunk),
            "has_showpage":has_show,
            "showpage_ordinal":show_ord if has_show else None,
            "image_ops":len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])",chunk)),
            "imagemask_ops":chunk.count(b"imagemask"),
            "lineto_tokens":chunk.count(b"lineto"),
            "moveto_tokens":chunk.count(b"moveto"),
            "show_tokens":chunk.count(b"show"),
        })
    return chunks


def main() -> None:
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:
        pri=list(csv.DictReader(fh))
    target=next((r for r in pri if r["sparc_ref_id"]=="Sw02"),None)
    if target is None or int(target["n_untouched_frozen_galaxies"])!=13:
        raise RuntimeError("Expected Sw02 13-galaxy priority block")
    targets=target["galaxies"].split(";")

    roles={}
    with SPLIT.open(newline="",encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh): roles[r["galaxy"].strip()]=r["stationary_role"].strip()

    ar=fetch(ARXIV,120)
    tf=tarfile.open(fileobj=io.BytesIO(ar),mode="r:*")
    tex=tf.extractfile("h3074.tex").read().decode("latin-1","replace")
    sample=parse_sample_order(tex)
    figs=appendix_figure_numbers(tex)

    raw=fetch(ATLAS,240)
    ps=gzip.decompress(raw)
    dsc=split_dsc_pages(ps)
    rendered=[p for p in dsc if p["has_showpage"]]

    structural_ok=(len(sample)==73 and figs==list(range(13,86)) and len(rendered)==89)
    if not structural_ok:
        raise RuntimeError(
            f"Ordering preconditions failed: sample={len(sample)} figs={len(figs)} "
            f"fig_range={figs[:3]}..{figs[-3:] if figs else []} showpages={len(rendered)}"
        )

    # Exact count identity leaves 16 non-atlas rendered pages before the 73 ordered atlas pages.
    paper_pages=len(rendered)-len(sample)
    if paper_pages != 16:
        raise RuntimeError(f"Expected 16 paper pages from 89-73 identity, got {paper_pages}")

    by_ugc={r["ugc"]:(i,r) for i,r in enumerate(sample)}
    # DDO64 is explicitly UGC5272 in Table A.1.
    target_ugc={"DDO064":5272}
    for g in targets:
        m=re.match(r"UGC0*(\d+)$",g)
        if m: target_ugc[g]=int(m.group(1))

    rows=[]
    for g in targets:
        ugc=target_ugc.get(g)
        hit=by_ugc.get(ugc) if ugc is not None else None
        if hit is None:
            rows.append({
                "galaxy":g,"stationary_role":roles.get(g,""),"ugc":ugc or "",
                "sample_index_0based":"","appendix_figure_number":"","atlas_page_ordinal_1based":"",
                "full_document_showpage_ordinal":"","dsc_index_0based":"","dsc_header":"",
                "page_bytes":"","image_ops":"","imagemask_ops":"","lineto_tokens":"","moveto_tokens":"",
                "mapping_status":"target_not_found_in_sample_order"
            })
            continue
        idx,sr=hit
        fig=13+idx
        full_ord=paper_pages+1+idx
        page=rendered[full_ord-1]
        rows.append({
            "galaxy":g,"stationary_role":roles.get(g,""),"ugc":ugc,
            "sample_index_0based":idx,"appendix_figure_number":fig,"atlas_page_ordinal_1based":idx+1,
            "full_document_showpage_ordinal":full_ord,"dsc_index_0based":page["dsc_index_0based"],
            "dsc_header":page["dsc_header"],"page_bytes":page["bytes"],"image_ops":page["image_ops"],
            "imagemask_ops":page["imagemask_ops"],"lineto_tokens":page["lineto_tokens"],
            "moveto_tokens":page["moveto_tokens"],"mapping_status":"mapped_by_published_sample_and_appendix_order"
        })

    OUTCSV.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0].keys())
    with OUTCSV.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)

    summary={
        "status":"SW02_RECOVERED_ATLAS_PAGE_MAP_BUILT",
        "source":"Swaters et al. 2002 A&A 390 829; full WHISPI atlas recovered from Wayback",
        "n_published_sample_rows":len(sample),
        "appendix_figure_first":figs[0],"appendix_figure_last":figs[-1],"n_appendix_figures":len(figs),
        "n_dsc_chunks":len(dsc),"n_rendered_showpages":len(rendered),"n_paper_showpages_before_atlas":paper_pages,
        "structural_identity":"16 paper showpages + 73 ordered sample galaxies = 89 recovered showpages",
        "n_targets":len(targets),"n_targets_mapped":sum(r["mapping_status"].startswith("mapped") for r in rows),
        "unmapped_targets":[r["galaxy"] for r in rows if not r["mapping_status"].startswith("mapped")],
        "target_page_map":rows,
        "interpretation_boundary":(
            "This establishes deterministic galaxy-to-atlas-page provenance from publication order only. "
            "It does not yet establish that the bottom-left radial H I curve on a mapped page is native vector data. "
            "Profile-panel geometry must be isolated and validated separately before numerical extraction."
        )
    }
    OUTJSON.parent.mkdir(parents=True,exist_ok=True)
    OUTJSON.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__": main()
