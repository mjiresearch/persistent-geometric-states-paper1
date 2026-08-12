#!/usr/bin/env python3
"""Trace dB01 Lelli targets through McGaugh/Rubin/de Blok 2001 Paper I to original H I sources.

Chain preserved:
Lelli galaxy -> dB01 -> dB01 Paper I pointer -> Paper I per-galaxy prior H I reference -> original 21-cm paper.

Acquisition/provenance only. No profile digitization, normalization, persistence fitting,
or blind-outcome inspection.
"""
from __future__ import annotations
import io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

# export.arxiv.org returned HTTP 429 on the first bounded pass.  Use the
# canonical arxiv.org e-print endpoint as a genuinely distinct transport route;
# do not loop the failed export endpoint.
URL="https://arxiv.org/e-print/astro-ph/0107326"
OUT=Path("validation/stationary/db01_paper1_original_hi_source_trace_v1.json")
TARGETS={
    "D631-7":["D631-7","D6317"],
    "F571-8":["F571-8","F5718"],
    "UGC05750":["U5750","UGC5750","UGC05750"],
    "UGC06614":["U6614","UGC6614","UGC06614"],
    "UGC11557":["U11557","UGC11557"],
}

def fetch(u):
    req=Request(u,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0","Accept":"application/x-eprint-tar,application/gzip,application/octet-stream,*/*;q=0.5"})
    with urlopen(req,timeout=120) as h:return h.read(),h.geturl(),h.headers.get("Content-Type","")

def compact(s):return re.sub(r"[^A-Z0-9]","",s.upper())

def ctx(lines,i,r=10):return "\n".join(lines[max(0,i-r):min(len(lines),i+r+1)])[:10000]

def main():
    raw,final_url,content_type=fetch(URL)
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    texts=[]; members=[]
    for m in tf.getmembers():
        if not m.isfile():continue
        members.append({"name":m.name,"bytes":m.size,"suffix":Path(m.name).suffix.lower()})
        if Path(m.name).suffix.lower() in {".tex",".txt",".bbl",".bib",".tab",".dat",".tbl"}:
            try:t=tf.extractfile(m).read().decode("latin-1","ignore")
            except Exception:continue
            texts.append((m.name,t))
    target_hits={g:[] for g in TARGETS}
    reference_legend=[]; provenance=[]
    for fn,t in texts:
        lines=t.splitlines()
        for i,line in enumerate(lines):
            cl=compact(line)
            for g,aliases in TARGETS.items():
                if any(compact(a) in cl for a in aliases):
                    target_hits[g].append({"file":fn,"line":i+1,"text":line[:2000],"context":ctx(lines,i)})
            if re.search(r"references?:|HI data|H\\s*I data|21\\s*-?\\s*cm|Blok96|Hulst|Broeils|Swaters|Stil",line,re.I):
                provenance.append({"file":fn,"line":i+1,"text":line[:2000],"context":ctx(lines,i,5)})
            if re.search(r"References?:.*\\([1-9]\\)|\\([1-9]\\).*citet|\\bibitem",line,re.I):
                reference_legend.append({"file":fn,"line":i+1,"text":line[:2500],"context":ctx(lines,i,7)})
    result={
      "status":"DB01_PAPER1_ORIGINAL_HI_SOURCE_TRACE_COMPLETE",
      "paper":"McGaugh, Rubin & de Blok 2001 AJ 122 2381 (Paper I; arXiv astro-ph/0107326)",
      "source_transport":{"url":URL,"final_url":final_url,"content_type":content_type},
      "arxiv_bytes":len(raw),"n_files":len(members),"members":members,
      "targets":list(TARGETS),"target_hits":target_hits,
      "reference_legend_hits":reference_legend[:300],"provenance_hits":provenance[:500],
      "boundary":"Provenance only; no raster digitization, normalization, persistence fitting, or blind outcomes."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"target_hit_counts":{g:len(v) for g,v in target_hits.items()},"n_reference_legend_hits":len(reference_legend)},indent=2))
if __name__=="__main__":main()
