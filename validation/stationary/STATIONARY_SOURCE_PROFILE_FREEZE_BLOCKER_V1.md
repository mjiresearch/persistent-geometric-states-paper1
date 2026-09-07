# Stationary source-profile freeze — blocker record v1

**Status:** BLOCKED — DO NOT FIT `L_A` OR `C_A`

## Purpose

This record documents why the stationary radial H I/source-profile freeze cannot yet be truthfully declared complete. It is a pre-fit guardrail, not a model result.

## What is already frozen

- Stationary observational master: 149 galaxies / 3,152 rotation-curve points.
- Predeclared roles: 104 calibration / 45 blind.
- Stellar surface-density basis from SPARC 3.6 micron disk/bulge profiles.
- Signed gas gravitational convention: `Vgas * abs(Vgas)`.
- `Vobs` is forbidden as the persistence source-current velocity.
- Primary current definition: `J(R) = Sigma_b(R) * V_model(R)`.
- Missing-profile handling is determined from data provenance, never model performance.

## Corrected public-data audit

The 2016 public SPARC mass-model release does not provide radial H I surface-density profiles. Hua et al. (A&A 703, A223, 2025; DOI 10.1051/0004-6361/202555721) independently searched the literature and report direct H I surface-density profiles for 169/175 SPARC galaxies. They identify six systems for which the H I rotation-curve references do not provide such profiles:

- D512-2
- D564-8
- D631-7
- NGC4138
- NGC5907
- UGC06818

A previous project note incorrectly counted only four of these in the frozen stationary master. Direct audit of `stationary_split_v1.csv` establishes that **five** are in the frozen 149-galaxy sample: D564-8, D631-7, NGC4138, NGC5907, and UGC06818. D512-2 is not in the frozen master.

Their predeclared roles are:

- D564-8 — calibration
- D631-7 — calibration
- NGC4138 — blind
- NGC5907 — calibration
- UGC06818 — calibration

Therefore, if all five remain unavailable after the public-data sweep, the intended direct-profile analysis sample is **144 galaxies = 100 calibration + 44 blind**. The original roles are preserved; no galaxy is reassigned because of data availability or model performance.

Yasin & Desmond (MNRAS 539, 2110, 2025; DOI 10.1093/mnras/staf453) state that the azimuthally averaged SPARC H I surface-density profiles they used were supplied by F. Lelli via private communication and were available for 169 galaxies. That private compilation is not used here. The current project is deliberately exhausting public primary/derived data routes first.

## Public direct-profile recovery completed so far

The public reconstruction has advanced beyond the original blocker state.

### Direct public map extraction

- DDO154 — 136 clean H I radial bins
- DDO168 — 113 clean H I radial bins

These profiles were extracted from public THINGS/LITTLE THINGS products with the frozen annular-deprojection and beam-smearing QC procedure.

### Public FEASTS direct radial profiles

Seven additional frozen-sample systems are available as direct radial H I profiles and have been rescaled to the frozen SPARC distance convention:

- NGC2841
- NGC2903
- NGC3198
- NGC3521
- NGC4559
- NGC5033
- NGC5055

### Public Leroy et al. (2008) THINGS radial profiles

CDS/VizieR `J/AJ/136/2782/table7` supplies machine-readable radial H I profiles for six additional frozen systems:

- IC2574
- NGC2403
- NGC2976
- NGC6946
- NGC7331
- NGC7793

The CDS values include helium; both `SigmaHI` and `e_SigmaHI` are divided by 1.36 to return to hydrogen-only surface density before the common downstream helium factor is applied. Leroy Table 4 distances are retained as source metadata and profile radii are rescaled to the frozen SPARC distances.

The current harmonized public build therefore contains:

- **15 frozen stationary galaxies**
- **740 direct H I radial measurements**
- **444 source-profile rows on frozen SPARC radii**
- **zero H I extrapolation**; interpolation is performed only within each measured radial interval.

The active build is reproducible from `analysis/stationary/build_public_harmonized_profiles.py` and its public-data acquisition records.

## Additional executable public routes

- Lelli et al. (2014), CDS `J/A+A/566/A71`: public H I FITS cubes. Frozen-sample overlaps include NGC4068 and UGC04483 after canonical UGC zero-padding normalization.
- Verheijen & Sancisi (2001): the corrected SPARC reference crosswalk identifies a 28-galaxy frozen-sample acquisition-lead block. Their public atlas contains radial H I profiles, although the VizieR summary tables do not directly expose the numerical radial samples. NGC4138 and UGC06818 are in this reference block but remain Hua-missing and must not be promoted without an actual recovered profile.
- Swaters et al. (2002), de Blok et al. (1996), Noordermeer et al. (2005), Richards et al. (2015/2016), Broeils (1992), and the remaining literature families remain under public archive/table/map audit.

## Required products still missing

The following cannot be honestly frozen until the public recovery sweep is exhausted and retained-profile coverage is finalized:

1. `stationary_hi_profiles_v1.csv` — harmonized face-on hydrogen-only radial H I surface-density values for the retained direct-profile sample;
2. `stationary_source_profiles_v1.csv` — combined gas+stellar baryonic source profiles on the declared interpolation grid;
3. interpolation/coverage QC for every retained galaxy;
4. resolved-profile cross-survey validation report;
5. redistribution/license provenance for each source family;
6. final `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` with hashes and retained calibration/blind counts.

## Scientific prohibition

Until the source-profile freeze is complete:

- do not fit `L_A` or `C_A`;
- do not use `Vgas(R)` as a surrogate for `Sigma_HI(R)` in the primary analysis;
- do not invert the observed rotation curve to manufacture a primary H I profile;
- do not extrapolate H I outside the measured profile range;
- do not alter calibration/blind roles;
- do not declare the source-profile stage frozen.

## Legitimate routes to completion

A. Continue the public reconstruction from machine-readable radial tables, public H I maps/cubes, and reproducible atlas digitization when no numerical/map product exists.

B. Only after Route A is exhaustively documented, request the private 169-profile compilation from its data provider/authors if material gaps remain.

Route A is now the primary project route because it can yield a reproducible public data product rather than requiring future researchers to repeat private communication.

## Next action

Continue the high-yield public source-family sweep, beginning with the Verheijen & Sancisi / WHISP block and the Lelli-2014 public cubes. Update the harmonized build as each verified profile family lands. Once public routes are exhausted, determine the final retained set, generate full QC/hashes, and only then replace this blocker with `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md`.
