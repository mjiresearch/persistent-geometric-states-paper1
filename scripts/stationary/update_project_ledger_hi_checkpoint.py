#!/usr/bin/env python3
"""Insert/replace the current stationary H I database checkpoint in PROJECT_LEDGER.md."""
from pathlib import Path

P=Path("PROJECT_LEDGER.md")
START="<!-- AUTO-STATIONARY-HI-CHECKPOINT-START -->"
END="<!-- AUTO-STATIONARY-HI-CHECKPOINT-END -->"
BLOCK=f'''{START}

## Current stationary H I database checkpoint — 2026-08-12

**Status:** PUBLIC-DATA ACQUISITION IN PROGRESS. `L_A` and `\\mathcal C_A` remain **LOCKED**.

- Frozen stationary sample remains **149 galaxies = 104 calibration + 45 blind**.
- Current reconciled public-source overlay covers **43/149 galaxies = 30 calibration + 13 blind**.
- Preferred source-quality state remains **16 actual recovered/ingested profiles = 11 calibration + 5 blind**: **14 machine-readable raw/source profiles + 2 analytic profiles**.
- Elson/WHISP public vector Appendix route is now recovered for **19 frozen galaxies = 15 calibration + 4 blind**, yielding **947 numerical candidate rows** with zero basic QC failures.
- WHISP distinction is locked: the **red H I curve geometry is exact vector data from the published Appendix PDFs**, while physical axis scales are reconstructed from audited source `R_HI` and mean-`Sigma_HI` anchors. These rows remain `vector_profile_candidate_recovered`, not final frozen source profiles.
- UGC05918/DDO87 and UGC07559/DDO126 retain their superior Iorio machine-readable profiles as preferred sources; WHISP is secondary QC for them. UGC05829 is upgraded from Taylor-map-only to a numerical WHISP candidate while Taylor 1994 provenance is retained.
- Lelli et al. (2016) SPARC Table 1 provenance has been converted into `sparc_hi_reference_map_v1.csv` for **all 149 frozen galaxies**, producing **271 galaxy-reference rows across 58 distinct SPARC reference IDs**. Five CDS shorthand IDs (`Ba06`, `Bm05`, `Fr02`, `VB99`, `VdH93`) remain explicitly unresolved rather than dropped.
- Lelli's per-galaxy `Ref` field is now the authoritative acquisition map to the original H I/Halpha observations. It does **not** establish that the later 169-galaxy azimuthally averaged H I profile compilation is publicly downloadable.
- Ranking only galaxies with **no current public-source overlay** leaves **106 untouched frozen galaxies across 45 Lelli/SPARC reference families**.
- Highest-yield untouched family is the **Ursa Major / Verheijen & Sancisi 2001 (`VS01`) / Sanders & Verheijen 1998 (`SV98`) block: 27 frozen galaxies = 19 calibration + 8 blind**.
- Verheijen & Sancisi (2001) explicitly published radial H I surface-density profiles in its 43-galaxy WSRT atlas. CDS `J/A+A/370/765` exposes membership, photometry, global H I, rotation-curve and synthesis-result tables, but not a numerical radial-`Sigma_HI` table. The live acquisition step is therefore a one-pass audit of the public arXiv/original atlas for reusable vector profile assets.
- **Do not retry** closed routes (dead legacy WHISP host, Bluedisk zero-overlap block, Stevens arXiv-no-array block, exhausted low-fidelity Cote/van Zee/NGC3741/Taylor routes) unless a genuinely new data mechanism appears.

**Current resume point:** Ursa Major `VS01/SV98` 27-galaxy public atlas/vector audit, then ingest if a defensible vector/numeric route exists; otherwise advance to the next Lelli-ranked family without looping.

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
        # insert after the authority-rule paragraph (next blank line)
        pos=text.find("\n\n",idx)
        pos=len(text) if pos<0 else pos+2
        text=text[:pos]+BLOCK+"\n"+text[pos:]
    else:
        text=BLOCK+"\n"+text
P.write_text(text,encoding="utf-8")
print("Updated",P)
