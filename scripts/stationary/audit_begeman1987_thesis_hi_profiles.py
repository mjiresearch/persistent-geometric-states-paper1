#!/usr/bin/env python3
"""Audit the official Groningen Begeman thesis for exact radial H I profiles.

Frozen Lelli/SPARC branch: Be87 = K.G. Begeman, PhD thesis,
"HI rotation curves of spiral galaxies".  The current Groningen portal exposes
both a full thesis PDF and chapter PDFs.  We probe the exact portal file IDs and
the Pure backend, then inspect recovered PDFs transiently.

Targets: NGC2903, NGC5033, NGC5371, NGC6503.

Strict gate: source-native radius-vs-Sigma_HI rows or unambiguous vector profile
geometry only.  No OCR, no raster digitization, no map-to-profile reconstruction,
no persistence fitting, and no blind-outcome inspection.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path

import fitz

UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
TARGETS=["NGC2903","NGC5033","NGC5371","NGC6503"]
OUT=Path("validation/stationary/begeman1987_thesis_hi_profile_audit_v1.json")

FILES=[
    ("thesis.pdf",2841681),
    ("c1.pdf",2841673),
    ("c2.pdf",2841674),
    ("c3.pdf",2841675),
    ("c4.pdf",2841676),
    ("c5.pdf",2841677),
]
PROFILE_PATTERNS=[
    r"surface\s+density",r"surface-density",r"radial\s+distribution",r"radial\s+profile",
    r"H\s*I\s+distribution",r"HI\s+distribution",r"column\s+density",r"gas\s+disk",
    r"gas\s+surface",r"mass\s+surface",r"annuli",r"rings?",
]


def candidate_urls(name,file_id):
    return [
        f"https://research.rug.nl/files/{file_id}/{name}",
        f"https://pure.rug.nl/ws/portalfiles/portal/{file_id}/{name}",
        f"https://pure.rug.nl/ws/api/524/files/{file_id}/{name}",
    ]


def fetch_one(name,file_id):
    attempts=[]
    for u in candidate_urls(name,file_id):
        rec={"url":u}
        try:
            req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
            with urllib.request.urlopen(req,timeout=180) as h:
                raw=h.read(); final=h.geturl(); ct=h.headers.get("Content-Type","")
            rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            if raw.startswith(b"%PDF-") and len(raw)>20_000:
                rec["valid_pdf"]=True;rec["sha256"]=hashlib.sha256(raw).hexdigest();attempts.append(rec)
                return raw,attempts
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)
    return None,attempts


def names(g):
    n=str(int(re.sub(r"\D","",g)))
    return [f"NGC {n}",f"NGC{n}",f"NGC {n.zfill(4)}",f"NGC{n.zfill(4)}"]


def contexts(text,patterns,radius=6):
    lines=text.splitlines();out=[]
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in patterns):
            lo=max(0,i-radius);hi=min(len(lines),i+radius+1)
            out.append({"line":i+1,"context":"\n".join(lines[lo:hi])[:6500]})
    return out[:100]


def inspect_pdf(raw,label):
    doc=fitz.open(stream=raw,filetype="pdf")
    pages=[]
    for i,p in enumerate(doc):
        text=p.get_text("text"); drawings=p.get_drawings(); images=p.get_images(full=True)
        pages.append({
            "i":i,"text":text,"native_text_chars":len(text),"n_drawings":len(drawings),
            "drawing_items_total":sum(len(d.get("items",[])) for d in drawings),"n_images":len(images),
        })
    per=[]
    for g in TARGETS:
        vv=names(g);hits=[]
        for r in pages:
            t=r["text"]
            if any(v.lower() in t.lower() for v in vv):
                hits.append({
                    "page_number_1based":r["i"]+1,
                    "matched_names":[v for v in vv if v.lower() in t.lower()],
                    "profile_contexts":contexts(t,PROFILE_PATTERNS,8),
                    "excerpt":" ".join(t.split())[:8000],
                    "n_drawings":r["n_drawings"],"drawing_items_total":r["drawing_items_total"],"n_images":r["n_images"],
                })
        per.append({"galaxy":g,"pages":hits})
    profile_pages=[]
    for r in pages:
        pats=[p for p in PROFILE_PATTERNS if re.search(p,r["text"],re.I)]
        if pats:
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?",r["text"])
            profile_pages.append({
                "page_number_1based":r["i"]+1,"matched_patterns":pats,"n_numeric_tokens":len(nums),
                "excerpt":" ".join(r["text"].split())[:7500],"n_drawings":r["n_drawings"],
                "drawing_items_total":r["drawing_items_total"],"n_images":r["n_images"],
            })
    geom={
        "pages":len(doc),"native_text_chars_total":sum(r["native_text_chars"] for r in pages),
        "pages_with_native_text":sum(bool(r["text"].strip()) for r in pages),
        "pages_with_drawings":sum(r["n_drawings"]>0 for r in pages),
        "pages_with_images":sum(r["n_images"]>0 for r in pages),
        "pages_with_images_no_drawings":sum(r["n_images"]>0 and r["n_drawings"]==0 for r in pages),
        "max_drawing_items":max((r["drawing_items_total"] for r in pages),default=0),
    }
    return {"label":label,"geometry":geom,"targets":per,"profile_language_pages":profile_pages}


def main():
    recovered=[]; all_attempts={}
    # Full thesis first.  Chapters are useful if the monolith is blocked or its text layer is weak.
    for name,file_id in FILES:
        raw,attempts=fetch_one(name,file_id);all_attempts[name]=attempts
        if raw is not None:
            recovered.append({
                "name":name,"file_id":file_id,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
                "audit":inspect_pdf(raw,name),
            })

    target_union={g:[] for g in TARGETS}
    for f in recovered:
        for tr in f["audit"]["targets"]:
            for p in tr["pages"]:
                target_union[tr["galaxy"]].append({"document":f["name"],**p})

    # Conservative candidate flag.  It only means a native-text page containing the target
    # and profile language deserves row-level QC; it is not automatically a radial table.
    numeric_candidates=[]
    for f in recovered:
        for tr in f["audit"]["targets"]:
            for p in tr["pages"]:
                if p["profile_contexts"]:
                    nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",p["excerpt"])
                    if len(nums)>=30:
                        numeric_candidates.append({"document":f["name"],"galaxy":tr["galaxy"],"page_number_1based":p["page_number_1based"],"n_numeric_tokens":len(nums),"excerpt":p["excerpt"]})

    out={
        "status":"BEGEMAN1987_THESIS_HI_PROFILE_AUDIT_COMPLETE",
        "source":"K.G. Begeman, HI rotation curves of spiral galaxies, PhD thesis, University of Groningen (1987; institutional deposit record 2006)",
        "official_portal":"https://research.rug.nl/en/publications/hi-rotation-curves-of-spiral-galaxies/",
        "portal_file_ids":{name:file_id for name,file_id in FILES},
        "transport_attempts":all_attempts,
        "recovered_documents":[{"name":f["name"],"file_id":f["file_id"],"bytes":f["bytes"],"sha256":f["sha256"],"geometry":f["audit"]["geometry"]} for f in recovered],
        "target_union":target_union,"native_numeric_profile_candidates":numeric_candidates,
        "document_audits":[f["audit"] for f in recovered],
        "decision_fields":{
            "full_thesis_recovered":any(f["name"]=="thesis.pdf" for f in recovered),
            "n_documents_recovered":len(recovered),
            "targets_with_native_text":{g:bool(v) for g,v in target_union.items()},
            "n_native_numeric_profile_candidates":len(numeric_candidates),
        },
        "promotion_rule":"Only a source-native radius-versus-Sigma_HI table or unambiguous vector profile geometry may be promoted. Rotation-curve tables, mass-model tables, and raster H I figures do not qualify.",
        "boundary":"Acquisition/provenance only. No OCR, raster digitization, map-to-profile reconstruction, normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],"decision_fields":out["decision_fields"],
        "recovered_documents":[{"name":x["name"],"pages":x["audit"]["geometry"]["pages"],"text_chars":x["audit"]["geometry"]["native_text_chars_total"],"drawings":x["audit"]["geometry"]["pages_with_drawings"],"images":x["audit"]["geometry"]["pages_with_images"]} for x in recovered],
    },indent=2))

if __name__=="__main__":main()
