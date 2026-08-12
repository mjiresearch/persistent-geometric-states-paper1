#!/usr/bin/env python3
"""One-pass audit of public Verheijen & Sancisi (2001) atlas source assets.

Live Paper I source family: SPARC Ref IDs VS01 / SV98.
This script performs acquisition-route inspection only. It does not digitize,
normalize, interpolate, or fit any persistence quantity.

The A&A PostScript endpoint returned HTTP 403 to the GitHub runner on the first
bounded audit. Per the project's no-loop rule, that route is recorded as closed
and is not requested again here. This pass uses only the successful arXiv source
package route.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen

ARXIV = "https://export.arxiv.org/e-print/astro-ph/0101404"
UA = "PersistenceFrameworkPaperI/1.0"


def get(url: str) -> tuple[bytes, str]:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=90) as r:
        return r.read(), r.headers.get("Content-Type", "")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def text_hits(text: str) -> list[dict]:
    pats = re.compile(r"surface density|surface-density|Sigma|helium|1\.33|1\.4|radial.*H.?I|H.?I.*radial|atlas|column density", re.I)
    out=[]
    for i,line in enumerate(text.splitlines(),1):
        if pats.search(line):
            out.append({"line":i,"text":line[:700]})
    return out[:300]


def audit_arxiv(raw: bytes) -> dict:
    result={"bytes":len(raw),"sha256":sha(raw),"files":[],"text_hits":[],"candidate_profile_assets":[]}
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    for m in tf.getmembers():
        if not m.isfile():
            continue
        suffix=Path(m.name).suffix.lower()
        rec={"name":m.name,"bytes":m.size,"suffix":suffix}
        result["files"].append(rec)
        low=m.name.lower()
        if suffix in {".eps",".ps",".pdf",".fig"} and any(k in low for k in ("atlas","surf","dens","prof","hi","gal","fig","app")):
            result["candidate_profile_assets"].append(rec)
        if suffix in {".tex",".txt",".dat",".tbl"}:
            try:
                text=tf.extractfile(m).read().decode("latin-1",errors="replace")
            except Exception:
                continue
            hits=text_hits(text)
            if hits:
                result["text_hits"].append({"file":m.name,"hits":hits})
    result["n_files"]=len(result["files"])
    result["n_candidate_profile_assets"]=len(result["candidate_profile_assets"])
    return result


def main() -> None:
    arxiv_raw, arxiv_ct=get(ARXIV)
    arxiv=audit_arxiv(arxiv_raw)
    out={
        "status":"VS01_ARXIV_ASSET_AUDIT_COMPLETE",
        "source":"Verheijen & Sancisi 2001 A&A 370 765-867; arXiv astro-ph/0101404",
        "arxiv_url":ARXIV,"arxiv_content_type":arxiv_ct,"arxiv":arxiv,
        "aanda_postscript_route":"CLOSED_AFTER_FIRST_PASS_HTTP_403_FROM_GITHUB_RUNNER_NO_RETRY",
        "interpretation_boundary":"Asset/provenance audit only. No profile values, source geometry, helium scaling, interpolation, persistence parameters, or blind outcomes changed or evaluated."
    }
    p=Path("validation/stationary/vs01_ursa_major_public_asset_audit_v1.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "arxiv_n_files":arxiv["n_files"],
        "arxiv_candidates":arxiv["candidate_profile_assets"],
        "text_hit_files":[x["file"] for x in arxiv["text_hits"]],
        "aanda_postscript_route":out["aanda_postscript_route"],
    },indent=2))


if __name__=="__main__":
    main()
