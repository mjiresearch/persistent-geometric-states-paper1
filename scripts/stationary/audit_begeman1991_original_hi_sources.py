#!/usr/bin/env python3
"""Audit Begeman, Broeils & Sanders (1991; Be91) back to original H I sources.

The live Lelli queue contains five frozen galaxies under SPARC ref Be91. The
1991 MNRAS paper is a selected rotation-curve analysis, not assumed to be the
original 21-cm observing source. This bounded audit retrieves the public MNRAS
PDF, locates each target in native text, records nearby citation/source context,
and inventories any direct radial H I/surface-density language.

No OCR, raster digitization, profile-value extraction, persistence fitting, or
blind-outcome inspection occurs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request,urlopen

import pymupdf

PDF="https://academic.oup.com/mnras/article-pdf/249/3/523/18160929/mnras249-0523.pdf"
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
PRIORITY=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT=Path("validation/stationary/begeman1991_original_hi_source_audit_v1.json")


def fetch(url):
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/pdf,*/*;q=0.8","Referer":"https://academic.oup.com/"})
    with urlopen(req,timeout=120) as h:return h.read(),h.geturl(),h.headers.get("Content-Type","")


def compact(s):return re.sub(r"[^A-Z0-9]","",s.upper())

def variants(g):
    c=compact(g);out={c}
    m=re.match(r"(NGC|UGC|DDO)0*(\d+)$",c)
    if m:
        p,n=m.groups();n=str(int(n));out|={p+n,p+n.zfill(3),p+n.zfill(5)}
    return out


def contexts(lines,indices,radius=8):
    out=[]
    for i in indices:
        lo=max(0,i-radius);hi=min(len(lines),i+radius+1)
        out.append({"line":i+1,"context":"\n".join(lines[lo:hi])[:6000]})
    return out


def main():
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:rows=list(csv.DictReader(fh))
    target=next((r for r in rows if r["sparc_ref_id"]=="Be91"),None)
    if target is None or int(target["n_untouched_frozen_galaxies"])!=5:
        raise RuntimeError("Expected Be91 five-galaxy actionable block")
    galaxies=target["galaxies"].split(";")

    raw,final,ct=fetch(PDF)
    if not raw.startswith(b"%PDF-"):raise RuntimeError(f"MNRAS route returned non-PDF {raw[:20]!r}")
    doc=pymupdf.open(stream=raw,filetype="pdf")
    pages=[p.get_text("text") for p in doc]
    alltext="\n\f\n".join(pages)

    per=[]
    for g in galaxies:
        vv=variants(g);hits=[]
        for pi,text in enumerate(pages):
            lines=text.splitlines(); idx=[]
            for i,line in enumerate(lines):
                cl=compact(line)
                if any(v and v in cl for v in vv):idx.append(i)
            if idx:
                low=text.lower()
                hits.append({
                    "page_number_1based":pi+1,
                    "contexts":contexts(lines,idx,10),
                    "surface_density_on_page":"surface density" in low,
                    "hi_or_21cm_on_page":bool(re.search(r"\bH\s*I\b|21\s*-?\s*cm|neutral hydrogen",text,re.I)),
                    "n_drawings":len(doc[pi].get_drawings()),
                    "n_images":len(doc[pi].get_images(full=True)),
                })
        per.append({"galaxy":g,"n_hit_pages":len(hits),"pages":hits})

    # Capture reference-section lines likely to be original H I data sources.
    reflines=[]
    lines=alltext.splitlines()
    source_pat=re.compile(r"Begeman|Broeils|Carignan|Puche|van Albada|Bosma|Shostak|Lake|Sancisi|Rogstad|Rots|Jobin|Newton",re.I)
    for i,line in enumerate(lines):
        if source_pat.search(line):reflines.append({"line":i+1,"text":line[:1000]})

    profile_hits=[]
    for pi,text in enumerate(pages):
        for i,line in enumerate(text.splitlines()):
            if re.search(r"surface\s+density|H\s*I\s+distribution|gas\s+distribution|21\s*-?\s*cm|rotation\s+curve",line,re.I):
                profile_hits.append({"page_number_1based":pi+1,"line":i+1,"text":line[:1000]})

    result={
        "status":"BEGEMAN1991_ORIGINAL_HI_SOURCE_AUDIT_COMPLETE",
        "source":"Begeman, Broeils & Sanders 1991 MNRAS 249 523-537",
        "pdf_url":final,"pdf_bytes":len(raw),"pdf_sha256":hashlib.sha256(raw).hexdigest(),"pdf_pages":len(doc),
        "n_priority_frozen_galaxies":len(galaxies),
        "priority_role_counts":{"calibration":int(target["n_calibration"]),"blind":int(target["n_blind"])},
        "priority_galaxies":galaxies,"target_contexts":per,
        "candidate_original_source_reference_lines":reflines[:300],
        "hi_profile_language_hits":profile_hits[:300],
        "classification":"downstream_selected_rotation_curve_analysis_requires_per_galaxy_original_source_resolution",
        "interpretation_rule":"Be91 is not promoted as a direct radial H I profile source merely because it models gas contributions. Each target must be traced to the underlying observing publication identified in the paper/context before acquisition.",
        "boundary":"No OCR, raster digitization, profile-value extraction, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"pdf_pages":len(doc),"targets":{x["galaxy"]:[p["page_number_1based"] for p in x["pages"]] for x in per},"n_candidate_source_lines":len(reflines)},indent=2))

if __name__=="__main__":main()
