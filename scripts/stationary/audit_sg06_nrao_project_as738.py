#!/usr/bin/env python3
"""Expand the SG06 NRAO recovery from one matched execution to VLA project AS738.

The first schema-correct NRAO TAP audit identified UGC11455 in project AS738.
This follow-up queries the complete project directly, avoiding historical target-
name alias guesses and the initially narrow date/name filter. It inventories all
science targets, execution blocks, dates, configurations and frequency ranges,
then maps the five frozen SG06 galaxies by exact/normalized target names.

Archive metadata only. No visibility download, calibration, imaging, profile
reconstruction, persistence fitting, or blind-outcome inspection.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pyvo

TAP="https://data-query.nrao.edu/tap"
TABLE="tap_schema.obscore"
PROJECT="AS738"
OUT=Path("validation/stationary/sg06_nrao_project_as738_audit_v1.json")
TARGETS={
 "ESO563-G021":["ESO563G21","ESO563G021","ESO563-G21","ESO563-G021","ESO563"],
 "IC4202":["IC4202"],
 "NGC2955":["NGC2955"],
 "NGC6195":["NGC6195"],
 "UGC11455":["UGC11455"],
}


def safe(v):
    try:
        if hasattr(v,"item"):v=v.item()
    except Exception:pass
    if isinstance(v,bytes):return v.decode("utf-8","replace")
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    return str(v)


def norm(s):return re.sub(r"[^A-Z0-9]","",str(s).upper())


def main():
    service=pyvo.dal.TAPService(TAP)
    cols=["obs_id","obs_publisher_did","project_code","target_name","t_min","t_max","t_exptime","freq_min","freq_max","facility_name","instrument_name","configuration","dataproduct_type","access_url","access_estsize","s_ra","s_dec","proprietary_status"]
    # Retain only registered columns so the audit survives minor schema drift.
    ct=service.search(f"SELECT column_name FROM TAP_SCHEMA.columns WHERE table_name='{TABLE}'").to_table()
    avail={str(r["column_name"]) for r in ct};selected=[c for c in cols if c in avail]
    query=f"SELECT TOP 20000 {', '.join(selected)} FROM {TABLE} WHERE project_code='{PROJECT}'"
    tab=service.search(query).to_table();rows=[{n:safe(r[n]) for n in tab.colnames} for r in tab]

    target_names=sorted({str(r.get("target_name") or "") for r in rows})
    execs=sorted({str(r.get("obs_publisher_did") or "") for r in rows if r.get("obs_publisher_did")})
    obsids=sorted({str(r.get("obs_id") or "") for r in rows if r.get("obs_id")})
    configs=sorted({str(r.get("configuration") or "") for r in rows if r.get("configuration")})
    per={g:[] for g in TARGETS}
    for r in rows:
        tn=norm(r.get("target_name"))
        for g,als in TARGETS.items():
            if any(norm(a) and norm(a) in tn for a in als):per[g].append(r)

    science_like=[]
    for name in target_names:
        n=norm(name)
        # Remove obvious calibrator nomenclature from the compact target inventory.
        if not (n.startswith("3C") or n.startswith("J") and len(n)>6 or "CAL" in n):science_like.append(name)

    result={
      "status":"SG06_NRAO_PROJECT_AS738_AUDIT_COMPLETE",
      "tap_service":TAP,"table":TABLE,"project_code":PROJECT,"query":query,
      "selected_columns":selected,"n_rows":len(rows),"n_execution_products":len(execs),
      "execution_products":execs,"obs_ids":obsids,"configurations":configs,
      "distinct_target_names":target_names,"science_like_target_names":science_like,
      "target_match_counts":{g:len(v) for g,v in per.items()},"target_matches":per,
      "t_min":min((float(r["t_min"]) for r in rows if r.get("t_min") not in (None,"")),default=None),
      "t_max":max((float(r["t_max"]) for r in rows if r.get("t_max") not in (None,"")),default=None),
      "freq_min":min((float(r["freq_min"]) for r in rows if r.get("freq_min") not in (None,"")),default=None),
      "freq_max":max((float(r["freq_max"]) for r in rows if r.get("freq_max") not in (None,"")),default=None),
      "all_rows":rows,
      "interpretation_rule":"Project-level metadata can identify the complete SG06 observing program without relying on historical target aliases. A matching visibility execution is raw provenance, not a radial Sigma_HI profile; profile reconstruction requires a separately frozen calibration/imaging/deconvolution protocol.",
      "boundary":"Metadata only; no visibility download, calibration, imaging, profile reconstruction, persistence fitting, or blind outcomes."
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"all_rows","target_matches"}},indent=2))
if __name__=="__main__":main()
