#!/usr/bin/env python3
"""Rebuild the frozen stationary SPARC observational master table.

This script intentionally constructs observational inputs only. It does not fit
or evaluate L_A, C_A, tau_A, or any persistence-model prediction.

Inputs
------
1. validation/stationary/stationary_sample_manifest_v1.csv
2. An extracted official SPARC Rotmod_LTG.zip directory containing
   <galaxy>_rotmod.dat files.

Output
------
data/stationary/frozen/stationary_master_v1.csv

The expected SHA-256 is pinned so an upstream-data or parsing change fails
loudly instead of silently changing the frozen analysis input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
from pathlib import Path

EXPECTED_SHA256 = "254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f"

FIELDS = [
    "galaxy",
    "distance_mpc",
    "radius_kpc",
    "v_obs_kms",
    "v_err_kms",
    "v_gas_kms",
    "v_disk_ml1_kms",
    "v_bulge_ml1_kms",
    "sb_disk_lsun_pc2",
    "sb_bulge_lsun_pc2",
    "quality_flag",
    "inclination_deg",
    "n_points_galaxy",
    "galaxy_point_index",
    "signed_gas_negative_flag",
    "source_file",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def locate_rotmod(root: Path, galaxy: str) -> Path:
    filename = f"{galaxy}_rotmod.dat"
    direct = root / filename
    if direct.exists():
        return direct
    matches = list(root.rglob(filename))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one {filename} below {root}; found {len(matches)}"
        )
    return matches[0]


def parse_rotmod(path: Path) -> tuple[float, list[dict[str, float]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Empty SPARC file: {path}")

    m = re.search(r"Distance\s*=\s*([0-9.]+)\s*Mpc", lines[0])
    if not m:
        raise ValueError(f"Distance header not found in {path}")
    distance = float(m.group(1))

    points: list[dict[str, float]] = []
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        values = line.split()
        if len(values) < 8:
            continue
        r, vobs, verr, vgas, vdisk, vbul, sbdisk, sbbul = map(float, values[:8])
        nums = [r, vobs, verr, vgas, vdisk, vbul, sbdisk, sbbul]
        if not all(math.isfinite(x) for x in nums):
            continue
        if r <= 0 or verr <= 0:
            continue
        points.append(
            {
                "radius_kpc": r,
                "v_obs_kms": vobs,
                "v_err_kms": verr,
                "v_gas_kms": vgas,
                "v_disk_ml1_kms": vdisk,
                "v_bulge_ml1_kms": vbul,
                "sb_disk_lsun_pc2": sbdisk,
                "sb_bulge_lsun_pc2": sbbul,
            }
        )
    return distance, points


def fmt(x: float) -> str:
    return f"{x:.12g}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--rotmod-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--expected-sha256", default=EXPECTED_SHA256)
    args = ap.parse_args()

    with args.manifest.open(newline="", encoding="utf-8-sig") as f:
        manifest = list(csv.DictReader(f))

    rows: list[dict[str, str]] = []
    for meta in manifest:
        galaxy = meta["galaxy"]
        quality = int(float(meta["quality_flag"]))
        inclination = float(meta["inclination_deg"])

        # The manifest itself is an eligibility record; assert the frozen cuts.
        if quality > 2:
            raise ValueError(f"Manifest includes Q>2 galaxy: {galaxy}")
        if inclination < 30:
            raise ValueError(f"Manifest includes i<30 deg galaxy: {galaxy}")

        source = locate_rotmod(args.rotmod_root, galaxy)
        distance, points = parse_rotmod(source)
        if len(points) < 5:
            raise ValueError(f"Manifest galaxy has <5 valid radial points: {galaxy}")
        if len(points) != int(meta["n_points"]):
            raise ValueError(
                f"Point-count mismatch for {galaxy}: rotmod={len(points)}, "
                f"manifest={meta['n_points']}"
            )

        radii = [p["radius_kpc"] for p in points]
        if any(b <= a for a, b in zip(radii, radii[1:])):
            raise ValueError(f"Non-increasing radial order: {galaxy}")

        for j, p in enumerate(points):
            rows.append(
                {
                    "galaxy": galaxy,
                    "distance_mpc": fmt(distance),
                    "radius_kpc": fmt(p["radius_kpc"]),
                    "v_obs_kms": fmt(p["v_obs_kms"]),
                    "v_err_kms": fmt(p["v_err_kms"]),
                    "v_gas_kms": fmt(p["v_gas_kms"]),
                    "v_disk_ml1_kms": fmt(p["v_disk_ml1_kms"]),
                    "v_bulge_ml1_kms": fmt(p["v_bulge_ml1_kms"]),
                    "sb_disk_lsun_pc2": fmt(p["sb_disk_lsun_pc2"]),
                    "sb_bulge_lsun_pc2": fmt(p["sb_bulge_lsun_pc2"]),
                    "quality_flag": str(quality),
                    "inclination_deg": fmt(inclination),
                    "n_points_galaxy": str(len(points)),
                    "galaxy_point_index": str(j),
                    "signed_gas_negative_flag": "1" if p["v_gas_kms"] < 0 else "0",
                    "source_file": source.name,
                }
            )

    if len(manifest) != 149:
        raise ValueError(f"Expected 149 galaxies, found {len(manifest)}")
    if len(rows) != 3152:
        raise ValueError(f"Expected 3152 rows, found {len(rows)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    digest = sha256_file(args.output)
    print(f"Wrote {len(rows)} rows for {len(manifest)} galaxies")
    print(f"SHA256 {digest}")
    if digest != args.expected_sha256:
        raise SystemExit(
            "Frozen-master hash mismatch. Do not replace the existing master "
            f"without a version change. Expected {args.expected_sha256}, got {digest}."
        )


if __name__ == "__main__":
    main()
