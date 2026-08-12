#!/usr/bin/env python3
"""Trace Be91 Lelli/SPARC targets to their original observing sources.

Begeman, Broeils & Sanders (1991), MNRAS 249, 523 is a rotation-curve
selection/modeling paper. This audit recovers the public article PDF and records
native-text contexts, table/source references and bibliography entries for the
five currently untouched Be91 frozen galaxies:
DDO170, NGC2903, NGC3109, NGC6503, UGC02259.

Acquisition/provenance only. No profile values, model fitting, or blind outcomes.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path

import pymupdf

UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
URLS=[
 "https://academic.oup.com/mnras/article-pdf/249/3/523/18160929/mnras249-0523.pdf",
 "https://articles.adsabs.harvard.edu/pdf/1991MNRAS.249..523B",
 "https://adsabs.harvard.edu/pdf/1991MNRAS.249..523B",
]
TARGETS={
 "DDO170":[r"DDO\s*170"],
 "NGC2903":[r"NGC\s*2903"],
 "NGC3109":[r"NGC\s*3109"],
 "NGC6503":[r"NGC\s*6503"],
 "UGC02259":[r"UGC\s*2259",r"UGC\s*02259"],
}
OUT=Path("validation/stationary/be91_original_hi_source_audit_v1.json")


def fetch(url,timeout=120):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as h:
        return h.read(),h.geturl(),h.headers.get("Content-Type","")


def contexts(lines,patterns,radius=7):
    regs=[re.compile(p,re.I) for p in patterns]
    out=[]
    for i,line in enumerate(lines):
        if any(r.search(line) for r in regs):
            lo=max(0,i-radius);hi=min(len(lines),i+radius+1)
            out.append({"hit_line":i+1,"context":"\n".join(lines[lo:hi])[:6000]})
    return out[:80]


def audit_pdf(raw):
    doc=pymupdf.open(stream=raw,filetype="pdf")
    pages=[p.get_text("text") for p in doc]
    full="\n\f\n".join(pages)
    lines=full.splitlines()
    target_hits={g:contexts(lines,pats,10) for g,pats in TARGETS.items()}
    source_terms=[
      r"rotation curve",r"H\s*I",r"21\s*cm",r"observ",r"data",r"taken from",
      r"reference",r"source",r"surface density",r"gas distribution",r"published",
    ]
    source_contexts=contexts(lines,source_terms,4)
    # Capture bibliography-like lines plus neighbors, preserving native text only.
    bib=[]
    for i,line in enumerate(lines):
        if re.search(r"REFERENCES|Begeman|Broeils|Carignan|Puche|Lake|Shostak|van Albada|Sancisi|Jobin|Rogstad|Bosma|Wevers|Kent|Casertano|van Gorkom",line,re.I):
            lo=max(0,i-2);hi=min(len(lines),i+3)
            bib.append({"line":i+1,"context":"\n".join(lines[lo:hi])[:2500]})
    # Tables are especially likely to contain compact per-galaxy reference codes.
    table=[]
    for i,line in enumerate(lines):
        if re.search(r"Table\s*1|Table\s*2|Ref\.?|References?",line,re.I):
            lo=max(0,i-8);hi=min(len(lines),i+20)
            table.append({"line":i+1,"context":"\n".join(lines[lo:hi])[:7000]})
    return {
      "pages":len(doc),
      "native_text_characters":sum(map(len,pages)),
      "target_contexts":target_hits,
      "targets_with_native_text":[g for g,h in target_hits.items() if h],
      "source_language_contexts":source_contexts[:250],
      "table_reference_contexts":table[:100],
      "bibliography_contexts":bib[:250],
    }


def main():
    attempts=[]; audit=None; recovered=None
    for u in URLS:
        rec={"url":u}
        try:
            raw,final,ct=fetch(u)
            rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:16].hex()})
            if raw.startswith(b"%PDF-") and len(raw)>100000:
                rec["sha256"]=hashlib.sha256(raw).hexdigest()
                audit=audit_pdf(raw);recovered=final;attempts.append(rec);break
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
        attempts.append(rec)
    out={
      "status":"BE91_ORIGINAL_HI_SOURCE_AUDIT_COMPLETE",
      "source":"Begeman, Broeils & Sanders 1991 MNRAS 249 523-537",
      "bibcode":"1991MNRAS.249..523B",
      "target_galaxies":list(TARGETS),
      "transport_attempts":attempts,
      "pdf_recovered":audit is not None,
      "recovered_url":recovered,
      "pdf_audit":audit,
      "interpretation_boundary":(
        "Be91 is treated as a downstream selection/mass-model paper until its own text supports a direct observing role. "
        "Per-galaxy source attribution must be supported by Be91 table/text/bibliography before an original paper is assigned."
      ),
      "boundary":"Acquisition/provenance only; no profile-value extraction, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"pdf_recovered":out["pdf_recovered"],"recovered_url":out["recovered_url"],"targets_with_native_text":[] if not audit else audit["targets_with_native_text"]},indent=2))

if __name__=="__main__":main()
