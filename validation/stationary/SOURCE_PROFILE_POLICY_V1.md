# Appendix I source-profile policy v1

**Status:** PREDECLARED BEFORE ANY FIT OF `L_A` OR `C_A`

This policy defines how baryonic surface-density profiles will be constructed for the stationary current-mediated analysis.

## 1. Stellar surface densities

The SPARC inclination-corrected 3.6 micron disk and bulge surface-brightness profiles are used directly as unit-mass-to-light surface-density bases:

- `Sigma_disk(R) = Upsilon_d * SBdisk(R)`
- `Sigma_bulge(R) = Upsilon_b * SBbulge(R)`

The primary fixed convention used in the current paper is `Upsilon_d = 0.5` and `Upsilon_b = 0.7`; any nuisance treatment must be predeclared and identical in calibration and blind evaluation.

## 2. Gas gravitational contribution

The signed SPARC velocity contribution is preserved. Whenever it enters a Newtonian squared-speed sum, the term is

`Vgas(R) * abs(Vgas(R))`.

The sign is never removed by replacing this expression with `Vgas**2`.

## 3. Gas surface density

`Vgas(R)` is **not** treated as a gas surface density.

The primary source-current analysis will use independently sourced radial H I surface-density profiles corresponding as closely as possible to the observations underlying the SPARC mass models. Profile provenance, distance convention, inclination/face-on correction, radial units, uncertainties where available, helium treatment, and redistribution status must be archived before the source profile is frozen.

The public 2016 SPARC mass-model release does not itself provide the azimuthally averaged radial H I surface-density profiles. Hua et al. compiled profiles from the literature for 169 of 175 SPARC galaxies. Yasin & Desmond (2025, MNRAS 539, 2110; DOI 10.1093/mnras/staf453) report using the 169-profile set supplied by Federico Lelli via private communication. This project therefore reconstructs the profiles from public literature/survey products first; private communication is the last resort.

Hua et al. identify six SPARC galaxies without a compiled profile: `D512-2`, `D564-8`, `D631-7`, `NGC5907`, `NGC7339`, and `UGC06818`. Intersecting that list with the already-frozen 149-galaxy stationary sample leaves exactly four systems:

| Galaxy | Frozen stationary role | Primary direct-profile status |
|---|---|---|
| D564-8 | calibration | unavailable in Hua compilation |
| D631-7 | calibration | unavailable in Hua compilation |
| NGC5907 | calibration | unavailable in Hua compilation |
| UGC06818 | blind | unavailable in Hua compilation |

`NGC4138` is not in the Hua missing-profile list and remains eligible for public acquisition.

## 4. Predeclared handling of missing profiles

The **primary stationary source-current analysis** requires an independently sourced radial H I profile. The four systems listed above will therefore not enter the primary direct-profile likelihood unless a direct profile is found and its provenance is independently verified before persistence fitting begins.

If no direct profiles are found for those systems, the expected primary direct-profile subset is 145 galaxies while retaining the already-frozen roles of all remaining systems:

- 101 calibration galaxies;
- 44 blind-validation galaxies.

This is a data-availability exclusion made before any evaluation of `L_A`, `C_A`, or persistence residuals.

A **secondary reconstruction test** may apply a predeclared gravitational inversion or other reconstruction to missing-profile systems only after that method has been validated on galaxies with direct H I profiles. Such a secondary test cannot replace or redefine the primary blind result.

## 5. Public reconstruction and standardization

Acquisition priority is fixed:

1. public machine-readable radial profile;
2. direct extraction from public FITS/moment maps;
3. documented atlas/figure digitization if no numerical/map product is available;
4. private communication only after public routes are exhausted.

The immutable public observational profile is retained before any standardization. Final profiles must then be placed on the common SPARC/Hua convention. Hua et al. standardized the literature profiles with GIPSY `Rotmod`, using the SPARC H I masses and distances and an exponential vertical density profile with 100 pc scale height. The final source-profile freeze therefore requires either the same `Rotmod` procedure or a separately validated numerically equivalent implementation. Until this check is complete, acquired profiles are labeled **pre-standardization** and may be used for acquisition/coverage QC but not for `L_A`/`C_A` fitting.

Radii are rescaled to the frozen SPARC distance. No inward or outward H I extrapolation is allowed during acquisition; alternate direct profiles are sought first for uncovered radii.

## 6. Third-party data stewardship

If direct radial H I profiles are supplied privately or under non-redistribution terms:

- the underlying files will not be committed to the public repository without explicit permission from the provider;
- the public archive may retain provenance, permitted metadata, processing code, validation records, and derived products that do not reconstruct restricted source data;
- any provider-specified citation, acknowledgement, access, or redistribution conditions will be followed; and
- supplying observational data does not imply collaboration or endorsement of the framework, analysis, or conclusions.

Public downloadability is not itself proof of redistribution permission. Every source family receives an explicit redistribution/license audit. The repository-level `DATA_POLICY.md` governs these materials.

## 7. Helium convention

The canonical profile layer stores hydrogen-only `Sigma_HI`. Source-specific helium corrections are removed before harmonization when necessary. For example, Leroy et al. (2008) includes helium with a factor of 1.36, so its tabulated `SigmaHI` and uncertainty are divided by 1.36.

The combined neutral-gas source uses one globally declared SPARC/Hua correction:

`Sigma_atomic_gas = 1.33 * Sigma_HI`.

No galaxy-specific helium factor may be selected to improve residuals, and source and common helium corrections must never be double-applied.

## 8. Source-current velocity

The stationary source current uses the self-consistent model velocity:

`J(R) = Sigma_b(R) * V(R)`.

`Vobs(R)` remains the target observable. It is never inserted as the current velocity in the primary fit.

## 9. Freeze boundary

No `L_A`, `C_A`, `tau_A`, or persistence prediction may be evaluated until:

1. direct/public H I profiles have been ingested for the retained primary sample;
2. the profile provenance and redistribution audit has passed;
3. units, helium convention, SPARC distance scaling, and `Rotmod`/validated-equivalent standardization have passed;
4. interpolation and radial-coverage rules have been frozen;
5. the source-profile validation subset has passed its declared tests; and
6. a versioned stationary source-profile freeze record has been committed.
