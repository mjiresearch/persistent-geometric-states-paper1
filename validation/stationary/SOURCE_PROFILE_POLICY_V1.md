# Appendix I source-profile policy v1

**Status:** PREDECLARED BEFORE ANY FIT OF `L_A` OR `C_A`

This policy defines how baryonic surface-density profiles will be constructed for the stationary current-mediated analysis.

## 1. Stellar surface densities

The SPARC inclination-corrected 3.6 micron disk and bulge surface-brightness profiles are used directly as unit-mass-to-light surface-density bases:

- `Sigma_disk(R) = Upsilon_d * SBdisk(R)`
- `Sigma_bulge(R) = Upsilon_b * SBbulge(R)`

`Upsilon_d` and `Upsilon_b` remain externally constrained nuisance parameters; they are not fixed by this data-construction step.

## 2. Gas gravitational contribution

The signed SPARC velocity contribution is preserved. Whenever it enters a Newtonian squared-speed sum, the term is

`Vgas(R) * abs(Vgas(R))`.

The sign is never removed by replacing this expression with `Vgas**2`.

## 3. Gas surface density

`Vgas(R)` is **not** treated as a gas surface density.

The primary source-current analysis will use independently sourced radial H I surface-density profiles corresponding as closely as possible to the observations underlying the SPARC mass models. Profile provenance, distance convention, inclination correction, radial units, uncertainties where available, and helium treatment must be archived before the source profile is frozen.

The public 2016 SPARC mass-model release does not itself provide the azimuthally averaged radial H I surface-density profiles. Yasin & Desmond (2025, MNRAS 539, 2110; DOI 10.1093/mnras/staf453) report using such profiles for 169 SPARC galaxies and state that they were supplied by Federico Lelli via private communication.

The working availability audit currently identifies four systems in the already-frozen 149-galaxy stationary sample without a direct profile in the target compilation:

| Galaxy | Frozen stationary role | Primary direct-profile status |
|---|---|---|
| D564-8 | calibration | unavailable |
| D631-7 | calibration | unavailable |
| NGC4138 | blind | unavailable |
| NGC5907 | calibration | unavailable |

## 4. Predeclared handling of missing profiles

The **primary stationary source-current analysis** requires an independently sourced radial H I profile. The four systems listed above will therefore not enter the primary direct-profile likelihood unless a direct profile is found and its provenance is independently verified before persistence fitting begins.

If no direct profiles are found for those systems, the expected primary direct-profile subset is 145 galaxies while retaining the already-frozen roles of all remaining systems:

- 101 calibration galaxies;
- 44 blind-validation galaxies.

This is a data-availability exclusion made before any evaluation of `L_A`, `C_A`, or persistence residuals.

A **secondary reconstruction test** may apply a predeclared gravitational inversion or other reconstruction to missing-profile systems only after that method has been validated on galaxies with direct H I profiles. Such a secondary test cannot replace or redefine the primary blind result.

## 5. Third-party data stewardship

If direct radial H I profiles are supplied privately or under non-redistribution terms:

- the underlying files will not be committed to the public repository without explicit permission from the provider;
- the public archive may retain provenance, permitted metadata, processing code, validation records, and derived products that do not reconstruct the restricted source data;
- any additional provider-specified citation, acknowledgement, access, or redistribution conditions will be followed; and
- supplying observational data does not imply collaboration or endorsement of the framework, analysis, or conclusions.

The repository-level `DATA_POLICY.md` governs these materials.

## 6. Helium convention

Direct H I surface density is converted to the neutral-gas mass convention used for the source model using a single globally declared helium correction. The working validation products use a factor of 1.33. The final factor and its provenance must be frozen before source-profile production; it may not vary by galaxy to improve rotation-curve residuals.

## 7. Source-current velocity

The stationary source current uses the self-consistent model velocity:

`J(R) = Sigma_b(R) * V(R)`.

`Vobs(R)` remains the target observable. It is never inserted as the current velocity in the primary fit.

## 8. Freeze boundary

No `L_A`, `C_A`, `tau_A`, or persistence prediction may be evaluated until:

1. direct H I profiles have been ingested for the primary sample;
2. the profile provenance audit has passed;
3. interpolation and radial continuation rules have been frozen;
4. the source-profile validation subset has passed its declared tests; and
5. a versioned stationary source-profile freeze record has been committed.
