# Appendix I — Baryonic Surface-Density and Source-Current Reconstruction

This directory documents the pre-fit physical source products used to construct the stationary baryonic current for Paper I.

## Scientific boundary

The stationary vector operator requires a baryonic source of the form

`J(R) = Sigma_b(R) V(R)`

with the self-consistent model velocity `V(R)`. The observed rotation speed `Vobs` is target data and is **not** inserted into the primary source current.

The frozen SPARC mass-model table directly supplies:

- inclination-corrected stellar disk surface brightness `SBdisk`;
- bulge surface brightness `SBbulge`;
- Newtonian component velocities `Vgas`, `Vdisk`, and `Vbulge`.

It does **not** directly supply the radial H I surface-density profile. Therefore `Vgas` is not treated as `Sigma_HI` or `Sigma_gas`.

## Stellar surface-density basis

For stellar mass-to-light nuisance parameters `Upsilon_d` and `Upsilon_b`,

`Sigma_disk(R) = Upsilon_d * SBdisk(R)`

`Sigma_bulge(R) = Upsilon_b * SBbulge(R)`

where the SPARC 3.6 micron surface-brightness quantities are in `Lsun/pc^2` and `Upsilon` is in `Msun/Lsun`.

The source-basis product stores the unit-M/L basis rather than silently fixing the nuisance parameters before inference.

## Signed gas gravitational contribution

The SPARC `Vgas` column is signed. Whenever it enters a Newtonian squared-speed sum, the contribution is retained as

`Vgas * abs(Vgas)`

rather than `Vgas**2`.

This preserves the sign convention in the public SPARC mass models.

## Radial H I surface-density profiles

The public 2016 SPARC mass-model tables do not themselves provide the azimuthally averaged radial H I surface-density profiles required by the source-current calculation.

Yasin & Desmond (2025, MNRAS 539, 2110; DOI 10.1093/mnras/staf453) report using azimuthally averaged H I surface-density profiles for 169 SPARC galaxies and state that those profiles were supplied by Federico Lelli via private communication. This repository therefore treats those profile files as **non-public unless and until the data provider authorizes redistribution**.

The primary analysis preference is to use independently sourced/direct radial H I profiles with documented provenance rather than infer `Sigma_HI(R)` from the published `Vgas(R)` curve.

A pre-fit availability audit identifies four systems in the frozen 149-galaxy stationary sample for which the working direct-profile compilation does not currently provide a profile:

- D564-8
- D631-7
- NGC4138
- NGC5907

The current primary direct-profile target is therefore 145 galaxies, while preserving the already-frozen calibration/blind role of every retained galaxy.

No persistence fit is permitted to determine how missing-profile systems are handled. A secondary inversion/reconstruction method, if used, must be declared and validated on galaxies possessing direct profiles before any blind persistence result is inspected.

## Restricted-data handling

If radial H I profiles are supplied privately:

1. the source files will not be committed to this public repository without explicit redistribution permission;
2. galaxy identifiers, units, distance convention, inclination convention, helium treatment, and provenance will be audited before use;
3. public records may include acquisition status, allowed metadata, checksums where appropriate, transformation code, and permitted derived products;
4. receipt of the profiles cannot alter the frozen calibration/blind split based on model performance; and
5. providing the profiles does not imply collaboration or endorsement of the theoretical framework or conclusions.

See the repository-level [`DATA_POLICY.md`](../../../DATA_POLICY.md) for the full policy.

## Source-current velocity

The primary stationary source current uses the self-consistent model velocity:

`J(R) = Sigma_b(R) * V(R)`.

`Vobs(R)` remains the target observable. It is never inserted as the current velocity in the primary fit.

## Current products

The source-reconstruction directory and validation records contain the pre-fit source basis, profile-availability/provenance records, and build summaries. These are observational/source-construction products only; they do not contain fitted `L_A`, `C_A`, or `tau_A` values.

## Freeze rule

This directory remains in the **source-reconstruction stage**, not the final source-profile freeze. The final `Sigma_HI(R)`, `Sigma_gas(R)`, `Sigma_b(R)`, interpolation/continuation rules, and source-current products will receive a separate versioned freeze record before stationary persistence fitting begins.
