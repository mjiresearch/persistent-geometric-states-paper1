#!/usr/bin/env python3
"""Deterministically map Swaters+2002 sample galaxies to recovered atlas pages.

The arXiv TeX contains the 73-galaxy WHISP sample and Appendix-B figure assets
h3074f13.ps ... h3074f85.ps (73 consecutive galaxy figures). The exact full
WHISPI.ps.gz recovered from Wayback is parsed as bytes only.

The strongest mapping route is retained dvips DSC provenance: locate each
embedded Appendix filename inside the monolithic PostScript and assign its byte
offset to the enclosing %%Page chunk. This avoids rendering PostScript and
avoids depending on galaxy labels that may be rasterized.

No profile coordinates are extracted. No raster digitization, model fitting,
helium conversion, distance rescaling, or blind-outcome inspection occurs.
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
    """Parse the 73 data rows of Table A.1 in publication order."""
    rows=[]
    for line_no,line in enumerate(tex.splitlines(),1):
        if not (1150 <= line_no <= 1260) or "&" not in line or "\\\\" not in line:
            continue
        fields=[f.strip() for f in line.split("&")]
        if len(fields)<8:
            continue
        # The earlier diagnostic accidentally admitted table header cells such as (1).
        # A genuine Table-A.1 galaxy row starts with a bare 3-5 digit UGC number.
        first=fields[0].strip()
        if not re.fullmatch(r"\d{3,5}", first):
            continue
        ugc=int(first)
        other=compact_name(fields[1]) if len(fields)>1 else ""
        rows.append({"line":line_no,"ugc":ugc,"other":other,"raw":line.strip()})
    out=[]; seen=set()
    for r in rows:
        if r["ugc"] in seen:
            continue
        seen.add(r["ugc"]); out.append(r)
    return out


def appendix_figure_numbers(tex: str) -> list[int]:
    nums=[]
    for m in re.finditer(r"includegraphics\{h3074f(\d+)\.ps\}",tex,re.I):
        n=int(m.group(1))
        if 13<=n<=85 and n not in nums:
            nums.append(n)
    return nums


def split_dsc_pages(ps: bytes) -> list[dict]:
    starts=list(re.finditer(rb"(?m)^%%Page:\s*([^\r\n]*)",ps))
    chunks=[]
    for i,m in enumerate(starts):
        lo=m.start(); hi=starts[i+1].start() if i+1<len(starts) else len(ps)
        chunk=ps[lo:hi]
        chunks.append({
            "dsc_index_0based":i,
            "dsc_header":m.group(1).decode("latin-1","replace"),
            "start_offset":lo,"end_offset":hi,"bytes":len(chunk),
            "showpage_tokens":len(re.findall(rb"(?<![A-Za-z])showpage(?![A-Za-z])",chunk)),
            "image_ops":len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])",chunk)),
            "colorimage_ops":chunk.count(b"colorimage"),
            "imagemask_ops":chunk.count(b"imagemask"),
            "lineto_tokens":chunk.count(b"lineto"),
            "moveto_tokens":chunk.count(b"moveto"),
            "show_tokens":chunk.count(b"show"),
        })
    return chunks


def containing_page(dsc: list[dict], offset: int):
    for p in dsc:
        if p["start_offset"] <= offset < p["end_offset"]:
            return p
    return None


def locate_embedded_figures(ps: bytes,dsc: list[dict],figs: list[int]) -> dict[int,dict]:
    out={}
    for n in figs:
        variants=[f"h3074f{n}.ps".encode(),f"h3074f{n}".encode()]
        offsets=[]
        for needle in variants:
            pos=0
            while True:
                j=ps.find(needle,pos)
                if j<0: break
                offsets.append(j); pos=j+1
            if offsets: break
        offsets=sorted(set(offsets))
        pages=[]
        for off in offsets:
            p=containing_page(dsc,off)
            pages.append(None if p is None else p["dsc_index_0based"])
        out[n]={"offsets":offsets,"dsc_indices":pages}
    return out


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
    loc=locate_embedded_figures(ps,dsc,figs)

    if len(sample)!=73 or figs!=list(range(13,86)):
        raise RuntimeError(
            f"Publication-order preconditions failed: sample={len(sample)} figs={len(figs)} "
            f"range={figs[:3]}..{figs[-3:] if figs else []}"
        )

    by_ugc={r["ugc"]:(i,r) for i,r in enumerate(sample)}
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
                "sample_index_0based":"","appendix_figure_number":"","figure_byte_offset":"",
                "dsc_index_0based":"","dsc_header":"","page_bytes":"","image_ops":"",
                "colorimage_ops":"","imagemask_ops":"","lineto_tokens":"","moveto_tokens":"",
                "mapping_status":"target_not_found_in_published_sample_order"
            }); continue
        idx,sr=hit; fig=13+idx; fl=loc[fig]
        valid=[(off,di) for off,di in zip(fl["offsets"],fl["dsc_indices"]) if di is not None]
        # Prefer an occurrence inside a DSC page. Repeated filename mentions are retained in summary diagnostics.
        if valid:
            off,di=valid[-1]
            p=dsc[di]
            status="mapped_by_table_order_and_embedded_figure_filename"
            rows.append({
                "galaxy":g,"stationary_role":roles.get(g,""),"ugc":ugc,
                "sample_index_0based":idx,"appendix_figure_number":fig,"figure_byte_offset":off,
                "dsc_index_0based":di,"dsc_header":p["dsc_header"],"page_bytes":p["bytes"],
                "image_ops":p["image_ops"],"colorimage_ops":p["colorimage_ops"],
                "imagemask_ops":p["imagemask_ops"],"lineto_tokens":p["lineto_tokens"],
                "moveto_tokens":p["moveto_tokens"],"mapping_status":status
            })
        else:
            rows.append({
                "galaxy":g,"stationary_role":roles.get(g,""),"ugc":ugc,
                "sample_index_0based":idx,"appendix_figure_number":fig,"figure_byte_offset":"",
                "dsc_index_0based":"","dsc_header":"","page_bytes":"","image_ops":"",
                "colorimage_ops":"","imagemask_ops":"","lineto_tokens":"","moveto_tokens":"",
                "mapping_status":"figure_order_known_but_embedded_filename_not_retained"
            })

    OUTCSV.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0].keys())
    with OUTCSV.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)

    n_figs_named=sum(bool(v["offsets"]) for v in loc.values())
    summary={
        "status":"SW02_RECOVERED_ATLAS_PAGE_MAP_AUDIT_COMPLETE",
        "source":"Swaters et al. 2002 A&A 390 829; full WHISPI atlas recovered from Wayback",
        "n_published_sample_rows":len(sample),
        "appendix_figure_first":figs[0],"appendix_figure_last":figs[-1],"n_appendix_figures":len(figs),
        "n_dsc_chunks":len(dsc),"raw_showpage_token_count":len(re.findall(rb"(?<![A-Za-z])showpage(?![A-Za-z])",ps)),
        "n_appendix_filenames_retained_in_monolithic_ps":n_figs_named,
        "n_targets":len(targets),
        "n_targets_mapped_to_dsc_page":sum(r["mapping_status"]=="mapped_by_table_order_and_embedded_figure_filename" for r in rows),
        "target_page_map":rows,
        "figure_locator_diagnostics":{str(k):v for k,v in loc.items()},
        "interpretation_boundary":(
            "Sample order fixes galaxy-to-Appendix-figure identity. A retained embedded filename additionally fixes the exact monolithic-PS DSC page. "
            "Neither establishes that the radial H I curve itself is native vector geometry; panel-level isolation and axis QC remain required before numerical extraction."
        ),
        "boundary":"PostScript parsed as inert bytes only; no rendering, raster digitization, persistence fitting, or blind-outcome inspection."
    }
    OUTJSON.parent.mkdir(parents=True,exist_ok=True)
    OUTJSON.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="figure_locator_diagnostics"},indent=2))


if __name__=="__main__": main()
