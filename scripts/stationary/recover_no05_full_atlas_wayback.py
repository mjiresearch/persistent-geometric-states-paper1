#!/usr/bin/env python3
"""Bounded Wayback recovery of Noordermeer et al. 2005 full WHISP-III atlas.

The original arXiv record advertised the complete atlas separately as
https://www.astro.rug.nl/~edo/WHISPIII.ps.gz. A direct live request is now 404.
Because the project subsequently recovered the analogous Swaters WHISP-I atlas
from Wayback, this is a genuinely new acquisition mechanism and is allowed by
the anti-loop rule.

Transport/provenance only. Recovered PostScript is treated as inert bytes; it
is not executed, rendered, digitized, or used for persistence/blind analysis.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

UA="PersistenceFrameworkPaperI/1.0"
URLS=[
    "https://www.astro.rug.nl/~edo/WHISPIII.ps.gz",
    "http://www.astro.rug.nl/~edo/WHISPIII.ps.gz",
]
OUT=Path("validation/stationary/no05_full_atlas_wayback_recovery_v1.json")


def fetch(url,timeout=120):
    req=Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urlopen(req,timeout=timeout) as h:
        return h.read(),h.geturl(),h.headers.get("Content-Type","")


def classify(raw):
    r={"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"prefix_hex":raw[:24].hex()}
    try:
        ps=gzip.decompress(raw)
        r.update({
            "gzip_valid":True,"decompressed_bytes":len(ps),
            "decompressed_sha256":hashlib.sha256(ps).hexdigest(),
            "postscript_header":ps[:24].decode("latin-1","replace"),
            "postscript_like":ps.startswith(b"%!") or b"%!PS" in ps[:128],
            "dsc_page_count":len(__import__('re').findall(rb"(?m)^%%Page:",ps)),
            "showpage_token_count":ps.count(b"showpage"),
            "image_token_count":ps.count(b" image")+ps.count(b"\nimage"),
            "lineto_token_count":ps.count(b"lineto"),
            "moveto_token_count":ps.count(b"moveto"),
        })
    except Exception as exc:
        r.update({"gzip_valid":False,"gzip_error":f"{type(exc).__name__}: {exc}"})
    return r


def main():
    attempts=[]; snapshots=[]; recovered=None
    for original in URLS:
        api="https://archive.org/wayback/available?url="+quote(original,safe="")
        rec={"original_url":original,"availability_api":api}
        try:
            raw,final,ct=fetch(api,45)
            data=json.loads(raw.decode("utf-8","replace"))
            rec["availability_response"]=data
            closest=data.get("archived_snapshots",{}).get("closest") or {}
            if closest.get("available") and closest.get("url"):
                snap=closest["url"]
                # raw replay keeps gzip bytes rather than Wayback wrapper HTML.
                if "/web/" in snap and "id_/" not in snap:
                    snap=snap.replace("/web/","/web/",1)
                    parts=snap.split("/web/",1)
                    if parts[1] and "/" in parts[1]:
                        ts,rest=parts[1].split("/",1)
                        snap=parts[0]+"/web/"+ts+"id_/"+rest
                snapshots.append(snap)
        except Exception as exc:
            rec["availability_error"]=f"{type(exc).__name__}: {exc}"
        attempts.append(rec)

    seen=set()
    for snap in snapshots:
        if snap in seen: continue
        seen.add(snap)
        rec={"route":"wayback_available","url":snap}
        try:
            raw,final,ct=fetch(snap,180)
            cl=classify(raw)
            rec.update({"status":"fetched","final_url":final,"content_type":ct,**cl})
            attempts.append(rec)
            if cl.get("gzip_valid") and cl.get("postscript_like"):
                recovered=rec; break
        except Exception as exc:
            rec.update({"status":"error","error":f"{type(exc).__name__}: {exc}"})
            attempts.append(rec)

    result={
        "status":"NO05_FULL_ATLAS_WAYBACK_RECOVERY_COMPLETE",
        "source":"Noordermeer et al. 2005 WHISP-III full atlas",
        "historical_urls":URLS,
        "attempts":attempts,
        "recovered":recovered is not None,
        "recovered_url":None if recovered is None else recovered.get("final_url"),
        "recovered_classification":recovered,
        "supersedes_boundary_if_recovered":"validation/stationary/NO05_NO07_HI_PROFILE_AUDIT_V1.md",
        "boundary":"Transport/provenance only; recovered PostScript remains inert bytes until separately audited."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
