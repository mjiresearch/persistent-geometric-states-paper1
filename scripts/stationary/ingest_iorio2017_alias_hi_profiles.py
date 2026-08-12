#!/usr/bin/env python3
"""Ingest Iorio et al. (2017) H I profiles hidden by DDO/UGC aliases.

Frozen Paper I aliases recovered from the LITTLE THINGS supplement:
  DDO 87  = UGC 5918 -> UGC05918
  DDO 126 = UGC 7559 -> UGC07559

The script selectively extracts only the Paper-I-relevant radius and Sdens
columns from the public OUP supplement. It does not redistribute the full
publisher archive or perform any normalization/persistence fit.
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
SOURCE_DOI = "10.1093/mnras/stw3285"

TARGETS = {
    "DDO87": {
        "canonical": "UGC05918",
        "role": "calibration",
        "member": "finalrot/ddo87_onlinetab.txt",
        "alias": "DDO 87 = UGC 5918",
    },
    "DDO126": {
        "canonical": "UGC07559",
        "role": "calibration",
        "member": "finalrot/ddo126_onlinetab.txt",
        "alias": "DDO 126 = UGC 7559",
    },
}


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


def load_split(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return {row["galaxy"]: row["stationary_role"] for row in csv.DictReader(fh)}


def nested_results(outer_data: bytes) -> zipfile.ZipFile:
    with zipfile.ZipFile(io.BytesIO(outer_data)) as outer:
        nested = outer.read("results.zip")
    return zipfile.ZipFile(io.BytesIO(nested))


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
        raise RuntimeError(f"Incomplete Iorio source metadata: {out}")
    return out


def parse_rows(text: str) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        vals = line.split()
        if len(vals) != 12:
            raise RuntimeError(f"Unexpected Iorio source row: {line!r}")
        nums = [float(v) for v in vals]
        rows.append(
            {
                "radius_arcsec": nums[0],
                "radius_kpc": nums[1],
                "sigma_hi": nums[10],
                "sigma_hi_err": nums[11],
            }
        )
    if not rows:
        raise RuntimeError("No numerical rows in Iorio source table")
    for a, b in zip(rows, rows[1:]):
        if b["radius_arcsec"] <= a["radius_arcsec"] or b["radius_kpc"] <= a["radius_kpc"]:
            raise RuntimeError("Iorio source radii are not strictly increasing")
    if any(r["sigma_hi"] < 0 or r["sigma_hi_err"] < 0 for r in rows):
        raise RuntimeError("Negative H I density/error in Iorio source table")
    return rows


def main() -> None:
    split_path = Path("validation/stationary/stationary_split_v1.csv")
    out_path = Path("data/stationary/source_reconstruction/iorio2017_alias_hi_profiles_v1.csv")
    summary_path = Path("validation/stationary/iorio2017_alias_hi_profiles_v1_summary.json")

    roles = load_split(split_path)
    for cfg in TARGETS.values():
        actual = roles.get(cfg["canonical"])
        if actual != cfg["role"]:
            raise RuntimeError(
                f"Frozen role mismatch for {cfg['canonical']}: expected {cfg['role']}, got {actual!r}"
            )

    outer = download(SUPPLEMENT_URL)
    output: list[dict[str, str]] = []
    summaries: dict[str, dict] = {}

    with nested_results(outer) as results:
        for source_name, cfg in TARGETS.items():
            raw = results.read(cfg["member"])
            text = raw.decode("utf-8", errors="strict")
            member_sha = sha256_bytes(raw)
            meta = parse_metadata(text)
            rows = parse_rows(text)

            for r in rows:
                output.append(
                    {
                        "galaxy": cfg["canonical"],
                        "stationary_role": cfg["role"],
                        "source_name": source_name,
                        "verified_alias": cfg["alias"],
                        "source_radius_arcsec": f"{r['radius_arcsec']:.2f}",
                        "source_radius_kpc": f"{r['radius_kpc']:.2f}",
                        "source_sigmaHI_msun_pc2": f"{r['sigma_hi']:.2f}",
                        "source_sigmaHI_err_msun_pc2": f"{r['sigma_hi_err']:.2f}",
                        "source_distance_mpc": f"{meta['distance']:.3g}",
                        "source_mean_inclination_deg": f"{meta['inclination']:.3g}",
                        "source_mean_pa_deg": f"{meta['pa']:.4g}",
                        "helium_already_included": "0",
                        "primary_beam_corrected": "1",
                        "source_values_transformed": "0",
                        "source_doi": SOURCE_DOI,
                        "source_member": "results.zip::" + cfg["member"],
                        "source_member_sha256": member_sha,
                    }
                )

            summaries[cfg["canonical"]] = {
                "source_name": source_name,
                "verified_alias": cfg["alias"],
                "n_rows": len(rows),
                "radius_arcsec_min": rows[0]["radius_arcsec"],
                "radius_arcsec_max": rows[-1]["radius_arcsec"],
                "radius_kpc_min": rows[0]["radius_kpc"],
                "radius_kpc_max": rows[-1]["radius_kpc"],
                "sigma_hi_min": min(r["sigma_hi"] for r in rows),
                "sigma_hi_max": max(r["sigma_hi"] for r in rows),
                "source_distance_mpc": meta["distance"],
                "source_mean_inclination_deg": meta["inclination"],
                "source_mean_pa_deg": meta["pa"],
                "source_member_sha256": member_sha,
            }

    output.sort(key=lambda r: (r["galaxy"], float(r["source_radius_kpc"])))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(output[0].keys()))
        writer.writeheader()
        writer.writerows(output)

    summary = {
        "status": "RAW_PUBLIC_ALIAS_PROFILES_ACQUIRED",
        "source_doi": SOURCE_DOI,
        "n_galaxies": len(TARGETS),
        "n_rows": len(output),
        "galaxies": summaries,
        "outer_zip_sha256": sha256_bytes(outer),
        "output_sha256": sha256_file(out_path),
        "helium_rule": (
            "Iorio Sdens is intrinsic HI surface density and is not corrected for helium. "
            "Values are preserved unchanged; common Paper I helium treatment remains locked."
        ),
        "normalization_rule": (
            "No distance/inclination rescaling, interpolation, extrapolation, taper, "
            "or persistence evaluation performed."
        ),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
