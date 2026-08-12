# Be91 original H I source-profile disposition v1

**Status:** ORIGINAL OBSERVING SOURCES AUDITED; NO EXACT NUMERICAL RADIAL H I PROFILE ROUTE CURRENTLY RECOVERABLE  
**Date:** 2026-08-12  
**SPARC/Lelli reference:** `Be91`  
**Scientific boundary:** acquisition/provenance only. `L_A` and `\mathcal C_A` remain locked. No blind outcomes inspected.

## Canonical Lelli-to-original-source map

Begeman, Broeils & Sanders (1991) is a downstream rotation-curve/mass-model analysis. Its five frozen Paper I targets are therefore followed to the original 21-cm observing sources identified by the paper's Table 1 reference codes and explicit prose:

- `DDO170` -> Lake, Schommer & van Gorkom (1990), AJ 99, 547.
- `NGC2903` -> Wevers, van der Kruit & Allen (1986), A&AS 66, 505-662.
- `NGC3109` -> Jobin & Carignan (1990), AJ 100, 648.
- `NGC6503` -> Wevers, van der Kruit & Allen (1986), A&AS 66, 505-662.
- `UGC02259` -> Carignan, Sancisi & van Albada (1988), AJ 95, 37.

Canonical map: `data/stationary/source_reconstruction/be91_original_hi_source_map_v2.csv`.

## Public recoverability result

### NGC2903 / NGC6503 — Wevers et al. 1986

The public ADS article is a 157-page image-scan PDF. The structural audit finds zero vector drawings on all pages and no native target/profile table route. It is not promoted by raster digitization.

Artifacts:
- `validation/stationary/wevers1986_hi_profile_audit_v1.json`
- `validation/stationary/wevers1986_pdf_geometry_audit_v1.json`

### DDO170 — Lake et al. 1990

The paper publishes the radial H I distribution in Figure 5 and states that an analytical Gaussian fit is used, with scale parameter `a = 95 arcsec`. The source-native text does not provide a complete numerical radial `Sigma_HI(R)` table or a complete independently normalized analytic profile outside the raster figure. The numerical amplitude would therefore have to be read from the plot or reconstructed from additional assumptions. Neither is admitted at acquisition time.

### NGC3109 — Jobin & Carignan 1990

The paper explicitly states that elliptical averaging of the zeroth-moment map produced the radial H I profile shown in Figure 6; the figure is inclination-corrected and expressed in the galaxy plane. The native numerical tables in the public paper cover observing/global H I properties, optical photometry, and the rotation curve; no source-native radial H I surface-density table is exposed. Figure coordinates are raster/image content and are not digitized.

### UGC02259 — Carignan, Sancisi & van Albada 1988

The paper explicitly publishes the H I radial distribution in Figure 5, obtained by averaging surface densities in circular rings in the plane of the galaxy. Table IV is the rotation curve, not a radial H I surface-density table. The H I surface-density values used in the mass model remain figure-only in the public paper and are not raster-digitized.

Combined audit: `validation/stationary/be91_remaining_original_hi_papers_audit_v1.json`.

## Disposition

- Original observing-paper identity: **COMPLETE for all five targets**.
- Public direct H I profile publication: **CONFIRMED** for the original papers where applicable.
- Machine-readable/native radial `Sigma_HI(R)` values: **NOT RECOVERED**.
- Exact vector profile geometry: **NOT RECOVERED**.
- Fully specified independently normalized analytic H I profile: **NOT RECOVERED**.
- Numerical ingest from Be91 source-level branch: **NONE**.
- Raster digitization: **NOT PERFORMED**.

## Reopen rule

Reopen a target only if a genuinely new public mechanism appears: a machine-readable source table, original calibrated map/cube with a separately frozen reconstruction protocol, exact vector republication, or a fully specified analytic H I profile. Do not repeat the current ADS scan/figure route.

The Lelli-directed acquisition queue may now advance beyond `Be91` while preserving this source-level provenance boundary.
