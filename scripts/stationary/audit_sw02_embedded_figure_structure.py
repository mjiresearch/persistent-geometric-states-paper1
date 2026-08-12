#!/usr/bin/env python3
"""Inspect embedded Swaters 2002 atlas figure structure without executing PS.

All 13 frozen Sw02 targets are deterministically mapped to Appendix figures
h3074f13..85 inside the recovered WHISPI.ps.gz. This audit extracts each parent
%%BeginDocument block as inert bytes and inventories its immediate nested
subdocuments, operator counts, bounding boxes and native literal strings.

No PostScript execution/rendering, raster digitization, scientific profile-value
extraction, persistence fitting, or blind-outcome inspection occurs.
"""
from __future__ import annotations
import csv,gzip,json,re
from pathlib import Path
from urllib.request import Request,urlopen

ATLAS="http://web.archive.org/web/20070824112627id_/http://www.robswork.net/publications/WHISPI.ps.gz"
UA="PersistenceFrameworkPaperI/1.0"
MAP=Path("data/stationary/source_reconstruction/sw02_recovered_atlas_page_map_v1.csv")
OUT=Path("validation/stationary/sw02_embedded_figure_structure_audit_v1.json")

def fetch(url,timeout=240):
    with urlopen(Request(url,headers={"User-Agent":UA,"Accept":"*/*"}),timeout=timeout) as h:return h.read()

def strings(b):
    out=[]
    for raw in re.findall(rb"\(((?:\\.|[^\\)])*)\)",b):
        s=raw.decode("latin-1","replace")
        s=re.sub(r"\\([0-7]{1,3})",lambda m:chr(int(m.group(1),8)),s)
        s=s.replace(r"\(","(").replace(r"\)",")").replace(r"\\","\\")
        if s.strip():out.append(s)
    return out

def ops(b):
    return {"image":len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])",b)),"colorimage":b.count(b"colorimage"),"imagemask":b.count(b"imagemask"),"moveto":b.count(b"moveto"),"lineto":b.count(b"lineto"),"curveto":b.count(b"curveto"),"stroke":b.count(b"stroke"),"show":b.count(b"show"),"translate":b.count(b"translate"),"scale":b.count(b"scale")}

def summarize(b,name,order=None):
    ss=strings(b); pat=re.compile(r"surface|dens|sigma|radius|radial|arcsec|kpc|m.?sun|h\s*i|hi\b",re.I)
    return {"name":name,"order":order,"bytes":len(b),"bounding_boxes":[x.decode("latin-1","replace") for x in re.findall(rb"(?m)^%%(?:HiRes)?BoundingBox:[^\r\n]*",b)[:10]],"operators":ops(b),"n_literal_strings":len(ss),"useful_strings":[s[:300] for s in ss if pat.search(s)][:100],"short_strings":[s for s in ss if len(s)<=100][:150]}

def parent_and_children(ps,fig):
    hit=ps.find(f"h3074f{fig}.ps".encode())
    if hit<0:return None
    begin=ps.rfind(b"%%BeginDocument",0,hit+1)
    if begin<0:return None
    marker=re.compile(rb"(?m)^%%(BeginDocument|EndDocument)(?::[^\r\n]*)?")
    depth=0; end=None; children=[]; child=None
    for m in marker.finditer(ps,begin):
        typ=m.group(1)
        if typ==b"BeginDocument":
            le=ps.find(b"\n",m.start()); le=len(ps) if le<0 else le
            txt=ps[m.start():le].decode("latin-1","replace"); name=txt.split(":",1)[1].strip() if ":" in txt else ""
            depth+=1
            if depth==2:child={"start":m.start(),"name":name}
        else:
            if depth==2 and child is not None:
                child["end"]=m.end();children.append(child);child=None
            if depth==1:end=m.end();break
            depth-=1
    if end is None:return None
    return begin,end,children

def main():
    with MAP.open(newline="",encoding="utf-8-sig") as fh:rows=list(csv.DictReader(fh))
    ps=gzip.decompress(fetch(ATLAS)); targets=[]
    for r in rows:
        fig=int(r["appendix_figure_number"]); blk=parent_and_children(ps,fig)
        if blk is None:
            targets.append({"galaxy":r["galaxy"],"figure":fig,"status":"parent_block_not_found"});continue
        a,b,ch=blk; children=[]
        for i,c in enumerate(ch,1):children.append(summarize(ps[c["start"]:c["end"]],c["name"],i))
        targets.append({"galaxy":r["galaxy"],"stationary_role":r["stationary_role"],"figure":fig,"status":"parent_block_found","parent":summarize(ps[a:b],f"h3074f{fig}.ps"),"n_immediate_child_documents":len(children),"children":children})
    ok=[t for t in targets if t["status"]=="parent_block_found"];dist={}
    for t in ok:dist[str(t["n_immediate_child_documents"])]=dist.get(str(t["n_immediate_child_documents"]),0)+1
    result={"status":"SW02_EMBEDDED_FIGURE_STRUCTURE_AUDIT_COMPLETE","source":"Recovered Swaters 2002 WHISP-I full atlas","n_targets":len(rows),"n_parent_blocks_found":len(ok),"child_count_distribution":dist,"targets":targets,"interpretation_rule":"A child with substantial native path operations and little/no image activity is only a vector-panel candidate; scientific panel identity and axes must be established separately.","boundary":"PostScript parsed as inert bytes only; no execution, rendering, raster digitization, profile extraction, persistence fitting, or blind outcomes."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="targets"},indent=2))
    for t in targets:
        print("TARGET",t["galaxy"],"fig",t["figure"],"children",t.get("n_immediate_child_documents"),[(c["order"],c["name"],c["operators"]) for c in t.get("children",[])])
if __name__=="__main__":main()
