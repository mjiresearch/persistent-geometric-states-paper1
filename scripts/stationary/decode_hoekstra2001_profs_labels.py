#!/usr/bin/env python3
"""Decode text-show operations in Hoekstra 2001 `profs.eps` without executing PS."""
from __future__ import annotations
import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen
URL="https://arxiv.org/e-print/astro-ph/0010569"
OUT=Path("validation/stationary/hoekstra2001_profs_label_decode_v1.json")

def main():
    with urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"}),timeout=120) as h:raw=h.read()
    tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*");m=next(x for x in tf.getmembers() if x.name.endswith("profs.eps"));s=tf.extractfile(m).read().decode("latin-1","replace");lines=s.splitlines()
    shows=[]; hexes=[]
    for i,line in enumerate(lines):
        if re.search(r"(?:\)|>)\s*T\b|\bshow\b",line):
            vals=re.findall(r"\(((?:\\.|[^\\)])*)\)",line)
            hv=re.findall(r"<([0-9A-Fa-f\s]+)>",line)
            decoded=[]
            for x in hv:
                try:decoded.append(bytes.fromhex(re.sub(r"\s+","",x)).decode("latin-1","replace"))
                except Exception:pass
            shows.append({"line":i+1,"text":line[:2400],"literal":vals,"hex_decoded":decoded,"context":"\n".join(lines[max(0,i-2):min(len(lines),i+3)])[:6000]})
        if "<" in line and ">" in line:
            hv=re.findall(r"<([0-9A-Fa-f\s]{2,})>",line)
            if hv:
                dec=[]
                for x in hv:
                    try:dec.append(bytes.fromhex(re.sub(r"\s+","",x)).decode("latin-1","replace"))
                    except Exception:pass
                hexes.append({"line":i+1,"text":line[:2000],"decoded":dec})
    result={"status":"HOEKSTRA2001_PROFS_LABEL_DECODE_COMPLETE","n_show_lines":len(shows),"show_lines":shows,"hex_lines":hexes,"boundary":"Static PS text parsing only; no execution."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"n_show_lines":len(shows),"examples":shows[:80]},indent=2))
if __name__=="__main__":main()
