# Post-Ha14 stationary H I checkpoint

Status: **HA14 PROMOTED; RECONCILE/RERANK NEXT**

- Ha14 extraction must not be restarted.
- UGC09037: 32 source-native radial H I points.
- UGC12506: 39 source-native radial H I points.
- Profile artifact: `data/stationary/source_reconstruction/ha14_vector_hi_profiles_v2.csv`
- Validation: `validation/stationary/ha14_vector_hi_profile_extraction_v2.json`
- Public overlay updated and Ha14 marked resolved.
- `L_A` and `C_A` remain locked.

## Resume point
Run the existing public-source reconciliation and Lelli/SPARC reference-family ranking. Then continue with the new highest-ranked actionable family. Do not revisit Ha14 unless its explicit reopen rule is satisfied.

## Reranked live queue
Next actionable family: **Le14** — 2 untouched frozen galaxies (2 calibration, 0 blind). Galaxies: NGC4068;UGC04483.

Priority summary: `validation/stationary/sparc_hi_reference_family_priority_v1_summary.json`
