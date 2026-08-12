# Taylor et al. (1994) — UGC05829 public H I source audit v1

**Status:** PUBLIC H I IMAGING SOURCE CONFIRMED; DIRECT RADIAL-PROFILE REPRESENTATION NOT YET VERIFIED  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `\mathcal C_A` remain locked.

## Frozen Paper I target

| Frozen galaxy | Frozen role | Frozen distance | Frozen inclination | Frozen radial mass-model range |
|---|---|---:|---:|---:|
| UGC05829 | blind | 8.64 Mpc | 34 deg | 0.63–6.91 kpc |

The frozen role is immutable and is not changed by source availability.

## Primary publication

C. L. Taylor, E. Brinks, R. W. Pogge & E. D. Skillman (1994), **“Star formation thresholds in H II galaxies with H I companions,”** *The Astronomical Journal* **107**, 971–983. DOI `10.1086/116910`.

The primary abstract describes high-resolution VLA 21-cm observations combined with earlier lower-resolution data and explicitly discusses radial H I profiles across the study samples. Independent later literature specifically identifies UGC 5829 H I synthesis mapping as Taylor et al. (1994).

## UGC05829 source attribution

A later large H I compilation explicitly lists:

- UGC 5829
- H I beam approximately `0.33 x 0.33 arcmin` (~20 x 20 arcsec)
- H I angular extent approximately `6.0 x 5.3 arcmin`
- heliocentric velocity about 629 km/s
- compilation distance 5.7 Mpc
- `log M_HI ~ 8.68`
- morphology `Im`
- H I reference: **Taylor et al. (1994)**

That same compilation leaves its inclination-corrected radial-profile diameter field blank for UGC5829. This matters: it supports the Taylor H I **map** attribution, but it does not establish that a publication-grade azimuthally averaged radial surface-density curve can be recovered directly from the 1994 paper.

## Current acquisition interpretation

The correct state is therefore:

`public_HI_synthesis_map_source_confirmed / radial_profile_representation_pending`

—not `profile_ingested`.

The Taylor paper must not be used as a direct radial profile until one of the following is recovered:

1. an explicit UGC5829 radial H I surface-density plot/table in the primary article;
2. a machine-readable H I map/cube from which the profile can be reconstructed using a frozen, documented annular-deprojection procedure; or
3. a later public source that explicitly republishes the azimuthally averaged Taylor H I radial profile with adequate provenance.

## Distance / geometry warning

The later compilation's 5.7-Mpc distance is a literature convention and must **not** overwrite the Paper I frozen distance of 8.64 Mpc. Any recovered angular profile/map should be preserved natively first and converted to the frozen physical-radius convention only under the later global normalization rules.

Likewise, no inclination-based surface-density rescaling is applied at this acquisition step. The frozen inclination is 34 deg; the source/map geometry must be recovered explicitly before any deprojection transformation is frozen.

## Why this corrects the van Zee false lead

UGC05829 was temporarily swept into the van Zee 1997 work because it lies next to van Zee galaxies in later H I compilations. The source table itself clearly attributes:

- UGC5716 -> van Zee et al. (1997)
- UGC5764 -> van Zee et al. (1997)
- UGC5829 -> **Taylor et al. (1994)**

That correction is now durable and UGC05829 has its own source block.

## Next action

Do one bounded primary/archive search for either the original UGC5829 radial profile or reusable VLA H I map/cube. If neither is publicly recoverable at sufficient fidelity, leave UGC05829 as `public_map_source_confirmed / numeric_profile_pending` and continue the remaining public source blocks rather than looping.

No persistence parameter or blind outcome has been inspected in making this source attribution.
