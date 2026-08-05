# Appendix I source-profile policy v1

**Status:** PREDECLARED BEFORE ANY FIT OF `L_A` OR `C_A`

This policy defines how baryonic surface-density profiles will be constructed
for the stationary current-mediated analysis.

## 1. Stellar surface densities

The SPARC inclination-corrected 3.6 micron disk and bulge surface-brightness
profiles are used directly as unit-mass-to-light surface-density bases:

- `Sigma_disk(R) = Upsilon_d * SBdisk(R)`
- `Sigma_bulge(R) = Upsilon_b * SBbulge(R)`

`Upsilon_d` and `Upsilon_b` remain externally constrained nuisance parameters;
they are not fixed by this data-construction step.

## 2. Gas gravitational contribution

The signed SPARC velocity contribution is preserved. Whenever it enters a
Newtonian squared-speed sum, the term is

`Vgas(R) * abs(Vgas(R))`.

The sign is never removed by replacing this expression with `Vgas**2`.

## 3. Gas surface density

`Vgas(R)` is **not** treated as a gas surface density.

The primary source-current analysis will use independently sourced radial HI
surface-density profiles that correspond to the HI data underlying the SPARC
mass models. The profile provenance, distance convention, inclination
correction, radial units, and helium treatment must be archived for every
galaxy before the source profile is frozen.

The 2016 public SPARC mass-model release does not itself provide radial HI
surface-density profiles. Hua et al. (2025, A&A 703, A223) report locating
radial HI profiles for 169 of 175 SPARC galaxies and identify six systems for
which the underlying rotation-curve references do not provide such profiles.

Four of those six systems occur in the already-frozen 149-galaxy stationary
sample:

| Galaxy | Frozen stationary role | Primary direct-profile status |
|---|---|---|
| D564-8 | calibration | unavailable |
| D631-7 | calibration | unavailable |
| NGC4138 | blind | unavailable |
| NGC5907 | calibration | unavailable |

## 4. Predeclared handling of missing profiles

The **primary stationary source-current analysis** will require an independently
sourced radial HI profile. The four systems listed above will therefore not be
used in the primary direct-profile likelihood unless a direct profile is found
and its provenance is independently verified before persistence fitting begins.

If no direct profiles are found, the expected primary direct-profile subset is
145 galaxies while retaining the already-frozen roles of all remaining systems:

- 101 calibration galaxies;
- 44 blind-validation galaxies.

This is a data-availability exclusion made before any evaluation of `L_A`,
`C_A`, or persistence residuals.

A **secondary reconstruction test** may apply a predeclared gravitational
inversion or other reconstruction to missing-profile systems only after that
method has been validated on galaxies with direct HI profiles. Such a secondary
test cannot replace or redefine the primary blind result.

## 5. Helium convention

Direct HI surface density is converted to the neutral-gas mass convention used
for the source model using a single globally declared helium correction. The
working validation products use a factor of 1.33. The final factor and its
provenance must be frozen before source-profile production; it may not vary by
galaxy to improve rotation-curve residuals.

## 6. Source-current velocity

The stationary source current uses the self-consistent model velocity:

`J(R) = Sigma_b(R) * V(R)`.

`Vobs(R)` remains the target observable. It is never inserted as the current
velocity in the primary fit.

## 7. Freeze boundary

No `L_A`, `C_A`, `tau_A`, or persistence prediction may be evaluated until:

1. direct HI profiles have been ingested for the primary sample;
2. the profile provenance audit has passed;
3. interpolation and radial continuation rules have been frozen;
4. the source-profile validation subset has passed its declared tests; and
5. a versioned stationary source-profile freeze record has been committed.
