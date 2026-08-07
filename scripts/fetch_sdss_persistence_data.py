#!/usr/bin/env python3
# Public SDSS persistence-history ingestion.
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
MAX_GITHUB_BYTES = 80 * 1024 * 1024

SOURCES = {
    "dr19_occam": "https://data.sdss.org/sas/dr19/vac/mwm/apogee-occam/",
    "dr19_minesweeper": "https://data.sdss.org/sas/dr19/vac/mwm/minesweeper/",
    "dr20_apogee_occam": "https://data.sdss.org/sas/dr20/vac/mwm/apogee-occam/",
    "dr20_boss_occam": "https://data.sdss.org/sas/dr20/vac/mwm/boss-occam/",
    "dr20_minesweeper": "https://data.sdss.org/sas/dr20/vac/mwm/minesweeper/",
    "dr20_orbits": "https://data.sdss.org/sas/dr20/vac/mwm/orbits/",
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
    return sorted(set(urljoin(url, a["href"]) for a in soup.find_all("a", href=True)
                      if a["href"].lower().endswith((".fits", ".fits.gz", ".csv", ".parquet"))))


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)


def select_columns(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        lc = c.lower()
        if any(re.search(rf"(^|_){re.escape(k)}($|_)", lc) for k in KEYWORDS):
            cols.append(c)
    return cols or list(df.columns[: min(40, len(df.columns))])


def fits_to_outputs(path: Path, outdir: Path) -> dict:
    table = Table.read(path)
    df = table.to_pandas()
    cols = select_columns(df)
    stem = path.name.replace(".fits.gz", "").replace(".fits", "")
    result = {"rows": len(df), "columns": len(df.columns), "selected_columns": cols}

    selected_gz = outdir / f"{stem}_persistence_selected.csv.gz"
    df[cols].to_csv(selected_gz, index=False, compression="gzip")
    result["selected_csv_gz"] = str(selected_gz)
    result["selected_csv_gz_bytes"] = selected_gz.stat().st_size

    parquet = outdir / f"{stem}.parquet"
    df.to_parquet(parquet, index=False, compression="zstd")
    if parquet.stat().st_size <= MAX_GITHUB_BYTES:
        result["parquet"] = str(parquet)
        result["parquet_bytes"] = parquet.stat().st_size
    else:
        result["parquet_omitted_from_git_bytes"] = parquet.stat().st_size
        parquet.unlink()

    del df, table
    return result


def probe_dr20() -> dict:
    root = "https://data.sdss.org/sas/dr20/vac/mwm/"
    try:
        r = requests.get(root, timeout=60)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        keys = ("occam", "gyro", "young", "clam", "minesweeper", "orbit")
        return {"status": r.status_code, "matches": sorted(set(urljoin(root, a["href"])
                for a in soup.find_all("a", href=True) if any(k in a["href"].lower() for k in keys)))}
    except Exception as e:
        return {"error": repr(e)}


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
                raw_bytes = dest.stat().st_size
                item = {"url": url, "path": str(dest), "bytes": raw_bytes, "sha256": sha256(dest)}
                if filename.lower().endswith((".fits", ".fits.gz")):
                    item.update(fits_to_outputs(dest, outdir))
                if raw_bytes > MAX_GITHUB_BYTES:
                    item["raw_omitted_from_git"] = True
                    dest.unlink()
                entry["files"].append(item)
            except Exception as e:
                entry["files"].append({"url": url, "error": repr(e)})
                if dest.exists():
                    dest.unlink()
        manifest["sources"][name] = entry

    (ROOT / "download_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
