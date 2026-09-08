# Stationary H I interpolation and continuation policy v1

**Status: FROZEN FOR THE CERTIFIED 34-PROFILE SOURCE PACKAGE BEFORE ANY PERSISTENCE FIT OR BLIND-OUTCOME INSPECTION.**

This policy promotes the candidate rule recorded in Section 5 of `STATIONARY_HI_COMMON_NORMALIZATION_POLICY_V1.md`. That earlier section remains the historical pre-promotion record; this file is the numerical authority for evaluating certified Paper-I H I profiles.

## Promotion evidence

- The synthetic rule validation passes all eight declared tests in `hi_interpolation_rule_v1_mock_validation.json`.
- The 34-profile common-normalized package contains 27 tabulated and 7 analytic profiles, with 25 calibration and 9 blind galaxies.
- The complete radial-support audit is `certified_hi_full_radial_coverage_v3.csv` and its summary JSON.
- The tabulated package has no negative surface densities and no interior missing interval requiring a separate rule.
- The audit identifies 11 profiles requiring inner continuation and 11 requiring outer continuation. The rule below covers all frozen rotation-grid radii without a galaxy-specific exception.

No rotation velocity, residual, persistence prediction, model preference, `L_A`, `C_A`, or `tau_A` was used to promote this rule.

## Frozen tabulated-profile rule

For a certified profile with strictly increasing measured radii `R_i >= 0` and finite nonnegative values `Sigma_i`:

1. At a measured node, retain the measured value exactly.
2. Between adjacent measured nodes, use piecewise-linear interpolation in `Sigma(R)` versus `R`.
3. At radii interior to the first measured node, use a constant value equal to the first measured `Sigma` down to `R=0`.
4. At every radius strictly beyond the last measured node, set `Sigma=0`.
5. Retain the last measured value at the last measured node; no taper is inferred beyond it.
6. Reject a profile with nonfinite or negative values, nonfinite or negative radii, duplicate/non-increasing radii, fewer than two finite samples, or an interior missing interval.
7. Do not clip, smooth, refit, or add a galaxy-specific continuation.

The outer rule is a conservative no-invented-mass boundary, not a claim that the physical H I disk is discontinuous. Any outer-tail sensitivity analysis must be separately predeclared and cannot replace or redefine the primary blind result.

## Analytic profiles

Certified analytic profiles are evaluated directly from their frozen source functions at `R >= 0`. The tabulated interpolation and continuation branches do not apply to them.

## Uncertainty boundary

This v1 source-grid product freezes central surface-density values. Source-reported measurement and parameter uncertainties remain preserved in the common-normalized upstream artifacts; they are not silently converted into independent point errors or propagated without covariance information.

## Versioning and blind firewall

The certified 34-profile v1 outputs are immutable once committed. Later author-supplied profiles must enter a new version under this same source-independent rule after provenance and normalization QC. This subset freeze does not complete the 149-galaxy source gate and does not unlock `L_A` or `C_A`.
