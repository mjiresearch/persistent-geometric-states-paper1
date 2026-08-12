#!/usr/bin/env python3
"""Audit public numerical/vector routes for Verheijen & Sancisi (2001) UMa HI profiles.

This is the highest-yield untouched Lelli/SPARC source family: 27 frozen
Paper-I galaxies currently have no public-source overlay and cite VS01/SV98.
The audit inspects the arXiv source package and CDS catalog structure for
reusable profile assets without digitizing raster figures or fitting any model.
"""
from __future__ import annotations

import csv, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV="https://export.arxiv.org/e-print/astro-ph/0101404"
UA="PersistenceFrameworkPaperI/1.0"
PRIORITY=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT=Path("validation/stationary/verheijen2001_uma_public_route_audit_v1.json")


def fetch(url):
    return urlopen(Request(url,headers={"User-Agent":UA}),timeout=120).read()


def main():
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:
        pr=list(csv.DictReader(fh))
    target=next((r for r in pr if r["sparc_ref_id"]=="VS01"),None)
    if target is None or int(target["n_untouched_frozen_galaxies"])!=27:
        raise RuntimeError("Expected VS01 27-galaxy priority block")
    galaxies=target["galaxies"].split(";")

    raw=fetch(ARXIV)
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    members=[m for m in tf.getmembers() if m.isfile()]
    files=[]; text_hits=[]
    vector_ext={".eps",".ps",".pdf"}
    raster_ext={".png",".jpg",".jpeg",".gif",".tif",".tiff"}
    profile_words=re.compile(r"surface\s*density|sigma.?hi|hi.?profile|radial.?profile|atlas|includegraphics|epsfig",re.I)
    for m in members:
        suffix=Path(m.name).suffix.lower()
        files.append({"name":m.name,"bytes":m.size,"suffix":suffix,"vector":suffix in vector_ext,"raster":suffix in raster_ext})
        if suffix in {".tex",".txt",".dat",".tab",".csv",".sty"}:
            try: text=tf.extractfile(m).read().decode("latin-1","ignore")
            except Exception: continue
            for i,line in enumerate(text.splitlines(),1):
                if profile_words.search(line):
                    text_hits.append({"file":m.name,"line":i,"text":line[:700]})

    vec=[f for f in files if f["vector"]]
    ras=[f for f in files if f["raster"]]
    dat=[f for f in files if f["suffix"] in {".dat",".tab",".csv",".txt"}]
    candidate=[f for f in files if re.search(r"prof|surf|dens|atlas|hi|fig|gal",f["name"],re.I)]

    summary={
        "status":"VERHEIJEN2001_UMA_PUBLIC_ROUTE_AUDIT_COMPLETE",
        "source":"Verheijen & Sancisi 2001 A&A 370 765; arXiv astro-ph/0101404; CDS J/A+A/370/765",
        "n_priority_frozen_galaxies":len(galaxies),
        "priority_role_counts":{"calibration":int(target["n_calibration"]),"blind":int(target["n_blind"])},
        "priority_galaxies":galaxies,
        "arxiv_bytes":len(raw),
        "n_arxiv_files":len(files),
        "n_vector_files":len(vec),
        "n_raster_files":len(ras),
        "n_data_like_files":len(dat),
        "vector_files":vec,
        "data_like_files":dat,
        "candidate_named_assets":candidate,
        "text_hits":text_hits[:250],
        "cds_known_tables":[
            "table1: UMa membership/sample (52 rows)",
            "table2: photometry (52 rows)",
            "table3: global HI widths/fluxes comparison (57 rows)",
            "table4: rotation curves (437 rows)",
            "table5: HI synthesis literature/results (43 rows)",
        ],
        "interpretation":"The paper explicitly publishes radial HI surface-density profiles in its atlas, but CDS does not expose them as a numeric radial-SigmaHI table. This audit determines whether the arXiv package supplies vector/profile assets suitable for reproducible extraction.",
        "boundary":"Acquisition-route audit only. No raster digitization, source normalization, helium conversion, persistence fitting, or blind-outcome inspection.",
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k not in {"vector_files","candidate_named_assets","text_hits"}},indent=2))
    print("VECTOR_FILES",[f["name"] for f in vec])
    print("DATA_FILES",[f["name"] for f in dat])

if __name__=="__main__": main()
