# Appendix I build status v1

**Stage:** PRE-FIT SOURCE RECONSTRUCTION

## Completed

- Frozen 149-galaxy / 3,152-point observational master.
- Frozen 104/45 calibration-blind role assignment.
- Stellar surface-density basis defined from SPARC 3.6 micron disk and bulge profiles.
- Signed gas gravitational convention fixed as `Vgas * abs(Vgas)`.
- `Vobs` prohibited as the source-current velocity.
- Missing-HI-profile handling predeclared before any persistence fitting.
- Appendix I compact manuscript text added under `manuscript_links/`.
- Reproducible source-basis builder and GitHub Actions workflow added.

## Current gating item

The primary analysis requires radial HI surface-density profiles with explicit
provenance. The 2016 public SPARC mass-model release does not contain these
profiles directly.

Hua et al. (2025, A&A 703, A223) report locating radial HI profiles in the
literature for 169/175 SPARC systems. Their six exceptions are D512-2, D564-8,
D631-7, NGC5907, NGC4138, and UGC06818. Four of these occur in the frozen
149-galaxy sample: D564-8, D631-7, NGC4138, and NGC5907.

If no additional direct profiles are found for those four systems, the primary
direct-profile subset will contain 145 galaxies while preserving the frozen
roles of all retained systems: 101 calibration and 44 blind galaxies.

## Required next products before L_A or C_A fitting

1. `stationary_hi_profile_provenance_v1.csv`
2. `stationary_hi_profiles_v1.csv`
3. `stationary_source_profiles_v1.csv`
4. direct-profile interpolation/coverage QC
5. resolved-profile validation report
6. `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md`

No stationary persistence fitting begins until those products are complete and
frozen.
