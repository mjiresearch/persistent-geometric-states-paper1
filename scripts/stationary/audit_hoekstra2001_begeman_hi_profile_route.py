#!/usr/bin/env python3
"""Audit Hoekstra, van Albada & Sancisi 2001 as a Be87 republication route.

The paper republishes observed radial HI surface-density profiles in Fig. 1 and
explicitly includes NGC5371 from Begeman (1987). We inspect the exact arXiv
source package for source-native arrays or exact vector profile geometry for the
Be87 targets NGC2903, NGC5033, NGC5371, NGC6503.

No PostScript execution, OCR, raster digitization, normalization, persistence
fitting, or blind-outcome inspection.
"""
from __future__ import annotations
import hashlib, io, json, re, tarfile
from pathlib import Path
from urllib.request import Request, urlopen

URLS=["https://arxiv.org/e-print/astro-ph/0010569","https://export.arxiv.org/e-print/astro-ph/0010569"]
OUT=Path("validation/stationary/hoekstra2001_begeman_hi_profile_route_v1.json")
TARGETS={"NGC2903":["NGC 2903","NGC2903"],"NGC5033":["NGC 5033","NGC5033"],"NGC5371":["NGC 5371","NGC5371"],"NGC6503":["NGC 6503","NGC6503"]}

def fetch():
    errs=[]
    for u in URLS:
        try:
            req=Request(u,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0","Accept":"application/gzip,application/octet-stream,*/*;q=0.5"})
            with urlopen(req,timeout=120) as h:return h.read(),u,h.geturl(),h.headers.get("Content-Type","")
        except Exception as e:errs.append({"url":u,"error":f"{type(e).__name__}: {e}"})
    raise RuntimeError(repr(errs))

def c(s):return re.sub(r"[^A-Z0-9]","",s.upper())
def ctx(lines,i,r=8):return "\n".join(lines[max(0,i-r):min(len(lines),i+r+1)])[:12000]
def ps(name,b):
    s=b.decode("latin-1","ignore")
    def n(tok):return len(re.findall(rb"(?<![A-Za-z])"+re.escape(tok)+rb"(?![A-Za-z])",b))
    strings=[x.decode("latin-1","ignore") for x in re.findall(rb"\(((?:\\.|[^\\)])*)\)",b)]
    return {"name":name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"image_ops":n(b"image"),"colorimage_ops":n(b"colorimage"),"imagemask_ops":n(b"imagemask"),"moveto_ops":n(b"moveto"),"lineto_ops":n(b"lineto"),"curveto_ops":n(b"curveto"),"stroke_ops":n(b"stroke"),"useful_strings":[x[:300] for x in strings if re.search(r"NGC|2903|5033|5371|6503|density|radius|Rout|pc",x,re.I)][:200],"mentions_targets":{g:any(c(a) in c(s) for a in aa) for g,aa in TARGETS.items()}}

def main():
    raw,req,final,ct=fetch(); tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    members=[]; texts=[]; data=[]; graphics=[]
    for m in tf.getmembers():
        if not m.isfile():continue
        b=tf.extractfile(m).read(); suf=Path(m.name).suffix.lower(); members.append({"name":m.name,"bytes":len(b),"suffix":suf})
        if suf in {".tex",".txt",".bbl",".bib",".dat",".tbl",".tab",".csv"}:texts.append((m.name,b.decode("latin-1","ignore")))
        if suf in {".dat",".tbl",".tab",".csv",".fits",".fit",".fts"}:data.append({"name":m.name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
        if suf in {".ps",".eps"}:graphics.append(ps(m.name,b))
    hits={g:[] for g in TARGETS}; fig1=[]; profile=[]
    for fn,t in texts:
        lines=t.splitlines()
        for i,line in enumerate(lines):
            cc=c(line)
            for g,aa in TARGETS.items():
                if any(c(a) in cc for a in aa):hits[g].append({"file":fn,"line":i+1,"text":line[:2500],"context":ctx(lines,i,8)})
            if re.search(r"Fig(?:ure)?\.?\s*1|fig1",line,re.I):fig1.append({"file":fn,"line":i+1,"text":line[:2500],"context":ctx(lines,i,10)})
            if re.search(r"H\s*I.*surface\s+density|surface\s+density.*H\s*I|surface density profiles",line,re.I):profile.append({"file":fn,"line":i+1,"text":line[:2500],"context":ctx(lines,i,8)})
    vector_candidates=[g for g in graphics if (g["lineto_ops"] or g["curveto_ops"]) and not (g["image_ops"] or g["colorimage_ops"] or g["imagemask_ops"])]
    result={"status":"HOEKSTRA2001_BEGEMAN_HI_PROFILE_ROUTE_AUDIT_COMPLETE","source":"Hoekstra, van Albada & Sancisi 2001 MNRAS 323 453; arXiv astro-ph/0010569","transport":{"requested":req,"final":final,"content_type":ct,"bytes":len(raw)},"members":members,"data_like_assets":data,"target_text_hits":hits,"fig1_contexts":fig1,"hi_profile_contexts":profile,"postscript_assets":graphics,"vector_only_assets":vector_candidates,"decision_fields":{"machine_readable_assets_present":bool(data),"target_hit_counts":{g:len(v) for g,v in hits.items()},"n_vector_only_assets":len(vector_candidates)},"interpretation_rule":"Fig.1 can be promoted only if its HI curves are source-native numeric rows or exact separable vector geometry with auditable axes; generic vector plots or raster images are insufficient.","boundary":"Be87 acquisition only; no PostScript execution, OCR, raster digitization, normalization, persistence fitting, or blind outcomes."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"data":data,"target_hit_counts":result["decision_fields"]["target_hit_counts"],"graphics":[{"name":x["name"],"image":x["image_ops"],"lineto":x["lineto_ops"],"curveto":x["curveto_ops"]} for x in graphics],"vector_only":[x["name"] for x in vector_candidates]},indent=2))
if __name__=="__main__":main()
