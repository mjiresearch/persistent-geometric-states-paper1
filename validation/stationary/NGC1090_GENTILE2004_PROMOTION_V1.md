# NGC1090 Gentile et al. 2004 H I profile promotion — V1

## Status

PROMOTED to the stationary public H I source-profile build.

## Public source

Gentile et al. (2004), public arXiv source package `astro-ph/0403154`, Fig. 2. The figure caption defines the filled circles as the average of the approaching and receding radial H I surface-density profiles. The text states that NGC1090's radial H I distribution was computed by integrating the total-intensity map over concentric ellipses.

## Frozen geometry

- SPARC frozen distance: 37.0 Mpc.
- Frozen SPARC source radii: 24 points, 0.35–30.09 kpc.

## Numerical extraction

The publication figure was rendered from the public EPS source and the filled-circle average series was recovered with a fixed marker template and calibrated plot axes. The committed numerical profile is `data/stationary/source_reconstruction/ngc1090_gentile2004_profile_v1.csv`.

## Independent physical QC

Gentile et al. tabulate `r_HI/r_d = 8.8` and `r_opt = 10.9 kpc`, with `r_opt = 3.2 r_d`. This implies `r_HI = 29.98 kpc` on the paper's physical scale. The recovered public profile crosses `Sigma_HI = 1 Msun pc^-2` at approximately 29.4–30.5 kpc depending on the exact marker subset/template calibration, i.e. within about 2% of the independent tabulated value.

## Coverage rule

The recovered profile extends through the maximum frozen SPARC source radius. No inward or outward H I extrapolation is required for NGC1090.

## Guardrail

The SPARC gas rotation contribution was not inverted or used to determine the H I profile. The profile comes directly from the public observational publication figure.
