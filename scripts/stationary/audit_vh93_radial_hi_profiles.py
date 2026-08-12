#!/usr/bin/env python3
"""Audit van der Hulst et al. (1993) for public exact radial H I profiles.

Lelli/SPARC -> VH93 is a direct VLA H I observing source.  dB01 additionally
redirects UGC5750 and UGC6614 here; dB02 may redirect UGC5005 here.  The public
University of Maryland author/institutional copy is checked first, ADS second.

The gate is strict: native radius-vs-Sigma_HI table or unambiguous vector profile
geometry only.  Aggregate properties such as peak radial average are retained as
provenance/QC but are not promoted as radial profiles. No OCR or raster digitizing.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path

import fitz

URLS=[
    "https://drum.lib.umd.edu/bitstreams/d1a54927-5c0d-4398-adcb-e7c8be1323ad/download",
    "https://articles.adsabs.harvard.edu/pdf/1993AJ....106..548V",
]
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
TARGETS=["UGC00128","UGC05005","UGC05750","UGC06614"]
OUT=Path("validation/stationary/vh93_radial_hi_profile_audit_v1.json")


def fetch():
    attempts=[]
    for u in URLS:
        rec={"url":u}
        try:
            req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
            with urllib.request.urlopen(req,timeout=180) as h:
                raw=h.read(); final=h.geturl(); ct=h.headers.get("Content-Type","")
            rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            if raw.startswith(b"%PDF-") and len(raw)>100000:
                rec["sha256"]=hashlib.sha256(raw).hexdigest(); attempts.append(rec); return raw,attempts
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)
    raise RuntimeError("No VH93 public PDF recovered: "+repr(attempts))


def names(g):
    n=str(int(re.sub(r"\D","",g)))
    return [f"UGC {n}",f"UGC {n.zfill(4)}",f"UGC{n}",f"UGC{n.zfill(4)}"]


def contexts(text,patterns,radius=5):
    lines=text.splitlines(); out=[]
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in patterns):
            lo=max(0,i-radius); hi=min(len(lines),i+radius+1)
            out.append({"line":i+1,"context":"\n".join(lines[lo:hi])[:6000]})
    return out[:100]


def main():
    raw,attempts=fetch(); doc=fitz.open(stream=raw,filetype="pdf")
    pages=[]
    for i,p in enumerate(doc):
        text=p.get_text("text"); drawings=p.get_drawings(); images=p.get_images(full=True)
        pages.append({
            "i":i,"text":text,"native_text_chars":len(text),"n_drawings":len(drawings),
            "drawing_items_total":sum(len(d.get("items",[])) for d in drawings),"n_images":len(images),
        })
    profile_patterns=[
        r"radial.*surface dens",r"surface densit",r"radially averaged",r"radial average",
        r"H\s*I.*density",r"density.*H\s*I",r"critical density",r"M.?pc.{0,3}-?2",
    ]
    per=[]
    for g in TARGETS:
        vv=names(g); hits=[]
        for r in pages:
            text=r["text"]
            if any(v.lower() in text.lower() for v in vv):
                hits.append({
                    "page_number_1based":r["i"]+1,
                    "name_variants":[v for v in vv if v.lower() in text.lower()],
                    "profile_contexts":contexts(text,profile_patterns,7),
                    "excerpt":" ".join(text.split())[:7000],
                    "n_drawings":r["n_drawings"],"drawing_items_total":r["drawing_items_total"],"n_images":r["n_images"],
                })
        per.append({"galaxy":g,"pages":hits})

    # Table 2 is useful QC but only aggregate properties, not Sigma_HI(r).
    table2=[]
    for r in pages:
        text=r["text"]
        if re.search(r"Table\s*2|Physical properties",text,re.I):
            table2.append({"page_number_1based":r["i"]+1,"excerpt":" ".join(text.split())[:9000]})

    profile_pages=[]
    for r in pages:
        pats=[p for p in profile_patterns if re.search(p,r["text"],re.I)]
        if pats:
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",r["text"])
            profile_pages.append({
                "page_number_1based":r["i"]+1,"matched_patterns":pats,"n_numeric_tokens":len(nums),
                "excerpt":" ".join(r["text"].split())[:7000],"n_drawings":r["n_drawings"],
                "drawing_items_total":r["drawing_items_total"],"n_images":r["n_images"],
            })

    geom={
        "pages":len(doc),"native_text_chars_total":sum(r["native_text_chars"] for r in pages),
        "pages_with_native_text":sum(r["native_text_chars"]>0 for r in pages),
        "pages_with_drawings":sum(r["n_drawings"]>0 for r in pages),
        "pages_with_images":sum(r["n_images"]>0 for r in pages),
        "pages_with_images_no_drawings":sum(r["n_images"]>0 and r["n_drawings"]==0 for r in pages),
        "max_drawing_items":max((r["drawing_items_total"] for r in pages),default=0),
    }
    native_table_candidate=False
    # A radial profile table would require native text with repeated radius/density rows;
    # Table 2 explicitly contains one aggregate 'Peak radial average' per galaxy only.
    for r in profile_pages:
        if r["n_numeric_tokens"]>=40 and "peak radial average" not in r["excerpt"].lower() and r["n_drawings"]==0 and r["n_images"]==0:
            native_table_candidate=True

    if geom["pages_with_drawings"]==0 and geom["pages_with_images"]>=len(doc)-1 and not native_table_candidate:
        classification="public_copy_page_image_scan_no_exact_vector_or_radial_table_route"
    elif native_table_candidate:
        classification="native_numeric_candidate_requires_row_level_qc"
    else:
        classification="mixed_content_requires_further_profile_isolation"

    out={
        "status":"VH93_RADIAL_HI_PROFILE_AUDIT_COMPLETE",
        "source":"van der Hulst et al. 1993 AJ 106 548-559",
        "bibcode":"1993AJ....106..548V",
        "title":"Star Formation Thresholds in Low Surface Brightness Galaxies",
        "transport_attempts":attempts,"pdf_bytes":len(raw),"pdf_sha256":hashlib.sha256(raw).hexdigest(),
        "targets":per,"table2_aggregate_property_contexts":table2,
        "profile_language_pages":profile_pages,"geometry":geom,"classification":classification,
        "table2_boundary":"Table 2 reports global/aggregate quantities including peak H I surface density and one peak radial average per galaxy; these are not radius-versus-Sigma_HI profiles and are not promoted.",
        "promotion_rule":"Only native radius-versus-Sigma_HI rows or unambiguous vector profile geometry may enter the source-profile overlay. Raster figures are not digitized.",
        "boundary":"Acquisition/provenance only; no OCR, raster digitization, helium/distance normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"classification":classification,"geometry":geom,"targets_found":{x["galaxy"]:[p["page_number_1based"] for p in x["pages"]] for x in per}},indent=2))

if __name__=="__main__": main()
