# Appendix I build status v1

**Stage:** PRE-FIT PUBLIC SOURCE RECONSTRUCTION

## Completed

- Frozen 149-galaxy / 3,152-point observational master.
- Frozen 104/45 calibration-blind role assignment.
- Stellar surface-density basis defined from SPARC 3.6 micron disk and bulge profiles.
- Signed gas gravitational convention fixed as `Vgas * abs(Vgas)`.
- `Vobs` prohibited as the source-current velocity.
- Missing-HI-profile handling predeclared before any persistence fitting.
- Public-first acquisition hierarchy and redistribution audit established.
- Nine frozen-sample public direct-profile systems have an acquisition-layer harmonized build (507 H I bins; 244 no-extrapolation source rows).
- Six additional THINGS systems have a verified machine-readable Leroy et al. (2008) profile route.
- Major Swaters/WHISP, Verheijen-Sancisi, Noordermeer, de Blok, and Lelli source-family queues are archived.
- Public profile standardization protocol is frozen before persistence fitting.

## Current gating item

The primary analysis requires radial H I surface-density profiles with explicit
provenance and common SPARC/Hua standardization. The 2016 public SPARC mass-model
release does not contain these profiles directly, so the project is reconstructing
them from public literature and survey products before requesting a private
compilation.

Hua et al. report locating radial H I profiles for 169/175 SPARC systems. Their
six exceptions are `D512-2`, `D564-8`, `D631-7`, `NGC5907`, `NGC7339`, and
`UGC06818`. Four occur in the frozen 149-galaxy sample:

- `D564-8` — calibration;
- `D631-7` — calibration;
- `NGC5907` — calibration;
- `UGC06818` — blind.

`NGC4138` was incorrectly listed as unavailable in an earlier scaffold. It is
eligible and remains in the public acquisition queue. The correction is
recorded in `HI_PROFILE_PROVENANCE_CORRECTION_V1.md`.

If no independently verified direct profiles are found for the four nominally
unavailable systems before fitting, the primary direct-profile subset will
contain 145 galaxies while preserving the frozen roles of all retained systems:
101 calibration and 44 blind galaxies.

## Standardization gate

Acquisition alone is not sufficient for final freeze. Hua standardized literature
profiles using GIPSY `Rotmod` with the SPARC H I mass and distance and an
exponential 100 pc vertical scale height. Final profile promotion therefore
requires either the same operation or a separately validated numerical
equivalent under a predeclared tolerance. Until then, acquired profiles remain
`pre-standardization` products.

## Required next products before L_A or C_A fitting

1. regenerated corrected `stationary_hi_profile_provenance_v1.csv`;
2. complete standardized `stationary_hi_profiles_v1.csv`;
3. complete `stationary_source_profiles_v1.csv`;
4. direct-profile interpolation/coverage QC;
5. Rotmod/equivalence validation report;
6. redistribution/license audit;
7. resolved-profile validation report;
8. `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md`.

No stationary persistence fitting begins until those products are complete and
frozen.
