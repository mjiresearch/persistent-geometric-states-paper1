# LAMOST DR11 OSC Cepheid RV recovery — frozen protocol

Status: **OUTCOME-BLIND / FROZEN BEFORE ANY H I COMPARISON**

Purpose: search for independent spectroscopic radial velocities for the already purity-qualified OSC Cepheid candidates without changing the frozen V3 geometry, support rule, bandwidth grid, or kinematic conventions.

## Candidate set
- Start from `osc_rv_target_rank/classification_audit/osc_single_pass_candidates_classification_audit.csv`.
- Retain only rows with `target_quality_pass=True`.
- QY Cyg / Gaia DR3 2072235820984829312 remains excluded.
- No candidate may be added or removed using H I information.

## Catalogs searched
- LAMOST DR11 V/162 low-resolution AFGK stellar-parameter catalog (`dr11sl`).
- LAMOST DR11 V/162 medium-resolution stellar-parameter catalog (`dr11sm`).
- Match by exact Gaia DR3 source ID where available; coordinate matching is not used to override a conflicting Gaia ID.

## RV acceptance rule
LAMOST is treated only as an additional source under the already frozen systemic-RV quality logic. A LAMOST-derived velocity is eligible only when:
1. there are at least **8 distinct observing epochs/dates** for that Gaia source in a single LAMOST resolution branch (LRS or MRS);
2. each contributing spectrum has a finite heliocentric RV and finite quoted RV uncertainty;
3. no velocity clipping or agreement-with-model selection is permitted;
4. the inverse-variance weighted mean RV is used as the candidate systemic velocity;
5. the uncertainty assigned to that mean is `max(formal weighted-mean error, empirical epoch scatter/sqrt(N), 1.0 km/s)`;
6. the resulting uncertainty must be <= **5 km/s**, matching the frozen Gaia mean-RV threshold;
7. if both LRS and MRS independently qualify, prefer MRS; otherwise use the qualifying branch.

A single-epoch or sparsely sampled LAMOST RV is **not** accepted as a systemic Cepheid velocity, regardless of precision.

## Frozen downstream rules
If a new LAMOST systemic RV qualifies, it is inserted only as a new independent RV source for an otherwise unsupported purity-qualified DCEP. All of the following remain unchanged:
- Reid+2019 A5 constants and sign convention;
- frozen Outer/OSC arm loci;
- bandwidth grid h={1,2,3,4,5,7,10} kpc;
- N_eff >= 3 independently in U and V;
- nearest phase tracer <= 2h;
- target within frozen arm width;
- RUWE < 1.4, fractional distance error <=20%, R>=4 kpc;
- propagated U/V uncertainty <=20 km/s;
- no velocity clipping;
- GRB031203 excluded.

## Stop rule
Recompute OSC support after genuine qualifying additions. If the OSC location becomes support-qualified, freeze the conventional OSC prediction immediately before any H I residual is opened. If LAMOST adds no qualifying systemic velocities, continue to the next independent spectroscopic archive without relaxing any rule.

## Outcome firewall
The recovery script and any downstream builder must not read any GRB H I spectrum, H I velocity, H I residual, prior GRB comparison outcome, or Persistence prediction.
