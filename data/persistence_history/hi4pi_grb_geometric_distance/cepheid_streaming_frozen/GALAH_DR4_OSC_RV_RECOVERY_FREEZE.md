# GALAH DR4 OSC Cepheid RV recovery — frozen protocol

Status: **OUTCOME-BLIND / FROZEN BEFORE ANY H I COMPARISON**

Purpose: recover independent multi-epoch systemic RVs for the already purity-qualified OSC Cepheid candidates from GALAH DR4 without changing any V3 geometry or support rule.

## Candidate set
- Start from the frozen purity audit candidate table with `target_quality_pass=True`.
- Gaia DR3 2072235820984829312 (QY Cyg) remains excluded.

## Catalog/matching
- Query VizieR `J/other/PASA/42.51/allspec` (GALAH DR4 per-spectrum table).
- Match by exact `GaiaDR3` source ID only.

## RV acceptance
1. use `rv_comp_1` and `e_rv_comp_1` from individual spectra;
2. require finite RV and positive finite uncertainty;
3. require `flag_sp == 0` when available;
4. require `rv_comp_nr == 1` when available, so an unresolved multi-component CCF is not treated as a systemic Cepheid velocity;
5. require at least **8 distinct MJD** epochs;
6. no clipping and no agreement-based selection;
7. systemic RV = inverse-variance weighted mean;
8. assigned uncertainty = max(formal weighted-mean error, empirical epoch scatter/sqrt(N), 1.0 km/s);
9. assigned uncertainty must be <= **5 km/s**.

## Frozen downstream rules
All V3 geometry, A5 constants, bandwidth grid h={1,2,3,4,5,7,10}, N_eff>=3 separately in U/V, arm-width/nearest-phase rules, RUWE/distance/velocity-error cuts, and GRB031203 exclusion remain unchanged.

## Stop rule
After any qualifying new tracer, recompute OSC support. If OSC qualifies, freeze the conventional prediction before opening H I. Otherwise continue to the next independent archive without relaxing any rule.

## Outcome firewall
No H I spectrum, H I velocity, H I residual, previous GRB comparison outcome, or Persistence prediction may be read.
