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
- Missing-profile handling must be determined from data provenance, never model performance.

## Public-data audit (2026-08-10)

The 2016 public SPARC mass-model release does not provide radial H I surface-density profiles. Hua et al. (A&A 703, A223, 2025; DOI 10.1051/0004-6361/202555721) independently searched the literature and report direct H I surface-density profiles for 169/175 SPARC galaxies. They identify six systems for which the H I rotation-curve references do not provide such profiles: D512-2, D564-8, D631-7, NGC5907, NGC4138, and UGC06818.

Four of those six are in the frozen 149-galaxy stationary sample: D564-8, D631-7, NGC4138, and NGC5907. Therefore the intended primary direct-profile subset remains 145 galaxies, preserving the original roles (101 calibration / 44 blind) if all other profiles are acquired.

Yasin & Desmond (MNRAS 539, 2110, 2025; DOI 10.1093/mnras/staf453) explicitly state that the azimuthally averaged SPARC H I surface-density profiles they used were supplied by F. Lelli via private communication and were available for 169 galaxies. No verified public machine-readable download of that 169-profile compilation was found in this audit.

Hua et al. provide the original literature reference for each profile in their Table A.1 and describe a consistent face-on reconstruction using the published H I profiles, SPARC distances/H I masses, and GIPSY ROTMOD. The article does not itself expose a verified public machine-readable 169-profile table in the sources checked here.

## Direct profiles already recovered independently

Prior project work has directly extracted annular H I profiles from survey FITS products for at least DDO154 and DDO168. A prepared FITS-ingestion workflow also identified NGC2366 and NGC4214 as immediately tractable LITTLE THINGS/SPARC overlap systems. These independent profiles are valuable validation/acquisition assets but do not constitute the required 145-galaxy primary source set.

## Required products still missing

The following cannot be honestly frozen until the profile values themselves are available with provenance:

1. `stationary_hi_profiles_v1.csv` — face-on radial H I surface-density values for the primary direct-profile subset;
2. `stationary_source_profiles_v1.csv` — combined gas+stellar baryonic source profiles on the declared interpolation grid;
3. interpolation/coverage QC for each retained galaxy;
4. resolved-profile validation report;
5. final `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` with hashes and retained-sample counts.

`stationary_hi_profile_provenance_v1.csv` exists, but most eligible galaxies are correctly marked `available_nonpublic_request_required`, `public_download_verified=0`, and `profile_data_ingested=0`.

## Scientific prohibition

Until the missing direct profile data are obtained or independently reconstructed from the original cited observations under a predeclared procedure:

- do not fit `L_A` or `C_A`;
- do not use `Vgas(R)` as a surrogate for `Sigma_HI(R)` in the primary analysis;
- do not invert the observed rotation curve to manufacture a primary H I profile;
- do not alter calibration/blind roles;
- do not declare the source-profile stage frozen.

## Legitimate routes to completion

A. Obtain the 169-profile compilation from its data provider/authors with permission and ingest it under `DATA_POLICY.md`.

B. Reconstruct the 145 required profiles independently from the original literature/data products listed by Hua et al. Table A.1, using one predeclared face-on conversion/interpolation protocol and cross-validating against independently extracted survey profiles.

Route A is preferred because it minimizes heterogeneous reprocessing. Route B remains scientifically valid but is a substantial data-reduction project.

## Next action

Acquire the radial H I profile values. Once acquired, run the existing provenance/source builders and QC, write hashes, confirm the retained 101/44 role counts, and only then replace this blocker record with `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md`.
