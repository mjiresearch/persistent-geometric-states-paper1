# Leroy et al. (2008) / THINGS radial H I profile audit v1

**Status:** PUBLIC MACHINE-READABLE RADIAL PROFILE BLOCK IDENTIFIED — 11 FROZEN PAPER I GALAXIES  
**Date:** 2026-08-12  
**Scientific boundary:** source acquisition only. `L_A` and `\mathcal C_A` remain locked.

## Primary source and public catalog

A. K. Leroy, F. Walter, E. Brinks, F. Bigiel, W. J. G. de Blok, B. Madore & M. D. Thornley (2008), **“The Star Formation Efficiency in Nearby Galaxies: Measuring Where Gas Forms Stars Effectively,”** *The Astronomical Journal* **136**, 2782–2845. DOI `10.1088/0004-6256/136/6/2782`; ADS bibcode `2008AJ....136.2782L`.

Public machine-readable catalog: **VizieR J/AJ/136/2782**, DOI `10.26093/cds/vizier.51362782`.

The catalog states that the work uses H I maps from **THINGS** and provides an electronic table of radial profiles. VizieR `table7` contains **687 radial rows** for the 23-galaxy Leroy sample.

Relevant `table7` columns are:

- `Name` — galaxy name;
- `r` — galactocentric ring-center radius in **kpc**;
- `r.n` — radius normalized to `r25`;
- `SigmaHI` — H I surface density in `Msun pc^-2`;
- `e_SigmaHI` — RMS uncertainty in `SigmaHI`.

VizieR Note (2) explicitly states that the tabulated `SigmaHI`/`SigmaH2` surface densities are **including helium**. The source-published `SigmaHI` column is therefore preserved unchanged as the authoritative acquisition quantity. No second helium correction is permitted.

The exact numerical helium factor used to define the published Leroy column is **not required for source preservation**. Until its primary-source convention is frozen explicitly, no raw-H-I column is produced by dividing the catalog values by an assumed factor.

## Exact crossmatch to the frozen 149-galaxy Paper I master

Eleven Leroy/THINGS galaxies are members of the frozen Paper I stationary sample:

| Galaxy | Frozen role | Leroy numeric source status |
|---|---|---|
| DDO154 | calibration | machine-readable `table7` profile available |
| IC2574 | calibration | machine-readable `table7` profile available |
| NGC2403 | blind | machine-readable `table7` profile available |
| NGC2841 | calibration | machine-readable `table7` profile available |
| NGC2976 | calibration | machine-readable `table7` profile available |
| NGC3198 | calibration | machine-readable `table7` profile available |
| NGC3521 | blind | machine-readable `table7` profile available |
| NGC5055 | blind | machine-readable `table7` profile available |
| NGC6946 | blind | machine-readable `table7` profile available |
| NGC7331 | calibration | machine-readable `table7` profile available |
| NGC7793 | blind | machine-readable `table7` profile available |

**Total:** 11 frozen galaxies = **6 calibration + 5 blind**.

No additional Leroy galaxy is promoted unless it is an exact/verified alias of a frozen master member.

## Why this source block is high-value

Unlike the Côté, van Zee and NGC3741 figure-recovery branches, this block does **not require graph digitization**. It provides public numerical radius/surface-density pairs and uncertainties directly from the electronic journal catalog.

This makes Leroy/THINGS a preferred direct-profile source for the 11 overlapping galaxies, subject to the global Paper I normalization and radial-coverage QC that will be frozen later.

## Source-coordinate and normalization rule

At acquisition time:

1. preserve Leroy `r` in kpc exactly as published;
2. preserve `r.n` exactly as published;
3. preserve helium-inclusive `SigmaHI` and `e_SigmaHI` exactly as published;
4. store the Leroy source distance/inclination separately from the frozen Paper I metadata when the sample-properties table is ingested;
5. do **not** silently rescale the published radius to the frozen SPARC distance yet;
6. do **not** apply a second helium factor;
7. do **not** interpolate, extrapolate or taper the profile yet;
8. do **not** inspect persistence fit quality while deciding source inclusion.

Any later transformation from the source-published coordinate/convention to the final Paper I canonical source profile must be explicit, versioned, and applied under one globally frozen rule.

## Reproducible acquisition path

A repository ingestion script is maintained at:

`scripts/stationary/ingest_leroy2008_things_hi_profiles.py`

It queries VizieR's tab-separated interface for `J/AJ/136/2782/table7`, retains only the predeclared 11-galaxy overlap, validates the expected frozen role mapping, and writes a provenance-preserving raw-source CSV.

Target output:

`data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv`

The output is a **source-data product**, not yet the final normalized `stationary_hi_profiles_v1.csv`.

## Acceptance/QC gates

Before the Leroy profiles are promoted into the final stationary H I source freeze:

- all 11 expected galaxies must be present;
- every retained galaxy must have at least one finite `r`/`SigmaHI` row;
- radii must be nonnegative and monotonically ordered within galaxy after source-row ordering is checked;
- no duplicate `(galaxy, r)` keys may be silently collapsed;
- missing/upper-limit surface-density values must remain explicitly missing/flagged rather than imputed;
- source and frozen distance/inclination conventions must be stored separately;
- radial coverage relative to the frozen SPARC rotation-curve domain must be reported;
- helium-inclusive status must remain explicit.

## Current disposition

- public source identity: **COMPLETE**
- machine-readable radial profile catalog: **COMPLETE / AVAILABLE**
- frozen-master crossmatch: **COMPLETE — 11 galaxies**
- frozen-role split: **6 calibration + 5 blind**
- source `SigmaHI` helium status: **CONFIRMED — already includes helium**
- reproducible ingestion code: **OPENED / TO BE RUN AGAINST VIZIER**
- raw-source profile CSV committed from catalog: **PENDING EXECUTION**
- global distance/inclination/helium normalization: **LOCKED pending common source-profile rules**
- `L_A`, `\mathcal C_A`: **LOCKED**
