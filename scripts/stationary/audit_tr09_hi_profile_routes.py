#!/usr/bin/env python3
"""Audit Trachternach+2009 (Tr09; arXiv:0907.5533) for exact radial HI profiles.

Frozen targets: D564-8 and D631-7 (calibration only).

This is a bounded acquisition audit. It inventories the arXiv source package,
searches text/tabular assets for target-specific radius-vs-HI-surface-density
content, and statically classifies target-relevant PS/EPS assets as vector or
raster-dominant. PostScript is never executed and figures are never digitized.
"""
from __future__ import annotations

import hashlib, io, json, re, tarfile, urllib.request
from pathlib import Path

URLS = [
    "https://arxiv.org/e-print/0907.5533",
    "https://export.arxiv.org/e-print/0907.5533",
]
UA = "Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
TARGETS = ["D564-8", "D631-7"]
OUT = Path("validation/stationary/tr09_hi_profile_route_audit_v1.json")

TEXT_EXT = {".tex", ".txt", ".dat", ".tbl", ".csv", ".tab", ".lis", ".out"}
TABULAR_EXT = {".txt", ".dat", ".tbl", ".csv", ".tab"}
GRAPHIC_EXT = {".eps", ".ps"}


def fetch():
    attempts=[]
    for u in URLS:
        rec={"url":u}
        try:
            req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"application/gzip,application/octet-stream,*/*;q=0.5"})
            with urllib.request.urlopen(req,timeout=180) as h:
                raw=h.read(); rec.update(status="fetched",final_url=h.geturl(),content_type=h.headers.get("Content-Type",""),bytes=len(raw)); attempts.append(rec); return raw,attempts
        except Exception as e:
            rec.update(status="error",error=f"{type(e).__name__}: {e}"); attempts.append(rec)
    raise RuntimeError("Tr09 arXiv source fetch failed")


def target_forms(t):
    c=re.sub(r"[^A-Z0-9]","",t.upper())
    return {c,t.upper(),t.replace("-","").upper(),t.replace("-"," ").upper()}


def compact(s): return re.sub(r"[^A-Z0-9]","",s.upper())


def text_hits(text, target):
    lines=text.splitlines(); forms=target_forms(target); out=[]
    for i,line in enumerate(lines,1):
        if compact(target) in compact(line):
            lo=max(1,i-3); hi=min(len(lines),i+5)
            out.append({"line":i,"context":"\n".join(f"{j}: {lines[j-1]}" for j in range(lo,hi+1))[:5000]})
    return out[:50]


def profile_language(text):
    low=text.lower().replace("h~i","hi")
    pats=["surface density","column density","radial profile","radial distribution","azimuthal","rings","m_sun pc","msun pc","atoms cm"]
    return [p for p in pats if p in low]


def numeric_profile_candidate(text,target):
    # Conservative textual signal only: target context plus profile language plus repeated numeric rows.
    if compact(target) not in compact(text): return False
    if not profile_language(text): return False
    numeric_rows=sum(bool(re.match(r"^\s*[-+]?\d+(?:\.\d+)?(?:\s+|[,&])[-+]?\d",ln)) for ln in text.splitlines())
    return numeric_rows >= 5


def ps_audit(b):
    return {
        "bytes":len(b),
        "sha256":hashlib.sha256(b).hexdigest(),
        "image_ops":len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])",b)),
        "colorimage_ops":b.count(b"colorimage"),
        "imagemask_ops":b.count(b"imagemask"),
        "moveto_tokens":b.count(b"moveto") + len(re.findall(rb"(?<![A-Za-z])M(?![A-Za-z])",b)),
        "lineto_tokens":b.count(b"lineto") + len(re.findall(rb"(?<![A-Za-z])R(?![A-Za-z])",b)) + len(re.findall(rb"(?<![A-Za-z])P(?![A-Za-z])",b)),
        "curveto_tokens":b.count(b"curveto"),
        "showpage_tokens":b.count(b"showpage"),
    }


def main():
    raw,attempts=fetch(); tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    members=[m for m in tf.getmembers() if m.isfile()]
    assets=[]; texts={}; graphics={}
    for m in members:
        b=tf.extractfile(m).read(); ext=Path(m.name).suffix.lower()
        rec={"name":m.name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"ext":ext}
        if ext in TEXT_EXT:
            txt=b.decode("latin-1","replace"); texts[m.name]=txt
            rec.update({"profile_language":profile_language(txt),"targets_found":[t for t in TARGETS if compact(t) in compact(txt)]})
        if ext in GRAPHIC_EXT:
            graphics[m.name]=b; rec["ps_audit"]=ps_audit(b)
        assets.append(rec)

    per={}
    for t in TARGETS:
        th=[]; tabs=[]
        for name,txt in texts.items():
            hits=text_hits(txt,t)
            if hits: th.append({"asset":name,"hits":hits,"profile_language":profile_language(txt)})
            if Path(name).suffix.lower() in TABULAR_EXT and numeric_profile_candidate(txt,t):
                tabs.append(name)
        # target-specific graphics are identified by target string in filename OR explicit includegraphic proximity in TeX contexts.
        gnames=set()
        tc=compact(t)
        for name in graphics:
            if tc in compact(name): gnames.add(name)
        for name,txt in texts.items():
            if Path(name).suffix.lower() != ".tex": continue
            lines=txt.splitlines()
            for i,line in enumerate(lines):
                if tc not in compact(line): continue
                for j in range(max(0,i-12),min(len(lines),i+13)):
                    for mm in re.finditer(r"(?:includegraphics(?:\[[^\]]*\])?\{|epsfig\{[^}]*file=)([^},]+)",lines[j],re.I):
                        base=mm.group(1).strip()
                        candidates=[base,base+".eps",base+".ps"]
                        for c in candidates:
                            for gn in graphics:
                                if gn==c or Path(gn).name==Path(c).name: gnames.add(gn)
        per[t]={
            "text_contexts":th,
            "numeric_tabular_profile_candidates":sorted(set(tabs)),
            "target_relevant_graphics":[{"name":g,"audit":ps_audit(graphics[g])} for g in sorted(gnames)],
        }

    result={
        "status":"TR09_HI_PROFILE_ROUTE_AUDIT_COMPLETE",
        "source":"Trachternach et al. 2009 A&A 505 577; arXiv:0907.5533",
        "targets":TARGETS,
        "source_fetch_attempts":attempts,
        "source_package_sha256":hashlib.sha256(raw).hexdigest(),
        "n_assets":len(assets),
        "assets":assets,
        "per_target":per,
        "decision_fields":{
            "any_numeric_tabular_profile_candidate":any(v["numeric_tabular_profile_candidates"] for v in per.values()),
            "any_target_relevant_graphic":any(v["target_relevant_graphics"] for v in per.values()),
        },
        "external_crosscheck":"Hua et al. 2025 (A&A 703 A223; arXiv:2510.17770) independently states that D564-8 and D631-7 are among six SPARC galaxies whose HI rotation-curve references do not provide HI surface-density profiles.",
        "boundary":"Source-package audit only. No OCR, raster digitization, moment-map/cube reconstruction, normalization, persistence fitting, or blind-outcome inspection. L_A and C_A remain locked."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"n_assets":result["n_assets"],"decision_fields":result["decision_fields"],"targets":{t:{"n_text_contexts":len(v["text_contexts"]),"numeric":v["numeric_tabular_profile_candidates"],"graphics":[g["name"] for g in v["target_relevant_graphics"]]} for t,v in per.items()}},indent=2))

if __name__=="__main__": main()
