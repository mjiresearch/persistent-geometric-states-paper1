# Lelli 2014 cube + Verheijen 2001 arXiv audit v1

**Status:** completed public-route audit; no persistence parameters opened.

## 1. Lelli et al. (2014) public cube audit

Frozen stationary overlaps audited:

- `NGC4068` — public CDS cube `NGC4068_HIcube_r20.FIT`
- `UGC04483` / UGC 4483 — public CDS cube `UGC4483_HIcube_r10.FIT`

### Audit result

The CDS products are science H I cubes, not publication-ready masked total-H I maps or radial profiles.

NGC4068 cube audit:

- shape: `123 x 512 x 512`
- `BUNIT = Jy/beam`
- finite fraction: `0.957489`
- positive voxel fraction: `0.479236`
- negative voxel fraction: `0.478253`
- robust cube RMS: `0.00207641 Jy/beam`
- primary-header `BMAJ/BMIN/BPA`: absent
- HISTORY preserves historical CLEAN-mask names, including `u7047mask`

UGC04483 cube audit:

- shape: `110 x 512 x 512`
- `BUNIT = Jy/beam`
- finite fraction: `0.904724`
- positive voxel fraction: `0.450906`
- negative voxel fraction: `0.453818`
- robust cube RMS: `0.000642480 Jy/beam`
- primary-header `BMAJ/BMIN/BPA`: absent
- HISTORY preserves `U4483_Mask2` and the historical CLEAN restoring-beam record

The nearly symmetric positive/negative populations show that the distributed cubes retain noise outside the source. Therefore a direct channel sum or a newly chosen n-sigma mask would introduce a new reduction choice and is **not admissible for confirmatory source-profile construction**.

### UGC04483 published-mask reproduction

A separate QC-only reconstruction workflow reproduces the published Lelli et al. (2012) masking concept from the public final cube:

- science spatial resolution: 10 arcsec
- effective science velocity resolution: 5.2 km/s
- mask target: 20 arcsec and 10.4 km/s
- mask clipping: approximately 3 sigma of the smoothed cube
- integration: original public final cube within the reconstructed mask
- radial profile: explicitly inclination-corrected, consistent with the published Fig. 6 definition

Two implementation corrections are frozen before any promotion:

1. the FITS channel grid is about 2.6 km/s and must be used as the spectral sampling interval when constructing the Gaussian smoothing kernel; 5.2 km/s is the effective science resolution, not the channel spacing;
2. the line-of-sight H I column density must be multiplied by `cos(i)` for the face-on/inclination-corrected surface-density profile.

The reconstructed profile is **QC only** until it agrees with the independent published UGC4483 profile parameters (`Sigma_0 = 10.5 Msun pc^-2`, Gaussian scale `s = 0.580 kpc`) and the mask provenance is judged reproducible enough for promotion.

NGC4068 remains unresolved by the direct-cube route because the public cube does not itself contain a uniquely recoverable publication mask. No arbitrary threshold may be introduced.

## 2. Verheijen & Sancisi (2001) arXiv atlas reroute

The original A&A PostScript endpoint returned HTTP 403 to GitHub Actions. The audit was rerouted successfully through the public arXiv PDF and source archive for `astro-ph/0101404`.

### PDF/vector audit result

- arXiv PDF: 33 pages
- UGC06399 is present in the appendix atlas on PDF pages 32 and 33
- page 32 contains 22,038 vector drawing objects
- page 33 contains 12,877 vector drawing objects
- the radial H I profile panel is therefore genuine extractable vector content, not a raster-only figure

The PDF contains only the UGC06399 appendix atlas example, not the complete published atlas for all candidate galaxies. Text matching therefore cannot recover the remaining frozen Verheijen systems from the arXiv PDF alone.

### arXiv source-archive audit

The source archive contains:

- `UMaHImap.ps`
- `fig1.ps` through `fig8.ps`
- `figA01a.ps`
- `figA01b.ps`
- `paper.tex`

`figA01a.ps` and `figA01b.ps` are the identifiable UGC06399 GIPSY atlas pages. They preserve true PostScript/vector plotting commands and are a viable direct-vector recovery route for UGC06399.

The source archive does **not** contain the equivalent appendix atlas pages for the other roughly 25 frozen Verheijen candidates.

### Figure 8 test

`fig8.ps` was separately audited because the paper describes Figure 8 as radial H I surface-density distributions.

Result:

- vector curves and normalized axes are present;
- no NGC/UGC galaxy identifiers are embedded in the PostScript or extracted text;
- the curves therefore cannot be assigned uniquely to frozen galaxies.

Figure 8 is **not admissible** as a bulk numerical-profile recovery source.

## 3. Frozen decisions

1. Do not generate Lelli NGC4068 or UGC04483 confirmatory profiles from a newly selected cube threshold.
2. UGC04483 mask reconstruction may be used only as a QC reproduction until it passes the published-profile comparison and provenance gate.
3. The Verheijen arXiv vector route is valid for UGC06399.
4. Do not claim that arXiv exposes all 26 Verheijen candidate radial profiles; it does not.
5. Do not assign anonymous Figure-8 curves to galaxies.
6. The remaining Verheijen candidates require the full published atlas / public WHISP products / legacy public archive route.
7. `L_A` and `C_A` remain unopened until source-profile freeze.

## 4. Next admissible acquisition routes

- Extract and validate the identifiable UGC06399 vector radial H I profile from `figA01b.ps`.
- For the other Verheijen systems, pursue the complete public atlas or WHISP/WSRT legacy archive products rather than anonymous curve assignment.
- For NGC4068, seek the published total-H I map/mask product or an independently documented public radial profile before considering cube reconstruction.
- For UGC04483, use the published Fig. 6 profile as the independent validation target for the public-cube mask reproduction.
