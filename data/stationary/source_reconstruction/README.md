# Appendix I — Baryonic Surface-Density and Source-Current Reconstruction

This directory contains the pre-fit physical source products used to construct
the stationary baryonic current for Paper I.

## Scientific boundary

The stationary vector operator requires a baryonic source of the form

`J(R) = Sigma_b(R) V(R)`

with the self-consistent model velocity `V(R)`. The observed velocity `Vobs` is
target data and is **not** inserted into the source current.

The frozen SPARC 2016 mass-model table directly supplies:

- inclination-corrected stellar disk surface brightness `SBdisk`;
- bulge surface brightness `SBbulge`;
- Newtonian component velocities `Vgas`, `Vdisk`, and `Vbulge`.

It does **not** directly supply the radial HI surface-density profile. Therefore
`Vgas` must not be treated as `Sigma_gas`.

## Stellar surface-density basis

For stellar mass-to-light nuisance parameters `Upsilon_d` and `Upsilon_b`,

`Sigma_disk(R) = Upsilon_d * SBdisk(R)`

`Sigma_bulge(R) = Upsilon_b * SBbulge(R)`

where the SPARC 3.6 micron surface-brightness quantities are in `Lsun/pc^2` and
`Upsilon` is in `Msun/Lsun`.

The file `stationary_source_basis_v1.csv` stores the unit-M/L basis rather than
silently fixing the nuisance parameters before inference.

## Signed gas gravitational contribution

The SPARC `Vgas` column is signed. The corresponding gravitational contribution
to a squared-speed sum is retained as

`Vgas * abs(Vgas)`

rather than `Vgas**2`.

This preserves the sign conventions in the public SPARC mass models.

## Gas surface-density acquisition

The first public SPARC mass-model release did not include radial HI surface-
density profiles. Hua et al. (2025, A&A 703, A223) report locating such profiles
in the literature for 169 of 175 SPARC systems. They identify six systems whose
underlying references do not provide radial HI profiles:

- D512-2
- D564-8
- D631-7
- NGC5907
- NGC4138
- UGC06818

Four of these systems are present in the frozen 149-galaxy stationary sample:
D564-8, D631-7, NGC5907, and NGC4138.

No persistence fit is permitted to determine how these four systems are handled.
A missing-profile policy must be frozen before fitting. Candidate policies are:

1. primary analysis restricted to galaxies with independently sourced HI radial
   profiles, with the missing-profile systems retained only for a predeclared
   secondary reconstruction test; or
2. a separately validated inversion/reconstruction method applied to the missing
   systems, with validation performed against galaxies possessing direct HI
   profiles before any blind persistence result is inspected.

The primary preference is direct profile ingestion rather than inversion.

## Current products

- `stationary_source_basis_v1.csv` — exact stellar-density and Newtonian-component
  basis derived from the frozen observational master, with no `L_A` or `C_A`.
- `../../../../validation/stationary/stationary_source_availability_v1.csv` —
  one-row-per-galaxy gas-profile acquisition status.
- `../../../../validation/stationary/stationary_source_basis_v1_summary.json` —
  machine-readable build summary and hashes.

## Freeze rule

This directory is still in the **source-reconstruction stage**, not the final
source-profile freeze. The final `Sigma_gas(R)`, `Sigma_b(R)`, and current-source
products will receive a separate versioned freeze record before stationary
persistence fitting begins.
