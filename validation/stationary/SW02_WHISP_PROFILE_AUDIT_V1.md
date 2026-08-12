# Swaters et al. 2002 — WHISP late-type dwarf H I profile audit v1

**Status:** DIRECT RADIAL H I PROFILES CONFIRMED; ARXIV FIGURE GEOMETRY NOT NUMERICALLY EXTRACTABLE; CLOSED FOR THIS PASS  
**Date:** 2026-08-12  
**SPARC/Lelli reference ID:** `Sw02`  
**Scientific boundary:** acquisition/provenance only. `L_A` and `\mathcal C_A` remain locked.

## Why this family was audited

The Lelli/SPARC source-family priority map assigns **13 still-untouched frozen Paper I galaxies = 7 calibration + 6 blind** to Swaters et al. (2002):

`DDO064, UGC00731, UGC01281, UGC04278, UGC05986, UGC07125, UGC07151, UGC07577, UGC07603, UGC08286, UGC08550, UGC08837, UGC11557`.

## Primary source

R. A. Swaters, T. S. van Albada, J. M. van der Hulst & R. Sancisi (2002), **“The Westerbork HI Survey of Spiral and Irregular Galaxies. I. HI Imaging of Late-type Dwarf Galaxies,”** *Astronomy & Astrophysics* **390**, 829–861; arXiv `astro-ph/0204525`.

The paper presents H I observations for **73 late-type dwarf galaxies** and explicitly states that it provides H I maps, velocity fields, global profiles and **radial H I surface-density profiles**.

## Profile-construction method recovered from the primary TeX source

The public arXiv source package contains the full manuscript TeX, which specifies the profile construction in detail:

1. Total H I maps are the starting data product.
2. For well-resolved systems with inclination below about 75 deg, H I is azimuthally averaged in concentric ellipses using the same orientation parameters as the rotation-curve analysis; approaching and receding sides are treated separately and blank/no-signal pixels are excluded.
3. For highly inclined or poorly resolved galaxies, radial profiles are derived from minor-axis H I strip integrals using the Warmels (1988b) / Lucy (1974) iterative deconvolution method, assuming axisymmetry.
4. The Lucy iteration is stopped after 10 iterations or earlier when the reconstructed strip integral matches the observed one at the 95% confidence level.
5. The paper defines `R_HI` at the **face-on-corrected H I surface density of 1 Msun pc^-2**.

This is a direct H I surface-density construction; no helium correction is introduced in the recovered profile-method text.

## Published profile figure and ordinate transform

The arXiv package contains `h3074f4.ps` and `h3074f5.ps`. The manuscript identifies these as the radial H I surface-density-profile figure and continuation.

The caption explicitly states that the full-line H I profiles are plotted on a **“magnitude scale”**:

`2.5 log Sigma_HI`

with dotted lines showing exponential fits to the outer profile. UGC numbers are said to appear in the lower-left corner of each panel.

Thus the plotted transform itself is unambiguous and reversible in principle if the physical axis calibration and curve geometry can be recovered.

## ArXiv asset structure

The public arXiv source archive contains 14 files, including the manuscript TeX and 12 PostScript figures. The archive SHA-256 is:

`9302f5dbc1e19775d00a1f182a4e99c5b5aa345aed4658f3e95c93f5c30b8cfa`

A dedicated inspection of `h3074f4.ps` found:

- file size: 190,087 bytes;
- BoundingBox: `30 125 563 740`;
- `moveto`: 10 occurrences;
- `lineto`: 5 occurrences;
- `setrgbcolor`: 1 occurrence;
- `show`: 2 occurrences;
- `stroke`: 6 occurrences;
- PostScript literal strings: 2, with **no useful UGC/axis/profile labels**;
- no available separate vector curve paths or panel labels recoverable from the PostScript drawing structure.

This structure is incompatible with 73 individually recoverable plotted profile curves as native PostScript paths. The scientific figure content has effectively been embedded/flattened rather than retained as separable vector geometry.

## Current disposition

- Lelli/SPARC source identity: **COMPLETE**
- 13 frozen-galaxy overlap: **COMPLETE**
- primary radial H I profiles published: **CONFIRMED**
- profile-construction method: **CONFIRMED**
- face-on `R_HI` convention: **CONFIRMED**
- plotted ordinate transform `2.5 log Sigma_HI`: **CONFIRMED**
- helium scaling in recovered profile method: **NONE FOUND; do not add during source acquisition**
- arXiv profile figures: **PRESENT BUT FLATTENED / NOT SEPARABLE AS PUBLICATION-GRADE VECTOR CURVES**
- machine-readable numerical radial profiles in this arXiv package: **ABSENT**
- Paper I numerical ingestion from `Sw02`: **PENDING A GENUINELY NEW PUBLIC DATA/TABLE/MAP MECHANISM**

## Anti-loop decision

Do **not** repeat the current arXiv Figure 4/5 vector inspection. Reopen `Sw02` only if a genuinely new mechanism appears, such as the original WHISP maps, a machine-readable radial-profile table, a non-flattened publisher asset, or a public republication of the profiles.

The Lelli-directed acquisition queue therefore advances to the next highest-yield untouched family rather than digitizing the flattened figures.

No persistence parameter or blind outcome was inspected in making this provenance decision.
