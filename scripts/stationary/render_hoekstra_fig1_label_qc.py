#!/usr/bin/env python3
"""Render the already-compiled arXiv PDF Figure 1 page for label/layout QC only.

This does not execute the EPS/PostScript source and is not used to digitize
curve values. It only permits visual panel-label identification so vector paths
can be mapped back to galaxies.
"""
from urllib.request import Request,urlopen
from pathlib import Path
import pymupdf
URL="https://arxiv.org/pdf/astro-ph/0010569"
OUT=Path("validation/stationary/_tmp_hoekstra_fig1_label_qc.png")
req=Request(URL,headers={"User-Agent":"Mozilla/5.0 PersistenceFrameworkPaperI/1.0","Accept":"application/pdf"})
with urlopen(req,timeout=120) as h: raw=h.read()
doc=pymupdf.open(stream=raw,filetype="pdf")
# Figure 1 occupies arXiv PDF page index 3 (journal page 4).
p=doc[3]
pix=p.get_pixmap(matrix=pymupdf.Matrix(2.0,2.0),alpha=False)
OUT.parent.mkdir(parents=True,exist_ok=True)
pix.save(str(OUT))
print(OUT,OUT.stat().st_size)
