#!/usr/bin/env python3
"""Build the frozen-sample galaxy -> original HI/Halpha reference crosswalk.

This is an acquisition/provenance product only.  SPARC Table1.mrt references are
used as *candidate* profile-source leads; they are not assumed to be the exact
radial-HI profile source until verified against the original paper/archive.

Inputs
------
validation/stationary/stationary_split_v1.csv
A local copy of SPARC_Lelli2016c.mrt (or --download from the public SPARC URL)

authoritative source:
https://astroweb.cwru.edu/SPARC/SPARC_Lelli2016c.mrt

Output
------
data/stationary/source_reconstruction/stationary_hi_reference_crosswalk_v1.csv
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPLIT = ROOT / "validation/stationary/stationary_split_v1.csv"
OUT = ROOT / "data/stationary/source_reconstruction/stationary_hi_reference_crosswalk_v1.csv"
URL = "https://astroweb.cwru.edu/SPARC/SPARC_Lelli2016c.mrt"

# Reference families explicitly named in the Hua et al. (2025) Appendix-A profile
# source inventory and/or already tracked by the acquisition registry.  Presence
# in this map means "priority acquisition lead", not "profile source verified".
PROFILE_LEAD_CODES = {
    "Ba05": "Barbieri et al. (2005)",
    "BC04": "Begum & Chengalur (2004)",
    "Bm03": "Begum et al. (2003)",
    "Bo08": "Boomsma et al. (2008)",
    "Br92": "Broeils (1992)",
    "Ca88": "Carignan et al. (1988)",
    "Ca90": "Carignan & Puche (1990a)",
    "CB89": "Carignan & Beaulieu (1989)",
    "Ch06": "Chemin et al. (2006)",
    "Co00": "Cote et al. (2000)",
    "Co91": "Cote et al. (1991)",
    "CP90": "Carignan & Puche (1990b)",
    "dB96": "de Blok et al. (1996)",
    "Fr11": "Fraternali et al. (2011)",
    "Ge04": "Gentile et al. (2004)",
    "Ha14": "Hallenbeck et al. (2014)",
    "JC90": "Jobin & Carignan (1990)",
    "Ke07": "Kepley et al. (2007)",
    "La90": "Lake et al. (1990)",
    "Le14": "Lelli et al. (2014)",
    "No05": "Noordermeer et al. (2005)",
    "Pu91": "Puche et al. (1991)",
    "RA85": "Roelfsema & Allen (1985)",
    "Rh96": "Rhee & van Albada (1996)",
    "Ri15": "Richards et al. (2015)",
    "SG06": "Spekkens & Giovanelli (2006)",
    "Sw02": "Swaters et al. (2002)",
    "VH93": "van der Hulst et al. (1993)",
    "VM97": "Verdes-Montenegro et al. (1997)",
    "VS01": "Verheijen & Sancisi (2001)",
    "vZ97": "van Zee et al. (1997)",
    "Wa97": "Walsh et al. (1997)",
}

KNOWN_HUA_MISSING = {"D512-2", "D564-8", "D631-7", "NGC5907", "NGC4138", "UGC06818"}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--sparc-table", type=pathlib.Path)
    p.add_argument("--download", action="store_true")
    return p.parse_args()


def obtain_table(args) -> str:
    if args.sparc_table:
        return args.sparc_table.read_text(encoding="utf-8")
    if not args.download:
        raise SystemExit("Pass --sparc-table PATH or --download")
    with urllib.request.urlopen(URL, timeout=60) as r:
        return r.read().decode("utf-8")


def parse_sparc_rows(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    in_data = False
    for raw in text.splitlines():
        if raw.startswith("       CamB") or raw.lstrip().startswith("CamB "):
            in_data = True
        if not in_data:
            continue
        if not raw.strip() or raw.startswith("-"):
            continue
        # The fixed-width table places galaxy in bytes 1-11 and references in
        # bytes 100-113.  Fall back to whitespace parsing only for robustness.
        galaxy = raw[:11].strip()
        refs = raw[99:113].strip() if len(raw) >= 100 else ""
        if galaxy and re.match(r"^[A-Za-z0-9-]+$", galaxy):
            out[galaxy] = refs
    return out


def main():
    args = parse_args()
    sparc = parse_sparc_rows(obtain_table(args))
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with SPLIT.open(newline="", encoding="utf-8") as f:
        split = list(csv.DictReader(f))

    fields = [
        "galaxy", "stationary_role", "sparc_hi_ha_refs", "candidate_profile_lead_codes",
        "candidate_profile_lead_families", "known_hua_profile_missing",
        "profile_source_verified", "public_numeric_route_verified",
        "redistribution_status", "notes",
    ]
    rows = []
    missing_refs = []
    for r in split:
        g = r["galaxy"]
        refs = sparc.get(g, "")
        if g not in sparc:
            missing_refs.append(g)
        codes = [x.strip() for x in refs.split(",") if x.strip()]
        leads = [c for c in codes if c in PROFILE_LEAD_CODES]
        families = [PROFILE_LEAD_CODES[c] for c in leads]
        rows.append({
            "galaxy": g,
            "stationary_role": r["stationary_role"],
            "sparc_hi_ha_refs": refs,
            "candidate_profile_lead_codes": ";".join(leads),
            "candidate_profile_lead_families": ";".join(families),
            "known_hua_profile_missing": int(g in KNOWN_HUA_MISSING),
            "profile_source_verified": 0,
            "public_numeric_route_verified": 0,
            "redistribution_status": "to_audit",
            "notes": "SPARC reference is an acquisition lead only; verify exact radial-HI provenance before ingestion.",
        })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    print(f"wrote {OUT}: {len(rows)} galaxies")
    print(f"known Hua-missing in frozen sample: {sum(int(r['known_hua_profile_missing']) for r in rows)}")
    if missing_refs:
        raise SystemExit(f"Frozen galaxies absent from SPARC table: {missing_refs}")


if __name__ == "__main__":
    main()
