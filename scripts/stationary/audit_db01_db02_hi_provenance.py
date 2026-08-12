#!/usr/bin/env python3
"""Audit de Blok 2001 (dB01) and de Blok & Bosma 2002 (dB02) H I provenance.

These are the two highest-yield actionable Lelli/SPARC reference families after
anti-loop filtering. Both are high-resolution optical/rotation-curve analyses;
this audit determines, target by target, which earlier 21-cm H I observations,
H I surface-density data, or published gas mass models they actually use.

The script inventories the public arXiv source packages, captures target-specific
contexts and reference/source language, and records data/vector/raster assets.
It does not assume a rotation-curve table is a radial H I profile.

Acquisition/provenance only. No raster digitization, inverse disk reconstruction,
helium correction, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations

import csv
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

UA = "PersistenceFrameworkPaperI/1.0"
SOURCES = {
    "dB01": {
        "arxiv": "https://export.arxiv.org/e-print/astro-ph/0107366",
        "citation": "de Blok, McGaugh & Rubin 2001 AJ 122 2396",
    },
    "dB02": {
        "arxiv": "https://export.arxiv.org/e-print/astro-ph/0201276",
        "citation": "de Blok & Bosma 2002 A&A 385 816",
    },
}
PRIORITY = Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT = Path("validation/stationary/db01_db02_hi_provenance_audit_v1.json")


def fetch(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=120) as h:
        return h.read()


def compact(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def variants(g: str) -> set[str]:
    c = compact(g)
    out = {c}
    m = re.match(r"(NGC|UGC|DDO|D|F)0*(\d+)(.*)$", c)
    if m:
        p, n, tail = m.groups()
        n2 = str(int(n))
        out |= {p + n2 + tail, p + n2.zfill(5) + tail}
    return out


def context(lines: list[str], i: int, radius: int = 6) -> str:
    return "\n".join(lines[max(0, i-radius):min(len(lines), i+radius+1)])[:7000]


def audit_one(ref_id: str, targets: list[str]) -> dict:
    meta = SOURCES[ref_id]
    raw = fetch(meta["arxiv"])
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:*")
    members = [m for m in tf.getmembers() if m.isfile()]
    files=[]; texts=[]
    for m in members:
        suffix=Path(m.name).suffix.lower()
        rec={
            "name":m.name,"bytes":m.size,"suffix":suffix,
            "data_like":suffix in {".dat",".tab",".csv",".txt",".tbl",".fits",".fit"},
            "vector":suffix in {".eps",".ps",".pdf"},
            "raster":suffix in {".png",".jpg",".jpeg",".gif",".tif",".tiff"},
        }
        files.append(rec)
        if suffix in {".tex",".txt",".dat",".tab",".csv",".tbl"}:
            try: txt=tf.extractfile(m).read().decode("latin-1","ignore")
            except Exception: continue
            texts.append((m.name,txt))

    target_hits={g:[] for g in targets}
    source_hits=[]
    pattern=re.compile(
        r"21\s*-?\s*cm|H\s*I\s+(?:data|observ|surface|distribution|profile)|"
        r"gas\s+(?:mass|surface|distribution|contribution)|surface\s+density|"
        r"mass\s+model|previous|published|de\s+Blok|van\s+der\s+Hulst|"
        r"McGaugh|Swaters|Broeils|Begeman|Bosma|Carignan|Wevers|references?",
        re.I,
    )
    for fname,txt in texts:
        lines=txt.splitlines()
        for i,line in enumerate(lines):
            if pattern.search(line):
                source_hits.append({"file":fname,"line":i+1,"text":line[:1500],"context":context(lines,i,4)})
            cl=compact(line)
            for g in targets:
                if any(v and v in cl for v in variants(g)):
                    target_hits[g].append({"file":fname,"line":i+1,"text":line[:1500],"context":context(lines,i,8)})

    vector_structure=[]
    for f in files:
        if not f["vector"]: continue
        try:b=tf.extractfile(f["name"]).read()
        except Exception:continue
        vector_structure.append({
            "name":f["name"],"bytes":len(b),
            "image_ops":len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])",b)),
            "colorimage_ops":b.count(b"colorimage"),"imagemask_ops":b.count(b"imagemask"),
            "moveto_tokens":b.count(b"moveto"),"lineto_tokens":b.count(b"lineto"),
            "curveto_tokens":b.count(b"curveto"),"stroke_tokens":b.count(b"stroke"),
        })

    return {
        "ref_id":ref_id,"citation":meta["citation"],"arxiv":meta["arxiv"],
        "arxiv_bytes":len(raw),"n_files":len(files),
        "data_like_files":[f for f in files if f["data_like"]],
        "vector_files":[f for f in files if f["vector"]],
        "raster_files":[f for f in files if f["raster"]],
        "vector_structure":vector_structure,
        "target_text_hits":target_hits,
        "n_targets_named":sum(bool(v) for v in target_hits.values()),
        "source_provenance_hits":source_hits[:1200],
    }


def main() -> None:
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:
        rows=list(csv.DictReader(fh))
    targets={}
    for rid,n in (("dB01",5),("dB02",5)):
        r=next((x for x in rows if x["sparc_ref_id"]==rid),None)
        if r is None or int(r["n_untouched_frozen_galaxies"])!=n:
            raise RuntimeError(f"Expected {rid} {n}-galaxy actionable block")
        targets[rid]={
            "galaxies":r["galaxies"].split(";"),
            "calibration":int(r["n_calibration"]),"blind":int(r["n_blind"]),
        }

    audits=[]
    for rid in ("dB01","dB02"):
        a=audit_one(rid,targets[rid]["galaxies"])
        a["priority_role_counts"]={"calibration":targets[rid]["calibration"],"blind":targets[rid]["blind"]}
        audits.append(a)

    result={
        "status":"DB01_DB02_HI_PROVENANCE_AUDIT_COMPLETE",
        "audits":audits,
        "interpretation_rule":(
            "A cited H I observation or gas mass model is an acquisition pointer, not automatically a radial Sigma_HI profile. "
            "Each target must be resolved to the earliest defensible observing/profile source before promotion."
        ),
        "boundary":"Acquisition/provenance only; no raster digitization, inverse disk reconstruction, helium correction, persistence fitting, or blind outcomes."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "families":[{
            "ref_id":a["ref_id"],"targets":targets[a["ref_id"]]["galaxies"],
            "n_files":a["n_files"],"n_data_like":len(a["data_like_files"]),
            "n_vector":len(a["vector_files"]),"n_targets_named":a["n_targets_named"]
        } for a in audits]
    },indent=2))

if __name__=="__main__":main()
