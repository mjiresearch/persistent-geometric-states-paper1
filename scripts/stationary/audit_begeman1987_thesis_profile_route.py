#!/usr/bin/env python3
"""Audit the public Begeman 1987 Groningen thesis for exact radial H I profile recovery.

Frozen Lelli branch: Be87 -> Begeman, HI Rotation Curves of Spiral Galaxies.
Targets: NGC2903, NGC5033, NGC5371, NGC6503.

The Groningen Pure record currently labels the deposit year 2006, but the thesis
itself is the 1987 dissertation.  This audit uses the exact full thesis PDF and
asks only whether source-native text/tables or vector geometry can support exact
radial Sigma_HI(R) extraction.  No OCR or scan digitization.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from urllib.request import Request, urlopen
import pymupdf

URL="https://pure.rug.nl/ws/portalfiles/portal/2841681/thesis.pdf"
OUT=Path("validation/stationary/begeman1987_thesis_profile_route_audit_v1.json")
TARGETS={"NGC2903":["NGC 2903","NGC2903"],"NGC5033":["NGC 5033","NGC5033"],"NGC5371":["NGC 5371","NGC5371"],"NGC6503":["NGC 6503","NGC6503"]}

def fetch():
    req=Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0","Accept":"application/pdf,*/*;q=0.5"})
    with urlopen(req,timeout=180) as h:return h.read(),h.geturl(),h.headers.get("Content-Type","")

def compact(s):return re.sub(r"[^A-Z0-9]","",s.upper())

def main():
    raw,final,ct=fetch()
    if raw[:5]!=b"%PDF-": raise RuntimeError("Begeman thesis route did not return PDF")
    doc=pymupdf.open(stream=raw,filetype="pdf")
    pages=[]; target_hits={g:[] for g in TARGETS}; profile_pages=[]
    for i,p in enumerate(doc):
        txt=p.get_text("text") or ""; c=compact(txt)
        drawings=len(p.get_drawings()); images=len(p.get_images(full=True))
        rec={"page_number_1based":i+1,"native_text_chars":len(txt),"n_drawings":drawings,"n_images":images,"text_excerpt":" ".join(txt.split())[:1200]}
        pages.append(rec)
        for g,aa in TARGETS.items():
            if any(compact(a) in c for a in aa):target_hits[g].append(rec)
        low=txt.lower()
        if ("surface density" in low or "column density" in low) and ("h i" in low or "hi" in low or "hydrogen" in low):profile_pages.append(rec)
    result={
      "status":"BEGEMAN1987_THESIS_PROFILE_ROUTE_AUDIT_COMPLETE",
      "source":"K.G. Begeman, HI Rotation Curves of Spiral Galaxies, PhD thesis, Rijksuniversiteit Groningen, defended 4 Dec 1987",
      "public_pdf":URL,"final_url":final,"content_type":ct,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"pages":len(doc),
      "targets":list(TARGETS),"target_native_text_hits":target_hits,"native_hi_profile_text_pages":profile_pages,
      "native_text_characters_total":sum(x["native_text_chars"] for x in pages),
      "pages_with_native_text":sum(x["native_text_chars"]>0 for x in pages),
      "total_drawings":sum(x["n_drawings"] for x in pages),"pages_with_drawings":sum(x["n_drawings"]>0 for x in pages),
      "total_images":sum(x["n_images"] for x in pages),"pages_with_images":sum(x["n_images"]>0 for x in pages),
      "all_pages_zero_drawings":all(x["n_drawings"]==0 for x in pages),
      "page_structure":pages,
      "interpretation_rule":"Exact promotion requires source-native numerical radial values or isolated vector profile geometry. An image-scan thesis page is not OCRed or graph-digitized.",
      "boundary":"Acquisition/provenance only; no OCR, raster digitization, profile inference, normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"page_structure","target_native_text_hits","native_hi_profile_text_pages"}},indent=2))
if __name__=="__main__":main()
