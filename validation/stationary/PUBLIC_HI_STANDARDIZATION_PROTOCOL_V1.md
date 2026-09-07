# Public H I profile standardization protocol v1

**Status:** FROZEN PROCEDURE; FINAL NORMALIZED DATA NOT YET FROZEN

## Purpose

The public-source reconstruction must remain reproducible while matching the
SPARC/Hua convention closely enough that the stationary calibration is not
sensitive to heterogeneous literature normalization choices.

## Public input layer

For each galaxy retain the source profile as an immutable observational layer:

- original/public source citation and product identifier;
- original profile radius and adopted source distance;
- published/directly extracted H I surface density and uncertainty;
- whether helium is included in the source values;
- inclination/geometry convention where known;
- public-product checksum where downloadable;
- acquisition method: machine-readable radial table, direct public map
  extraction, or documented digitization fallback.

Never infer `Sigma_HI(R)` from `Vgas`, `Vobs`, halo residuals, or any
persistence-model quantity.

## Unit convention

The canonical stored `Sigma_HI` is hydrogen-only, face-on surface density in
`Msun pc^-2`.

Known source conversions are explicit. Example: Leroy et al. (2008), CDS
`J/AJ/136/2782/table7`, includes helium with factor 1.36; both `SigmaHI` and its
rms uncertainty are divided by 1.36 before entering the hydrogen-only layer.

The combined gas source uses the SPARC/Hua common factor

`Sigma_atomic_gas = 1.33 * Sigma_HI`.

Do not apply both factors.

## Distance convention

Radial coordinates are rescaled to the frozen SPARC distance:

`R_frozen = R_source * D_SPARC / D_source`.

Surface density is not distance-rescaled.

## Face-on / total-mass standardization

Hua et al. (2025) state that the literature H I profiles were standardized with
GIPSY `Rotmod`, using the same SPARC H I masses and distances as Lelli et al.
(2016). `Rotmod` takes the observed radial profile and total disk mass and
returns a circular-speed contribution and face-on surface density. Hua used an
exponential vertical profile with scale height 100 pc; for the face-on surface
density integrated over z this has negligible effect.

Therefore the final public reconstruction must use one of the following, in
priority order:

1. **Exact GIPSY Rotmod reproduction.** Run the public observed profile through
   `Rotmod` with frozen SPARC distance, H I mass, and 100 pc exponential scale
   height.
2. **Validated equivalent implementation.** A shape-preserving numerical
   normalization may replace `Rotmod` only after it is tested galaxy-by-galaxy
   against `Rotmod` on a representative subset and the residual tolerance is
   frozen before calibration.

Until one of these checks is complete, public profiles may be used for
acquisition/coverage QC but are labeled `pre_standardization`, not final
`stationary_hi_profiles_v1`.

## Interpolation and coverage

- Linear interpolation is allowed only between measured profile radii.
- No inward or outward H I extrapolation is allowed during acquisition.
- If a SPARC rotation point lies outside the profile range, first seek an
  alternate direct public profile/map with suitable coverage.
- Any common continuation rule, if ultimately unavoidable, must be
  preregistered before `L_A` or `C_A` calibration and reported separately from
  directly covered points.

## Stellar component

The combined stationary source table uses the predeclared SPARC convention:

- disk `M/L_3.6 = 0.5`;
- bulge `M/L_3.6 = 0.7`.

## Source-current guardrail

The persistence source current uses the self-consistent model velocity.
`Vobs` is target data and may never enter the source-current construction.

## Freeze gate

`stationary_hi_profiles_v1.csv`, `stationary_source_profiles_v1.csv`, and
`STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` may be marked final only after:

1. public acquisition provenance is complete for the retained sample;
2. helium/unit conventions are audited;
3. distance rescaling is audited;
4. Rotmod/equivalent face-on and SPARC-MHI normalization is complete;
5. profile coverage/interpolation QC is complete;
6. redistribution rights are recorded;
7. calibration/blind roles remain the original frozen roles after any
   predeclared availability exclusions.

No persistence fit may be used to decide any item above.
