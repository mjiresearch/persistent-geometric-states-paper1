#!/usr/bin/env python3
"""Fetch the public SDSS VACs and exact Gaia DR3 phase space for protocol v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

from dr20_current_field_v1 import load_protocol


GAIA_TAP_SYNC = "https://gea.esac.esa.int/tap-server/tap/sync"
GAIA_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "parallax",
    "parallax_error",
    "pmra",
    "pmra_error",
    "pmdec",
    "pmdec_error",
    "radial_velocity",
    "radial_velocity_error",
    "ruwe",
    "astrometric_params_solved",
    "duplicated_source",
]


def digest(path: Path, algorithm: str = "sha1") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download(url: str, destination: Path, expected_sha1: str) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists() or digest(destination) != expected_sha1:
        partial = destination.with_suffix(destination.suffix + ".part")
        with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
        if digest(partial) != expected_sha1:
            raise RuntimeError(f"SHA1 mismatch for {url}")
        partial.replace(destination)
    return {
        "url": url,
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha1": digest(destination),
    }


def gyro_source_ids(path: Path) -> tuple[list[str], str]:
    from astropy.table import Table

    table = Table.read(path)
    lower = {str(column).lower(): str(column) for column in table.colnames}
    candidates = ["gaia_dr3_source_id", "gaiadr3_source_id", "gaia_source_id", "source_id", "gaiadr3_id"]
    column = next((lower[name] for name in candidates if name in lower), None)
    if column is None:
        raise ValueError(f"Cannot find Gaia source_id in gyro columns {table.colnames}")
    ids = pd.Series(table[column]).astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    ids = ids[ids.str.fullmatch(r"[0-9]+", na=False)].drop_duplicates().tolist()
    return ids, column


def query_gaia_batch(source_ids: list[str], retries: int = 4) -> pd.DataFrame:
    import requests

    query = (
        "SELECT "
        + ",".join(GAIA_COLUMNS)
        + " FROM gaiadr3.gaia_source WHERE source_id IN ("
        + ",".join(source_ids)
        + ")"
    )
    payload = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.post(GAIA_TAP_SYNC, data=payload, timeout=180)
            response.raise_for_status()
            from io import StringIO

            return pd.read_csv(StringIO(response.text), dtype={"source_id": "string"})
        except Exception as error:  # network services occasionally return transient 5xx responses
            last_error = error
            time.sleep(2**attempt)
    raise RuntimeError(f"Gaia TAP batch failed after {retries} attempts: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/external/sdss/dr20_independent_current_field_v1")
    )
    parser.add_argument("--batch-size", type=int, default=400)
    parser.add_argument("--skip-gaia", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = load_protocol(args.protocol)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    gyro_spec = protocol["sources"]["gyro"]
    ob_spec = protocol["sources"]["ob_kinematics"]
    gyro_path = args.output_dir / "gyro_age_dwarf-1.0.0.fits"
    ob_path = args.output_dir / "ob_vac-1.0.0.fits"
    manifest = {
        "protocol_id": protocol["protocol_id"],
        "gyro": download(gyro_spec["url"], gyro_path, gyro_spec["sha1"]),
        "ob_kinematics_coverage_audit": download(ob_spec["url"], ob_path, ob_spec["sha1"]),
    }
    ids, source_column = gyro_source_ids(gyro_path)
    manifest["gyro"]["source_id_column"] = source_column
    manifest["gyro"]["unique_valid_source_ids"] = len(ids)
    if not args.skip_gaia:
        batches = []
        for start in range(0, len(ids), args.batch_size):
            batches.append(query_gaia_batch(ids[start : start + args.batch_size]))
        gaia = pd.concat(batches, ignore_index=True)
        gaia["source_id"] = gaia["source_id"].astype("string")
        gaia = gaia.drop_duplicates("source_id").sort_values("source_id").reset_index(drop=True)
        gaia_path = args.output_dir / "gyro_gaia_dr3_exact.csv.gz"
        gaia.to_csv(gaia_path, index=False, compression="gzip")
        manifest["gaia_exact_match"] = {
            "tap_table": "gaiadr3.gaia_source",
            "join_rule": "exact integer source_id",
            "requested_unique_source_ids": len(ids),
            "returned_unique_source_ids": int(gaia["source_id"].nunique()),
            "rows_with_radial_velocity": int(pd.to_numeric(gaia["radial_velocity"], errors="coerce").notna().sum()),
            "path": str(gaia_path),
            "bytes": gaia_path.stat().st_size,
            "sha256": digest(gaia_path, "sha256"),
            "columns": GAIA_COLUMNS,
        }
    manifest_path = args.output_dir / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
