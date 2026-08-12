# Leroy et al. (2008) / THINGS radial H I profile audit v1

**Status:** COMPLETE RAW-SOURCE ACQUISITION — 11 FROZEN PAPER I GALAXIES / 369 RADIAL ROWS  
**Date:** 2026-08-12  
**Scientific boundary:** source acquisition only. `L_A` and `\mathcal C_A` remain locked.

## Primary source and public catalog

A. K. Leroy, F. Walter, E. Brinks, F. Bigiel, W. J. G. de Blok, B. Madore & M. D. Thornley (2008), **“The Star Formation Efficiency in Nearby Galaxies: Measuring Where Gas Forms Stars Effectively,”** *The Astronomical Journal* **136**, 2782–2845. DOI `10.1088/0004-6256/136/6/2782`; ADS bibcode `2008AJ....136.2782L`.

Public machine-readable catalog: **VizieR J/AJ/136/2782**, DOI `10.26093/cds/vizier.51362782`.

VizieR `table7` contains **687 radial rows** for the 23-galaxy Leroy sample. Relevant source columns are `Name`, galactocentric `r` in kpc, `r.n`, `SigmaHI`, and `e_SigmaHI`.

VizieR Note (2) explicitly states that the tabulated gas surface densities are **including helium**. Paper I therefore preserves the source-published `SigmaHI` and uncertainty unchanged. No second helium correction or assumed raw-H-I back-conversion is applied in this acquisition product.

## Frozen Paper I overlap and acquired rows

| Galaxy | Frozen role | Acquired radial rows |
|---|---|---:|
| DDO154 | calibration | 7 |
| IC2574 | calibration | 46 |
| NGC2403 | blind | 57 |
| NGC2841 | calibration | 25 |
| NGC2976 | calibration | 26 |
| NGC3198 | calibration | 23 |
| NGC3521 | blind | 30 |
| NGC5055 | blind | 43 |
| NGC6946 | blind | 41 |
| NGC7331 | calibration | 33 |
| NGC7793 | blind | 38 |

**Total acquired:** **369 radial profile rows across 11 frozen galaxies = 6 calibration + 5 blind.**

## Reproducible ingestion result

The repository script

`scripts/stationary/ingest_leroy2008_things_hi_profiles.py`

queries VizieR's public TSV interface, normalizes only catalogue-name spacing for the frozen-master crossmatch while preserving the original VizieR name separately, verifies all immutable calibration/blind roles, checks nonnegative/increasing source radii and duplicate keys, and writes:

`data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv`

The successful GitHub Actions run ingested all 687 public source rows, retained the predeclared 369 rows belonging to the 11 frozen overlaps, and committed the generated source product to `main`.

Canonical machine-generated summary:

`validation/stationary/leroy2008_things_hi_profiles_v1_summary.json`

Recorded output SHA-256:

`d0cc498aaf7b378bf9affe19f0ca5ea7f638622e23517986ee2ee6477d7ddc75`

Recorded frozen-split SHA-256 used for role validation:

`eceac43dc287326eb126b150a940d6681b4bbfe0015e5efc8ef4769876f9a9d1`

## What has and has not been transformed

The committed Leroy CSV is deliberately a **raw-source profile product**:

- source radius in kpc is preserved as published;
- source normalized radius is preserved as published;
- source helium-inclusive `SigmaHI` is preserved as published;
- source uncertainty is preserved as published;
- no frozen-distance radius rescaling has been applied;
- no inclination-amplitude rescaling has been applied;
- no helium removal/reapplication has been performed;
- no interpolation, extrapolation, taper or common-grid resampling has been performed;
- no persistence parameter or blind-test outcome has been evaluated.

The Leroy source distance/inclination metadata and radial coverage relative to the frozen SPARC rotation-curve domains remain part of the later common normalization/QC stage.

## Scientific/database consequence

This is the first large Paper I source block in which public numerical radial H I profiles have been ingested directly rather than reconstructed or digitized. These 11 profiles therefore move from `public_source_available` to **`raw_source_profile_ingested`**.

They are **not yet** the final `stationary_hi_profiles_v1.csv`; that promotion occurs only after the common distance/inclination/helium/interpolation rules are globally frozen and the coverage QC is completed.

## Current disposition

- public source identity: **COMPLETE**
- machine-readable radial profile catalog: **COMPLETE**
- frozen-master crossmatch: **COMPLETE — 11 galaxies**
- raw numerical profile ingestion: **COMPLETE — 369 rows**
- source helium status: **CONFIRMED — already includes helium**
- reproducible Actions validation: **PASSED**
- common source normalization / radial-coverage QC: **NEXT**
- final `stationary_hi_profiles_v1.csv`: **NOT YET FROZEN**
- `L_A`, `\mathcal C_A`: **LOCKED**
