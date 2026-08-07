#!/usr/bin/env python3
# Triggered ingestion entrypoint for public SDSS persistence-history products.
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from astropy.table import Table
from bs4 import BeautifulSoup

ROOT = Path("data/external/sdss")
ROOT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "dr19_occam": "https://data.sdss.org/sas/dr19/vac/mwm/apogee-occam/",
    "dr19_minesweeper": "https://data.sdss.org/sas/dr19/vac/mwm/minesweeper/",
}

KEYWORDS = [
    "source", "gaia", "sdss", "catalog", "ra", "dec", "l", "b", "pm", "parallax",
    "rv", "radial", "distance", "age", "teff", "logg", "fe", "alpha", "metal",
    "cluster", "member", "orbit", "peri", "apo", "ecc", "zmax", "energy", "action",
    "jr", "jphi", "jz", "lz", "guid", "x", "y", "z", "vx", "vy", "vz"
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def list_files(url: str) -> list[str]:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".fits", ".fits.gz", ".csv", ".parquet")):
            out.append(urljoin(url, href))
    return sorted(set(out))


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)


def fits_to_outputs(path: Path, outdir: Path) -> dict:
    table = Table.read(path)
    df = table.to_pandas()
    full_parquet = outdir / (path.stem.replace(".fits", "") + ".parquet")
    df.to_parquet(full_parquet, index=False)

    cols = []
    for c in df.columns:
        lc = c.lower()
        if any(re.search(rf"(^|_){re.escape(k)}($|_)", lc) for k in KEYWORDS):
            cols.append(c)
    if not cols:
        cols = list(df.columns[: min(40, len(df.columns))])
    selected = df[cols].copy()
    selected_csv = outdir / (path.stem.replace(".fits", "") + "_persistence_selected.csv")
    selected.to_csv(selected_csv, index=False)
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "selected_columns": cols,
        "parquet": str(full_parquet),
        "selected_csv": str(selected_csv),
    }


def probe_dr20() -> dict:
    roots = [
        "https://data.sdss.org/sas/dr20/vac/mwm/",
        "https://data.sdss.org/sas/dr20/vac/",
    ]
    keywords = ("occam", "gyro", "young", "clam", "minesweeper", "orbit")
    results = {}
    for root in roots:
        try:
            r = requests.get(root, timeout=60)
            results[root] = {"status": r.status_code, "matches": []}
            if r.ok:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if any(k in href.lower() for k in keywords):
                        results[root]["matches"].append(urljoin(root, href))
        except Exception as e:
            results[root] = {"error": repr(e)}
    return results


def main() -> None:
    manifest = {"sources": {}, "dr20_probe": probe_dr20()}
    for name, base in SOURCES.items():
        outdir = ROOT / name
        outdir.mkdir(parents=True, exist_ok=True)
        entry = {"base_url": base, "files": []}
        try:
            files = list_files(base)
        except Exception as e:
            entry["error"] = repr(e)
            manifest["sources"][name] = entry
            continue
        for url in files:
            filename = url.rsplit("/", 1)[-1]
            dest = outdir / filename
            try:
                download(url, dest)
                item = {"url": url, "path": str(dest), "bytes": dest.stat().st_size, "sha256": sha256(dest)}
                if filename.lower().endswith((".fits", ".fits.gz")):
                    item.update(fits_to_outputs(dest, outdir))
                entry["files"].append(item)
            except Exception as e:
                entry["files"].append({"url": url, "error": repr(e)})
        manifest["sources"][name] = entry

    (ROOT / "download_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
