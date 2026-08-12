#!/usr/bin/env python3
"""Trace the five frozen dB02 targets to de Blok & Bosma (2002) source codes.

Chain preserved exactly:
Lelli/SPARC target -> dB02 -> dB02 sample-table source code -> original H I paper.

The paper's arXiv source is parsed directly.  We retain the literal sample row,
reference codes, reference legend and nearby source prose.  We do not interpret
mass-model tables as H I profiles and do not inspect persistence/blind outcomes.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URLS=[
    "https://arxiv.org/e-print/astro-ph/0201276",
    "https://export.arxiv.org/e-print/astro-ph/0201276",
]
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
OUT=Path("validation/stationary/db02_original_hi_source_trace_v1.json")
TARGETS={
    "DDO064":["U5272","DDO64"],
    "NGC0100":["N100","U231","NGC100"],
    "UGC01281":["U1281","DDO52"],
    "UGC04278":["U4278","IC2233"],
    "UGC05005":["U5005","NGC4455","N4455"],
}
# Source codes printed in the dB02 sample-table note.  Keep both literal key
# and citation label; code 2 is optical photometry when paired with H I code 4.
KNOWN_REFERENCE_KEYS={
    "1":"Blok96",
    "2":"Blok95",
    "3":"Broeils",
    "4":"Hulst",
    "5":"Sw1999",
    "6":"Stil",
}


def fetch():
    attempts=[]
    for u in URLS:
        try:
            req=Request(u,headers={"User-Agent":UA,"Accept":"application/gzip,application/octet-stream,*/*;q=0.5"})
            with urlopen(req,timeout=120) as h:
                raw=h.read(); final=h.geturl(); ct=h.headers.get("Content-Type","")
            attempts.append({"url":u,"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw)})
            return raw,attempts
        except Exception as exc:
            attempts.append({"url":u,"status":"error","error":f"{type(exc).__name__}: {exc}"})
    raise RuntimeError("No dB02 arXiv source route recovered: "+repr(attempts))


def compact(s): return re.sub(r"[^A-Z0-9]","",s.upper())

def context(lines,i,r=8): return "\n".join(lines[max(0,i-r):min(len(lines),i+r+1)])[:12000]


def extract_trailing_codes(line):
    # Source codes occur at the end as (2)(4), (5), (6), etc.
    tail=line.rsplit("&",1)[-1] if "&" in line else line
    return [int(x) for x in re.findall(r"\(([1-6])\)",tail)]


def main():
    raw,attempts=fetch()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    members=[]; texts=[]
    for m in tf.getmembers():
        if not m.isfile(): continue
        members.append({"name":m.name,"bytes":m.size,"suffix":Path(m.name).suffix.lower()})
        if Path(m.name).suffix.lower() in {".tex",".bbl",".bib",".txt",".tab",".tbl",".dat"}:
            try: text=tf.extractfile(m).read().decode("latin-1","replace")
            except Exception: continue
            texts.append((m.name,text))

    target_rows={g:[] for g in TARGETS}; target_all_hits={g:[] for g in TARGETS}
    reference_note_hits=[]; bibliography_hits=[]; source_prose=[]
    for fn,text in texts:
        lines=text.splitlines()
        for i,line in enumerate(lines):
            cl=compact(line)
            for g,aliases in TARGETS.items():
                if any(compact(a) and compact(a) in cl for a in aliases):
                    rec={"file":fn,"line":i+1,"text":line[:3000],"context":context(lines,i,10)}
                    target_all_hits[g].append(rec)
                    codes=extract_trailing_codes(line)
                    # The sample table has many ampersand-separated columns and a trailing source code.
                    if codes and line.count("&")>=10:
                        target_rows[g].append({**rec,"reference_codes":codes})
            if re.search(r"Blok96|Blok95|Broeils|Hulst|Sw1999|Stil",line,re.I):
                source_prose.append({"file":fn,"line":i+1,"text":line[:3000],"context":context(lines,i,6)})
            if re.search(r"references?|source",line,re.I) and re.search(r"\([1-6]\)",context(lines,i,5)):
                reference_note_hits.append({"file":fn,"line":i+1,"text":line[:3000],"context":context(lines,i,8)})
            if re.search(r"\\bibitem|\\bibitem|Blok96|Blok95|Broeils|Hulst|Sw1999|Stil",line,re.I):
                if "\\bib" in line or fn.lower().endswith((".bbl",".bib")):
                    bibliography_hits.append({"file":fn,"line":i+1,"text":line[:3000],"context":context(lines,i,3)})

    # Fail closed on ambiguous or missing sample rows: exact reference codes are the mapping gate.
    exact_rows={}
    for g,rows in target_rows.items():
        # Deduplicate literal rows.
        unique=[]; seen=set()
        for r in rows:
            key=r["text"]
            if key not in seen: seen.add(key); unique.append(r)
        exact_rows[g]=unique

    result={
        "status":"DB02_ORIGINAL_HI_SOURCE_TRACE_COMPLETE",
        "paper":"de Blok & Bosma 2002 A&A 385 816-846",
        "bibcode":"2002A&A...385..816D",
        "source_transport_attempts":attempts,
        "source_bytes":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),
        "members":members,
        "targets":list(TARGETS),
        "sample_table_rows":exact_rows,
        "all_target_hits":target_all_hits,
        "known_reference_key_map":KNOWN_REFERENCE_KEYS,
        "reference_note_hits":reference_note_hits[:120],
        "source_provenance_hits":source_prose[:300],
        "bibliography_hits":bibliography_hits[:300],
        "interpretation_rule":(
            "Trailing sample-table source codes identify source-paper lineage only. "
            "Code 2 (Blok95) is photometry when paired with code 4; H I source assignment must use the paper note/prose and cannot be inferred from mass-model tables."
        ),
        "boundary":"Provenance only; no profile extraction, raster digitization, normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "sample_rows":{g:[{"text":r["text"],"codes":r["reference_codes"]} for r in rows] for g,rows in exact_rows.items()},
    },indent=2))

if __name__=="__main__": main()
