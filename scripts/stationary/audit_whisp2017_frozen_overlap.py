#!/usr/bin/env python3
"""Crossmatch the 37-galaxy WHISP sample used by Butler et al. (2017)
against the frozen Paper I stationary split.

Butler et al. (2017, MNRAS 472, 4551) explicitly derived HI mass-surface-
density profiles from downloadable 30-arcsec WHISP total-intensity maps.
Table 1 of that paper gives the 37 UGC identifiers used here.

This is an acquisition audit only. It does not download maps, reconstruct
profiles, normalize source conventions, or evaluate persistence parameters.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

UGC_NUMBERS = [
    2023, 2034, 2455, 3371, 3711, 3966, 4173, 4305, 4325, 4499,
    4543, 5272, 5414, 5721, 5829, 5918, 6446, 6628, 7047, 7232,
    7261, 7323, 7399, 7524, 7559, 7608, 7690, 7866, 7971, 8490,
    9211, 9992, 10310, 11861, 12060, 12632, 12732,
]


def canonical_ugc(n: int) -> str:
    return f"UGC{n:05d}"


def main() -> None:
    split = Path("validation/stationary/stationary_split_v1.csv")
    with split.open(newline="", encoding="utf-8-sig") as fh:
        frozen = {r["galaxy"]: r["stationary_role"] for r in csv.DictReader(fh)}

    rows = []
    for n in UGC_NUMBERS:
        name = canonical_ugc(n)
        role = frozen.get(name, "not_in_frozen_149")
        rows.append(
            {
                "whisp_ugc_number": n,
                "canonical_candidate": name,
                "stationary_role": role,
                "in_frozen_149": int(role in {"calibration", "blind"}),
                "source_study": "Butler et al. 2017 MNRAS 472 4551",
                "source_profile_route": "30arcsec_WHISP_total_intensity_map_reconstruction",
            }
        )

    out = Path("data/stationary/source_reconstruction/whisp2017_frozen_overlap_audit_v1.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    matches = [r for r in rows if r["in_frozen_149"]]
    summary = {
        "status": "WHISP2017_FROZEN_CROSSMATCH_COMPLETE",
        "source_sample_size": len(rows),
        "n_frozen_matches": len(matches),
        "role_counts": {
            "calibration": sum(r["stationary_role"] == "calibration" for r in matches),
            "blind": sum(r["stationary_role"] == "blind" for r in matches),
        },
        "frozen_matches": matches,
        "source_method": (
            "Butler et al. 2017 selected 37 WHISP galaxies and derived HI mass "
            "surface-density profiles from publicly downloaded 30-arcsec WHISP "
            "HI total-intensity maps."
        ),
        "boundary": (
            "Crossmatch only; no map/profile reconstruction, source normalization, "
            "helium correction, interpolation, persistence fitting, or blind inspection."
        ),
    }
    spath = Path("validation/stationary/whisp2017_frozen_overlap_audit_v1_summary.json")
    spath.parent.mkdir(parents=True, exist_ok=True)
    spath.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
