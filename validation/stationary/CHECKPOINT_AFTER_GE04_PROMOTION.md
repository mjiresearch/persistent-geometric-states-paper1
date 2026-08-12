# Post-Ge04 stationary H I checkpoint

Status: **GE04 PROMOTED; RECONCILE/RERANK NEXT**

- Do not restart Ge04 extraction.
- ESO079-G014 (calibration): 12 source-native radial H I points.
- ESO116-G012 (blind): 14 source-native radial H I points.
- Profile artifact: `data/stationary/source_reconstruction/ge04_vector_hi_profiles_v1.csv`
- Validation: `validation/stationary/ge04_vector_hi_profile_extraction_v1.json`
- Public overlay updated and Ge04 marked resolved.
- Blind profile acquisition was performed without inspecting any persistence outcome.
- `L_A` and `C_A` remain locked.

## Resume point
Run the existing public-source reconciliation and Lelli/SPARC reference-family ranking. Then continue with the new highest-ranked actionable family. Do not revisit Ge04 unless its explicit reopen rule is satisfied.

## Reranked live queue
Next actionable family: **dB97** — 2 untouched frozen galaxies (1 calibration, 1 blind). Galaxies: F565-V2;F571-V1.

Untouched frozen galaxies remaining: 93.
Priority summary: `validation/stationary/sparc_hi_reference_family_priority_v1_summary.json`
