#!/usr/bin/env python3
"""Insert/replace the current stationary H I database checkpoint in PROJECT_LEDGER.md.

The checkpoint is generated from the current durable acquisition products rather
than hard-coded counts, so GitHub remains the cross-session source of truth. Once
the certified source subset and pre-receipt author intake contract exist, the
legacy acquisition updater preserves that newer manually reconciled checkpoint.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

P=Path("PROJECT_LEDGER.md")
RECON=Path("validation/stationary/stationary_hi_profile_provenance_reconciled_v1_summary.json")
PRIORITY=Path("validation/stationary/sparc_hi_reference_family_priority_v1_summary.json")
DISP=Path("data/stationary/source_reconstruction/sparc_hi_reference_family_disposition_v1.csv")
START="<!-- AUTO-STATIONARY-HI-CHECKPOINT-START -->"
END="<!-- AUTO-STATIONARY-HI-CHECKPOINT-END -->"

CERTIFIED_FREEZE=Path("validation/stationary/STATIONARY_SOURCE_PROFILE_FREEZE_V1.md")
AUTHOR_INTAKE=Path("validation/stationary/LELLI_HI_PROFILE_AUTHOR_PACKAGE_INTAKE_PROTOCOL_V1.md")
AUTHOR_INTAKE_VALIDATION=Path("validation/stationary/lelli_hi_author_package_validator_v1_synthetic_validation.json")

if CERTIFIED_FREEZE.is_file() and AUTHOR_INTAKE.is_file() and AUTHOR_INTAKE_VALIDATION.is_file():
    current=P.read_text(encoding="utf-8")
    required_markers=(
        "AUTHOR-PACKAGE INTAKE CONTRACT FROZEN",
        "112-galaxy author request",
        "frozen fail-closed intake validator",
        "14/14",
    )
    missing=[marker for marker in required_markers if marker not in current]
    if missing:
        raise RuntimeError(
            "refusing to replace the frozen certified/intake checkpoint; "
            f"PROJECT_LEDGER.md is missing markers: {missing}"
        )
    print("Preserved certified-subset and author-intake ledger checkpoint")
    raise SystemExit(0)

recon=json.loads(RECON.read_text(encoding="utf-8"))
priority=json.loads(PRIORITY.read_text(encoding="utf-8"))
with DISP.open(newline="",encoding="utf-8-sig") as fh:
    dispositions={r["sparc_ref_id"]:r for r in csv.DictReader(fh)}

profile_counts=recon["profile_recovered_or_ingested_role_counts"]
overlay_counts=recon["overlay_role_counts"]
effective=recon["effective_status_counts"]
raw_n=int(effective.get("raw_source_profile_ingested",0))
analytic_n=int(effective.get("analytic_profile_recovered",0))
vector_n=int(effective.get("vector_profile_candidate_recovered",0))

# Find first genuinely actionable family after applying the durable disposition file.
next_family=None
for fam in priority.get("top_15_actionable_reference_families",[]):
    ref=fam["sparc_ref_id"]
    d=dispositions.get(ref)
    if d and d.get("queue_status") in {"defer_until_new_mechanism","redirected_to_original_sources"}:
        continue
    if d and d.get("queue_status")=="partially_resolved":
        # Partial families remain available only for their documented residual subset,
        # but do not outrank a larger untouched family solely because the priority file
        # predates the disposition update.
        continue
    next_family=fam
    break

if next_family is None:
    next_line="No undispositioned multi-galaxy family remains in the current priority list; regenerate the priority queue."
else:
    next_line=(
        f"**{next_family['sparc_ref_id']} — {next_family['author']}**: "
        f"{next_family['n_untouched_frozen_galaxies']} untouched frozen galaxies "
        f"({next_family['n_calibration']} calibration + {next_family['n_blind']} blind): "
        f"{next_family['galaxies']}."
    )

closed=[]
for ref in ("VS01","SV98","Sw02","Sw09","Sa96","No05","No07"):
    if ref in dispositions:
        d=dispositions[ref]
        closed.append(f"`{ref}` → {d['queue_status']} / {d['disposition']}")
closed_text="; ".join(closed)

db96=dispositions.get("dB96",{})
db96_line=(
    "`dB96` is **partially resolved**: public analytic atomic-H I profiles are recovered for "
    "F568-3, F568-V1, F574-1, F583-1 and F583-4; only F565-V2, F571-8 and F571-V1 remain pending."
) if db96 else ""

BLOCK=f'''{START}

## Current stationary H I database checkpoint — 2026-08-12

**Status:** PUBLIC-DATA ACQUISITION IN PROGRESS. `L_A` and `\\mathcal C_A` remain **LOCKED**.

- Frozen stationary sample remains **{recon['n_frozen_galaxies']} galaxies = 104 calibration + 45 blind**.
- Current reconciled public-source overlay covers **{recon['n_public_overlay_galaxies']}/149 galaxies = {overlay_counts['calibration']} calibration + {overlay_counts['blind']} blind**.
- **{recon['n_profile_recovered_or_ingested']} galaxies now have an actual recovered/ingested profile or analytic model = {profile_counts['calibration']} calibration + {profile_counts['blind']} blind**.
- Preferred recovered-source breakdown: **{raw_n} machine-readable raw/source profiles + {analytic_n} analytic profiles**. An additional **{vector_n} WHISP vector-profile candidates** remain candidate-level rather than final frozen source profiles.
- Lelli et al. (2016) SPARC provenance has been converted into a per-galaxy H I/Halpha source map for **all 149 frozen galaxies**. The current acquisition queue is therefore source-directed rather than a blind literature search.
- Lelli's `Ref` field identifies the underlying observational/source publication, but it does **not** by itself prove that the cited paper contains a direct machine-readable radial `Sigma_HI(R)` profile; each family is classified separately as direct profile, map/cube, downstream analysis, or unresolved.
- Current untouched pool after public-source overlay: **{priority['n_untouched_no_public_overlay']} galaxies** across **{priority['n_reference_families_covering_untouched']} reference families**; **{priority['n_actionable_reference_families']}** are currently actionable before applying newly landed dispositions.
- Durable anti-loop dispositions: {closed_text}.
- {db96_line}
- `Sa96` has been decomposed into its original observing citations; do not treat Sanders 1996 itself as an H I profile source again.
- **Do not retry** a dispositioned source mechanism unless the file's explicit `reopen_rule` is satisfied by a genuinely new public mechanism.

**Current resume point:** {next_line}

{END}
'''

text=P.read_text(encoding="utf-8")
if START in text and END in text:
    a=text.index(START); b=text.index(END,a)+len(END)
    text=text[:a]+BLOCK.strip()+text[b:]
else:
    marker="> **Authority rule:**"
    idx=text.find(marker)
    if idx>=0:
        pos=text.find("\n\n",idx)
        pos=len(text) if pos<0 else pos+2
        text=text[:pos]+BLOCK+"\n"+text[pos:]
    else:
        text=BLOCK+"\n"+text
P.write_text(text,encoding="utf-8")
print("Updated",P)
print("resume:",next_line)
