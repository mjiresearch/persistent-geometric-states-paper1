#!/usr/bin/env python3
"""Classify the recovered Wevers 1986 ADS PDF as vector/text versus page-image scan.

No OCR, no image interpretation and no numerical extraction. This is only the
final exact-vector viability gate for the Be91 -> Wevers 1986 branch.
"""
from __future__ import annotations
import hashlib,json,urllib.request
from pathlib import Path
import pymupdf

URL="https://articles.adsabs.harvard.edu/pdf/1986A%26AS...66..505W"
OUT=Path("validation/stationary/wevers1986_pdf_geometry_v1.json")
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"

def main():
    req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
    with urllib.request.urlopen(req,timeout=180) as h: raw=h.read()
    if not raw.startswith(b"%PDF-"): raise RuntimeError("Not a PDF")
    doc=pymupdf.open(stream=raw,filetype="pdf")
    rows=[]
    for i,p in enumerate(doc):
        text=p.get_text("text")
        drawings=p.get_drawings(); images=p.get_images(full=True)
        rows.append({
            "page_number_1based":i+1,"native_text_chars":len(text),
            "n_drawings":len(drawings),"drawing_items_total":sum(len(d.get("items",[])) for d in drawings),
            "n_images":len(images),
        })
    out={
        "status":"WEVERS1986_PDF_GEOMETRY_AUDIT_COMPLETE",
        "source":"Wevers, van der Kruit & Allen 1986 A&AS 66 505-662",
        "url":URL,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"pages":len(doc),
        "native_text_chars_total":sum(r["native_text_chars"] for r in rows),
        "pages_with_any_native_text":sum(r["native_text_chars"]>0 for r in rows),
        "pages_with_drawings":sum(r["n_drawings"]>0 for r in rows),
        "pages_with_images":sum(r["n_images"]>0 for r in rows),
        "pages_with_images_and_no_drawings":sum(r["n_images"]>0 and r["n_drawings"]==0 for r in rows),
        "max_drawing_items_on_any_page":max((r["drawing_items_total"] for r in rows),default=0),
        "page_geometry":rows,
        "classification":"page_image_scan_no_native_vector_profile_route" if all(r["n_drawings"]==0 for r in rows) and sum(r["n_images"]>0 for r in rows)>=len(rows)-2 else "mixed_or_vector_content_requires_further_audit",
        "boundary":"Geometry classification only. No OCR, raster digitization, profile extraction, persistence fitting or blind inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in out.items() if k!="page_geometry"},indent=2))

if __name__=="__main__":main()
