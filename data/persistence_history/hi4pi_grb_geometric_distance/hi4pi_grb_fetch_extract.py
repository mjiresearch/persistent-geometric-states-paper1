#!/usr/bin/env python3
"""
Fetch the public HI4PI Galactic spectral cubes from CDS and extract 1-D H I
spectra at the three GRB sightlines used in the X-ray dust-distance comparison.

Authoritative catalog:
  CDS/VizieR J/A+A/594/A116  (HI4PI Collaboration 2016)

The script deliberately reads cubes_gal.dat first, so it resolves the actual
CAR tile names from the public archive instead of assuming them.

Requirements:
  python >= 3.10
  numpy
  astropy

Example:
  python hi4pi_grb_fetch_extract.py --output hi4pi_grb_data

Outputs:
  hi4pi_grb_data/cubes_gal.dat
  hi4pi_grb_data/<selected HI4PI FITS tiles>
  hi4pi_grb_data/GRB_221009A_hi4pi.csv
  hi4pi_grb_data/GRB_160623A_hi4pi.csv
  hi4pi_grb_data/GRB_031203_hi4pi.csv
  hi4pi_grb_data/selected_tiles.csv

Downloads are resumable using HTTP Range requests.
"""

from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

CDS_ROOT = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/594/A116"

TARGETS = [
    {"name": "GRB_221009A", "l_deg": 52.96, "b_deg": 4.32},
    {"name": "GRB_160623A", "l_deg": 84.17, "b_deg": -2.69},
    {"name": "GRB_031203", "l_deg": 255.74, "b_deg": -4.80},
]


