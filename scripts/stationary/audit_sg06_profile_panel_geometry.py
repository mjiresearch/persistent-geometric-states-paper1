#!/usr/bin/env python3
"""Map SG06 radial H I profile figures and audit exact vector/raster geometry.

Spekkens & Giovanelli (2006) explicitly derive Sigma_HI(r) and state that panel
(d) of each galaxy summary figure is the radial H I surface-density profile.
This audit maps source macros/figure labels to EPS assets, inventories each EPS
as inert PostScript bytes, and classifies whether the scientific profile panel
can plausibly be recovered as native vector geometry rather than a rasterized
image.

No PostScript execution/rendering and no raster digitization. No profile values,
helium conversion, distance rescaling, persistence fitting or blind outcomes.
"""
from __future__ import annotations

import io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen

ARXIV="https://export.arxiv.org/e-print/astro-ph/0605542"
UA="PersistenceFrameworkPaperI/1.0"
OUT=Path("validation/stationary/sg06_profile_panel_geometry_audit_v1.json")
TARGETS=["ESO563-G021","IC4202","NGC2955","NGC6195","UGC11455"]


def fetch():
    with urlopen(Request(ARXIV,headers={"User-Agent":UA}),timeout=120) as h:return h.read()


def compact(s):return re.sub(r"[^A-Z0-9]","",s.upper())


def ps_metrics(b):
    return {
      "bytes":len(b),
      "image_ops":len(re.findall(rb"(?<![A-Za-z])image(?![A-Za-z])",b)),
      "colorimage_ops":b.count(b"colorimage"),
      "imagemask_ops":b.count(b"imagemask"),
      "moveto_tokens":b.count(b"moveto"),
      "lineto_tokens":b.count(b"lineto"),
      "curveto_tokens":b.count(b"curveto"),
      "stroke_tokens":b.count(b"stroke"),
      "show_tokens":b.count(b"show"),
      "clip_tokens":b.count(b"clip"),
      "bbox_lines":[x.decode("latin-1","replace") for x in re.findall(rb"(?m)^%%(?:HiRes)?BoundingBox:[^\r\n]*",b)[:10]],
      "raster_signal":bool(re.search(rb"(?<![A-Za-z])(?:image|colorimage|imagemask)(?![A-Za-z])",b)),
      "substantial_path_signal":(b.count(b"lineto")+b.count(b"curveto")>=20),
    }


def main():
    raw=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    texm=next(m for m in tf.getmembers() if m.isfile() and m.name.endswith(".tex"))
    tex=tf.extractfile(texm).read().decode("latin-1","ignore")
    lines=tex.splitlines()

    # Macro definitions establish the paper's aliases, including ESO563G21.
    macros={}
    for i,line in enumerate(lines,1):
        m=re.search(r"\\newcommand\{\\([A-Za-z0-9]+)\}\{([^}]*)\}",line)
        if m:macros[m.group(1)]={"value":m.group(2),"line":i}

    # Capture complete figure environments with EPS asset names, labels and captions.
    figures=[]
    infig=False;buf=[];start=0
    for i,line in enumerate(lines,1):
        if re.search(r"\\begin\{figure\*?\}",line):infig=True;buf=[line];start=i;continue
        if infig:
            buf.append(line)
            if re.search(r"\\end\{figure\*?\}",line):
                block="\n".join(buf)
                assets=re.findall(r"(?:plotone|plottwo|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}",block)
                # plottwo's second braced argument can be missed by generic regex.
                for mm in re.finditer(r"\\plottwo\{([^}]+)\}\{([^}]+)\}",block):assets.extend([mm.group(1),mm.group(2)])
                labels=re.findall(r"\\label\{([^}]+)\}",block)
                figures.append({"start_line":start,"end_line":i,"assets":list(dict.fromkeys(assets)),"labels":labels,"block":block[:10000]})
                infig=False

    members={m.name:m for m in tf.getmembers() if m.isfile()}
    eps={}
    for name,m in members.items():
        if Path(name).suffix.lower() in {".eps",".ps"}:
            b=tf.extractfile(m).read();eps[name]=ps_metrics(b)

    # Link the summary-figure labels explicitly referenced in Sigma_HI text to assets.
    sigma_refs=[]
    for i,line in enumerate(lines,1):
        if "Sigma_{HI}" in line or "Sigma_{\\rm HI}" in line or "surface density profile" in line.lower():
            sigma_refs.append({"line":i,"text":line[:1500],"figure_refs":re.findall(r"\\ref\{([^}]+)\}",line)})
    sigma_labels={x for r in sigma_refs for x in r["figure_refs"] if "fig" in x.lower()}
    linked=[f for f in figures if sigma_labels.intersection(f["labels"])]

    result={
      "status":"SG06_PROFILE_PANEL_GEOMETRY_AUDIT_COMPLETE",
      "source":"Spekkens & Giovanelli 2006; arXiv astro-ph/0605542",
      "targets":TARGETS,
      "macro_definitions":macros,
      "sigma_hi_text_references":sigma_refs,
      "sigma_hi_figure_labels":sorted(sigma_labels),
      "linked_sigma_hi_figure_environments":linked,
      "eps_metrics":eps,
      "n_eps_assets":len(eps),
      "n_eps_with_raster_signal":sum(v["raster_signal"] for v in eps.values()),
      "n_eps_with_substantial_path_signal":sum(v["substantial_path_signal"] for v in eps.values()),
      "interpretation_rule":"A native radial-profile recovery requires the Sigma_HI panel itself to be represented by substantial recoverable path geometry. An EPS wrapper containing a colorimage/raster payload is not treated as vector profile data merely because the file extension is EPS.",
      "boundary":"Inert PostScript/source inspection only; no execution, rendering, raster digitization, profile extraction, persistence fitting, or blind outcomes."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"sigma_labels":sorted(sigma_labels),"linked":[{"labels":f["labels"],"assets":f["assets"],"start":f["start_line"]} for f in linked],"eps":eps},indent=2))

if __name__=="__main__":main()
