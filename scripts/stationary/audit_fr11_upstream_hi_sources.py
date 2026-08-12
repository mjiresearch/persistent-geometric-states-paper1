#!/usr/bin/env python3
"""Audit the two original H I observation sources used by Fr11.

Frozen provenance from Fraternali et al. 2011 TeX:
- NGC891  -> Oosterloo, Fraternali & Sancisi 2007, AJ 134, 1019
- NGC7814 -> Kamphuis 2008 PhD thesis, University of Groningen

Fr11 states that its gas density versus R was obtained by deprojecting the total
H I maps. This audit therefore asks whether either upstream source itself exposes
source-native radial Sigma_HI(R) rows or unambiguous vector profile geometry.
2-D H I maps/cubes and summary scalars do not count as radial profiles.

No OCR, no raster digitization, no map-to-profile reconstruction, no persistence
fitting, and no blind-outcome inspection.
"""
from __future__ import annotations

import hashlib, io, json, re, tarfile, urllib.parse, urllib.request
from pathlib import Path
import fitz

UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
OUT=Path("validation/stationary/fr11_upstream_hi_source_audit_v1.json")
OOSTERLOO_URLS=["https://arxiv.org/e-print/0705.4034","https://export.arxiv.org/e-print/0705.4034"]
KAMPHUIS_PORTAL="https://research.rug.nl/en/publications/the-structure-and-kinematics-of-halos-in-disk-galaxies"
PROFILE_PATS=[r"surface\s+density",r"radial\s+profile",r"radial\s+distribution",r"gas\s+density",r"density\s+profile",r"deproject",r"azimuth",r"annuli",r"rings?"]


def fetch(url, timeout=180, accept="*/*"):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":accept})
    with urllib.request.urlopen(req,timeout=timeout) as h:
        return h.read(),h.geturl(),h.headers.get("Content-Type","")


def context(lines,i,r=7):
    return "\n".join(lines[max(0,i-r):min(len(lines),i+r+1)])[:12000]


def tok(b,t):
    return len(re.findall(rb"(?<![A-Za-z])"+re.escape(t)+rb"(?![A-Za-z])",b))


def psinfo(name,b):
    return {"name":name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),
            "image_ops":tok(b,b"image"),"colorimage_ops":tok(b,b"colorimage"),"imagemask_ops":tok(b,b"imagemask"),
            "moveto_ops":tok(b,b"moveto"),"lineto_ops":tok(b,b"lineto"),"curveto_ops":tok(b,b"curveto"),"stroke_ops":tok(b,b"stroke")}


