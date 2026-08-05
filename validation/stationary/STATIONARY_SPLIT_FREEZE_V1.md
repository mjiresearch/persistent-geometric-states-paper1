# Stationary calibration/blind split freeze v1

**Status:** FROZEN BEFORE PERSISTENCE FITTING

The 149-galaxy stationary sample is divided into **104 calibration** and
**45 blind-validation** galaxies (30.201% blind).

The split uses no rotation-curve residuals and no values or trial fits of
`L_A`, `C_A`, or `tau_A`.

## Deterministic seed

The random seed is `625874907`, obtained from the first eight hexadecimal
characters of the already-frozen stationary-master SHA-256
`254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f`. This prevents discretionary seed selection after model results
are known.

## Balance procedure

Exactly 50,000 candidate 70/30 random splits are generated from that
fixed pseudo-random sequence. The retained split minimizes a predeclared
covariate-balance objective using only independent observational/sample
quantities: luminosity, effective surface brightness, HI-to-3.6um luminosity
ratio, characteristic rotation speed, characteristic disk size, radial
coverage relative to size, radial-point count, inclination, broad morphology,
and SPARC quality flag.

The objective matches calibration and blind first moments, partially matches
second moments, and matches broad categorical proportions. It never evaluates
a persistence prediction.

## Frozen file

`validation/stationary/stationary_split_v1.csv`

Any later change to membership requires a new versioned split and cannot replace
this file silently. The original blind result must remain reportable.
