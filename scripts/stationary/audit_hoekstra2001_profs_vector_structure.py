#!/usr/bin/env python3
"""Static structural audit of Hoekstra et al. 2001 Fig.1 `profs.eps`.

No PostScript is executed. We recover the EPS as plain text, identify operator
aliases, dash-state changes, panel/glyph strings and path-like command streams.
The goal is to determine whether the dashed H I radial profiles are exactly
separable vector geometry with auditable axes.
"""
from __future__ import annotations
import io,json,re,tarfile,hashlib
from pathlib import Path
from urllib.request import Request,urlopen

URL="https://arxiv.org/e-print/astro-ph/0010569"
OUT=Path("validation/stationary/hoekstra2001_profs_vector_structure_v1.json")

def fetch():
    req=Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0"})
    with urlopen(req,timeout=120) as h:return h.read()

def main():
    raw=fetch(); tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    m=next(x for x in tf.getmembers() if x.isfile() and x.name.endswith("profs.eps"))
    b=tf.extractfile(m).read(); s=b.decode("latin-1","replace"); lines=s.splitlines()
    defs=[]; dash=[]; strings=[]; op_lines=[]; comments=[]
    for i,line in enumerate(lines):
        if line.startswith("%"): comments.append({"line":i+1,"text":line[:1200]})
        if re.search(r"/(\S+)\s*\{?[^%]*(?:moveto|lineto|curveto|stroke|show|setdash|setlinewidth)",line,re.I): defs.append({"line":i+1,"text":line[:1800]})
        if re.search(r"setdash|\[[^\]]*\]\s+\d*\s*setdash",line,re.I): dash.append({"line":i+1,"text":line[:1800],"context":"\n".join(lines[max(0,i-3):min(len(lines),i+4)])[:6000]})
        if "(" in line and ")" in line:
            vals=re.findall(r"\(((?:\\.|[^\\)])*)\)",line)
            if vals: strings.append({"line":i+1,"text":line[:1800],"strings":[v[:500] for v in vals]})
        if re.search(r"\b(?:moveto|lineto|curveto|stroke|show|setdash|setlinewidth)\b",line): op_lines.append({"line":i+1,"text":line[:1800]})
    # Extract all /name definitions, not only obvious operator lines, to resolve aliases.
    all_defs=[]
    for i,line in enumerate(lines):
        if re.match(r"\s*/\S+\s+",line): all_defs.append({"line":i+1,"text":line[:1800]})
    # Count frequent short tokens likely to be path aliases.
    toks=re.findall(r"(?<![/A-Za-z0-9_.-])([A-Za-z]{1,4})(?![A-Za-z0-9_.-])",s)
    from collections import Counter
    freq=Counter(toks)
    short_freq=freq.most_common(120)
    # Candidate numeric path lines: >=4 numbers plus at least one short alphabetic command.
    pathish=[]
    for i,line in enumerate(lines):
        nums=re.findall(r"[-+]?\d+(?:\.\d+)?",line)
        if len(nums)>=4 and re.search(r"\b[A-Za-z]{1,4}\b",line) and not line.startswith("%"):
            pathish.append({"line":i+1,"text":line[:2000],"n_numbers":len(nums)})
    result={
      "status":"HOEKSTRA2001_PROFS_VECTOR_STRUCTURE_COMPLETE",
      "asset":"profs.eps","bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"n_lines":len(lines),
      "comments":comments[:150],"operator_alias_definitions":defs,"all_name_definitions":all_defs[:500],
      "dash_state_lines":dash,"literal_strings":strings[:1000],"operator_lines":op_lines[:800],
      "frequent_short_tokens":short_freq,"pathish_lines":pathish[:1200],
      "counts":{"all_defs":len(all_defs),"dash_lines":len(dash),"string_lines":len(strings),"operator_lines":len(op_lines),"pathish_lines":len(pathish)},
      "boundary":"Static text parsing only; PostScript never executed. No profile digitization, fitting, or blind outcomes."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"counts":result["counts"],"operator_alias_definitions":defs[:50],"dash_state_lines":dash[:30],"frequent_short_tokens":short_freq[:40]},indent=2))
if __name__=="__main__":main()
