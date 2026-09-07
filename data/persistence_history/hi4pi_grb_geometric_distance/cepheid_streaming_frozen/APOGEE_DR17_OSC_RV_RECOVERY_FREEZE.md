# APOGEE DR17 OSC Cepheid RV recovery — frozen protocol

Status: **OUTCOME-BLIND / FROZEN BEFORE ANY H I COMPARISON**

Purpose: recover independent multi-epoch systemic radial velocities for the already purity-qualified OSC Cepheid candidates without changing any frozen V3 geometry or support rule.

## Candidate set
- Use `osc_rv_target_rank/classification_audit/osc_single_pass_candidates_classification_audit.csv`.
- Retain only `target_quality_pass=True`.
- Gaia DR3 2072235820984829312 (QY Cyg) remains excluded.

## Catalog
- APOGEE-2 DR17 VizieR `III/286/allvis` visit catalog.
- Search each frozen Gaia position within 1.5 arcsec.
- A candidate is usable only if the cone search resolves to exactly one distinct APOGEE_ID within the matching radius. Multiple APOGEE_ID counterparts are treated as ambiguous and rejected.

## RV acceptance
For the unique APOGEE counterpart:
1. use visit-level barycentric/heliocentric `VHelio` values and the visit `e_RV` uncertainty;
2. require finite VHelio and finite positive e_RV;
3. require APOGEE visit RV flag `FlRV == 0` when that field is present;
4. require at least **8 distinct MJD epochs**;
5. no velocity clipping, no agreement filtering, and no selection based on any Galactic model or GRB outcome;
6. systemic RV = inverse-variance weighted mean of accepted visit VHelio values;
7. assigned uncertainty = max(formal weighted-mean error, empirical visit scatter/sqrt(N), 1.0 km/s);
8. assigned uncertainty must be <= **5 km/s**, matching the frozen Gaia mean-RV threshold.

## Frozen downstream rules
Any qualifying APOGEE systemic RV may be added only for an otherwise unsupported purity-qualified DCEP. Unchanged downstream rules include:
- Reid+2019 A5 Galactic constants/sign convention;
- frozen Outer/OSC arm loci;
- bandwidth grid h={1,2,3,4,5,7,10} kpc;
- N_eff>=3 independently in U and V;
- nearest phase tracer<=2h;
- target within frozen arm width;
- RUWE<1.4, fractional distance error<=20%, R>=4 kpc;
- propagated U/V uncertainty<=20 km/s;
- no velocity clipping;
- GRB031203 excluded.

## Stop rule
After any genuine qualifying addition, recompute OSC support. If OSC becomes support-qualified, freeze the conventional prediction immediately before reading any H I residual. If APOGEE yields no qualifying velocity, continue to the next independent spectroscopic archive without changing the frozen rules.

## Outcome firewall
No GRB H I spectrum, H I velocity, H I residual, previous GRB comparison outcome, or Persistence prediction may be read by this recovery step.
