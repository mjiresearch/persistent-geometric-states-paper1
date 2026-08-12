#!/usr/bin/env python3
"""Recover the published analytic thin-disk H I radial profile for NGC891.

Frozen chain:
Lelli/SPARC NGC0891 -> Fr11 -> Oosterloo, Fraternali & Sancisi 2007.

Oosterloo et al. explicitly fit the observed thin-disk radial H I surface density
with a tapered exponential and add a compact exponential component for the inner
ring.  This script verifies the exact TeX statements before writing the analytic
parameter record.  It does not sample the function or apply helium/distance
renormalization.
"""
from __future__ import annotations
import csv,hashlib,io,json,re,tarfile
from pathlib import Path
from urllib.request import Request,urlopen

URLS=["https://arxiv.org/e-print/0705.4034","https://export.arxiv.org/e-print/0705.4034"]
UA="Mozilla/5.0 PersistenceFrameworkPaperI/1.0"
CSV=Path("data/stationary/source_reconstruction/oosterloo2007_ngc891_hi_analytic_profile_v1.csv")
VAL=Path("validation/stationary/oosterloo2007_ngc891_hi_analytic_profile_v1.json")


def fetch():
    attempts=[]
    for u in URLS:
        try:
            req=Request(u,headers={"User-Agent":UA,"Accept":"application/gzip,application/octet-stream,*/*;q=0.5"})
            with urlopen(req,timeout=120) as h:raw=h.read();final=h.geturl();ct=h.headers.get("Content-Type","")
            attempts.append({"url":u,"status":"fetched","final_url":final,"content_type":ct,"bytes":len(raw)})
            return raw,attempts
        except Exception as exc:attempts.append({"url":u,"status":"error","error":f"{type(exc).__name__}: {exc}"})
    raise RuntimeError(repr(attempts))

def main():
    raw,attempts=fetch();tf=tarfile.open(fileobj=io.BytesIO(raw),mode="r:*")
    texdocs=[]
    for m in tf.getmembers():
        if m.isfile() and Path(m.name).suffix.lower() in {".tex",".sty"}:
            texdocs.append((m.name,tf.extractfile(m).read().decode("latin-1","replace")))
    text="\n".join(t for _,t in texdocs)
    required=[
      r"\\Sigma\(R\)=\\Sigma_\{\\rm 0\} \\left\( 1 \+ \\frac\{R\}\{R_\*\} \\right\) \^\{\\alpha\} \\exp\{\(-R/R_\*\)\}",
      r"\\Sigma_\{\\rm 0\}=6\.2 \\times 10\^\{-4\}\\ \\mopc",
      r"\\alpha=7\.8",
      r"R_\*=1\.2.*kpc",
      r"inner ring, we add an extra exponential component",
      r"\\Sigma_\{\\rm 0\}=6\.3\\ \\mopc",
    ]
    missing=[p for p in required if not re.search(p,text,re.S)]
    if missing:raise RuntimeError("Expected Oosterloo analytic-fit statements not found: "+repr(missing))

    # Preserve exact source contexts and any macro definition of \mopc if present.
    lines=text.splitlines(); contexts=[]
    for i,line in enumerate(lines):
        if "Sigma_{\\rm 0}=6.2" in line or "inner ring, we add" in line or "Sigma(R)=" in line or "mopc" in line and ("def" in line or "newcommand" in line):
            contexts.append({"line":i+1,"context":"\n".join(lines[max(0,i-5):min(len(lines),i+9)])[:8000]})

    row={
      "galaxy":"NGC0891","stationary_role":"calibration",
      "source":"Oosterloo, Fraternali & Sancisi 2007 AJ 134 1019",
      "source_quantity":"thin-disk atomic HI radial surface density",
      "formula":"Sigma_HI(R)=Sigma0_outer*(1+R/Rstar_outer)^alpha*exp(-R/Rstar_outer)+Sigma0_inner*exp(-R/Rstar_inner)",
      "sigma0_outer_msun_pc2":"6.2e-4","alpha":"7.8","rstar_outer_kpc":"1.2",
      "sigma0_inner_msun_pc2":"6.3","rstar_inner_kpc":"1.2",
      "radius_unit":"kpc","surface_density_unit":"Msun pc^-2",
      "helium_status":"helium not included; source quantity is HI",
      "source_note":"Outer tapered fit to observed thin-disk HI radial surface density; compact exponential added for inner HI ring. Parameters retained exactly; function not sampled."
    }
    CSV.parent.mkdir(parents=True,exist_ok=True)
    with CSV.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(row));w.writeheader();w.writerow(row)
    out={"status":"OOSTERLOO2007_NGC891_ANALYTIC_HI_RECOVERED","transport_attempts":attempts,"source_bytes":len(raw),"source_sha256":hashlib.sha256(raw).hexdigest(),"record":row,"source_contexts":contexts,"boundary":"Exact analytic source representation only; no resampling, helium factor, distance normalization, persistence fitting, or blind inspection."}
    VAL.parent.mkdir(parents=True,exist_ok=True);VAL.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
