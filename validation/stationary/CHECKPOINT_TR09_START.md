# Tr09 stationary H I resume checkpoint

Status: **TR09 LIVE — SOURCE-PACKAGE / ONLINE-MATERIAL AUDIT NEXT**

This is the durable resume point after the Ha14 and Le14 promotions.

## Locked state
- Ha14 is already promoted and must not be restarted.
  - UGC09037: 32 source-native radial H I points.
  - UGC12506: 39 source-native radial H I points.
  - Artifact: `data/stationary/source_reconstruction/ha14_vector_hi_profiles_v2.csv`
- Le14 is already split/closed and must not be restarted.
  - UGC04483: 10 source-native whole-galaxy H I points promoted.
  - NGC4068 -> Sw02/WHISP, already deferred after exact public route exhaustion.
- `L_A` and `C_A` remain locked.

## Current Lelli/SPARC chain
Lelli/SPARC galaxy -> Lelli Ref -> original observational paper -> exact public radial H I table/vector profile gate -> ingest or disposition -> rerank.

## Current live family
- SPARC Ref: `Tr09`
- Paper: Trachternach et al. 2009, A&A 505, 577; arXiv:0907.5533; DOI 10.1051/0004-6361/200811136.
- Frozen targets: `D564-8`, `D631-7`.
- Both are calibration galaxies.
- Tr09 is itself an H I synthesis-observation paper (11 dwarf galaxies), so the first provenance gate does not redirect upstream.

## Exact next action
Audit the Tr09 arXiv source package and A&A online-material assets for:
1. machine-readable radius vs H I surface-density arrays/tables for D564-8 or D631-7;
2. source-native EPS/PS vector radial H I profile figures that can be decoded without raster digitization;
3. if neither exists, record a durable no-exact-public-route disposition and rerank.

Do not raster-digitize figures, reconstruct radial profiles from moment maps/cubes, touch persistence quantities, or inspect blind outcomes.

Previous queue checkpoint reported 95 untouched frozen galaxies before Tr09 processing.
