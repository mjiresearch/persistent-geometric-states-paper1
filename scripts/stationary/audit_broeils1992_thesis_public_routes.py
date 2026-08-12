#!/usr/bin/env python3
"""Audit Broeils (1992) thesis public routes for six Br92 frozen galaxies.

Lelli/SPARC ref Br92 is the current highest-yield actionable family: six frozen
galaxies. The University of Groningen Pure record advertises the 255-page thesis
PDF, but the current file endpoint may reject automated retrieval. This script
tries a bounded set of exact institutional URLs and Internet Archive snapshots.

If a PDF is recovered, it is opened as a document (not OCRed) and audited for
native text, target-galaxy mentions, radial H I/surface-density language, vector
drawings and embedded images. No raster digitization, profile-value extraction,
persistence fitting, or blind-outcome inspection occurs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pymupdf

UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
PUBLICATION="https://research.rug.nl/en/publications/dark-and-visible-matter-in-spiral-galaxies/"
URLS=[
    "https://research.rug.nl/files/3332246/broeils.PDF",
    "https://pure.rug.nl/ws/portalfiles/portal/3332246/broeils.PDF",
    "http://irs.ub.rug.nl/ppn/123456789/broeils.PDF",
]
PRIORITY=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT=Path("validation/stationary/broeils1992_thesis_public_route_audit_v1.json")


def fetch(url,timeout=120):
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/pdf,application/json,text/html,*/*;q=0.8"})
    with urlopen(req,timeout=timeout) as h:
        return h.read(),h.geturl(),h.headers.get("Content-Type","")


def compact(s):
    return re.sub(r"[^A-Z0-9]","",s.upper())


def variants(g):
    c=compact(g); out={c}
    m=re.match(r"(NGC|UGC)0*(\d+)$",c)
    if m:
        p,n=m.groups(); n=str(int(n)); out|={p+n,p+" "+n}
    return {compact(x) for x in out}


def classify_pdf(raw,targets):
    doc=pymupdf.open(stream=raw,filetype="pdf")
    page_text=[p.get_text("text") for p in doc]
    compact_text=[compact(t) for t in page_text]
    per=[]
    for g in targets:
        vv=variants(g); hits=[]
        for i,t in enumerate(compact_text):
            if any(v and v in t for v in vv):
                p=doc[i]; txt=page_text[i]; low=txt.lower()
                hits.append({
                    "page_number_1based":i+1,
                    "surface_density_text":("surface density" in low),
                    "hi_text":bool(re.search(r"\bh\s*i\b|hydrogen",low,re.I)),
                    "radial_profile_text":bool(re.search(r"radial.*profile|profile.*radial",low,re.I|re.S)),
                    "n_drawings":len(p.get_drawings()),
                    "n_images":len(p.get_images(full=True)),
                    "text_excerpt":" ".join(txt.split())[:2500],
                })
        per.append({"galaxy":g,"n_matching_pages":len(hits),"pages":hits})
    surface_pages=[]
    for i,t in enumerate(page_text):
        low=t.lower()
        if "surface density" in low and re.search(r"\bh\s*i\b|hydrogen",low,re.I):
            surface_pages.append({"page_number_1based":i+1,"text_excerpt":" ".join(t.split())[:1800]})
    return {
        "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"pages":len(doc),
        "native_text_characters":sum(len(t) for t in page_text),
        "n_total_drawings":sum(len(p.get_drawings()) for p in doc),
        "n_total_images":sum(len(p.get_images(full=True)) for p in doc),
        "n_targets_found":sum(x["n_matching_pages"]>0 for x in per),
        "targets":per,
        "n_hi_surface_density_text_pages":len(surface_pages),
        "hi_surface_density_text_pages":surface_pages[:100],
    }


def wayback_candidates(original):
    out=[]; diag={"original":original}
    api="https://archive.org/wayback/available?url="+quote(original,safe="")
    try:
        raw,_,_=fetch(api,45); data=json.loads(raw.decode("utf-8","replace")); diag["availability"]=data
        c=data.get("archived_snapshots",{}).get("closest") or {}
        if c.get("available") and c.get("url"):
            u=c["url"]
            m=re.search(r"/web/(\d+)/(.*)$",u)
            if m: u=f"https://web.archive.org/web/{m.group(1)}id_/{m.group(2)}"
            out.append(u)
    except Exception as exc:
        diag["availability_error"]=f"{type(exc).__name__}: {exc}"
    return out,diag


def main():
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:rows=list(csv.DictReader(fh))
    target=next((r for r in rows if r["sparc_ref_id"]=="Br92"),None)
    if target is None or int(target["n_untouched_frozen_galaxies"])!=6:
        raise RuntimeError("Expected Br92 six-galaxy actionable block")
    galaxies=target["galaxies"].split(";")

    attempts=[]; archived=[]; recovered=None
    for u in URLS:
        rec={"route":"live","url":u}
        try:
            raw,final,ct=fetch(u,45); rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            if raw[:5]==b"%PDF-":
                rec["pdf_audit"]=classify_pdf(raw,galaxies); recovered=rec; attempts.append(rec); break
        except Exception as exc:rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)
        cands,diag=wayback_candidates(u); archived.append(diag)
        for snap in cands:
            srec={"route":"wayback","original_url":u,"url":snap}
            try:
                raw,final,ct=fetch(snap,120); srec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
                if raw[:5]==b"%PDF-":
                    srec["pdf_audit"]=classify_pdf(raw,galaxies); recovered=srec; attempts.append(srec); break
            except Exception as exc:srec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
            attempts.append(srec)
        if recovered:break

    pa=None if recovered is None else recovered.get("pdf_audit")
    result={
        "status":"BROEILS1992_THESIS_PUBLIC_ROUTE_AUDIT_COMPLETE",
        "source":"A.H. Broeils 1992 PhD thesis, Dark and visible matter in spiral galaxies, University of Groningen",
        "publication_page":PUBLICATION,
        "n_priority_frozen_galaxies":len(galaxies),
        "priority_role_counts":{"calibration":int(target["n_calibration"]),"blind":int(target["n_blind"])},
        "priority_galaxies":galaxies,
        "attempts":attempts,"wayback_diagnostics":archived,
        "pdf_recovered":recovered is not None,
        "recovered_route":None if recovered is None else recovered["route"],
        "recovered_url":None if recovered is None else recovered.get("final_url",recovered.get("url")),
        "pdf_audit":pa,
        "route_has_target_native_text":bool(pa and pa["n_targets_found"]>0),
        "route_has_hi_surface_density_native_text":bool(pa and pa["n_hi_surface_density_text_pages"]>0),
        "interpretation_rule":"A recovered thesis PDF establishes a public provenance route. Native text/drawing presence is only an acquisition signal; no plotted profile is promoted without direct numerical/vector or analytic recovery and QC.",
        "boundary":"No OCR, raster digitization, profile-value extraction, helium conversion, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"attempts","wayback_diagnostics","pdf_audit"}},indent=2))
    if pa:print(json.dumps({k:v for k,v in pa.items() if k not in {"targets","hi_surface_density_text_pages"}},indent=2))

if __name__=="__main__":main()
