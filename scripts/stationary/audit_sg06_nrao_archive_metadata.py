#!/usr/bin/env python3
"""Recover SG06 historical VLA program metadata from the NRAO TAP archive.

The published SG06 Sigma_HI panels are rasterized in the arXiv source package,
but the paper reports new VLA observations in 2001-2002. NRAO's current archive
provides scripted metadata access through TAP. This audit first discovers the
actual registered archive table/column names from TAP_SCHEMA, then queries SG06
target-number substrings in the paper's date window and L-band frequency range.

The NRAO TAP dialect does not expose SQL UPPER(), so all string matching in ADQL
uses numeric target substrings only; final target/instrument classification is
done locally in Python.

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
    return dt.timestamp() / 86400.0 + 40587.0


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


def discover_archive_table(service):
    tt = service.search("SELECT table_name, description FROM TAP_SCHEMA.tables").to_table()
    tables = [{"table_name": str(r["table_name"]), "description": str(r["description"])} for r in tt]
    candidates = []
    for r in tables:
        name = r["table_name"]
        low = (name + " " + r["description"]).lower()
        if "obscore" in low or "observation" in low or "archive" in low:
            candidates.append(name)
    scored = []
    for name in candidates or [r["table_name"] for r in tables]:
        qname = name.replace("'", "''")
        try:
            ct = service.search(
                f"SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name='{qname}'"
            ).to_table()
        except Exception:
            continue
        cols = {str(r["column_name"]) for r in ct}
        need = {"target_name", "t_min", "freq_min", "freq_max", "instrument_name"}
        score = len(need & cols)
        if score:
            scored.append((score, name, sorted(cols)))
    if not scored:
        raise RuntimeError(f"No NRAO archive observation table found; discovered tables={tables}")
    scored.sort(reverse=True)
    score, name, cols = scored[0]
    if score < 5:
        raise RuntimeError(f"Best TAP table lacks required archive fields: {name} score={score} cols={cols}")
    return name, cols, tables, scored[:20]


def main() -> None:
    service = pyvo.dal.TAPService(TAP)
    table_name, available_cols, discovered_tables, table_scores = discover_archive_table(service)
    start = mjd("2001-06-01")
    end = mjd("2003-02-01")

    digits_by_target = {}
    for g, vals in TARGETS.items():
        digs = set()
        for n in vals:
            d = "".join(re.findall(r"\d+", n))
            if len(d) >= 4:
                digs.add(d)
        digits_by_target[g] = sorted(digs)
    all_digits = sorted({d for vals in digits_by_target.values() for d in vals})
    clauses = [f"target_name LIKE '%{d}%'" for d in all_digits]

    wanted = [
        "obs_id", "obs_publisher_did", "target_name", "t_min", "t_max", "t_exptime",
        "freq_min", "freq_max", "center_frequencies", "bandwidths", "nums_channels",
        "spectral_resolutions", "facility_name", "instrument_name", "configuration",
        "dataproduct_type", "access_url", "access_estsize", "s_ra", "s_dec",
        "obs_collection", "proposal_id", "project_code"
    ]
    selected = [c for c in wanted if c in available_cols]
    query = f"""
    SELECT TOP 10000 {', '.join(selected)}
    FROM {table_name}
    WHERE t_min >= {start:.8f} AND t_min <= {end:.8f}
      AND freq_min < 1.50e9 AND freq_max > 1.30e9
      AND ({' OR '.join(clauses)})
    """
    table = service.search(query).to_table()
    raw_rows = [{name: safe(r[name]) for name in table.colnames} for r in table]

    # Keep VLA-family rows locally rather than using unsupported SQL case functions.
    rows = []
    for rec in raw_rows:
        inst = str(rec.get("instrument_name") or "").upper()
        fac = str(rec.get("facility_name") or "").upper()
        coll = str(rec.get("obs_collection") or "").upper()
        if "VLA" in inst or "VLA" in fac or "VLA" in coll:
            rows.append(rec)

    per = {g: [] for g in TARGETS}
    for rec in rows:
        tn = str(rec.get("target_name") or "").upper().replace(" ", "").replace("-", "")
        for g, aliases in TARGETS.items():
            matched = False
            for a in aliases:
                aa = a.upper().replace(" ", "").replace("-", "")
                digits = "".join(re.findall(r"\d+", aa))
                if (aa and aa in tn) or (len(digits) >= 4 and digits in tn):
                    matched = True
                    break
            if matched:
                per[g].append(rec)

    id_fields = [c for c in ("proposal_id", "project_code", "obs_id", "obs_publisher_did", "obs_collection") if c in selected]
    ids = sorted({
        f"{k}={rec.get(k)}"
        for rec in rows for k in id_fields
        if rec.get(k) not in (None, "")
    })
    result = {
        "status": "SG06_NRAO_ARCHIVE_METADATA_AUDIT_COMPLETE",
        "tap_service": TAP,
        "resolved_table_name": table_name,
        "selected_columns": selected,
        "discovered_tables": discovered_tables,
        "table_scores": table_scores,
        "query": " ".join(query.split()),
        "date_window": ["2001-06-01", "2003-02-01"],
        "frequency_window_hz": [1.30e9, 1.50e9],
        "n_query_rows_before_local_vla_filter": len(raw_rows),
        "n_rows": len(rows),
        "archive_identifiers": ids,
        "target_match_counts": {g: len(v) for g, v in per.items()},
        "target_matches": per,
        "all_rows": rows,
        "route_viable": all(len(per[g]) > 0 for g in TARGETS),
        "interpretation_rule": (
            "A metadata match establishes that historical VLA visibility data for the target/time/frequency is indexed by NRAO. "
            "It does not reproduce SG06's published Sigma_HI profile. Visibility-level reconstruction would require a separately frozen "
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
        "resolved_table_name": table_name,
        "selected_columns": selected,
        "n_query_rows_before_local_vla_filter": len(raw_rows),
        "n_rows": len(rows),
        "target_match_counts": result["target_match_counts"],
        "archive_identifiers": ids,
        "route_viable": result["route_viable"],
    }, indent=2))


if __name__ == "__main__":
    main()
