#!/usr/bin/env python3
"""Extract dB02 Table 1 source codes for the five frozen Lelli targets.

This is a provenance-only parser of the original arXiv TeX.  de Blok & Bosma
(2002) explicitly state that the gas component uses H I surface densities from
the references in Table 1.  We therefore preserve the exact Table 1 row and
reference-code legend before following those source papers.

No profile values, normalization, persistence fitting, or blind outcomes.
"""
from __future__ import annotations
import io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URLS=[
    "https://arxiv.org/e-print/astro-ph/0201276",
    "https://export.arxiv.org/e-print/astro-ph/0201276",
]
OUT=Path("validation/stationary/db02_table1_hi_source_codes_v1.json")
ALIASES={
    "DDO064":["U5272","DDO64"],
    "NGC0100":["N100","NGC100","U231"],
    "UGC01281":["U1281","UGC1281"],
    "UGC04278":["U4278","UGC4278"],
    "UGC05005":["U5005","UGC5005"],
}

def fetch():
    errs=[]
    for u in URLS:
        try:
            req=Request(u,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0","Accept":"application/gzip,application/octet-stream,*/*;q=0.5"})
            with urlopen(req,timeout=120) as h:return h.read(),u,h.geturl(),h.headers.get("Content-Type","")
        except Exception as exc: errs.append({"url":u,"error":f"{type(exc).__name__}: {exc}"})
    raise RuntimeError(f"All bounded arXiv routes failed: {errs}")

def compact(s): return re.sub(r"[^A-Z0-9]","",s.upper())

def main():
    raw,requested,final,ct=fetch()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    member=next((m for m in tf.getmembers() if m.isfile() and m.name.endswith("lsbohp7b.tex")),None)
    if member is None: raise RuntimeError("lsbohp7b.tex missing")
    text=tf.extractfile(member).read().decode("latin-1","ignore")
    lines=text.splitlines()
    exact_rows={g:[] for g in ALIASES}
    for i,line in enumerate(lines):
        c=compact(line)
        for g,aa in ALIASES.items():
            if any(compact(a) in c for a in aa):
                # Keep table-looking rows only; require ampersands and a parenthesized source code.
                if "&" in line and re.search(r"\([1-6]\)",line):
                    exact_rows[g].append({"line":i+1,"text":line})
    legend=[]
    gas=[]
    for i,line in enumerate(lines):
        if "References:" in line or (i>0 and "References:" in lines[i-1]):
            legend.append({"line":i+1,"text":line,"context":"\n".join(lines[max(0,i-3):min(len(lines),i+5)])})
        if "For the gas component we used" in line or ("HI" in compact(line) and "REFERENCESGIVENINTABLE1" in compact(" ".join(lines[max(0,i-1):i+3]))):
            gas.append({"line":i+1,"text":line,"context":"\n".join(lines[max(0,i-3):min(len(lines),i+8)])})
    result={
      "status":"DB02_TABLE1_HI_SOURCE_CODES_COMPLETE",
      "source":"de Blok & Bosma 2002 A&A 385 816; arXiv astro-ph/0201276",
      "transport":{"requested":requested,"final":final,"content_type":ct,"bytes":len(raw)},
      "target_rows":exact_rows,"reference_legend":legend,"gas_component_context":gas,
      "interpretation_rule":"dB02 says the gas component uses H I surface densities from Table 1 references; source codes are provenance pointers, not new dB02 H I measurements.",
      "boundary":"Provenance only; no profile extraction, raster digitization, normalization, persistence fitting, or blind outcomes."
    }
    missing=[g for g,r in exact_rows.items() if not r]
    if missing: result["missing_table_rows"]=missing
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"target_rows":exact_rows,"missing":missing},indent=2))
if __name__=="__main__": main()