def audit_oosterloo():
    attempts=[]; raw=None
    for u in OOSTERLOO_URLS:
        rec={"url":u}
        try:
            raw,final,ct=fetch(u,120,"application/gzip,application/octet-stream,*/*;q=0.5")
            rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw)});attempts.append(rec);break
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"});attempts.append(rec)
    if raw is None:return {"recovered":False,"attempts":attempts}
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*");texts=[];graphics=[];data=[];members=[]
    for m in tf.getmembers():
        if not m.isfile():continue
        b=tf.extractfile(m).read();suf=Path(m.name).suffix.lower();members.append({"name":m.name,"bytes":m.size,"suffix":suf})
        if suf in {".tex",".txt",".bbl",".bib",".dat",".tbl",".tab",".csv"}:texts.append((m.name,b.decode("latin-1","replace")))
        if suf in {".ps",".eps"}:graphics.append(psinfo(m.name,b))
        if suf in {".dat",".tbl",".tab",".csv",".fits",".fit",".fts"}:data.append({"name":m.name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
    target=[];profile=[];figrefs=[];numeric=[]
    for fn,text in texts:
        lines=text.splitlines()
        for i,line in enumerate(lines):
            if re.search(r"NGC\\?,?\s*891|NGC\s*891",line,re.I):target.append({"file":fn,"line":i+1,"text":line[:2500],"context":context(lines,i,8)})
            if any(re.search(p,line,re.I) for p in PROFILE_PATS):profile.append({"file":fn,"line":i+1,"text":line[:2500],"context":context(lines,i,7)})
            if re.search(r"includegraphics|epsfig|psfig",line,re.I):figrefs.append({"file":fn,"line":i+1,"text":line[:2500],"context":context(lines,i,4)})
        if Path(fn).suffix.lower() in {".dat",".tbl",".tab",".csv",".txt"} and re.search(r"891",text) and re.search(r"surface|density|H.?I",text,re.I):
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",text);numeric.append({"name":fn,"numeric_tokens":len(nums),"excerpt":text[:10000]})
    return {"recovered":True,"attempts":attempts,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"members":members,"data_assets":data,
            "numeric_profile_candidates":numeric,"target_hits":target,"profile_hits":profile,"figure_refs":figrefs,"postscript_assets":graphics}


def extract_portal_files(html,base):
    text=html.decode("utf-8","replace");out=[];seen=set()
    for href in re.findall(r'''href=["']([^"']+)["']''',text,re.I):
        u=urllib.parse.urljoin(base,href.replace("&amp;","&"))
        m=re.search(r"/files/(\d+)/([^/?#]+\.pdf)",u,re.I)
        if m:
            key=(int(m.group(1)),urllib.parse.unquote(m.group(2)))
            if key not in seen:seen.add(key);out.append({"file_id":key[0],"name":key[1],"portal_url":u})
    return out


def pdf_audit(raw,name):
    doc=fitz.open(stream=raw,filetype="pdf");targets=[];prof=[];geom=[];native_candidates=[]
    for i,p in enumerate(doc):
        text=p.get_text("text");draw=p.get_drawings();imgs=p.get_images(full=True);low=text.lower()
        geom.append({"page":i+1,"text_chars":len(text),"drawings":len(draw),"drawing_items":sum(len(d.get("items",[])) for d in draw),"images":len(imgs)})
        named=bool(re.search(r"NGC\s*7814|NGC7814",text,re.I));pats=[x for x in PROFILE_PATS if re.search(x,text,re.I)]
        if named:targets.append({"page":i+1,"profile_patterns":pats,"excerpt":" ".join(text.split())[:8000],"drawings":len(draw),"drawing_items":sum(len(d.get("items",[])) for d in draw),"images":len(imgs)})
        if pats:prof.append({"page":i+1,"patterns":pats,"excerpt":" ".join(text.split())[:6000],"drawings":len(draw),"drawing_items":sum(len(d.get("items",[])) for d in draw),"images":len(imgs)})
        if named and pats:
            nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?",text)
            if len(nums)>=30:native_candidates.append({"page":i+1,"numeric_tokens":len(nums),"excerpt":" ".join(text.split())[:9000]})
    return {"name":name,"pages":len(doc),"native_text_chars":sum(x["text_chars"] for x in geom),"pages_with_drawings":sum(x["drawings"]>0 for x in geom),
            "pages_with_images":sum(x["images"]>0 for x in geom),"max_drawing_items":max((x["drawing_items"] for x in geom),default=0),
            "target_pages":targets,"profile_language_pages":prof[:150],"native_numeric_candidates":native_candidates,"geometry":geom}


def audit_kamphuis():
    portal_attempt={};files=[]
    try:
        html,final,ct=fetch(KAMPHUIS_PORTAL,90,"text/html,*/*");portal_attempt={"status":"fetched","final_url":final,"content_type":ct,"bytes":len(html)};files=extract_portal_files(html,final)
    except Exception as exc:portal_attempt={"status":"error","error":f"{type(exc).__name__}: {exc}"}
    attempts=[];recovered=[]
    # Prefer full thesis, then chapters/appendix. If portal HTML hides IDs, no guessing is promoted.
    files=sorted(files,key=lambda x:(0 if "Pagesfromkamphuisthesis" in x["name"] else 1,x["name"]))
    for f in files:
        urls=[f["portal_url"],f"https://pure.rug.nl/ws/portalfiles/portal/{f['file_id']}/{urllib.parse.quote(f['name'])}"]
        got=None
        for u in urls:
            rec={"name":f["name"],"file_id":f["file_id"],"url":u}
            try:
                raw,final,ct=fetch(u,180,"application/pdf,*/*");rec.update({"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw),"prefix_hex":raw[:12].hex()})
                if raw.startswith(b"%PDF-") and len(raw)>20000:
                    rec["valid_pdf"]=True;rec["sha256"]=hashlib.sha256(raw).hexdigest();got=raw;attempts.append(rec);break
            except Exception as exc:rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
            attempts.append(rec)
        if got is not None:
            recovered.append({"name":f["name"],"file_id":f["file_id"],"bytes":len(got),"sha256":hashlib.sha256(got).hexdigest(),"audit":pdf_audit(got,f["name"])})
            if "Pagesfromkamphuisthesis" in f["name"]:break
    return {"portal_attempt":portal_attempt,"portal_files":files,"transport_attempts":attempts,"recovered_documents":recovered}


def main():
    o=audit_oosterloo();k=audit_kamphuis()
    out={"status":"FR11_UPSTREAM_HI_SOURCE_AUDIT_COMPLETE",
         "fr11_provenance":{"NGC0891":"Oosterloo, Fraternali & Sancisi 2007 AJ 134 1019","NGC7814":"Kamphuis 2008 PhD thesis, University of Groningen"},
         "oosterloo2007":o,"kamphuis2008":k,
         "promotion_rule":"Only source-native radius-versus-Sigma_HI rows or unambiguous vector radial-profile geometry may be promoted. 2-D maps/cubes and raster figures are not digitized or deprojected under the current freeze.",
         "boundary":"Acquisition/provenance only; no OCR, raster digitization, map-to-profile reconstruction, normalization, persistence fitting, or blind-outcome inspection."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],
      "oosterloo":{"recovered":o.get("recovered"),"data_assets":o.get("data_assets"),"numeric_candidates":o.get("numeric_profile_candidates"),"graphics":[{"name":g["name"],"image":g["image_ops"],"lineto":g["lineto_ops"],"curveto":g["curveto_ops"]} for g in o.get("postscript_assets",[])]},
      "kamphuis":{"portal_files":[{"id":x["file_id"],"name":x["name"]} for x in k.get("portal_files",[])],"recovered":[{"name":x["name"],"pages":x["audit"]["pages"],"text":x["audit"]["native_text_chars"],"draw_pages":x["audit"]["pages_with_drawings"],"image_pages":x["audit"]["pages_with_images"],"target_pages":[p["page"] for p in x["audit"]["target_pages"]],"numeric_candidates":len(x["audit"]["native_numeric_candidates"])} for x in k.get("recovered_documents",[])]}},indent=2))

if __name__=="__main__":main()
