# OSC final public-data closure

Status: CLOSED WITH CURRENT PUBLIC DATA — NO SUPPORT-QUALIFIED CONVENTIONAL PREDICTION

## Scope
This closes the GRB 221009A OSC conventional-streaming test using the frozen Cepheid geometry, purity, RV-quality, bandwidth, and effective-sample-size rules. No scientific threshold was relaxed to obtain a prediction.

## Frozen requirement
A valid OSC prediction requires both effective components to satisfy the pre-frozen support criterion, N_eff,U >= 3 and N_eff,V >= 3, at a bandwidth selected from the frozen grid. The V3 public-data sample does not meet this condition.

## Recovery trail exhausted
Public recovery attempts were made without changing the frozen model:
- Gaia DR3 generic/source and Cepheid-specific RV products.
- VELOCE DR1 systemic velocities.
- Melnik et al. 2015 Cepheid heliocentric velocities.
- Gaia DR3 public variable-star epoch RV tables.
- LAMOST DR11 LRS/MRS.
- APOGEE DR17.
- SDSS DR20 BOSS/Astra target products.
- GALAH DR4.
- Legacy frozen sweep: Gorynya Cepheid time series, Borgniet et al. Cepheid time series, CRaV/Evans et al., Cruz Reyes cluster-Cepheid velocities, and RAVE DR6.

The final mirror-based legacy sweep executed 144 target/catalog queries for the 24 purity-qualified missing-RV candidates and returned zero positional matches with zero query errors.

SDSS DR20 did observe seven relevant candidates, but none had the pre-frozen minimum of eight independent observing epochs; therefore no SDSS value was promoted into the conventional streaming field.

## Scientific verdict
The OSC point cannot be used as a valid predictive conventional-vs-observation test with the current public spectroscopy. The correct status is NO PREDICTION / DATA-LIMITED, not a conventional-model failure.

The previously measured OSC geometric H I residual may remain interesting as a target for future spectroscopy, but it cannot be counted as evidence for Persistence because the comparison model lacks a support-qualified prediction and because broad conventional streaming amplitudes can already accommodate residuals of this scale.

## What would reopen the case
Only genuinely new information should reopen this test: one or more new/published systemic RV measurements that independently satisfy the already-frozen quality rules for the high-leverage OSC Cepheid candidates. No redefinition of arm geometry, bandwidth grid, purity criteria, RV-error threshold, or N_eff threshold is allowed.

## Project-level implication
The OSC case does not rescue the Persistence framework. It remains unresolved because of missing spectroscopy, while the two completed blind Outer-arm tests are consistent with the conventional streaming reconstruction. Any future revival of Persistence requires a precomputed quantitative Persistence prediction that succeeds out of sample, not merely an unexplained residual.
