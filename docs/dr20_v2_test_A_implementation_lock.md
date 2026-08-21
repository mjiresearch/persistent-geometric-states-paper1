# DR20-v2 Test A implementation lock

Status: **implementation details fixed before Test-A outcome execution**.

This note resolves only details left unspecified by the frozen scientific protocol `sdss-dr20-conventional-dynamics-challenge-v2`. It does not change any scientific threshold, cohort cut, voxel definition, decision rule, or interpretation rule.

## Input authority

Test A reads the immutable v1 star-level product:

`data/persistence_history/dr20_independent/field_v1/field_star_sample.csv.gz`

The script re-applies the frozen uncertainty-separated age definitions and frozen v1 voxel assignment, then keeps only the same class of supported voxels (at least ten young and ten old stars). It does not rebuild the Gaia join or modify the v1 result.

## Radial tracer-density implementation

For the frozen pooled-sample fit of `d ln(nu sigma_R^2) / d ln R`, the implementation defines `nu` as the catalog-tracer count divided by the geometric volume of the corresponding full cylindrical annulus and the frozen absolute-z slab. Radial bins have width `0.5 kpc`. The two signed sides of each absolute-z slab are included in the volume. Only the logarithmic radial slope is used.

This remains a catalog-tracer density, not a stellar mass density or a corrected survey selection function. The gradient is fitted from the pooled young+old cohort sample and is therefore label-invariant; the same fitted slope is applied to both cohorts in a voxel.

A frozen stratum must have at least four populated radial bins. Supported v1 voxels outside `|z|<0.5 kpc`, or in a stratum whose common radial gradient cannot be fitted, are marked unavailable for the baseline Test-A estimand rather than reassigned to another stratum or used to relax thresholds.

## Jeans solution

For each cohort in each eligible voxel, the implementation computes unbiased (`ddof=1`) sample dispersions and solves the frozen Jeans relation for the positive prograde root:

`mean(v_phi)_AD = sqrt(V_c^2 - [sigma_phi^2 - sigma_R^2(1+gradient) - tilt_term])`.

The baseline sets `tilt_term=0`. A negative square-root argument is recorded as unavailable and is never clipped to create a finite prediction.

## Bootstrap

The frozen 2,000-resample bootstrap uses seed `20260821`. Stars are resampled with replacement separately inside every voxel and cohort. The common radial gradient is held fixed because it is a pooled label-invariant nuisance estimate; the cohort dispersions and Jeans prediction are recomputed on each resample. The 2.5th and 97.5th percentiles of the equal-voxel predicted old-minus-young `Delta v_phi_AD` form the frozen 95% prediction interval.

## Residual permutation

The residual test permutes young/old labels inside each supported eligible voxel while preserving the observed cohort counts. For every permutation, cohort dispersions and voxel-level Jeans predictions are recomputed; the common radial gradient remains fixed. The statistic is the equal-voxel mean of

`Delta v_phi_observed - Delta v_phi_AD`.

Because the frozen question is whether *any* residual age contrast remains after drift subtraction, the residual permutation p-value is two-sided using absolute statistic magnitude. The machine-readable protocol fixes 2,000 permutations and alpha `0.01` but does not separately assign this permutation a seed. Before outcome execution, the implementation fixes the deterministic seed to `20260822`, i.e. the Test-A bootstrap seed plus one. This value coincides with the separately frozen Test-C seed but the random streams and tests are independent.

## Tilt sensitivity

The mandatory sensitivity term is estimated separately for young and old stars in `0.5 kpc` radial bins and signed `0.1 kpc` z layers. For a cohort/radial/z cell, `nu <v_R v_z>` uses the cell tracer density times the unbiased sample covariance. A centered finite difference is evaluated only when both immediately adjacent signed-z layers are populated with at least two stars. The corresponding `(R/nu) d(nu <v_R v_z>)/dz` term is then used in the frozen Jeans equation.

Tilt-inclusive results are reported only for voxels where the required term is available for both cohorts. They are a mandatory sensitivity analysis and cannot replace the baseline decision post hoc.

## Decision

Asymmetric drift is quantitatively sufficient only if both frozen conditions hold:

1. the observed equal-voxel old-minus-young `Delta v_phi` is inside the baseline Jeans 95% bootstrap prediction interval; and
2. the drift-subtracted residual permutation p-value is greater than `0.01`.

Failure of either condition means only that this frozen asymmetric-drift implementation is insufficient. It is not evidence for persistence, and Tests B-D remain mandatory.
