# SDSS DR20 OSC Cepheid RV recovery — frozen protocol

Status: **OUTCOME-BLIND / FROZEN BEFORE ANY H I COMPARISON**

Purpose: recover independent multi-epoch systemic radial velocities for the already purity-qualified OSC Cepheid candidates from SDSS DR20 (especially SDSS-V/MWM BOSS spectroscopy) without changing any frozen V3 geometry or support rule.

## Candidate set
- Use `osc_rv_target_rank/classification_audit/osc_single_pass_candidates_classification_audit.csv`.
- Retain only `target_quality_pass=True`.
- Gaia DR3 2072235820984829312 (QY Cyg) remains excluded.

## SDSS target matching
- Use the public DR20 Valis API.
- Search the frozen Gaia position with radius **1.5 arcsec**.
- A source is eligible only if the search resolves to one physical `sdss_id` within 1.5 arcsec. Ambiguous multiple counterparts are rejected unless they are demonstrably repeated records of the same `sdss_id`.
- Gaia/alternative-ID information may be used to validate a match but never to override a positional conflict.

## RV acceptance
For an SDSS-matched candidate:
1. use only visit/night/epoch-level stellar radial velocities that are explicitly barycentric or heliocentric and provide an uncertainty;
2. require finite RV and finite positive uncertainty;
3. apply the relevant SDSS pipeline's documented fatal-quality flags before averaging; no empirical clipping is allowed;
4. require at least **8 distinct observing epochs/nights**;
5. no velocity clipping, no agreement-with-model selection, and no selection based on any GRB outcome;
6. systemic RV = inverse-variance weighted mean of accepted epoch velocities;
7. assigned uncertainty = `max(formal weighted-mean error, empirical epoch scatter/sqrt(N), 1.0 km/s)`;
8. assigned uncertainty must be <= **5 km/s**, matching the frozen Gaia mean-RV threshold.

A coadd-only RV or fewer than 8 distinct epochs is not accepted as a systemic Cepheid velocity.

## Frozen downstream rules
Any qualifying SDSS systemic RV may be added only for an otherwise unsupported purity-qualified DCEP. The following remain unchanged:
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
After any genuine qualifying addition, recompute OSC support. If OSC becomes support-qualified, freeze the conventional OSC prediction immediately before reading any H I residual. If SDSS DR20 yields no qualifying systemic velocity, continue to another independent public spectroscopic archive without relaxing the rules.

## Outcome firewall
No GRB H I spectrum, H I velocity, H I residual, previous GRB comparison outcome, or Persistence prediction may be read by this recovery step.
