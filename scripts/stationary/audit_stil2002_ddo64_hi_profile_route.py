#!/usr/bin/env python3
"""Audit Stil & Israel (2002) Paper I as the public Stil-1999 DDO64 route.

Frozen provenance chain:
Lelli/SPARC DDO064 -> dB02 Table 1 code (6) -> Stil 1999 PhD thesis ->
Stil & Israel 2002, "Neutral hydrogen in dwarf galaxies I. The spatial
distribution of HI" (astro-ph/0203128).

This audit asks one narrow acquisition question: does the public Paper-I source
package expose an exact radial H I surface-density profile for DDO64/UGC5272,
either as machine-readable rows or native vector geometry?  A 2-D column-density
map or summary scalar is not a radial profile.

No PostScript is executed. No raster digitization, profile inference,
normalization, persistence fitting, or blind-outcome inspection.
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
    "https://arxiv.org/e-print/astro-ph/0203128",
    "https://export.arxiv.org/e-print/astro-ph/0203128",
]
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
OUT=Path("validation/stationary/stil2002_ddo64_hi_profile_route_v1.json")
TARGET_PATTERNS=[r"DDO\s*64\b",r"UGC\s*5272\b",r"U\s*5272\b"]
PROFILE_PATTERNS=[
    r"radial",r"azimuth",r"surface\s+density\s+profile",r"density\s+profile",
    r"radial\s+profile",r"radial\s+distribution",r"annuli",r"rings?",
]
HI_PATTERNS=[r"H\s*I",r"\\HI",r"neutral\s+hydrogen",r"column\s+density"]


def fetch():
    attempts=[]
    for url in URLS:
        rec={"url":url}
        try:
            req=Request(url,headers={"User-Agent":UA,"Accept":"application/gzip,application/octet-stream,*/*;q=0.5"})
            with urlopen(req,timeout=120) as h:
                raw=h.read(); final=h.geturl(); ct=h.headers.get("Content-Type","")
            rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw)})
            attempts.append(rec)
            return raw,attempts
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
            attempts.append(rec)
    raise RuntimeError("No Stil 2002 arXiv source route recovered: "+repr(attempts))


def context(lines,i,r=8):
    return "\n".join(lines[max(0,i-r):min(len(lines),i+r+1)])[:14000]


def inspect_postscript(name: str, b: bytes) -> dict:
    text=b.decode("latin-1","replace")
    comments=[line[:500] for line in text.splitlines() if line.startswith("%")][:100]
    def token(tok: bytes) -> int:
        return len(re.findall(rb"(?<![A-Za-z])"+re.escape(tok)+rb"(?![A-Za-z])",b))
    strings=[]
    for raw in re.findall(rb"\(((?:\\.|[^\\)])*)\)",b):
        try:s=raw.decode("latin-1","replace")
        except Exception:continue
        if s.strip():strings.append(s[:300])
    return {
        "name":name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),
        "bounding_box_lines":[x for x in comments if "BoundingBox" in x][:10],
        "creator_lines":[x for x in comments if re.search(r"Creator|Producer|Title|CreationDate",x,re.I)][:20],
        "image_ops":token(b"image"),"colorimage_ops":token(b"colorimage"),"imagemask_ops":token(b"imagemask"),
        "moveto_ops":token(b"moveto"),"lineto_ops":token(b"lineto"),"curveto_ops":token(b"curveto"),"stroke_ops":token(b"stroke"),
        "literal_string_count":len(strings),
        "useful_strings":[s for s in strings if re.search(r"DDO|UGC|5272|HI|H I|density|radius|kpc|pc",s,re.I)][:100],
    }


def main():
    raw,attempts=fetch()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    members=[]; texts=[]; ps_assets=[]; data_assets=[]
    for m in tf.getmembers():
        if not m.isfile():continue
        suffix=Path(m.name).suffix.lower()
        members.append({"name":m.name,"bytes":m.size,"suffix":suffix})
        b=tf.extractfile(m).read()
        if suffix in {".tex",".txt",".bbl",".bib",".dat",".tbl",".tab",".csv"}:
            texts.append((m.name,b.decode("latin-1","replace")))
        if suffix in {".ps",".eps"}:
            ps_assets.append(inspect_postscript(m.name,b))
        if suffix in {".dat",".tbl",".tab",".csv",".fits",".fit",".fts"}:
            data_assets.append({"name":m.name,"bytes":m.size,"suffix":suffix,"sha256":hashlib.sha256(b).hexdigest()})

    target_hits=[]; profile_hits=[]; figure_refs=[]; section_hits=[]
    combined=[]
    for fn,text in texts:
        lines=text.splitlines(); combined.append(text)
        for i,line in enumerate(lines):
            if any(re.search(p,line,re.I) for p in TARGET_PATTERNS):
                target_hits.append({"file":fn,"line":i+1,"text":line[:3000],"context":context(lines,i,10)})
                # Capture figure assets mentioned in the same local target context.
                c=context(lines,i,14)
                refs=sorted(set(re.findall(r"(?:includegraphics|epsfbox|psfig(?:\{[^}]*\})?)[^\n{}=]*[={]\s*([^}\s,]+)",c,re.I)))
                if refs:
                    figure_refs.append({"file":fn,"line":i+1,"target_context_figure_refs":refs,"context":c})
            if any(re.search(p,line,re.I) for p in PROFILE_PATTERNS):
                c=context(lines,i,8)
                profile_hits.append({
                    "file":fn,"line":i+1,"text":line[:3000],"context":c,
                    "mentions_hi":any(re.search(p,c,re.I) for p in HI_PATTERNS),
                    "mentions_target":any(re.search(p,c,re.I) for p in TARGET_PATTERNS),
                })
            if re.search(r"\\section|\\subsection",line) and re.search(r"distribution|surface|H.?I|results",line,re.I):
                section_hits.append({"file":fn,"line":i+1,"text":line[:2000]})

    all_text="\n".join(combined)
    radial_target_contexts=[h for h in profile_hits if h["mentions_target"] and h["mentions_hi"]]
    radial_hi_contexts=[h for h in profile_hits if h["mentions_hi"]]

    # Determine whether any data-like text asset actually contains DDO64/UGC5272
    # plus repeated numeric rows. This is a locator only, not a promotion by itself.
    numeric_candidates=[]
    for fn,text in texts:
        if Path(fn).suffix.lower() not in {".dat",".tbl",".tab",".csv",".txt"}:continue
        if not any(re.search(p,text,re.I) for p in TARGET_PATTERNS):continue
        nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?",text)
        numeric_candidates.append({"name":fn,"numeric_token_count":len(nums),"excerpt":text[:10000]})

    result={
        "status":"STIL2002_DDO64_HI_PROFILE_ROUTE_AUDIT_COMPLETE",
        "source":"Stil & Israel 2002, Neutral hydrogen in dwarf galaxies I. The spatial distribution of HI",
        "arxiv":"astro-ph/0203128",
        "provenance_chain":"Lelli/SPARC DDO064 -> dB02 Table 1 code 6 -> Stil 1999 thesis -> Stil & Israel 2002 Paper I",
        "transport_attempts":attempts,"source_bytes":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),
        "members":members,"data_like_assets":data_assets,"numeric_target_candidates":numeric_candidates,
        "target_hits":target_hits,"profile_language_hits":profile_hits,"target_radial_hi_contexts":radial_target_contexts,
        "global_radial_hi_contexts":radial_hi_contexts,"target_context_figure_refs":figure_refs,"relevant_sections":section_hits,
        "postscript_assets":ps_assets,
        "decision_fields":{
            "ddo64_present_in_source_text":bool(target_hits),
            "machine_readable_target_profile_candidate":bool(numeric_candidates),
            "target_specific_radial_hi_text_evidence":bool(radial_target_contexts),
            "n_postscript_assets":len(ps_assets),
        },
        "interpretation_rule":(
            "A 2-D H I column-density map, global H I mass/diameter, or profile discussed only as a visual figure does not count as an exact radial Sigma_HI(R) product. "
            "Only source-native numeric rows or clearly isolated vector radial-profile geometry can be promoted."
        ),
        "boundary":"Acquisition/provenance only. PostScript is parsed but never executed. No OCR, raster digitization, map-to-profile reconstruction, normalization, persistence fitting, or blind-outcome inspection."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "n_target_hits":len(target_hits),"n_target_radial_hi_contexts":len(radial_target_contexts),
        "data_like_assets":data_assets,"numeric_target_candidates":numeric_candidates,
        "postscript_summary":[{"name":p["name"],"image_ops":p["image_ops"],"lineto_ops":p["lineto_ops"],"curveto_ops":p["curveto_ops"]} for p in ps_assets],
    },indent=2))

if __name__=="__main__":main()
