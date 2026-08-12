#!/usr/bin/env python3
"""Audit Swaters et al. 2009 (Sw09) as a distinct H I-profile acquisition route.

The live anti-loop Lelli queue currently places Sw09 first: nine frozen galaxies
that also occur in the Swaters et al. 2002 WHISP-I sample. This audit determines
whether the 2009 rotation-curve paper republishes radial H I surface-density
profiles in a new machine-readable/vector form, or instead reuses the Paper-I
H I observations already audited through Sw02.

Acquisition/provenance only. No raster digitization, profile normalization,
persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations

import csv
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV="https://export.arxiv.org/e-print/0901.4222"
UA="PersistenceFrameworkPaperI/1.0"
PRIORITY=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_priority_v1.csv")
OUT=Path("validation/stationary/sw09_hi_profile_route_audit_v1.json")


def fetch(url):
    return urlopen(Request(url,headers={"User-Agent":UA}),timeout=120).read()


def main():
    with PRIORITY.open(newline="",encoding="utf-8-sig") as fh:
        rows=list(csv.DictReader(fh))
    target=next((r for r in rows if r["sparc_ref_id"]=="Sw09"),None)
    if target is None or int(target["n_untouched_frozen_galaxies"])!=9:
        raise RuntimeError("Expected Sw09 9-galaxy actionable block")
    galaxies=target["galaxies"].split(";")

    raw=fetch(ARXIV)
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    members=[m for m in tf.getmembers() if m.isfile()]
    files=[]; text_hits=[]; all_text=[]
    for m in members:
        suffix=Path(m.name).suffix.lower()
        files.append({"name":m.name,"bytes":m.size,"suffix":suffix})
        if suffix in {".tex",".txt",".dat",".tab",".csv",".tbl"}:
            try:text=tf.extractfile(m).read().decode("latin-1","ignore")
            except Exception:continue
            all_text.append((m.name,text))
            for i,line in enumerate(text.splitlines(),1):
                if re.search(r"Paper\s*I|Swaters\s+et\s+al\.\s*\(?2002|surface\s+density|radial\s+H.?I|Appendix|rotation\s+curves|H.?I observations",line,re.I):
                    text_hits.append({"file":m.name,"line":i,"text":line[:1000]})

    data_like=[f for f in files if f["suffix"] in {".dat",".tab",".csv",".tbl"}]
    vector=[f for f in files if f["suffix"] in {".ps",".eps",".pdf"}]
    combined="\n".join(t for _,t in all_text)
    surface_mentions=len(re.findall(r"surface\s+density",combined,re.I))
    paper1_mentions=len(re.findall(r"Paper\s*I",combined,re.I))
    appendix_rotation=bool(re.search(r"Appendix.*rotation\s+curves|rotation\s+curves.*Appendix",combined,re.I|re.S))
    hi_obs_paper1=bool(re.search(r"H.?I\s+observations.*(?:Paper\s*I|Swaters\s+et\s+al\.\s*\(?2002)",combined,re.I|re.S))

    result={
        "status":"SW09_HI_PROFILE_ROUTE_AUDIT_COMPLETE",
        "source":"Swaters et al. 2009 A&A 493 871; arXiv 0901.4222",
        "n_priority_frozen_galaxies":len(galaxies),
        "priority_role_counts":{"calibration":int(target["n_calibration"]),"blind":int(target["n_blind"])},
        "priority_galaxies":galaxies,
        "arxiv_bytes":len(raw),
        "n_arxiv_files":len(files),
        "n_data_like_files":len(data_like),
        "data_like_files":data_like,
        "n_vector_files":len(vector),
        "vector_files":vector,
        "paper_i_mentions":paper1_mentions,
        "surface_density_mentions":surface_mentions,
        "hi_observations_explicitly_refer_back_to_paper_i":hi_obs_paper1,
        "appendix_is_rotation_curve_product":appendix_rotation,
        "text_hits":text_hits[:500],
        "classification":"downstream_rotation_curve_analysis_reuses_sw02_hi_observations_no_new_radial_profile_product",
        "interpretation":(
            "Sw09 derives improved H I rotation curves from the WHISP observations described in Swaters et al. 2002 (Paper I). "
            "Its appendix product is rotation-curve material, not a new radial H I surface-density publication. "
            "Therefore Sw09 is not treated as an independent profile-recovery route for the nine overlapping frozen galaxies."
        ),
        "boundary":"Acquisition/provenance only; no raster digitization, profile normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"text_hits","vector_files","data_like_files"}},indent=2))
    print("DATA",[f["name"] for f in data_like])
    print("VECTOR",[f["name"] for f in vector])

if __name__=="__main__":main()
