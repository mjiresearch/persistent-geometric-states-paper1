# Stil 1999 / Stil & Israel 2002 — DDO064 radial H I profile QC v1

**Status:** ORIGINAL H I LINEAGE CONFIRMED; PUBLIC REPUBLICATION HAS MAPS BUT NO EXACT RADIAL `Sigma_HI(R)` PRODUCT  
**Date:** 2026-08-12  
**Scientific boundary:** acquisition/provenance only. `L_A` and `\mathcal C_A` remain locked. No blind-outcome inspection and no raster/map digitization.

## Provenance chain

`Lelli/SPARC DDO064 -> dB02 -> Table 1 source code (6) -> Stil 1999 Leiden PhD thesis -> Stil & Israel 2002 Paper I`

The dB02 source states that its gas component uses H I surface densities from the references in Table 1. For DDO64/U5272 the Table 1 code is `(6)`, identified as J. Stil's 1999 Leiden PhD thesis. The thesis H I sample was subsequently published as:

J. M. Stil & F. P. Israel (2002), **“Neutral hydrogen in dwarf galaxies I. The spatial distribution of HI,”** A&A 389, 29–41, arXiv `astro-ph/0203128`.

## Public thesis route

A bounded search for a public Leiden institutional/handle copy of the 1999 Stil thesis did not produce a retrievable thesis payload in this pass. Do not loop that search absent a new archive mechanism.

## 2002 public source-package audit

The exact arXiv source package was recovered and audited in:

`validation/stationary/stil2002_ddo64_hi_profile_route_v1.json`

Key results:

- DDO64 is explicitly present in the source package.
- There are **no machine-readable `.dat/.tbl/.tab/.csv/.fits` H I profile assets**.
- There is **no target numerical radial-profile candidate**.
- There is **no target-specific native-text evidence of a radial H I `Sigma_HI(R)` product** in Paper I.
- DDO64 is included through `DDO64.NHI.ps` in the paper's **H I column-density map** figure.
- A 2-D column-density map is not substituted for a source-native radial surface-density profile under the Paper I acquisition rule.

The package also contains `HIprof1.ps`/`HIprof2.ps`, but the paper identifies these as **integrated/global H I line profiles**, not radial H I surface-density profiles; they are not promoted as `Sigma_HI(R)`.

## Disposition

- original 21-cm observing lineage: **CONFIRMED**
- public 2002 republication: **RECOVERED**
- 2-D H I column-density map for DDO64: **RECOVERED**
- native radial `Sigma_HI(R)` table: **ABSENT**
- fully specified analytic radial profile: **ABSENT**
- exact radial-profile vector geometry: **NOT PRESENT AS A RADIAL PRODUCT**
- raster/map-to-profile reconstruction: **NOT PERFORMED**
- Paper I numerical ingestion from this route: **NONE**

## Reopen rule

Reopen DDO064 through the Stil lineage only if a genuinely new public mechanism appears: the original thesis with source-native radial values, a machine-readable radial profile, an exact radial-profile republication, or an original calibrated map/cube after a separately frozen reconstruction protocol is adopted.

The `dB02` Lelli family remains correctly redirected to its original H I source branches and the acquisition queue may advance.
