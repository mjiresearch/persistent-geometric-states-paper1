#!/usr/bin/env python3
"""Fetch the public Leroy+2008 THINGS radial H I profiles used by Paper I.

Source:
  VizieR J/AJ/136/2782/table7 (Leroy et al. 2008, AJ 136, 2782).

This is a source-acquisition step only. It preserves the source-published
helium-inclusive SigmaHI values and source radius. It does not rescale radii,
remove helium, interpolate profiles, or evaluate persistence parameters.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CATALOG = "J/AJ/136/2782/table7"
VIZIER_ENDPOINT = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"

EXPECTED_ROLES = {
    "DDO154": "calibration",
    "IC2574": "calibration",
    "NGC2403": "blind",
    "NGC2841": "calibration",
    "NGC2976": "calibration",
    "NGC3198": "calibration",
    "NGC3521": "blind",
    "NGC5055": "blind",
    "NGC6946": "blind",
    "NGC7331": "calibration",
    "NGC7793": "blind",
}

SOURCE_COLUMNS = ["Name", "r", "r.n", "SigmaHI", "e_SigmaHI"]


def canonicalize_source_name(name: str) -> str:
    """Map VizieR display names such as ``NGC 2403`` to SPARC-style IDs."""
    return "".join(name.split())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_url() -> str:
    query = urlencode(
        {
            "-source": CATALOG,
            "-out": ",".join(SOURCE_COLUMNS),
            "-out.max": "10000",
        }
    )
    return f"{VIZIER_ENDPOINT}?{query}"


def fetch_text(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "PersistenceFrameworkPaperI/1.0 "
            "(public-reproducibility source acquisition)"
        },
    )
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="strict")


def read_text(path: Path | None, url: str) -> str:
    if path is not None:
        return path.read_text(encoding="utf-8")
    return fetch_text(url)


def parse_vizier_tsv(text: str) -> list[dict[str, str]]:
    """Parse an ASU-TSV response while ignoring VizieR metadata/comment rows."""
    lines = text.splitlines()
    header_idx = None
    header = None
    for idx, line in enumerate(lines):
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if all(name in cols for name in SOURCE_COLUMNS):
            header_idx = idx
            header = cols
            break
    if header_idx is None or header is None:
        raise RuntimeError("Could not locate the expected VizieR table7 header.")

    rows: list[dict[str, str]] = []
    for line in lines[header_idx + 1 :]:
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        # VizieR often places a dashed units/separator row below the header.
        if cols and all((not c) or set(c) <= {"-"} for c in cols):
            continue
        if len(cols) != len(header):
            continue
        row = dict(zip(header, cols))
        name = row.get("Name", "").strip()
        if not name:
            continue
        rows.append({key: row.get(key, "").strip() for key in SOURCE_COLUMNS})
    return rows


def load_split(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return {
            row["galaxy"]: row["stationary_role"]
            for row in csv.DictReader(fh)
        }


def finite_float(value: str, *, allow_blank: bool = False) -> float | None:
    value = value.strip()
    if not value or value in {"--", "---"}:
        if allow_blank:
            return None
        raise ValueError("required numeric value is blank")
    x = float(value)
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError(f"non-finite value: {value!r}")
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--split",
        default="validation/stationary/stationary_split_v1.csv",
        help="Frozen 104/45 split CSV used only to verify immutable roles.",
    )
    ap.add_argument(
        "--input-tsv",
        help="Optional previously downloaded VizieR ASU-TSV file for offline replay.",
    )
    ap.add_argument(
        "--out",
        default="data/stationary/source_reconstruction/"
        "leroy2008_things_hi_profiles_v1.csv",
    )
    ap.add_argument(
        "--summary",
        default="validation/stationary/"
        "leroy2008_things_hi_profiles_v1_summary.json",
    )
    args = ap.parse_args()

    split_path = Path(args.split)
    input_path = Path(args.input_tsv) if args.input_tsv else None
    out_path = Path(args.out)
    summary_path = Path(args.summary)

    roles = load_split(split_path)
    for galaxy, expected_role in EXPECTED_ROLES.items():
        actual = roles.get(galaxy)
        if actual != expected_role:
            raise RuntimeError(
                f"Frozen role mismatch for {galaxy}: "
                f"expected {expected_role}, got {actual!r}"
            )

    url = build_url()
    source_rows = parse_vizier_tsv(read_text(input_path, url))

    retained = [
        r for r in source_rows
        if canonicalize_source_name(r["Name"]) in EXPECTED_ROLES
    ]
    found = {canonicalize_source_name(r["Name"]) for r in retained}
    missing = set(EXPECTED_ROLES) - found
    if missing:
        raise RuntimeError(f"Missing expected Leroy profiles: {sorted(missing)}")

    output_rows = []
    seen_keys: set[tuple[str, float]] = set()
    last_radius: dict[str, float] = {}

    for row in retained:
        source_name = row["Name"]
        galaxy = canonicalize_source_name(source_name)
        radius = finite_float(row["r"])
        sigma_hi = finite_float(row["SigmaHI"], allow_blank=True)
        sigma_err = finite_float(row["e_SigmaHI"], allow_blank=True)
        rnorm = finite_float(row["r.n"], allow_blank=True)
        assert radius is not None
        if radius < 0:
            raise RuntimeError(f"Negative source radius for {galaxy}: {radius}")

        key = (galaxy, radius)
        if key in seen_keys:
            raise RuntimeError(f"Duplicate source key: {key}")
        seen_keys.add(key)

        previous = last_radius.get(galaxy)
        if previous is not None and radius <= previous:
            raise RuntimeError(
                f"Non-increasing Leroy source radius for {galaxy}: "
                f"{previous} -> {radius}"
            )
        last_radius[galaxy] = radius

        output_rows.append(
            {
                "galaxy": galaxy,
                "stationary_role": EXPECTED_ROLES[galaxy],
                "source_name_vizier": source_name,
                "source_catalog": "J/AJ/136/2782",
                "source_table": "table7",
                "source_radius_kpc": f"{radius:g}",
                "source_radius_over_r25": "" if rnorm is None else f"{rnorm:g}",
                "source_sigmaHI_including_helium_msun_pc2": (
                    "" if sigma_hi is None else f"{sigma_hi:g}"
                ),
                "source_sigmaHI_rms_msun_pc2": (
                    "" if sigma_err is None else f"{sigma_err:g}"
                ),
                "helium_already_included": "1",
                "source_values_transformed": "0",
                "source_bibcode": "2008AJ....136.2782L",
                "source_doi": "10.1088/0004-6256/136/6/2782",
                "vizier_catalog_doi": "10.26093/cds/vizier.51362782",
            }
        )

    output_rows.sort(key=lambda r: (r["galaxy"], float(r["source_radius_kpc"])))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(output_rows[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    counts = {
        galaxy: sum(r["galaxy"] == galaxy for r in output_rows)
        for galaxy in EXPECTED_ROLES
    }
    summary = {
        "status": "RAW_PUBLIC_SOURCE_PROFILE_ACQUIRED",
        "source_catalog": "J/AJ/136/2782/table7",
        "source_url": url,
        "source_rows_total": len(source_rows),
        "retained_rows": len(output_rows),
        "n_galaxies": len(found),
        "n_calibration": sum(v == "calibration" for v in EXPECTED_ROLES.values()),
        "n_blind": sum(v == "blind" for v in EXPECTED_ROLES.values()),
        "rows_per_galaxy": counts,
        "helium_rule": (
            "Source-published SigmaHI already includes helium; values preserved "
            "unchanged. No second helium correction and no raw-HI back-conversion "
            "in this acquisition product."
        ),
        "normalization_rule": (
            "No distance rescaling, inclination rescaling, interpolation, "
            "extrapolation, taper, or persistence evaluation performed."
        ),
        "split_sha256": sha256(split_path),
        "output_sha256": sha256(out_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
