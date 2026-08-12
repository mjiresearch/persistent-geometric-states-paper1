#!/usr/bin/env python3
"""Trace SPARC/Lelli Sa96 galaxies through Sanders (1996) to original data sources.

Sanders 1996 is a downstream analysis of already-published extended rotation
curves. This audit inspects the public arXiv source package and records every
context in which the 13 currently untouched frozen Sa96 galaxies are named,
plus the bibliography/source-table structure needed to map them to the actual
H I observing papers.

Acquisition/provenance only: no profile values or persistence parameters.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV = "https://export.arxiv.org/e-print/astro-ph/9606089"
UA = "PersistenceFrameworkPaperI/1.0"
TARGETS = {
    "NGC0055": [r"NGC\s*55\b", r"NGC\s*0055\b"],
    "NGC0247": [r"NGC\s*247\b", r"NGC\s*0247\b"],
    "NGC0300": [r"NGC\s*300\b", r"NGC\s*0300\b"],
    "NGC0801": [r"NGC\s*801\b", r"NGC\s*0801\b"],
    "NGC1003": [r"NGC\s*1003\b"],
    "NGC2683": [r"NGC\s*2683\b"],
    "NGC2998": [r"NGC\s*2998\b"],
    "NGC5033": [r"NGC\s*5033\b"],
    "NGC5371": [r"NGC\s*5371\b"],
    "NGC5585": [r"NGC\s*5585\b"],
    "NGC5907": [r"NGC\s*5907\b"],
    "NGC6674": [r"NGC\s*6674\b"],
    "UGC02885": [r"UGC\s*2885\b", r"UGC\s*02885\b"],
}


def fetch(url: str) -> tuple[bytes, str]:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=90) as r:
        return r.read(), r.headers.get("Content-Type", "")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def contexts(lines: list[str], patterns: list[str], radius: int = 3) -> list[dict]:
    regs = [re.compile(p, re.I) for p in patterns]
    hits=[]
    seen=set()
    for i,line in enumerate(lines):
        if any(r.search(line) for r in regs):
            lo=max(0,i-radius); hi=min(len(lines),i+radius+1)
            key=(lo,hi)
            if key in seen: continue
            seen.add(key)
            hits.append({
                "hit_line":i+1,
                "context_start":lo+1,
                "context_end":hi,
                "lines":[{"line":j+1,"text":lines[j][:1000]} for j in range(lo,hi)],
            })
    return hits


def main() -> None:
    raw, ct = fetch(ARXIV)
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    files=[]; texdocs=[]
    for m in tf.getmembers():
        if not m.isfile(): continue
        files.append({"name":m.name,"bytes":m.size,"suffix":Path(m.name).suffix.lower()})
        if Path(m.name).suffix.lower() in {".tex",".txt",".dat",".tbl",".bib"}:
            b=tf.extractfile(m).read()
            texdocs.append((m.name,b.decode("latin-1",errors="replace")))

    target_hits={}
    source_language_hits=[]
    table_ref_hits=[]
    reference_hits=[]
    source_pat=re.compile(r"published|rotation curve|H.?I|21\s*cm|data|surface density|gas distribution|reference|observ",re.I)
    table_pat=re.compile(r"table|ref\.|reference|source",re.I)

    for name,text in texdocs:
        lines=text.splitlines()
        for target,pats in TARGETS.items():
            cc=contexts(lines,pats,4)
            if cc:
                target_hits.setdefault(target,[]).append({"file":name,"contexts":cc})
        for i,line in enumerate(lines):
            if source_pat.search(line):
                source_language_hits.append({"file":name,"line":i+1,"text":line[:1000]})
            if table_pat.search(line) and any(k in line.lower() for k in ("table","ref","source")):
                table_ref_hits.append({"file":name,"line":i+1,"text":line[:1000]})
            # Capture likely bibliography entries with author-year strings.
            if re.search(r"\\bibitem|\\reference|et al\.|ApJ|AJ|A&A|MNRAS",line,re.I):
                reference_hits.append({"file":name,"line":i+1,"text":line[:1200]})

    out={
        "status":"SA96_ORIGINAL_SOURCE_PROVENANCE_AUDIT_COMPLETE",
        "source":"Sanders 1996 ApJ 473 117-129; arXiv astro-ph/9606089",
        "arxiv_url":ARXIV,"content_type":ct,"archive_bytes":len(raw),"archive_sha256":sha(raw),
        "files":files,
        "target_count":len(TARGETS),
        "targets_with_hits":sorted(target_hits),
        "target_contexts":target_hits,
        "source_language_hits":source_language_hits[:500],
        "table_reference_hits":table_ref_hits[:300],
        "bibliography_like_hits":reference_hits[:500],
        "interpretation_boundary":"Sanders 1996 is treated as a downstream published-curve analysis. A target is not assigned an original H I source until the Sanders source text explicitly supports that attribution."
    }
    p=Path("validation/stationary/sa96_original_source_provenance_audit_v1.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "files":files,
        "targets_with_hits":out["targets_with_hits"],
        "n_source_language_hits":len(source_language_hits),
        "n_table_reference_hits":len(table_ref_hits),
        "n_bibliography_like_hits":len(reference_hits),
    },indent=2))


if __name__ == "__main__":
    main()
