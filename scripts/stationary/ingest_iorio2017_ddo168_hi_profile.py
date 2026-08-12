#!/usr/bin/env python3
"""Ingest the public Iorio et al. (2017) DDO168 radial H I profile.

Source: OUP supplementary archive for MNRAS 466, 4159 (doi:10.1093/mnras/stw3285),
member results.zip::finalrot/ddo168_onlinetab.txt.

Only the Paper-I-relevant radius and H I surface-density columns are written.
The publisher source file is not redistributed wholesale. No distance or
inclination rescaling, helium correction, interpolation, or persistence fit is
performed.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

SUPPLEMENT_URL = "https://oup.silverchair-cdn.com/oup/backfile/Content_public/Journal/mnras/466/4/10.1093_mnras_stw3285/7/stw3285_Supplementary_Data.zip?Expires=2147483647&Key-Pair-Id=APKAIE5G5CRDK6RD3PGA&Signature=03skimALbafA23r-3ex-zWS2bc89EIZgd~sFBft28yRY0BnMlCp8ERTZ3MfyBPPnBRY14PZDhsjv10pbLm2iDQDCe6AJtwVgTgDUg5SK6OhehqDxnaGr7-Qw3qPTW9v4KLuSEWWSd4NZ3porWPOhEqrgkqApYuKdB0td17fIQ8umbOYSWDbxCc9iG8k~vEsJqEMhdo5Iy9Ims5KLMyczUekMCXBYckdRj~1yjHgRWBqUEK2aUXpKftOxgPC46hAh4xo6tndQWeu55bXUWRNWG5l~~oqqOQse6D0NjdYTNVzS8Bif1uu8LbdyV~rcCJSa7Vyu5bE-sE3SPvb133JWnw__"
SOURCE_MEMBER = "finalrot/ddo168_onlinetab.txt"
GALAXY = "DDO168"
EXPECTED_ROLE = "calibration"
SOURCE_DOI = "10.1093/mnras/stw3285"
SOURCE_DISTANCE_MPC = 4.3
SOURCE_MEAN_INCLINATION_DEG = 62.0
SOURCE_MEAN_PA_DEG = 272.7


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "PersistenceFrameworkPaperI/1.0"})
    with urlopen(req, timeout=90) as resp:
        return resp.read()


def source_text(outer_data: bytes) -> tuple[str, str]:
    with zipfile.ZipFile(io.BytesIO(outer_data)) as outer:
        nested = outer.read("results.zip")
    with zipfile.ZipFile(io.BytesIO(nested)) as results:
        raw = results.read(SOURCE_MEMBER)
    return raw.decode("utf-8", errors="strict"), sha256_bytes(raw)


def load_role(split_path: Path) -> str:
    with split_path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["galaxy"] == GALAXY:
                return row["stationary_role"]
    raise RuntimeError(f"{GALAXY} not found in frozen split")


def parse_metadata(text: str) -> dict[str, float]:
    patterns = {
        "distance": r"^# Distance:\s*([0-9.]+)\s*Mpc",
        "inclination": r"^# Mean Inclination:\s*([0-9.]+)\s*degree",
        "pa": r"^# Mean PA:\s*([0-9.]+)\s*degree",
    }
    out: dict[str, float] = {}
    for line in text.splitlines():
        for key, pattern in patterns.items():
            m = re.match(pattern, line)
            if m:
                out[key] = float(m.group(1))
    if set(out) != set(patterns):
        raise RuntimeError(f"Could not parse all source metadata: {out}")
    return out


def parse_rows(text: str) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        vals = line.split()
        if len(vals) != 12:
            raise RuntimeError(f"Unexpected DDO168 source row: {line!r}")
        nums = [float(x) for x in vals]
        rows.append(
            {
                "radius_arcsec": nums[0],
                "radius_kpc": nums[1],
                "sigma_hi": nums[10],
                "sigma_hi_err": nums[11],
            }
        )
    if len(rows) != 15:
        raise RuntimeError(f"Expected 15 DDO168 source rows, found {len(rows)}")
    for a, b in zip(rows, rows[1:]):
        if b["radius_arcsec"] <= a["radius_arcsec"] or b["radius_kpc"] <= a["radius_kpc"]:
            raise RuntimeError("Source radii are not strictly increasing")
    if any(r["sigma_hi"] < 0 or r["sigma_hi_err"] < 0 for r in rows):
        raise RuntimeError("Negative source H I density/error encountered")
    return rows


def main() -> None:
    split_path = Path("validation/stationary/stationary_split_v1.csv")
    out_path = Path("data/stationary/source_reconstruction/iorio2017_ddo168_hi_profile_v1.csv")
    summary_path = Path("validation/stationary/iorio2017_ddo168_hi_profile_v1_summary.json")

    role = load_role(split_path)
    if role != EXPECTED_ROLE:
        raise RuntimeError(f"Frozen role mismatch: expected {EXPECTED_ROLE}, got {role}")

    outer = download(SUPPLEMENT_URL)
    text, member_sha = source_text(outer)
    metadata = parse_metadata(text)
    if abs(metadata["distance"] - SOURCE_DISTANCE_MPC) > 1e-9:
        raise RuntimeError(f"Unexpected source distance: {metadata['distance']}")
    if abs(metadata["inclination"] - SOURCE_MEAN_INCLINATION_DEG) > 1e-9:
        raise RuntimeError(f"Unexpected source inclination: {metadata['inclination']}")
    if abs(metadata["pa"] - SOURCE_MEAN_PA_DEG) > 1e-9:
        raise RuntimeError(f"Unexpected source PA: {metadata['pa']}")

    rows = parse_rows(text)
    output = []
    for r in rows:
        output.append(
            {
                "galaxy": GALAXY,
                "stationary_role": role,
                "source_radius_arcsec": f"{r['radius_arcsec']:.2f}",
                "source_radius_kpc": f"{r['radius_kpc']:.2f}",
                "source_sigmaHI_msun_pc2": f"{r['sigma_hi']:.2f}",
                "source_sigmaHI_err_msun_pc2": f"{r['sigma_hi_err']:.2f}",
                "source_distance_mpc": f"{SOURCE_DISTANCE_MPC:.1f}",
                "source_mean_inclination_deg": f"{SOURCE_MEAN_INCLINATION_DEG:.1f}",
                "source_mean_pa_deg": f"{SOURCE_MEAN_PA_DEG:.1f}",
                "helium_already_included": "0",
                "primary_beam_corrected": "1",
                "source_values_transformed": "0",
                "source_doi": SOURCE_DOI,
                "source_member": "results.zip::" + SOURCE_MEMBER,
                "source_member_sha256": member_sha,
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(output[0].keys()))
        writer.writeheader()
        writer.writerows(output)

    summary = {
        "status": "RAW_PUBLIC_SOURCE_PROFILE_ACQUIRED",
        "galaxy": GALAXY,
        "stationary_role": role,
        "n_rows": len(output),
        "radius_arcsec_min": rows[0]["radius_arcsec"],
        "radius_arcsec_max": rows[-1]["radius_arcsec"],
        "radius_kpc_min": rows[0]["radius_kpc"],
        "radius_kpc_max": rows[-1]["radius_kpc"],
        "sigma_hi_min": min(r["sigma_hi"] for r in rows),
        "sigma_hi_max": max(r["sigma_hi"] for r in rows),
        "source_distance_mpc": SOURCE_DISTANCE_MPC,
        "source_mean_inclination_deg": SOURCE_MEAN_INCLINATION_DEG,
        "source_mean_pa_deg": SOURCE_MEAN_PA_DEG,
        "source_member_sha256": member_sha,
        "outer_zip_sha256": sha256_bytes(outer),
        "output_sha256": sha256_file(out_path),
        "helium_rule": (
            "Iorio source Sdens is intrinsic HI surface density not corrected for "
            "helium. Acquisition values are preserved unchanged; helium is not "
            "applied until the common Paper I normalization convention is frozen."
        ),
        "normalization_rule": (
            "No source-to-frozen distance rescaling, inclination rescaling, "
            "interpolation, extrapolation, taper, or persistence evaluation performed."
        ),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
