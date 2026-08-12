# Be91 original-source radial H I profile QC — v1

Status: **complete / no exact public numerical profile promoted**

Scope: Lelli/SPARC `Be91` frozen galaxies only. This audit follows the frozen chain

`Lelli/SPARC galaxy -> Be91 -> Be91 original 21-cm source -> public recoverability -> ingest or defer`.

`L_A` and `C_A` are not touched. No blind outcomes are inspected. No raster profile is digitized.

## Canonical Be91 source map

The controlling source map is `data/stationary/source_reconstruction/be91_original_hi_source_map_v2.csv`, built from Be91 Table 1 reference codes plus explicit source prose:

- DDO170 -> Lake, Schommer & van Gorkom (1990)
- NGC2903 -> Wevers, van der Kruit & Allen (1986)
- NGC3109 -> Jobin & Carignan (1990)
- NGC6503 -> Wevers, van der Kruit & Allen (1986)
- UGC02259 -> Carignan, Sancisi & van Albada (1988)

The earlier prose-only v1 map is superseded; its summary documents the correction.

## Wevers, van der Kruit & Allen (1986)

Artifacts:

- `validation/stationary/wevers1986_hi_profile_audit_v1.json`
- `validation/stationary/wevers1986_pdf_geometry_v1.json`

The full public ADS atlas was recovered (157 PDF pages). Every page contains image content and **zero PDF drawing objects**; the maximum native drawing-item count is zero. The tiny text layer does not expose target radial H I tables. Therefore NGC2903 and NGC6503 have no exact native-vector/table route in this public copy. No raster digitization was performed.

## Lake, Schommer & van Gorkom (1990) — DDO170

Artifact: `validation/stationary/be91_remaining_original_hi_papers_audit_v1.json`.

The public ADS paper is recoverable with searchable text, but the H I radial surface-density distribution is referenced as a **figure** (the mass-model discussion states that the disk surface density is set by the H I observations and points to Fig. 5 / the H I section). The searchable tables encountered in the paper are observation/model/rotation products rather than a radius-versus-Sigma_HI table. The PDF page geometry contains images and no native vector drawings. No exact radial H I table was identified; no raster digitization was performed.

## Jobin & Carignan (1990) — NGC3109

Artifact: `validation/stationary/be91_remaining_original_hi_papers_audit_v1.json`.

The paper states explicitly that elliptical averaging of the total H I map produced the H I radial profile of **Fig. 6**. Its table inventory does not supply that profile numerically:

- Table I: VLA observing parameters
- Table II: optical ellipse fits
- Table III: optical parameters
- Table IV: optical luminosity profile
- Table V: comparison of total H I properties / H I mass from instruments
- Table VI: adopted rotation curve
- Table VII: mass-model properties

Thus the exact Sigma_HI(r) data are figure-only in the public paper. The PDF has image content and no native vector drawings. No raster digitization was performed.

## Carignan, Sancisi & van Albada (1988) — UGC02259

Artifact: `validation/stationary/be91_remaining_original_hi_papers_audit_v1.json`.

The paper states explicitly that the radial H I distribution is **Fig. 5**, obtained by averaging the H I surface densities in circular rings in the plane of the galaxy. The mass-model section again says that the H I component uses the surface densities shown in Fig. 5. The searchable tables are observing/orientation/rotation/mass-model products rather than a numerical Sigma_HI(r) table; in particular, Table IV is the rotation curve and Table VI is component velocities. The PDF has image content and no native vector drawings. No raster digitization was performed.

## CDS/VizieR check

A bounded CDS/VizieR search by the three exact AJ bibcodes and target/profile terms did not identify a matching machine-readable radial H I surface-density catalogue for these original papers. An unrelated modern catalogue result was rejected.

## Disposition

`Be91` should move from `redirected_to_original_sources` to `defer_until_new_mechanism` because all five mapped original-source branches have now passed the direct public recoverability gate without yielding an exact radius-versus-Sigma_HI numerical table or native vector profile.

Reopen only for a genuinely new mechanism, such as:

1. a machine-readable source table,
2. a public calibrated H I map/cube from which the source profile can be reproducibly re-derived under a separately frozen map-to-profile protocol, or
3. an exact analytic/numerical republication of the radial H I profile.

This is an acquisition boundary, not a scientific failure and not permission to digitize the published raster figures.
