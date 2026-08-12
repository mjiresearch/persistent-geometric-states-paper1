#!/usr/bin/env python3
"""Audit Fraternali, Sancisi & Kamphuis (2011) H I profile source assets.

Frozen Lelli/SPARC branch: Fr11 -> NGC0891, NGC7814.
Paper: A&A 531 A64; arXiv:1105.3867.

The paper explicitly plots H I surface-density profiles in the middle panels of
its rotation-curve decomposition figure. This audit inspects the source package
for (a) original H I observation provenance, (b) machine-readable profile arrays,
and (c) native vector geometry for the decomposition figure.

PostScript/EPS is parsed as text/geometry operators only and never executed.
No raster digitization, normalization, persistence fitting, or blind outcomes.
"""
from __future__ import annotations

import hashlib,io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen

URLS=["https://arxiv.org/e-print/1105.3867","https://export.arxiv.org/e-print/1105.3867"]
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
OUT=Path("validation/stationary/fr11_hi_profile_source_asset_audit_v1.json")
TARGETS={"NGC0891":[r"NGC\s*891\b"],"NGC7814":[r"NGC\s*7814\b"]}


def fetch():
    attempts=[]
    for u in URLS:
        rec={"url":u}
        try:
            req=Request(u,headers={"User-Agent":UA,"Accept":"application/gzip,application/octet-stream,*/*;q=0.5"})
            with urlopen(req,timeout=120) as h:
                raw=h.read();final=h.geturl();ct=h.headers.get("Content-Type","")
            rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw)})
            attempts.append(rec);return raw,attempts
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"});attempts.append(rec)
    raise RuntimeError("No Fr11 arXiv source route: "+repr(attempts))


def ctx(lines,i,r=8):return "\n".join(lines[max(0,i-r):min(len(lines),i+r+1)])[:14000]

def token(b,t):return len(re.findall(rb"(?<![A-Za-z])"+re.escape(t)+rb"(?![A-Za-z])",b))

def psinfo(name,b):
    s=b.decode("latin-1","replace");comments=[x[:500] for x in s.splitlines() if x.startswith("%")][:120]
    strings=[]
    for raw in re.findall(rb"\(((?:\\.|[^\\)])*)\)",b):
        st=raw.decode("latin-1","replace")
        if st.strip():strings.append(st[:400])
    return {
      "name":name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),
      "bounding_boxes":[x for x in comments if "BoundingBox" in x][:10],
      "creator_lines":[x for x in comments if re.search(r"Creator|Producer|Title|CreationDate",x,re.I)][:20],
      "image_ops":token(b,b"image"),"colorimage_ops":token(b,b"colorimage"),"imagemask_ops":token(b,b"imagemask"),
      "moveto_ops":token(b,b"moveto"),"lineto_ops":token(b,b"lineto"),"curveto_ops":token(b,b"curveto"),"stroke_ops":token(b,b"stroke"),
      "show_ops":token(b,b"show"),"literal_strings":len(strings),
      "useful_strings":[x for x in strings if re.search(r"NGC|891|7814|HI|H I|Radius|kpc|pc|Gas|Bulge|Disk|surface|density",x,re.I)][:200]
    }

def main():
    raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    members=[];texts=[];graphics=[];data=[]
    for m in tf.getmembers():
        if not m.isfile():continue
        b=tf.extractfile(m).read();suffix=Path(m.name).suffix.lower()
        members.append({"name":m.name,"bytes":m.size,"suffix":suffix})
        if suffix in {".tex",".bbl",".bib",".txt",".dat",".tbl",".tab",".csv"}:
            texts.append((m.name,b.decode("latin-1","replace")))
        if suffix in {".ps",".eps"}:graphics.append(psinfo(m.name,b))
        if suffix in {".dat",".tbl",".tab",".csv",".fits",".fit",".fts"}:
            data.append({"name":m.name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})

    target_hits={g:[] for g in TARGETS};profile_hits=[];provenance=[];figure_refs=[];captions=[]
    for fn,text in texts:
        lines=text.splitlines()
        for i,line in enumerate(lines):
            for g,pats in TARGETS.items():
                if any(re.search(p,line,re.I) for p in pats):
                    target_hits[g].append({"file":fn,"line":i+1,"text":line[:3000],"context":ctx(lines,i,10)})
            if re.search(r"surface\s+density|surface-density|H\s*I\s*\(|HI\s*\(|gas\s+surface|middle panels?",line,re.I):
                profile_hits.append({"file":fn,"line":i+1,"text":line[:3000],"context":ctx(lines,i,8)})
            if re.search(r"observations?|data were|data are|H\s*I\s+data|HI\s+data|Oosterloo|Sancisi|Kamphuis|WSRT|VLA",line,re.I):
                provenance.append({"file":fn,"line":i+1,"text":line[:3000],"context":ctx(lines,i,7)})
            if re.search(r"includegraphics|epsfig|psfig",line,re.I):
                figure_refs.append({"file":fn,"line":i+1,"text":line[:3000],"context":ctx(lines,i,4)})
            if re.search(r"\\caption",line):captions.append({"file":fn,"line":i+1,"context":ctx(lines,i,5)})

    numeric=[]
    for fn,text in texts:
        if Path(fn).suffix.lower() not in {".dat",".tbl",".tab",".csv",".txt"}:continue
        if re.search(r"891|7814",text) and re.search(r"HI|H I|surface",text,re.I):
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?",text)
            numeric.append({"name":fn,"numeric_tokens":len(nums),"excerpt":text[:12000]})

    # Identify likely decomposition-figure assets by caption/figure-reference neighborhood.
    decomp_refs=[]
    for r in figure_refs:
        c=r["context"]
        if re.search(r"decompos|surface density|Gas|Bulge|Disk|Fig\.?\s*7|fig:decomp",c,re.I):decomp_refs.append(r)

    out={
      "status":"FR11_HI_PROFILE_SOURCE_ASSET_AUDIT_COMPLETE",
      "source":"Fraternali, Sancisi & Kamphuis 2011 A&A 531 A64",
      "arxiv":"1105.3867","targets":list(TARGETS),"transport_attempts":attempts,
      "source_bytes":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),"members":members,
      "data_like_assets":data,"numeric_target_profile_candidates":numeric,
      "target_text_hits":target_hits,"profile_language_hits":profile_hits[:300],"observation_provenance_hits":provenance[:400],
      "figure_references":figure_refs,"decomposition_figure_references":decomp_refs,"captions":captions,
      "postscript_assets":graphics,
      "decision_fields":{
        "machine_readable_target_profile_candidate":bool(numeric),
        "n_postscript_assets":len(graphics),
        "n_decomposition_figure_references":len(decomp_refs),
      },
      "promotion_rule":"Fr11 profile values may be promoted only if the H I middle panels are source-native numeric rows or unambiguously recoverable vector geometry with calibrated axes. Raster figures are not digitized.",
      "boundary":"Acquisition/provenance only. PostScript is parsed, never executed. No raster digitization, normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":out["status"],"data_assets":data,"numeric_candidates":numeric,
      "decomp_refs":decomp_refs,
      "graphics":[{"name":g["name"],"bytes":g["bytes"],"image":g["image_ops"],"lineto":g["lineto_ops"],"curveto":g["curveto_ops"],"strings":g["useful_strings"][:20]} for g in graphics]
    },indent=2))

if __name__=="__main__":main()
