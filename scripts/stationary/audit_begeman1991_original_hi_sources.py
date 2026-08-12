#!/usr/bin/env python3
"""Audit Begeman, Broeils & Sanders (1991; Be91) back to original H I sources.

The five frozen Be91 galaxies are traced through the 1991 MNRAS paper to the
underlying 21-cm observing literature. Transport is deliberately multi-route:
OUP first, NASA ADS scanned-paper service second, then one exact Wayback lookup.
A publisher 403 is therefore not mistaken for scientific-route exhaustion.

No OCR, raster digitization, profile-value extraction, persistence fitting, or
blind-outcome inspection occurs.
"""
from __future__ import annotations

import csv, hashlib, json, re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

import pymupdf

URLS=[
 "https://academic.oup.com/mnras/article-pdf/249/3/523/18160929/mnras249-0523.pdf",
 "https://articles.adsabs.harvard.edu/pdf/1991MNRAS.249..523B",
]
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
PRIORITY=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT=Path("validation/stationary/begeman1991_original_hi_source_audit_v1.json")


def fetch(url,timeout=120):
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/pdf,application/json,*/*;q=0.8"})
    with urlopen(req,timeout=timeout) as h:return h.read(),h.geturl(),h.headers.get("Content-Type","")


def wayback(url):
    api="https://archive.org/wayback/available?url="+quote(url,safe="")
    try:
        raw,_,_=fetch(api,45); data=json.loads(raw.decode("utf-8","replace"))
        c=data.get("archived_snapshots",{}).get("closest") or {}
        if c.get("available") and c.get("url"):
            u=c["url"]
            m=re.search(r"/web/(\d+)/(.*)$",u)
            if m:u=f"https://web.archive.org/web/{m.group(1)}id_/{m.group(2)}"
            return u,data
        return None,data
    except Exception as exc:return None,{"error":f"{type(exc).__name__}: {exc}"}


def compact(s):return re.sub(r"[^A-Z0-9]","",s.upper())

def variants(g):
    c=compact(g);out={c}
    m=re.match(r"(NGC|UGC|DDO)0*(\d+)$",c)
    if m:
        p,n=m.groups();n=str(int(n));out|={p+n,p+n.zfill(3),p+n.zfill(5)}
    return out

def contexts(lines,indices,radius=8):
    return [{"line":i+1,"context":"\n".join(lines[max(0,i-radius):min(len(lines),i+radius+1)])[:6000]} for i in indices]


def obtain_pdf():
    attempts=[]
    for u in URLS:
        rec={"route":"live","url":u}
        try:
            raw,final,ct=fetch(u);rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            attempts.append(rec)
            if raw.startswith(b"%PDF-"):return raw,final,attempts
        except Exception as exc:rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"});attempts.append(rec)
    snap,diag=wayback(URLS[0]);attempts.append({"route":"wayback_availability","url":URLS[0],"diagnostic":diag})
    if snap:
        rec={"route":"wayback","url":snap}
        try:
            raw,final,ct=fetch(snap,180);rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()});attempts.append(rec)
            if raw.startswith(b"%PDF-"):return raw,final,attempts
        except Exception as exc:rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"});attempts.append(rec)
    return None,None,attempts


def main():
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:rows=list(csv.DictReader(fh))
    target=next((r for r in rows if r["sparc_ref_id"]=="Be91"),None)
    if target is None or int(target["n_untouched_frozen_galaxies"])!=5:raise RuntimeError("Expected Be91 five-galaxy actionable block")
    galaxies=target["galaxies"].split(";")

    raw,final,attempts=obtain_pdf()
    if raw is None:
        result={"status":"BEGEMAN1991_ORIGINAL_HI_SOURCE_AUDIT_TRANSPORT_BLOCKED","source":"Begeman, Broeils & Sanders 1991 MNRAS 249 523-537","transport_attempts":attempts,"priority_galaxies":galaxies,"boundary":"Transport failure is not scientific-route exhaustion."}
        OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2));return

    doc=pymupdf.open(stream=raw,filetype="pdf");pages=[p.get_text("text") for p in doc];alltext="\n\f\n".join(pages)
    per=[]
    for g in galaxies:
        vv=variants(g);hits=[]
        for pi,text in enumerate(pages):
            lines=text.splitlines();idx=[i for i,line in enumerate(lines) if any(v and v in compact(line) for v in vv)]
            if idx:
                low=text.lower();hits.append({"page_number_1based":pi+1,"contexts":contexts(lines,idx,10),"surface_density_on_page":"surface density" in low,"hi_or_21cm_on_page":bool(re.search(r"\bH\s*I\b|21\s*-?\s*cm|neutral hydrogen",text,re.I)),"n_drawings":len(doc[pi].get_drawings()),"n_images":len(doc[pi].get_images(full=True))})
        per.append({"galaxy":g,"n_hit_pages":len(hits),"pages":hits})

    reflines=[];lines=alltext.splitlines();source_pat=re.compile(r"Begeman|Broeils|Carignan|Puche|van Albada|Bosma|Shostak|Lake|Sancisi|Rogstad|Rots|Jobin|Newton|van Gorkom",re.I)
    for i,line in enumerate(lines):
        if source_pat.search(line):reflines.append({"line":i+1,"text":line[:1000]})
    profile_hits=[]
    for pi,text in enumerate(pages):
        for i,line in enumerate(text.splitlines()):
            if re.search(r"surface\s+density|H\s*I\s+distribution|gas\s+distribution|21\s*-?\s*cm|rotation\s+curve",line,re.I):profile_hits.append({"page_number_1based":pi+1,"line":i+1,"text":line[:1000]})

    result={"status":"BEGEMAN1991_ORIGINAL_HI_SOURCE_AUDIT_COMPLETE","source":"Begeman, Broeils & Sanders 1991 MNRAS 249 523-537","pdf_url":final,"pdf_bytes":len(raw),"pdf_sha256":hashlib.sha256(raw).hexdigest(),"pdf_pages":len(doc),"transport_attempts":attempts,"n_priority_frozen_galaxies":len(galaxies),"priority_role_counts":{"calibration":int(target["n_calibration"]),"blind":int(target["n_blind"])},"priority_galaxies":galaxies,"target_contexts":per,"candidate_original_source_reference_lines":reflines[:300],"hi_profile_language_hits":profile_hits[:300],"classification":"downstream_selected_rotation_curve_analysis_requires_per_galaxy_original_source_resolution","interpretation_rule":"Be91 is not promoted as a direct radial H I profile source merely because it models gas contributions. Each target must be traced to the underlying observing publication identified in the paper/context before acquisition.","boundary":"No OCR, raster digitization, profile-value extraction, persistence fitting, or blind-outcome inspection."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"pdf_url":final,"pdf_pages":len(doc),"targets":{x["galaxy"]:[p["page_number_1based"] for p in x["pages"]] for x in per},"n_candidate_source_lines":len(reflines)},indent=2))

if __name__=="__main__":main()
