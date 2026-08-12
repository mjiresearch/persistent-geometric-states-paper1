# van der Hulst et al. 1993 (VH93) — public radial H I profile audit v1

**Status:** DIRECT RADIAL H I PROFILES CONFIRMED; CURRENT PUBLIC PROFILE PRODUCT IS FIGURE/SCAN ONLY; NO EXACT NUMERICAL INGEST  
**Date:** 2026-08-12  
**SPARC/Lelli reference:** `VH93`  
**Scientific boundary:** acquisition/provenance only. `L_A` and `\mathcal C_A` remain locked. No blind-outcome inspection and no raster digitization.

## Source

J. M. van der Hulst et al. (1993), **“Star Formation Thresholds in Low Surface Brightness Galaxies,”** AJ 106, 548–559, bibcode `1993AJ....106..548V`.

Public repository copy:

`https://drum.lib.umd.edu/bitstreams/d1a54927-5c0d-4398-adcb-e7c8be1323ad/download`

The paper reports VLA H I imaging of eight LSB galaxies.

## Frozen/source-trail overlap

The source is relevant to the direct Lelli `VH93` branch and to the original-source decomposition of `dB01`:

- `UGC00128` — direct `VH93` Lelli target;
- `UGC05005` — direct `VH93` Lelli target;
- `UGC06614` — direct `VH93` Lelli target and dB01 original-source target;
- `UGC05750` — dB01 original-source target.

## Radial H I product

The paper explicitly states that the radial H I surface-density distributions are shown in **Figure 2**. Figure 2 contains the radial H I points (crosses, right-hand H I surface-density axis) for the resolved galaxies, including UGC 128, UGC 5005, UGC 5750 and UGC 6614.

For UGC 6614 the text additionally states that the radial H I surface-density distribution was derived from the original high-resolution 24-arcsec map.

The paper states that no radial distribution was calculated for UGC 5209 because it is essentially unresolved; that object is not promoted by inference.

## Table boundary

Table 2 contains physical-summary quantities such as:

- H I flux integral;
- peak H I surface density;
- H I diameter at 1 M_sun pc^-2;
- total H I mass;
- peak radial average;
- orientation/global optical quantities.

It does **not** provide the radius-by-radius H I surface-density arrays shown in Figure 2.

## Public recoverability decision

The current DRUM PDF is a scanned journal reproduction. The radial H I curves/points are preserved visually in the Figure 2 page rather than as a machine-readable radial table. The current public route therefore does not provide exact source-native `(R, Sigma_HI)` coordinates that meet the Paper I acquisition rule.

No values are read from the raster plot, and no curve digitization is performed.

A structural PDF workflow (`audit_vh93_public_profile_route.py`) has also been added to record page drawing/image structure when the GitHub runner completes; this is supplemental QC and does not change the present no-digitization boundary.

## Disposition

- direct H I observing source: **CONFIRMED**
- radial H I surface-density profiles published: **CONFIRMED**
- relevant target profiles visible in Fig. 2: **CONFIRMED**
- native numerical radial table: **NOT FOUND**
- exact source-vector profile route from current public product: **NOT ESTABLISHED**
- raster digitization: **NOT PERFORMED**
- Paper I numerical ingestion from this route: **NONE**

## Reopen rule

Reopen `VH93` only if a genuinely new mechanism appears: a machine-readable radial table, original calibrated map/cube with a separately frozen reconstruction protocol, or an exact vector/numerical republication of the Figure 2 profiles.
