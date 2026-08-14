# Stationary H I missing-value policy v1

**Status:** FROZEN BEFORE ANY EVALUATION OF `L_A`, `C_A`, `tau_A`, PERSISTENCE PREDICTIONS, OR BLIND OUTCOMES.

This policy applies to certified tabulated H I source profiles after provenance recovery and before common-profile interpolation.

## Audit result

Across all 24 certified tabulated H I profiles, the source-value audit found:

- no negative H I surface-density measurements;
- no zero H I surface-density measurements;
- 13 blank/nonfinite source values, all from Leroy et al. (2008) THINGS table 7;
- the blanks occur in only two calibration galaxies:
  - NGC2841: five contiguous **leading/innermost** bins are blank, followed by valid measurements;
  - NGC2976: eight contiguous **trailing/outermost** bins are blank, following the last valid measurement;
- no certified tabulated profile contains an interior missing-value gap.

The durable audit is `validation/stationary/certified_hi_nonpositive_value_audit_v1.json`.

## Frozen rule

1. A blank/nonfinite source `Sigma_HI` value is retained as missing provenance and is **not** converted to zero.
2. Missing rows are excluded from the measured radial support used to construct the common tabulated profile.
3. No interpolation is performed across a missing source row or missing interior interval. An interior missing interval would fail closed and require a new explicit rule before use.
4. Because the audited blanks are edge-only, the valid measured support begins at the first finite source value and ends at the last finite source value.
5. Values required interior to the first valid measured radius or exterior to the last valid measured radius may only be supplied by the independently predeclared continuation rule after that rule is finally frozen.
6. Source radii, uncertainties, and the existence/location of omitted blank bins remain preserved in the source artifact and missing-value audit.
7. No positive measured H I surface density is clipped, thresholded, smoothed, or altered under this policy.

## Scientific boundary

This is an observational-data handling rule chosen from source-table structure only. It was frozen without evaluating persistence parameters, persistence predictions, blind residuals, or model preference. `L_A` and `C_A` remain locked.
