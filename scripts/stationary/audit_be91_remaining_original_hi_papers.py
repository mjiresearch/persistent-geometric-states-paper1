#!/usr/bin/env python3
"""Audit the three non-Wevers original H I papers reached through Be91.

Be91 canonical source map v2:
- DDO170 -> Lake, Schommer & van Gorkom 1990, AJ 99, 547
- NGC3109 -> Jobin & Carignan 1990, AJ 100, 648
- UGC02259 -> Carignan, Sancisi & van Albada 1988, AJ 95, 37

Public ADS PDFs are inspected transiently for native tables/text/vector geometry.
No OCR, no raster digitization, no profile normalization, no persistence fitting.
"""
from __future__ import annotations
import hashlib,json,re,urllib.parse,urllib.request
from pathlib import Path
import pymupdf

UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
PAPERS=[
 {"galaxy":"DDO170","bibcode":"1990AJ.....99..547L","source":"Lake, Schommer & van Gorkom 1990","title":"The distribution of dark matter in the dwarf galaxy DDO 170"},
 {"galaxy":"NGC3109","bibcode":"1990AJ....100..648J","source":"Jobin & Carignan 1990","title":"The dark side of NGC 3109"},
 {"galaxy":"UGC02259","bibcode":"1988AJ.....95...37C","source":"Carignan, Sancisi & van Albada 1988","title":"H I and Mass Distribution in the Dwarf Regular Galaxy UGC 2259"},
]
OUT=Path("validation/stationary/be91_remaining_original_hi_papers_audit_v1.json")

TERMS=[
 r"surface\s+density",r"surface-density",r"radial\s+distribution",r"radial\s+profile",
 r"H\s*I\s+distribution",r"HI\s+distribution",r"column\s+density",r"gas\s+distribution",
 r"mass\s+surface",r"density\s+profile",r"azimuthal",r"annuli",r"ring",
]

def fetch_pdf(bibcode):
    enc=urllib.parse.quote(bibcode,safe=".")
    urls=[f"https://articles.adsabs.harvard.edu/pdf/{enc}",f"https://articles.adsabs.harvard.edu/pdf/{bibcode}",f"https://adsabs.harvard.edu/pdf/{enc}"]
    attempts=[]
    for u in urls:
        rec={"url":u}
        try:
            req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
            with urllib.request.urlopen(req,timeout=180) as h:
                raw=h.read(); final=h.geturl(); ct=h.headers.get("Content-Type","")
            rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            if raw.startswith(b"%PDF-") and len(raw)>100000:
                rec["sha256"]=hashlib.sha256(raw).hexdigest();attempts.append(rec);return raw,final,attempts
        except Exception as exc:rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)
    return None,None,attempts

def variants(g):
    if g=="DDO170":return ["DDO 170","DDO170"]
    if g=="NGC3109":return ["NGC 3109","NGC3109"]
    return ["UGC 2259","UGC2259","UGC 02259","UGC02259"]

def contexts(text,patterns,radius=6):
    lines=text.splitlines();out=[]
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in patterns):
            lo=max(0,i-radius);hi=min(len(lines),i+radius+1)
            out.append({"line":i+1,"context":"\n".join(lines[lo:hi])[:5000]})
    return out[:100]

def inspect(raw,galaxy):
    doc=pymupdf.open(stream=raw,filetype="pdf"); vv=variants(galaxy); pages=[]
    for i,p in enumerate(doc):
        text=p.get_text("text"); drawings=p.get_drawings(); images=p.get_images(full=True)
        pages.append({"i":i,"text":text,"n_drawings":len(drawings),"drawing_items_total":sum(len(d.get("items",[])) for d in drawings),"n_images":len(images)})
    hits=[]; profile_pages=[]; table_candidates=[]
    for r in pages:
        t=r["text"]
        named=any(v.lower() in t.lower() for v in vv)
        terms=[pat for pat in TERMS if re.search(pat,t,re.I)]
        if named:
            hits.append({"page_number_1based":r["i"]+1,"name_contexts":contexts(t,[re.escape(v) for v in vv],5),"profile_contexts":contexts(t,TERMS,6),"excerpt":" ".join(t.split())[:6000],"n_drawings":r["n_drawings"],"drawing_items_total":r["drawing_items_total"],"n_images":r["n_images"]})
        if terms:
            profile_pages.append({"page_number_1based":r["i"]+1,"matched_patterns":terms,"excerpt":" ".join(t.split())[:4000],"n_drawings":r["n_drawings"],"drawing_items_total":r["drawing_items_total"],"n_images":r["n_images"]})
        if named and terms:
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?",t)
            table_candidates.append({"page_number_1based":r["i"]+1,"n_numeric_tokens":len(nums),"first_numeric_tokens":nums[:180],"excerpt":" ".join(t.split())[:6500]})
    geom={
      "pages":len(doc),"native_text_chars_total":sum(len(r["text"]) for r in pages),
      "pages_with_native_text":sum(bool(r["text"].strip()) for r in pages),
      "pages_with_drawings":sum(r["n_drawings"]>0 for r in pages),
      "pages_with_images":sum(r["n_images"]>0 for r in pages),
      "pages_with_images_no_drawings":sum(r["n_images"]>0 and r["n_drawings"]==0 for r in pages),
      "max_drawing_items":max((r["drawing_items_total"] for r in pages),default=0),
    }
    if table_candidates:
        cls="native_text_profile_candidate_requires_manual_table_qc"
    elif geom["pages_with_drawings"]>0 and geom["max_drawing_items"]>=100:
        cls="possible_vector_geometry_requires_profile_panel_isolation"
    elif geom["pages_with_images_no_drawings"]>=max(1,len(doc)-1):
        cls="page_image_scan_no_exact_vector_or_native_table_route"
    else:
        cls="no_exact_numeric_route_identified_in_public_pdf"
    return {"geometry":geom,"target_pages":hits,"global_profile_language_pages":profile_pages,"target_native_numeric_candidates":table_candidates,"classification":cls}

def main():
    results=[]
    for p in PAPERS:
        raw,final,attempts=fetch_pdf(p["bibcode"])
        audit=inspect(raw,p["galaxy"]) if raw else None
        results.append({**p,"transport_attempts":attempts,"pdf_recovered":raw is not None,"recovered_url":final,"pdf_sha256":None if raw is None else hashlib.sha256(raw).hexdigest(),"audit":audit})
    out={
      "status":"BE91_REMAINING_ORIGINAL_HI_PAPERS_AUDIT_COMPLETE","papers":results,
      "promotion_rule":"Promote only native machine-readable/tabular values or unambiguous vector profile geometry. Raster plots are not digitized.",
      "boundary":"Acquisition/provenance only; no OCR, raster digitization, helium/distance normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"papers":[{"galaxy":r["galaxy"],"recovered":r["pdf_recovered"],"classification":None if not r["audit"] else r["audit"]["classification"],"pages":None if not r["audit"] else r["audit"]["geometry"]["pages"],"native_candidates":0 if not r["audit"] else len(r["audit"]["target_native_numeric_candidates"])} for r in results]},indent=2))

if __name__=="__main__":main()
