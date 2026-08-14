#!/usr/bin/env python3
"""Build and evaluate the frozen DR20 young-old current-field sample."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from dr20_current_field_v1 import analyze_current_field, load_protocol


def read_table(path: Path, *, source_id_as_string: bool = False) -> pd.DataFrame:
    suffixes = path.suffixes
    if path.suffix.lower() in {".fits", ".fit", ".fz"}:
        from astropy.table import Table

        return Table.read(path).to_pandas()
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    dtype = {"source_id": "string"} if source_id_as_string else None
    return pd.read_csv(path, low_memory=False, dtype=dtype)


def resolve_column(frame: pd.DataFrame, candidates: list[str], explicit: str | None, role: str) -> str:
    if explicit:
        if explicit not in frame.columns:
            raise ValueError(f"Requested {role} column {explicit!r} is absent; columns={list(frame.columns)}")
        return explicit
    lower = {str(column).lower(): str(column) for column in frame.columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    raise ValueError(f"Could not resolve {role}; tried {candidates}; columns={list(frame.columns)}")


def _numeric(series: pd.Series) -> np.ndarray:
    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)


def standardize_gyro(gyro: pd.DataFrame, args: argparse.Namespace) -> tuple[pd.DataFrame, dict]:
    source_column = resolve_column(
        gyro,
        ["gaia_dr3_source_id", "gaiadr3_source_id", "gaia_source_id", "source_id", "gaiadr3_id"],
        args.source_id_column,
        "Gaia DR3 source_id",
    )
    age_column = resolve_column(
        gyro,
        ["age_gyr", "gyro_age_gyr", "gyro_age", "age"],
        args.age_column,
        "gyro age",
    )
    symmetric_error = None
    try:
        lower_column = resolve_column(
            gyro,
            ["age_err_lower_gyr", "age_lerr", "age_err_low", "age_err_minus", "e_age_low"],
            args.age_error_lower_column,
            "lower age error",
        )
    except ValueError:
        lower_column = ""
    try:
        upper_column = resolve_column(
            gyro,
            ["age_err_upper_gyr", "age_uerr", "age_err_high", "age_err_plus", "e_age_high"],
            args.age_error_upper_column,
            "upper age error",
        )
    except ValueError:
        upper_column = ""
    if not lower_column or not upper_column:
        symmetric_error = resolve_column(
            gyro,
            ["age_err_gyr", "gyro_age_err", "age_err", "e_age", "age_error"],
            args.age_error_column,
            "symmetric age error",
        )
        lower_column = upper_column = symmetric_error

    age_raw = _numeric(gyro[age_column])
    lower_raw = np.abs(_numeric(gyro[lower_column]))
    upper_raw = np.abs(_numeric(gyro[upper_column]))
    if args.age_is_log10_years:
        age = np.power(10.0, age_raw) / 1.0e9
        lower = age - np.power(10.0, age_raw - lower_raw) / 1.0e9
        upper = np.power(10.0, age_raw + upper_raw) / 1.0e9 - age
        unit_rule = "log10(years) converted to Gyr with asymmetric linear errors"
    else:
        finite_age = age_raw[np.isfinite(age_raw)]
        scale = 1.0e-9 if finite_age.size and float(np.nanmedian(finite_age)) > 1.0e6 else 1.0
        age, lower, upper = age_raw * scale, lower_raw * scale, upper_raw * scale
        unit_rule = "catalog age interpreted as years" if scale != 1 else "catalog age interpreted as Gyr"

    source_text = gyro[source_column].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    standardized = pd.DataFrame(
        {
            "source_id": source_text,
            "age_gyr": age,
            "age_err_lower_gyr": lower,
            "age_err_upper_gyr": upper,
        }
    )
    standardized = standardized[standardized["source_id"].str.fullmatch(r"[0-9]+", na=False)].copy()
    duplicated = standardized["source_id"].duplicated(keep=False)
    if duplicated.any():
        raise ValueError(
            f"Gyro catalog contains {int(duplicated.sum())} duplicate exact source_id rows; "
            "the frozen protocol does not permit outcome-informed de-duplication"
        )
    mapping = {
        "source_id_column": source_column,
        "age_column": age_column,
        "age_error_lower_column": lower_column,
        "age_error_upper_column": upper_column,
        "symmetric_error_column": symmetric_error,
        "age_unit_rule": unit_rule,
        "standardized_rows": int(len(standardized)),
    }
    return standardized, mapping


def build_phase_space(gyro: pd.DataFrame, gaia: pd.DataFrame, protocol: dict) -> tuple[pd.DataFrame, dict]:
    from astropy import units as u
    from astropy.coordinates import CartesianDifferential, Galactocentric, SkyCoord

    lower = {str(column).lower(): str(column) for column in gaia.columns}
    rename = {}
    for required in [
        "source_id",
        "ra",
        "dec",
        "parallax",
        "parallax_error",
        "pmra",
        "pmdec",
        "radial_velocity",
        "ruwe",
        "duplicated_source",
    ]:
        if required not in lower:
            raise ValueError(f"Gaia exact-match table is missing {required!r}; columns={list(gaia.columns)}")
        rename[lower[required]] = required
    gaia = gaia.rename(columns=rename).copy()
    gaia["source_id"] = gaia["source_id"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    if gaia["source_id"].duplicated().any():
        raise ValueError("Gaia input contains duplicate source_id rows")
    joined = gyro.merge(gaia, on="source_id", how="left", validate="one_to_one", indicator=True)
    numeric = ["ra", "dec", "parallax", "parallax_error", "pmra", "pmdec", "radial_velocity", "ruwe"]
    for column in numeric:
        joined[column] = pd.to_numeric(joined[column], errors="coerce")
    duplicate_flag = joined["duplicated_source"].astype("string").str.lower().isin(["true", "1", "t", "yes"])
    finite = np.isfinite(joined[numeric].to_numpy(dtype=float)).all(axis=1)
    quality = (
        (joined["_merge"] == "both")
        & finite
        & (joined["parallax"] > 0)
        & (joined["parallax_error"] > 0)
        & ((joined["parallax"] / joined["parallax_error"]) >= 10.0)
        & (joined["ruwe"] <= 1.4)
        & (~duplicate_flag)
    )
    d = joined.loc[quality].copy()
    d["distance_kpc"] = 1.0 / d["parallax"]
    sky = SkyCoord(
        ra=d["ra"].to_numpy(dtype=float) * u.deg,
        dec=d["dec"].to_numpy(dtype=float) * u.deg,
        distance=d["distance_kpc"].to_numpy(dtype=float) * u.kpc,
        pm_ra_cosdec=d["pmra"].to_numpy(dtype=float) * u.mas / u.yr,
        pm_dec=d["pmdec"].to_numpy(dtype=float) * u.mas / u.yr,
        radial_velocity=d["radial_velocity"].to_numpy(dtype=float) * u.km / u.s,
        frame="icrs",
    )
    frame_spec = protocol["field_test"]["galactocentric_frame"]
    galactocentric = Galactocentric(
        galcen_distance=float(frame_spec["galcen_distance_kpc"]) * u.kpc,
        z_sun=float(frame_spec["z_sun_kpc"]) * u.kpc,
        galcen_v_sun=CartesianDifferential(
            np.asarray(frame_spec["galcen_v_sun_cartesian_kms"], dtype=float) * u.km / u.s
        ),
    )
    transformed = sky.transform_to(galactocentric)
    x = transformed.cartesian.x.to_value(u.kpc)
    y = transformed.cartesian.y.to_value(u.kpc)
    z = transformed.cartesian.z.to_value(u.kpc)
    vx = transformed.velocity.d_x.to_value(u.km / u.s)
    vy = transformed.velocity.d_y.to_value(u.km / u.s)
    vz = transformed.velocity.d_z.to_value(u.km / u.s)
    radius = np.hypot(x, y)
    v_r = (x * vx + y * vy) / radius
    v_phi = (-y * vx + x * vy) / radius
    sign = -1.0 if float(np.nanmedian(v_phi)) < 0 else 1.0
    d["x_kpc"], d["y_kpc"], d["z_kpc"] = x, y, z
    d["R_kpc"] = radius
    d["phi_deg"] = (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0
    d["v_R_kms"], d["v_phi_kms"], d["v_z_kms"] = v_r, sign * v_phi, vz
    report = {
        "gyro_rows": int(len(gyro)),
        "exact_gaia_matches": int((joined["_merge"] == "both").sum()),
        "quality_6d_rows": int(len(d)),
        "v_phi_sign_applied": sign,
    }
    return d, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gyro", type=Path, required=True)
    parser.add_argument("--gaia", type=Path, required=True)
    parser.add_argument(
        "--protocol", type=Path, default=Path("data/persistence_history/dr20_independent/protocol_v1.json")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/persistence_history/dr20_independent/field_v1")
    )
    parser.add_argument("--source-id-column")
    parser.add_argument("--age-column")
    parser.add_argument("--age-error-column")
    parser.add_argument("--age-error-lower-column")
    parser.add_argument("--age-error-upper-column")
    parser.add_argument("--age-is-log10-years", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = load_protocol(args.protocol)
    if protocol["status"] != "frozen_pre_outcome":
        raise RuntimeError("Refusing to run an unfrozen protocol")
    gyro_raw = read_table(args.gyro)
    gyro, gyro_mapping = standardize_gyro(gyro_raw, args)
    gaia = read_table(args.gaia, source_id_as_string=True)
    phase_space, phase_report = build_phase_space(gyro, gaia, protocol)
    summary, voxels, permutations = analyze_current_field(phase_space, protocol)
    summary["gyro_schema_mapping"] = gyro_mapping
    summary["phase_space_build"] = phase_report
    args.output_dir.mkdir(parents=True, exist_ok=True)
    phase_space.to_csv(args.output_dir / "field_star_sample.csv.gz", index=False, compression="gzip")
    voxels.to_csv(args.output_dir / "field_voxel_currents.csv", index=False)
    pd.DataFrame({"T_permuted": permutations}).to_csv(
        args.output_dir / "field_permutation_distribution.csv.gz", index=False, compression="gzip"
    )
    (args.output_dir / "field_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
