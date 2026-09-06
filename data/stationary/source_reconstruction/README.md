# Appendix I — Baryonic Surface-Density and Source-Current Reconstruction

This directory documents the pre-fit physical source products used to construct the stationary baryonic current for Paper I.

## Scientific boundary

The stationary vector operator requires a baryonic source of the form

`J(R) = Sigma_b(R) V(R)`

with the self-consistent model velocity `V(R)`. The observed rotation speed `Vobs` is target data and is **not** inserted into the primary source current.

The frozen SPARC mass-model table directly supplies inclination-corrected stellar disk and bulge surface brightness and the Newtonian component velocities. It does **not** directly supply the radial H I surface-density profile. Therefore `Vgas` is never treated as `Sigma_HI` or `Sigma_gas`.

## Public-first acquisition policy

The 169-profile set used by later SPARC analyses was assembled from literature H I observations and has also circulated through private communication. This project is rebuilding the source profiles from public primary products before asking for that private compilation.

Acquisition priority is:

1. public machine-readable radial profile;
2. public FITS/moment-map extraction;
3. documented figure/atlas digitization only when no numerical/map product is available;
4. private communication only after the public routes are exhausted.

The public observational layer is retained losslessly with source citation/product identifier, source distance, units, helium convention, geometry, QC, and redistribution status.

## Corrected Hua availability intersection

Hua et al. identify six SPARC systems without a compiled H I surface-density profile: `D512-2`, `D564-8`, `D631-7`, `NGC5907`, `NGC7339`, and `UGC06818`.

Only four are in the frozen 149-galaxy stationary sample:

- `D564-8` — calibration;
- `D631-7` — calibration;
- `NGC5907` — calibration;
- `UGC06818` — blind.

`NGC4138` was incorrectly listed as unavailable in an earlier scaffold. It is not in Hua's missing set and remains eligible for public acquisition. The expected retained sample remains 145 = 101 calibration + 44 blind if none of the four nominally unavailable systems is independently recovered before fitting.

The correction is archived in `validation/stationary/HI_PROFILE_PROVENANCE_CORRECTION_V1.md`. Any older generated provenance table carrying the NGC4138 flag is superseded for availability decisions until regenerated from the corrected builder.

## Current public recovery state

### Direct profiles already harmonized at the acquisition layer

Two frozen-sample systems have direct THINGS/LITTLE THINGS map extractions:

- DDO154;
- DDO168.

Seven more have direct public FEASTS radial profiles:

- NGC2841;
- NGC2903;
- NGC3198;
- NGC3521;
- NGC4559;
- NGC5033;
- NGC5055.

Together the acquisition-layer build contains 507 direct radial H I measurements. Interpolation only inside measured profile coverage gives 244 source rows on frozen SPARC radii. These products are **pre-standardization**, not yet the final source freeze.

### Six THINGS systems with machine-readable public profiles

The public Leroy et al. (2008) CDS catalogue `J/AJ/136/2782/table7` contains radial H I profiles for the six remaining high-priority frozen THINGS systems:

- IC2574;
- NGC2403;
- NGC2976;
- NGC6946;
- NGC7331;
- NGC7793.

The importer is `analysis/stationary/import_leroy2008_hi_profiles.py`. Leroy's `SigmaHI` includes helium using factor 1.36; the importer removes that factor to restore hydrogen-only `Sigma_HI` before the common SPARC/Hua gas correction is applied.

### Largest literature families

`major_public_family_queue_v1.csv` records the frozen-sample intersection for the largest source families. Current queue sizes include:

- Swaters et al. 2002 / WHISP: 26 frozen systems;
- Verheijen & Sancisi 2001 / Ursa Major: 27 frozen systems (with UGC06818 retained as a special Hua-missing audit target, not presumed recovered);
- Noordermeer et al. 2005 / WHISP: 12 frozen systems;
- de Blok et al. 1996: 8 frozen systems;
- Lelli et al. 2014: NGC4068 in the frozen sample via the direct SPARC reference code.

The SPARC `Ref.` codes are acquisition leads; profile provenance is confirmed only after the actual public radial profile/map is inspected.

## Standardization to the SPARC/Hua convention

Public acquisition and final profile standardization are separate stages.

Hua et al. standardized the literature profiles using GIPSY `Rotmod`, with the SPARC H I mass and distance and an exponential 100 pc vertical scale height. Therefore a profile is not promoted to final `stationary_hi_profiles_v1.csv` until either:

1. the same `Rotmod` operation is reproduced, or
2. a numerically equivalent implementation is validated against `Rotmod` on a representative subset under a predeclared tolerance.

See `validation/stationary/PUBLIC_HI_STANDARDIZATION_PROTOCOL_V1.md`.

## Stellar and gas conventions

The current canonical convention is

- `Upsilon_disk = 0.5`;
- `Upsilon_bulge = 0.7`;
- canonical stored profile is hydrogen-only `Sigma_HI`;
- combined atomic gas uses `Sigma_atomic = 1.33 * Sigma_HI`.

Source-specific helium factors are removed before the common 1.33 correction; they are never double-applied.

## Signed gas gravitational contribution

The SPARC `Vgas` column is signed. Whenever it enters a Newtonian squared-speed sum, preserve

`Vgas * abs(Vgas)`

rather than `Vgas**2`.

## Restricted-data and redistribution handling

Public downloadability does not automatically imply permission to mirror raw files. For each source family we record license/rights status separately. Where raw redistribution is restricted, the public release will provide the reproducible acquisition/extraction code, provenance, permitted metadata, and legally redistributable derived products rather than republishing restricted raw files.

If private data are eventually required, no private source file is committed without explicit redistribution permission. Providing observational data never implies collaboration or endorsement of the persistence framework.

See repository-level `DATA_POLICY.md`.

## Freeze rule

This directory remains in the **source-reconstruction stage**. No `L_A`, `C_A`, `tau_A`, or persistence prediction may be evaluated until acquisition, standardization, coverage/interpolation QC, redistribution audit, and the versioned source-profile freeze are complete.
