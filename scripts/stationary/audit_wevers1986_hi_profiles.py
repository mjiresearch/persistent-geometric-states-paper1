#!/usr/bin/env python3
"""Audit Wevers, van der Kruit & Allen (1986) for exact radial H I profiles.

Lelli/SPARC -> Be91 -> Be91 Table 1 ref. 7 -> Wevers et al. 1986,
A&AS 66, 505, The Palomar-Westerbork survey of northern spiral galaxies.

The full public ADS scan is inspected transiently. Native PDF text and graphics
objects are used; no OCR is run and no raster plots are digitized. The immediate
Be91 targets are NGC2903 and NGC6503. NGC5033/NGC5371 are included as same-atlas
cross-reference candidates because they occur elsewhere in the Lelli sourcing
trail and can be resolved at no scientific-rule cost if the source contains them.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pymupdf

BIBCODE="1986A&AS...66..505W"
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
TARGETS=["NGC2903","NGC6503","NGC5033","NGC5371"]
OUT=Path("validation/stationary/wevers1986_hi_profile_audit_v1.json")


def urls():
    encoded=urllib.parse.quote(BIBCODE,safe=".")
    return [
        f"https://articles.adsabs.harvard.edu/pdf/{encoded}",
        f"https://articles.adsabs.harvard.edu/pdf/{BIBCODE}",
        f"https://adsabs.harvard.edu/pdf/{encoded}",
    ]


def fetch(url,timeout=180):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as h:
        return h.read(),h.geturl(),h.headers.get("Content-Type","")


def compact(s):
    return re.sub(r"[^A-Z0-9]","",s.upper())


def variants(g):
    m=re.match(r"NGC0*(\d+)",compact(g)); n=str(int(m.group(1)))
    return [f"NGC {n}",f"NGC{n}",f"NGC {n.zfill(4)}",f"NGC{n.zfill(4)}"]


def term_context(text, terms, radius=5):
    lines=text.splitlines(); out=[]
    for i,line in enumerate(lines):
        if any(re.search(t,line,re.I) for t in terms):
            lo=max(0,i-radius);hi=min(len(lines),i+radius+1)
            out.append({"line":i+1,"context":"\n".join(lines[lo:hi])[:5000]})
    return out[:100]


def inspect(raw):
    doc=pymupdf.open(stream=raw,filetype="pdf")
    pages=[]
    for i,p in enumerate(doc):
        text=p.get_text("text")
        pages.append({
            "index":i,
            "text":text,
            "n_drawings":len(p.get_drawings()),
            "drawing_items_total":sum(len(d.get("items",[])) for d in p.get_drawings()),
            "n_images":len(p.get_images(full=True)),
        })

    terms=[
        r"surface\s+density",r"surface-density",r"radial\s+distribution",r"H\s*I\s+distribution",
        r"HI\s+distribution",r"column\s+density",r"strip\s+integral",r"azimuthal",
        r"mass\s+surface",r"radial\s+profile",r"density\s+profile",
    ]
    per=[]
    inspect_page_ids=set()
    for g in TARGETS:
        vv=variants(g); hits=[]
        for rec in pages:
            t=rec["text"]
            if any(v.lower() in t.lower() for v in vv):
                idx=rec["index"]; inspect_page_ids.update(j for j in (idx-1,idx,idx+1) if 0<=j<len(pages))
                hits.append({
                    "page_number_1based":idx+1,
                    "matched_name_variants":[v for v in vv if v.lower() in t.lower()],
                    "science_contexts":term_context(t,terms,7),
                    "text_excerpt":" ".join(t.split())[:7000],
                    "n_drawings":rec["n_drawings"],
                    "drawing_items_total":rec["drawing_items_total"],
                    "n_images":rec["n_images"],
                })
        per.append({"galaxy":g,"n_pages":len(hits),"pages":hits})

    global_profile=[]
    for rec in pages:
        t=rec["text"]
        matched=[pat for pat in terms if re.search(pat,t,re.I)]
        if matched:
            global_profile.append({
                "page_number_1based":rec["index"]+1,
                "matched_patterns":matched,
                "excerpt":" ".join(t.split())[:4000],
                "n_drawings":rec["n_drawings"],
                "drawing_items_total":rec["drawing_items_total"],
                "n_images":rec["n_images"],
            })

    # Native-number-table candidates: pages containing a target and surface-density
    # language plus many numeric tokens. This is only a locator/QC gate, not extraction.
    table_candidates=[]
    for rec in pages:
        t=rec["text"]
        target_names=[g for g in TARGETS if any(v.lower() in t.lower() for v in variants(g))]
        if not target_names: continue
        if not any(re.search(pat,t,re.I) for pat in terms): continue
        nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?",t)
        table_candidates.append({
            "page_number_1based":rec["index"]+1,
            "targets":target_names,
            "n_numeric_tokens":len(nums),
            "first_numeric_tokens":nums[:150],
            "excerpt":" ".join(t.split())[:6000],
        })

    return {
        "pages":len(doc),
        "native_text_characters":sum(len(r["text"]) for r in pages),
        "targets":per,
        "targets_found":[r["galaxy"] for r in per if r["n_pages"]],
        "global_profile_language_pages":global_profile[:200],
        "target_native_numeric_table_candidates":table_candidates,
        "graphics_summary_on_target_neighbor_pages":[
            {"page_number_1based":i+1,"n_drawings":pages[i]["n_drawings"],"drawing_items_total":pages[i]["drawing_items_total"],"n_images":pages[i]["n_images"]}
            for i in sorted(inspect_page_ids)
        ],
    }


def main():
    attempts=[]; data=None; recovered=None
    for u in urls():
        rec={"url":u}
        try:
            raw,final,ct=fetch(u); rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            if raw.startswith(b"%PDF-") and len(raw)>500000:
                rec["sha256"]=hashlib.sha256(raw).hexdigest(); data=raw; recovered=final; attempts.append(rec); break
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)

    audit=inspect(data) if data is not None else None
    out={
        "status":"WEVERS1986_HI_PROFILE_AUDIT_COMPLETE",
        "source":"Wevers, van der Kruit & Allen 1986, A&AS 66, 505-662",
        "bibcode":BIBCODE,
        "title":"The Palomar-Westerbork survey of northern spiral galaxies",
        "immediate_be91_targets":["NGC2903","NGC6503"],
        "same_atlas_cross_reference_targets":["NGC5033","NGC5371"],
        "transport_attempts":attempts,
        "pdf_recovered":data is not None,
        "recovered_url":recovered,
        "pdf_sha256":None if data is None else hashlib.sha256(data).hexdigest(),
        "pdf_audit":audit,
        "promotion_rule":"Only native machine-readable/tabular values or unambiguous vector profile geometry may be promoted. Raster atlas panels are not digitized.",
        "boundary":"Acquisition/provenance only; no OCR, raster digitization, helium/distance normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],"pdf_recovered":out["pdf_recovered"],
        "targets_found":[] if not audit else audit["targets_found"],
        "n_table_candidates":0 if not audit else len(audit["target_native_numeric_table_candidates"]),
        "pages":None if not audit else audit["pages"],
    },indent=2))

if __name__=="__main__":main()
