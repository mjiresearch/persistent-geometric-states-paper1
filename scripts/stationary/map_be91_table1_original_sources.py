#!/usr/bin/env python3
"""Map Be91 frozen galaxies to Table-1 original 21-cm source codes.

Begeman, Broeils & Sanders (1991) Table 1 explicitly defines reference numbers
for the photometry and 21-cm rotation curve. We recover the ADS scan and use
native PDF word coordinates to reconstruct the target rows, preserving the row
geometry and the numbered source legend for auditability.

No OCR, raster digitization, profile extraction, persistence fitting, or blind
outcome inspection occurs.
"""
from __future__ import annotations
import csv, json, re
from pathlib import Path
from urllib.request import Request,urlopen
import pymupdf

PDF="https://articles.adsabs.harvard.edu/pdf/1991MNRAS.249..523B"
UA="PersistenceFrameworkPaperI/1.0"
PRIORITY=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUTCSV=Path("data/stationary/source_reconstruction/be91_original_hi_source_map_v1.csv")
OUTJSON=Path("validation/stationary/be91_original_hi_source_map_v1_summary.json")
LEGEND={
 1:"Begeman (1987)",
 2:"Broeils (1990)",
 3:"Carignan, Sancisi & van Albada (1988)",
 4:"Carignan & Beaulieu (1989)",
 5:"Kent (1987)",
 6:"Lake, Schommer & van Gorkom (1990)",
 7:"Wevers, van der Kruit & Allen (1986)",
}

def fetch():
    req=Request(PDF,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
    with urlopen(req,timeout=120) as h:return h.read()

def compact(s):return re.sub(r"[^A-Z0-9]","",s.upper())

def row_candidates(page,target):
    words=page.get_text("words")
    # Group words by approximate baseline y; native scan has one row per galaxy.
    groups=[]
    for w in words:
        x0,y0,x1,y1,text,*_=w
        placed=False
        for g in groups:
            if abs(g["y"]-y0)<2.2:
                g["words"].append((x0,y0,x1,y1,text));g["y"]=(g["y"]+y0)/2;placed=True;break
        if not placed:groups.append({"y":y0,"words":[(x0,y0,x1,y1,text)]})
    ct=compact(target)
    out=[]
    for g in groups:
        ws=sorted(g["words"],key=lambda z:z[0]); txt=" ".join(z[4] for z in ws)
        if ct in compact(txt):
            out.append({"y":round(g["y"],3),"text":txt,"words":[{"x0":round(z[0],2),"x1":round(z[2],2),"text":z[4]} for z in ws]})
    return out

def main():
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:rows=list(csv.DictReader(fh))
    p=next((r for r in rows if r["sparc_ref_id"]=="Be91"),None)
    if p is None or int(p["n_untouched_frozen_galaxies"])!=5:raise RuntimeError("Expected Be91 5-galaxy block")
    targets=p["galaxies"].split(";")
    raw=fetch();doc=pymupdf.open(stream=raw,filetype="pdf")
    table_pages=[]
    for i,page in enumerate(doc):
        text=page.get_text("text")
        if "Table 1" in text and "references for photometry and 21-cm rotation curve" in text:
            table_pages.append(i)
    if not table_pages:
        # legend and table can straddle extraction; accept page containing Table 1 plus nearby page.
        for i,page in enumerate(doc):
            if "Table 1" in page.get_text("text"):table_pages.extend([i,min(i+1,len(doc)-1)])
        table_pages=sorted(set(table_pages))
    audits=[]
    for t in targets:
        display=t
        m=re.match(r"(NGC|UGC|DDO)0*(\d+)$",t)
        if m:display=m.group(1)+" "+str(int(m.group(2)))
        cand=[]
        for pi in table_pages:
            for r in row_candidates(doc[pi],display):cand.append({"page":pi+1,**r})
        audits.append({"galaxy":t,"display":display,"candidates":cand})

    # Determine the rightmost single-digit code in the native target row. For robustness,
    # only accept 1..7 and retain all row words for independent verification.
    output=[]
    for a in audits:
        codes=[]
        for c in a["candidates"]:
            for w in c["words"]:
                s=w["text"].strip().strip(",.;")
                if re.fullmatch(r"[1-7]",s):codes.append((w["x0"],int(s),c["page"],c["text"]))
        # The source-reference column is the rightmost eligible 1..7 in the row.
        best=max(codes,key=lambda z:z[0]) if codes else None
        output.append({
          "galaxy":a["galaxy"],"be91_reference_number":"" if best is None else best[1],
          "cited_source":"" if best is None else LEGEND[best[1]],
          "table_page":"" if best is None else best[2],
          "mapping_status":"mapped_from_native_table1_geometry" if best else "unresolved_table_geometry",
        })

    OUTCSV.parent.mkdir(parents=True,exist_ok=True)
    with OUTCSV.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    summary={
      "status":"BE91_TABLE1_ORIGINAL_HI_SOURCE_MAP_COMPLETE",
      "source":"Begeman, Broeils & Sanders 1991 MNRAS 249 523-537; ADS scan",
      "reference_legend":{str(k):v for k,v in LEGEND.items()},
      "table_pages_1based":[x+1 for x in table_pages],
      "n_targets":len(targets),"n_mapped":sum(r["mapping_status"].startswith("mapped") for r in output),
      "map":output,"native_row_geometry_audit":audits,
      "interpretation_boundary":"These are Be91's own Table-1 references for photometry and 21-cm rotation curves. They identify acquisition sources but do not themselves prove each cited paper exposes radial Sigma_HI numerically.",
      "boundary":"Native PDF text/geometry only; no OCR, raster digitization, profile extraction, persistence fitting, or blind outcomes."
    }
    OUTJSON.parent.mkdir(parents=True,exist_ok=True);OUTJSON.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":summary["status"],"n_mapped":summary["n_mapped"],"map":output},indent=2))
if __name__=="__main__":main()
