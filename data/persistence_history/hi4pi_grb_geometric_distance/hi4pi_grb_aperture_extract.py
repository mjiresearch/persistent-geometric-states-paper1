#!/usr/bin/env python3
"""Aperture-average HI4PI spectra at the three GRB sightlines.

This reproduces the spatial averaging described by Vaia et al. (2026):
15 arcmin circular regions for GRB 221009A and GRB 160623A, and 30 arcmin
for GRB 031203.  It reuses the public-CDS downloader and cube-index logic in
hi4pi_grb_fetch_extract.py.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

import hi4pi_grb_fetch_extract as base

APERTURE_ARCMIN = {
    "GRB_221009A": 15.0,
    "GRB_160623A": 15.0,
    "GRB_031203": 30.0,
}


def velocity_axis(header, nvel):
    import astropy.units as u
    p = np.arange(nvel, dtype=float) + 1.0
    raw = float(header["CRVAL3"]) + (p - float(header["CRPIX3"])) * float(header["CDELT3"])
    cunit = str(header.get("CUNIT3", "")).strip()
    try:
        unit = u.Unit(cunit) if cunit else (u.m / u.s)
        return (raw * unit).to(u.km / u.s).value
    except Exception:
        return raw / 1000.0 if np.nanmedian(np.abs(np.diff(raw))) > 10 else raw


def extract_aperture(fits_path: Path, l_deg: float, b_deg: float, radius_arcmin: float):
    from astropy.io import fits
    from astropy.wcs import WCS
    from astropy.wcs.utils import proj_plane_pixel_scales
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    with fits.open(fits_path, memmap=True) as hdul:
        hdu = hdul[0]
        header = hdu.header
        data = hdu.data
        while data.ndim > 3:
            data = data[0]
        if data.ndim != 3:
            raise RuntimeError(f"Expected 3-D cube, got shape {data.shape}")

        celestial = WCS(header).celestial
        target = SkyCoord(l=l_deg*u.deg, b=b_deg*u.deg, frame="galactic")
        x0, y0 = celestial.world_to_pixel(target)

        scales = np.abs(proj_plane_pixel_scales(celestial))  # deg / pixel
        rdeg = radius_arcmin / 60.0
        rpix = int(np.ceil(rdeg / float(np.min(scales)))) + 2

        xmin = max(0, int(np.floor(x0)) - rpix)
        xmax = min(data.shape[2] - 1, int(np.ceil(x0)) + rpix)
        ymin = max(0, int(np.floor(y0)) - rpix)
        ymax = min(data.shape[1] - 1, int(np.ceil(y0)) + rpix)

        yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
        sky = celestial.pixel_to_world(xx, yy)
        sep = sky.separation(target).to_value(u.deg)
        mask = sep <= rdeg
        if not np.any(mask):
            raise RuntimeError("No spatial pixels fell inside requested aperture")

        xs = xx[mask].astype(int)
        ys = yy[mask].astype(int)
        spectra = np.asarray(data[:, ys, xs], dtype=float)
        spec = np.nanmean(spectra, axis=1)
        vel = velocity_axis(header, data.shape[0])

        return np.asarray(vel, float), spec, {
            "n_spatial_pixels": int(mask.sum()),
            "radius_arcmin": float(radius_arcmin),
            "center_pixel_x": float(x0),
            "center_pixel_y": float(y0),
        }


def write_csv(path, vel, temp):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["velocity_lsr_km_s", "brightness_temperature_K"])
        for v, t in zip(vel, temp):
            w.writerow([f"{v:.9g}", f"{t:.9g}"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="hi4pi_grb_data")
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    catalog = out / "cubes_gal.dat"
    base.download_resume(f"{base.CDS_ROOT}/cubes_gal.dat", catalog)
    rows = base.parse_cubes_gal(catalog)

    selected = []
    local_tiles = {}
    for t in base.TARGETS:
        row = base.choose_car_tile(rows, t["l_deg"], t["b_deg"])
        rec = {**t, **row, "url": base.cube_url(row),
               "aperture_radius_arcmin": APERTURE_ARCMIN[t["name"]]}
        selected.append(rec)
        if row["filename"] not in local_tiles:
            p = out / row["filename"]
            print(f"Downloading {row['filename']} (resumable)...")
            base.download_resume(rec["url"], p)
            local_tiles[row["filename"]] = p

    metadata = []
    for r in selected:
        print(f"Aperture extracting {r['name']} at {r['aperture_radius_arcmin']:.1f} arcmin...")
        vel, temp, meta = extract_aperture(
            local_tiles[r["filename"]], r["l_deg"], r["b_deg"],
            r["aperture_radius_arcmin"]
        )
        path = out / f"{r['name']}_hi4pi_aperture.csv"
        write_csv(path, vel, temp)
        metadata.append({**r, **meta, "spectrum_file": path.name})
        print(f"  {path}: {len(vel)} channels, {meta['n_spatial_pixels']} spatial pixels")

    cols = ["name","l_deg","b_deg","aperture_radius_arcmin","glon","glat","proj",
            "filename","url","n_spatial_pixels","center_pixel_x","center_pixel_y","spectrum_file"]
    with open(out / "aperture_extraction_manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(metadata)


if __name__ == "__main__":
    main()