def download_resume(url: str, path: Path, retries: int = 8) -> Path:
    """Download URL to path with resume/retry support."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return path

    part = path.with_name(path.name + ".part")
    for attempt in range(retries):
        offset = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": "HI4PI-GRB-repro/1.0"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        req = Request(url, headers=headers)

        try:
            with urlopen(req, timeout=90) as r:
                status = getattr(r, "status", 200)
                # If a server ignores Range and returns 200, restart rather than append.
                append = bool(offset and status == 206)
                mode = "ab" if append else "wb"
                if offset and not append:
                    offset = 0
                with open(part, mode) as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
            part.replace(path)
            return path
        except Exception as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"Failed to download {url}: {exc}") from exc
            time.sleep(min(2 ** attempt, 30))

    raise RuntimeError(f"Failed to download {url}")


def wrapped_lon_diff(a_deg: float, b_deg: float) -> float:
    """Signed shortest longitude difference a-b in degrees."""
    return (a_deg - b_deg + 180.0) % 360.0 - 180.0


def parse_cubes_gal(path: Path) -> list[dict]:
    """
    Parse the CDS cubes_gal.dat table.

    The ReadMe defines columns GLON, GLAT, WCSproj, FileName.  We accept both
    whitespace-separated and fixed-width-looking rows to remain robust.
    """
    rows = []
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            glon = float(parts[0])
            glat = float(parts[1])
        except ValueError:
            continue
        proj = parts[2].strip()
        filename = parts[3].strip()
        rows.append(
            {"glon": glon, "glat": glat, "proj": proj, "filename": filename}
        )
    if not rows:
        raise RuntimeError("Could not parse any rows from cubes_gal.dat")
    return rows


def choose_car_tile(rows: list[dict], l_deg: float, b_deg: float) -> dict:
    """
    Select the nearest CAR cube center.

    HI4PI Galactic cubes are approximately 20° x 20°.  Nearest-center selection
    is robust for our targets, which are comfortably inside the expected tiles.
    """
    car = [r for r in rows if r["proj"].upper() == "CAR"]
    if not car:
        raise RuntimeError("No CAR rows found in cubes_gal.dat")

    def score(r):
        dl = wrapped_lon_diff(l_deg, r["glon"])
        db = b_deg - r["glat"]
        return dl * dl + db * db

    best = min(car, key=score)
    dl = abs(wrapped_lon_diff(l_deg, best["glon"]))
    db = abs(b_deg - best["glat"])
    if dl > 11.0 or db > 11.0:
        raise RuntimeError(
            f"Nearest CAR tile looks too far away: target ({l_deg},{b_deg}), "
            f"center ({best['glon']},{best['glat']})"
        )
    return best


def cube_url(row: dict) -> str:
    """
    Construct the archive URL.

    CDS stores projection-specific Galactic cubes under CUBES/GAL/<projection>/.
    """
    return f"{CDS_ROOT}/CUBES/GAL/{row['proj'].upper()}/{row['filename']}"


def extract_spectrum(fits_path: Path, l_deg: float, b_deg: float):
    """Return velocity_km_s, brightness_K, and extraction metadata."""
    from astropy.io import fits
    from astropy.wcs import WCS
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    with fits.open(fits_path, memmap=True) as hdul:
        hdu = hdul[0]
        header = hdu.header
        data = np.asarray(hdu.data)

        # Standard HI4PI cube layout is FITS axes:
        # 1 = Galactic longitude, 2 = Galactic latitude, 3 = velocity.
        # NumPy reverses FITS axis order -> [velocity, latitude, longitude].
        while data.ndim > 3:
            data = data[0]
        if data.ndim != 3:
            raise RuntimeError(f"Expected 3-D cube, got shape {data.shape}")

        ctype1 = str(header.get("CTYPE1", "")).upper()
        ctype2 = str(header.get("CTYPE2", "")).upper()
        if "GLON" not in ctype1 or "GLAT" not in ctype2:
            raise RuntimeError(
                f"Unexpected spatial WCS: CTYPE1={ctype1}, CTYPE2={ctype2}"
            )

        celestial = WCS(header).celestial
        target = SkyCoord(l=l_deg * u.deg, b=b_deg * u.deg, frame="galactic")
        xpix, ypix = celestial.world_to_pixel(target)
        ix, iy = int(round(float(xpix))), int(round(float(ypix)))

        if not (0 <= ix < data.shape[2] and 0 <= iy < data.shape[1]):
            raise RuntimeError(
                f"Target maps outside cube: pixel ({ix},{iy}), shape={data.shape}"
            )

        spec = np.asarray(data[:, iy, ix], dtype=float)

        nvel = data.shape[0]
        p = np.arange(nvel, dtype=float) + 1.0  # FITS pixels are 1-indexed
        raw_vel = (
            float(header["CRVAL3"])
            + (p - float(header["CRPIX3"])) * float(header["CDELT3"])
        )

        cunit3 = str(header.get("CUNIT3", "")).strip()
        try:
            unit = u.Unit(cunit3) if cunit3 else (u.m / u.s)
            vel = (raw_vel * unit).to(u.km / u.s).value
        except Exception:
            # Safe fallback for common velocity encodings.
            vel = raw_vel / 1000.0 if np.nanmedian(np.abs(np.diff(raw_vel))) > 10 else raw_vel

        meta = {
            "pixel_x": ix,
            "pixel_y": iy,
            "ctype1": ctype1,
            "ctype2": ctype2,
            "ctype3": str(header.get("CTYPE3", "")),
            "cunit3": cunit3,
        }
        return np.asarray(vel, float), spec, meta


def write_spectrum_csv(path: Path, velocity: np.ndarray, temp: np.ndarray):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["velocity_lsr_km_s", "brightness_temperature_K"])
        for v, t in zip(velocity, temp):
            w.writerow([f"{v:.9g}", f"{t:.9g}"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output",
        default="hi4pi_grb_data",
        help="Output directory (default: hi4pi_grb_data)",
    )
    ap.add_argument(
        "--catalog-only",
        action="store_true",
        help="Resolve target tiles but do not download FITS cubes",
    )
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    catalog = out / "cubes_gal.dat"
    print("Fetching HI4PI cube index...")
    download_resume(f"{CDS_ROOT}/cubes_gal.dat", catalog)
    rows = parse_cubes_gal(catalog)

    selected = []
    for t in TARGETS:
        row = choose_car_tile(rows, t["l_deg"], t["b_deg"])
        rec = {**t, **row, "url": cube_url(row)}
        selected.append(rec)
        print(
            f"{t['name']}: l={t['l_deg']:.2f}, b={t['b_deg']:.2f} -> "
            f"{row['filename']} center=({row['glon']:.1f},{row['glat']:.1f})"
        )

    with open(out / "selected_tiles.csv", "w", newline="") as f:
        cols = [
            "name", "l_deg", "b_deg", "glon", "glat",
            "proj", "filename", "url"
        ]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(selected)

    if args.catalog_only:
        print(f"Wrote {out / 'selected_tiles.csv'}")
        return

    # Download each unique tile only once.
    local_tiles = {}
    for r in selected:
        key = r["filename"]
        if key not in local_tiles:
            p = out / key
            print(f"Downloading {key} (resumable)...")
            download_resume(r["url"], p)
            local_tiles[key] = p

    for r in selected:
        print(f"Extracting {r['name']}...")
        vel, temp, meta = extract_spectrum(
            local_tiles[r["filename"]], r["l_deg"], r["b_deg"]
        )
        csv_path = out / f"{r['name']}_hi4pi.csv"
        write_spectrum_csv(csv_path, vel, temp)
        print(
            f"  {csv_path} — {len(vel)} channels, "
            f"pixel=({meta['pixel_x']},{meta['pixel_y']})"
        )

    print("Done.")


if __name__ == "__main__":
    main()
