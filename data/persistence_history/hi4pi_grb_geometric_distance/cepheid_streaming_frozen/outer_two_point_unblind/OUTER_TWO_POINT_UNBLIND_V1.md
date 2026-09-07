# Two-point Outer-arm unblind — frozen Cepheid conventional prediction vs H I residual

Status: **UNBLINDED ONLY FOR THE TWO PRE-SPECIFIED OUTER-ARM TARGETS**

Targets included:
1. GRB 221009A — Outer
2. GRB 160623A — Outer

Targets not used:
- GRB 221009A — OSC remains without a support-qualified conventional prediction.
- GRB 031203 remains excluded by the frozen arm-geometry rule.

## Frozen conventional predictions
Source: `cepheid_streaming_frozen/outputs_v3/freeze_summary_v3.json`, protocol `GAIA_CEPHEID_STREAMING_AUGMENT_V3`, status `FROZEN_BEFORE_HI_COMPARISON`.

- GRB 221009A Outer: predicted LOS streaming residual = -1.0329498307 km/s; bootstrap p16/p50/p84 = -2.1436193767 / -0.9917557124 / +0.0762526727 km/s.
- GRB 160623A Outer: predicted LOS streaming residual = -0.6708097561 km/s; bootstrap p16/p50/p84 = -1.7386120114 / -0.6027327825 / +0.3482785892 km/s.

## Unblinded H I outcomes
Source: `bonn_results/geometric_kinematic_residuals.csv`.

- GRB 221009A Outer: observed-minus-Reid residual = +0.365137 km/s; distance-propagated Reid uncertainty = 1.057124 km/s.
- GRB 160623A Outer: observed-minus-Reid residual = +6.686603 km/s; distance-propagated Reid uncertainty = 5.996132 km/s.

## Fixed comparison
No model re-fit, bandwidth change, tracer change, clipping, or arm reassignment is made after unblinding.

For a compact diagnostic only, approximate the frozen bootstrap 1-sigma width as `(p84-p16)/2`, combine it in quadrature with the already-tabulated geometric-distance uncertainty, and evaluate

`z = (observed residual - frozen predicted residual) / sigma_combined`.

Results:

| target | observed residual | frozen prediction | observed - prediction | sigma_model | sigma_distance | sigma_combined | z |
|---|---:|---:|---:|---:|---:|---:|---:|
| GRB 221009A Outer | +0.365137 | -1.032950 | +1.398087 | 1.109936 | 1.057124 | 1.532798 | +0.912 |
| GRB 160623A Outer | +6.686603 | -0.670810 | +7.357413 | 1.043445 | 5.996132 | 6.086245 | +1.209 |

Under an independent-Gaussian approximation, chi-square = 2.2933 for 2 points (2 dof), corresponding to p ~= 0.318.

## Verdict
The two unblinded Outer-arm observations are **not in significant tension with the frozen conventional Cepheid streaming model**. Neither point exceeds ~1.21 sigma after the pre-existing geometric-distance uncertainty is included, and the joint two-point diagnostic does not reject the conventional prediction.

This is **not evidence for Persistence**. It is a small-N conventional-model survival test. The more discriminating OSC case still lacks a support-qualified conventional prediction, and no independently frozen Persistence prediction has yet been supplied for a head-to-head model comparison.

Association caveat: the independently frozen arm-association audit retained GRB 160623A Outer using an external parallax-arm bracket and GRB 221009A Outer at medium confidence from first-quadrant arm-ridge ordering.
