#!/usr/bin/env python3
"""Audit the public van der Hulst et al. 1993 (VH93) PDF for exact radial H I profile recovery.

The publication explicitly places the radial H I surface-density distributions in
Figure 2. This audit determines whether the public University of Maryland PDF
preserves that figure as native vector geometry or only as scanned/raster content.
No OCR, raster digitization, normalization, fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from urllib.request import Request, urlopen
import pymupdf

URL="https://drum.lib.umd.edu/bitstreams/d1a54927-5c0d-4398-adcb-e7c8be1323ad/download"
OUT=Path("validation/stationary/vh93_public_profile_route_audit_v1.json")
TARGETS={"UGC00128":"UGC 128","UGC05005":"UGC 5005","UGC05750":"UGC 5750","UGC06614":"UGC 6614"}

def fetch():
    req=Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0","Accept":"application/pdf,*/*;q=0.5"})
    with urlopen(req,timeout=120) as h:return h.read(),h.geturl(),h.headers.get("Content-Type","")

def main():
    raw,final,ct=fetch()
    if raw[:5] != b"%PDF-": raise RuntimeError("VH93 public route did not return a PDF")
    doc=pymupdf.open(stream=raw,filetype="pdf")
    pages=[]; fig2=[]; target_pages={g:[] for g in TARGETS}
    for i,p in enumerate(doc):
        txt=p.get_text("text")
        rec={
          "page_number_1based":i+1,
          "native_text_chars":len(txt),
          "n_drawings":len(p.get_drawings()),
          "n_images":len(p.get_images(full=True)),
          "has_figure2_text":bool(re.search(r"FIG\.?\s*2|Fig\.?\s*2",txt)),
          "has_hi_surface_density_text":bool(re.search(r"H\s*I.*surface\s+density|surface\s+density.*H\s*I",txt,re.I|re.S)),
        }
        pages.append(rec)
        if rec["has_figure2_text"]: fig2.append(rec)
        compact=re.sub(r"[^A-Z0-9]","",txt.upper())
        for g,label in TARGETS.items():
            if re.sub(r"[^A-Z0-9]","",label.upper()) in compact:
                target_pages[g].append(i+1)
    result={
      "status":"VH93_PUBLIC_PROFILE_ROUTE_AUDIT_COMPLETE",
      "source":"van der Hulst et al. 1993 AJ 106 548-559",
      "bibcode":"1993AJ....106..548V",
      "public_pdf_url":URL,"final_url":final,"content_type":ct,
      "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"pages":len(doc),
      "target_galaxies":list(TARGETS),"target_pages":target_pages,
      "page_structure":pages,"figure2_candidate_pages":fig2,
      "total_drawings":sum(x["n_drawings"] for x in pages),
      "total_images":sum(x["n_images"] for x in pages),
      "all_pages_zero_drawings":all(x["n_drawings"]==0 for x in pages),
      "interpretation_rule":"VH93 explicitly publishes radial H I surface-density profiles in Figure 2. Promotion requires native numerical values or exact vector geometry; a scanned/raster figure is not digitized.",
      "boundary":"Acquisition/provenance only; no OCR, raster digitization, helium scaling, persistence fitting, or blind outcomes."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"page_structure","target_pages"}},indent=2))
if __name__=="__main__":main()
