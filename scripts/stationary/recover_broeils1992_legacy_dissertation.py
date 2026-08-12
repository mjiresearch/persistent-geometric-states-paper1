#!/usr/bin/env python3
"""Recover the full Broeils 1992 thesis from Groningen's legacy dissertation archive.

The current Pure attachment named broeils.PDF is only a three-page object despite
the catalogue record describing a 255-page thesis. Groningen historically served
science theses under predictable paths such as:
  dissertations.ub.rug.nl/faculties/science/<year>/<initials.surname>/
This bounded audit probes the Broeils path and Internet Archive CDX snapshots.

Recovered PDFs are inspected transiently and are not committed. No OCR, raster
profile digitization, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pymupdf

UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
TARGETS=["NGC0801","NGC1003","NGC2683","NGC2998","NGC5985","NGC6674"]
BASES=[
 "http://dissertations.ub.rug.nl/faculties/science/1992/a.h.broeils/",
 "https://dissertations.ub.rug.nl/faculties/science/1992/a.h.broeils/",
 "http://dissertations.ub.rug.nl/nl/FILES/faculties/science/1992/a.h.broeils/",
 "https://dissertations.ub.rug.nl/nl/FILES/faculties/science/1992/a.h.broeils/",
]
OUT=Path("validation/stationary/broeils1992_legacy_dissertation_recovery_v1.json")


def fetch(url,timeout=90):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as h:
        return h.read(),h.geturl(),h.headers.get("Content-Type","")


def cdx(base):
    # Query both exact directory and wildcard descendants.
    q=("https://web.archive.org/cdx/search/cdx?url="+
       urllib.parse.quote(base+"*",safe="")+
       "&output=json&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype,statuscode,digest,length")
    try:
        raw,final,ct=fetch(q,60)
        data=json.loads(raw.decode("utf-8","replace"))
        if not isinstance(data,list) or not data:return {"query":q,"rows":[]}
        head=data[0]; rows=[dict(zip(head,r)) for r in data[1:]]
        return {"query":q,"rows":rows}
    except Exception as exc:
        return {"query":q,"error":f"{type(exc).__name__}: {exc}","rows":[]}


def compact(s):return re.sub(r"[^A-Z0-9]","",s.upper())


def pdf_audit(raw):
    doc=pymupdf.open(stream=raw,filetype="pdf")
    page_text=[p.get_text("text") for p in doc]
    per=[]
    for g in TARGETS:
        c=compact(g); m=re.match(r"NGC0*(\d+)",c); n=str(int(m.group(1))) if m else ""
        vv={compact(g),"NGC"+n}
        hits=[]
        for i,t in enumerate(page_text):
            ct=compact(t)
            if any(v in ct for v in vv if v):
                p=doc[i]; low=t.lower()
                hits.append({
                    "page_number_1based":i+1,
                    "n_drawings":len(p.get_drawings()),"n_images":len(p.get_images(full=True)),
                    "surface_density":("surface density" in low),
                    "hi_or_hydrogen":bool(re.search(r"\bh\s*i\b|neutral hydrogen|hydrogen",low,re.I)),
                    "excerpt":" ".join(t.split())[:3000],
                })
        per.append({"galaxy":g,"pages":hits})
    terms=[]
    for i,t in enumerate(page_text):
        low=t.lower()
        if ("surface density" in low or "strip integral" in low or "radial distribution" in low) and re.search(r"h\s*i|hydrogen",low,re.I):
            terms.append({"page_number_1based":i+1,"excerpt":" ".join(t.split())[:2500]})
    return {
        "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"pages":len(doc),
        "native_text_characters":sum(map(len,page_text)),
        "n_drawings":sum(len(p.get_drawings()) for p in doc),
        "n_images":sum(len(p.get_images(full=True)) for p in doc),
        "n_targets_found":sum(bool(x["pages"]) for x in per),"targets":per,
        "n_hi_profile_language_pages":len(terms),"hi_profile_language_pages":terms[:100],
    }


def html_links(raw,base):
    text=raw.decode("latin-1","replace")
    hrefs=re.findall(r'''href\s*=\s*["']([^"']+)["']''',text,re.I)
    return [urllib.parse.urljoin(base,h) for h in hrefs if re.search(r"\.pdf(?:$|[?#])",h,re.I)]


def main():
    live=[]; indexes=[]; candidates=[]
    for b in BASES:
        rec={"url":b}
        try:
            raw,final,ct=fetch(b,30); rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw)})
            links=html_links(raw,final); rec["pdf_links"]=links; candidates.extend(("live_index",u,None) for u in links)
        except Exception as exc:rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        live.append(rec)
        di=cdx(b); indexes.append({"base":b,**di})
        for r in di.get("rows",[]):
            orig=r.get("original",""); mime=r.get("mimetype","")
            if re.search(r"\.pdf(?:$|[?#])",orig,re.I) or "pdf" in mime.lower():
                ts=r.get("timestamp","")
                if ts and orig:
                    candidates.append(("wayback_cdx",f"https://web.archive.org/web/{ts}id_/{orig}",r))

    # Additional filename guesses, but only beneath the historical author path.
    for b in BASES[:2]:
        for f in ["thesis.pdf","broeils.pdf","broeils.PDF","dissertation.pdf","title.pdf","contents.pdf"]:
            candidates.append(("legacy_filename_guess",urllib.parse.urljoin(b,f),None))

    # Deduplicate and audit any real PDF. Prefer a document substantially larger than the 3-page Pure wrapper.
    attempts=[]; recovered=[]; seen=set()
    for route,u,meta in candidates:
        if u in seen:continue
        seen.add(u)
        rec={"route":route,"url":u,"cdx":meta}
        try:
            raw,final,ct=fetch(u,120); rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            if raw.startswith(b"%PDF-"):
                try:
                    pa=pdf_audit(raw); rec["pdf_audit"]=pa
                    if pa["pages"]>10:recovered.append(rec)
                except Exception as exc:rec["pdf_error"]=f"{type(exc).__name__}: {exc}"
        except Exception as exc:rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)
        if recovered and recovered[-1].get("pdf_audit",{}).get("pages",0)>=200:
            break

    best=max(recovered,key=lambda r:r["pdf_audit"]["pages"],default=None)
    out={
        "status":"BROEILS1992_LEGACY_DISSERTATION_RECOVERY_COMPLETE",
        "source":"A.H. Broeils 1992 PhD thesis, University of Groningen",
        "legacy_bases":BASES,"live_directory_probes":live,"cdx_indexes":indexes,
        "n_pdf_candidates_attempted":len(attempts),"attempts":attempts,
        "full_thesis_recovered":bool(best and best["pdf_audit"]["pages"]>=200),
        "best_recovered_url":None if best is None else best.get("final_url",best["url"]),
        "best_pdf_audit":None if best is None else best["pdf_audit"],
        "interpretation_rule":"Only a recovered multi-page dissertation with target/native profile evidence can advance to exact table/vector extraction. A catalogue wrapper is not treated as the thesis.",
        "boundary":"Bounded legacy-repository recovery only; no OCR, raster digitization, normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"full_thesis_recovered":out["full_thesis_recovered"],"best_recovered_url":out["best_recovered_url"],"best_pages":None if best is None else best["pdf_audit"]["pages"],"n_candidates":len(attempts)},indent=2))

if __name__=="__main__":main()
