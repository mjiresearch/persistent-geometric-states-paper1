#!/usr/bin/env python3
"""Recover SG06 historical VLA program metadata from the NRAO TAP archive.

The published SG06 Sigma_HI panels are rasterized in the arXiv source package,
but the paper reports new VLA observations in 2001-2002. NRAO's current archive
provides scripted metadata access through its TAP/ObsCore service. This bounded
audit queries that service for SG06 target-name variants in the paper's date
window and L-band frequency range, recording public execution-block/file-set IDs
that can be used to retrieve the original visibility data through the NRAO AAT.

Metadata/provenance only. No visibility download, calibration, imaging, radial
profile reconstruction, persistence fitting, or blind-outcome inspection occurs.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pyvo

TAP = "https://data-query.nrao.edu/tap"
OUT = Path("validation/stationary/sg06_nrao_archive_metadata_audit_v1.json")
TARGETS = {
    "ESO563-G021": ["ESO563", "ESO 563", "563G21", "563-G21", "563G021", "563-G021"],
    "IC4202": ["IC4202", "IC 4202", "4202"],
    "NGC2955": ["NGC2955", "NGC 2955", "2955"],
    "NGC6195": ["NGC6195", "NGC 6195", "6195"],
    "UGC11455": ["UGC11455", "UGC 11455", "11455"],
}


def mjd(s: str) -> float:
    dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    unix_days = dt.timestamp() / 86400.0
    return unix_days + 40587.0


def safe(v):
    try:
        if hasattr(v, "item"):
            v = v.item()
    except Exception:
        pass
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def main() -> None:
    service = pyvo.dal.TAPService(TAP)
    start = mjd("2001-06-01")
    end = mjd("2003-02-01")

    # Numeric substrings are intentionally included because historical VLA
    # target naming is not perfectly standardized (spaces, prefixes, hyphens).
    needles = sorted({x.upper().replace(" ", "") for vals in TARGETS.values() for x in vals})
    clauses = []
    for n in needles:
        # Keep the distinctive numeric portion for archive aliases.
        digits = "".join(re.findall(r"\d+", n))
        if len(digits) >= 4:
            clauses.append(f"UPPER(target_name) LIKE '%{digits}%'")
    clauses = sorted(set(clauses))

    query = f"""
    SELECT TOP 10000
      obs_id, obs_publisher_did, target_name, t_min, t_max, t_exptime,
      freq_min, freq_max, center_frequencies, bandwidths, nums_channels,
      spectral_resolutions, facility_name, instrument_name, configuration,
      dataproduct_type, access_url, access_estsize, s_ra, s_dec
    FROM ivoa.obscore
    WHERE t_min >= {start:.8f} AND t_min <= {end:.8f}
      AND UPPER(instrument_name) LIKE '%VLA%'
      AND freq_min < 1.50e9 AND freq_max > 1.30e9
      AND ({' OR '.join(clauses)})
    """
    table = service.search(query).to_table()
    rows = []
    for r in table:
        rec = {name: safe(r[name]) for name in table.colnames}
        rows.append(rec)

    per = {g: [] for g in TARGETS}
    for rec in rows:
        tn = str(rec.get("target_name") or "").upper().replace(" ", "").replace("-", "")
        for g, aliases in TARGETS.items():
            for a in aliases:
                aa = a.upper().replace(" ", "").replace("-", "")
                digits = "".join(re.findall(r"\d+", aa))
                if (aa and aa in tn) or (len(digits) >= 4 and digits in tn):
                    per[g].append(rec)
                    break

    # Project/execution identifiers are usually encoded in obs_id or
    # obs_publisher_did; retain unique values exactly as the archive returns them.
    ids = sorted({
        str(v)
        for rec in rows
        for k in ("obs_id", "obs_publisher_did")
        for v in [rec.get(k)] if v not in (None, "")
    })
    result = {
        "status": "SG06_NRAO_ARCHIVE_METADATA_AUDIT_COMPLETE",
        "tap_service": TAP,
        "query": " ".join(query.split()),
        "date_window": ["2001-06-01", "2003-02-01"],
        "frequency_window_hz": [1.30e9, 1.50e9],
        "n_rows": len(rows),
        "n_unique_archive_identifiers": len(ids),
        "archive_identifiers": ids,
        "target_match_counts": {g: len(v) for g, v in per.items()},
        "target_matches": per,
        "all_rows": rows,
        "route_viable": all(len(per[g]) > 0 for g in TARGETS),
        "interpretation_rule": (
            "A metadata match establishes that public historical VLA visibility data for the target/time/frequency exists in the NRAO archive. "
            "It does not reproduce SG06's published Sigma_HI profile. Any visibility-level reconstruction would require a separately frozen "
            "calibration/imaging/deconvolution protocol and validation against the paper before profile promotion."
        ),
        "boundary": (
            "Archive metadata only. No visibility download, calibration, imaging, radial-profile reconstruction, persistence fitting, or blind outcomes."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "n_rows": len(rows),
        "target_match_counts": result["target_match_counts"],
        "archive_identifiers": ids,
        "route_viable": result["route_viable"],
    }, indent=2))


if __name__ == "__main__":
    main()
