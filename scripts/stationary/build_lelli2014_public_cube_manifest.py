#!/usr/bin/env python3
"""Build a public HI-cube acquisition manifest for Lelli et al. (2014)."""
from __future__ import annotations

import argparse
import csv
import re
import urllib.request
from pathlib import Path

CATALOG = "J/A+A/566/A71"
BASE = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/566/A71"
LIST_URL = f"{BASE}/list.dat"


def norm_name(s: str) -> str:
    x = re.sub(r"[^A-Z0-9]", "", s.upper())
    # CDS literature names commonly omit the zero padding used by SPARC for UGC.
    m = re.fullmatch(r"UGC0*(\d+)", x)
    if m:
        return f"UGC{int(m.group(1)):05d}"
    return x


def read_url_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("ascii", errors="replace")


def parse_cds_list(text: str):
    rows=[]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"): continue
        name=raw[0:12].strip(); ra=raw[13:22].strip(); dec=raw[22:31].strip(); scale=raw[32:35].strip(); nxny=raw[36:45].strip(); nz=raw[46:49].strip(); bvel=raw[56:65].strip(); Bvel=raw[72:80].strip(); dvel=raw[85:92].strip(); size=raw[93:99].strip(); filename=raw[100:126].strip(); title=raw[127:164].strip()
        if name and filename:
            rows.append({"catalog_name":name,"catalog_name_norm":norm_name(name),"ra_deg":ra,"dec_deg":dec,"pixel_scale_arcsec":scale,"nx_ny":nxny,"n_channels":nz,"v_lower_kms":bvel,"v_upper_kms":Bvel,"dv_kms":dvel,"size_kib":size,"filename":filename,"title":title,"download_url":f"{BASE}/fits/{filename}"})
    return rows


def read_split(path: Path):
    with path.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    return {norm_name(r["galaxy"]):r for r in rows}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--split",type=Path,default=Path("validation/stationary/stationary_split_v1.csv")); ap.add_argument("--out",type=Path,default=Path("data/stationary/source_reconstruction/lelli2014_public_cube_manifest_v1.csv")); ap.add_argument("--download-dir",type=Path); args=ap.parse_args()
    split=read_split(args.split); catalog_rows=parse_cds_list(read_url_text(LIST_URL)); out_rows=[]
    for c in catalog_rows:
        s=split.get(c["catalog_name_norm"])
        if s is None: continue
        out={"galaxy":s["galaxy"],"stationary_role":s["stationary_role"],"source_family":"Lelli et al. (2014)","vizier_catalog":CATALOG,"acquisition_method":"public_CDS_HI_datacube",**c}; out_rows.append(out)
        if args.download_dir:
            args.download_dir.mkdir(parents=True,exist_ok=True); target=args.download_dir/c["filename"]
            if not target.exists(): urllib.request.urlretrieve(c["download_url"],target)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    fields=["galaxy","stationary_role","source_family","vizier_catalog","acquisition_method","catalog_name","catalog_name_norm","ra_deg","dec_deg","pixel_scale_arcsec","nx_ny","n_channels","v_lower_kms","v_upper_kms","dv_kms","size_kib","filename","download_url","title"]
    with args.out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out_rows)
    print(f"catalog cubes: {len(catalog_rows)}"); print(f"stationary overlap: {len(out_rows)}"); print("overlap galaxies:", [r["galaxy"] for r in out_rows]); print(f"wrote: {args.out}")

if __name__ == "__main__": main()
