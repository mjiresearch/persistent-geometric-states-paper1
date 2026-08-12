# Ha14 native H I recovery checkpoint

Status: **RECOVERED_V2**

- Lelli family: Ha14 / Hallenbeck et al. 2014
- Galaxies: UGC09037, UGC12506
- Source: arXiv 1407.1744, Figure 9, `fig-density.eps`
- Recovery method: source-native IDL filled-circle (`F`) markers plus matching vector error bars.
- CSV: `data/stationary/source_reconstruction/ha14_vector_hi_profiles_v2.csv`
- Validation: `validation/stationary/ha14_vector_hi_profile_extraction_v2.json`
- v1 failure resolved: later R_HI is fit-derived and is not a hard QC for direct plotted-point crossing.
- Boundary: acquisition/provenance only; `L_A` and `C_A` remain locked.

## Resume point
If interrupted, **do not restart Ha14**. Read the CSV and validation above, ingest/promote the two profiles under the stationary source-profile provenance rules, update the family disposition/coverage ledgers, then rerank to the next unresolved Lelli reference family.
