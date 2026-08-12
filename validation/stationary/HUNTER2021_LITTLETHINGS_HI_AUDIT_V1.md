# Hunter et al. (2021) / LITTLE THINGS H I Sérsic audit v1

**Status:** PUBLIC ANALYTIC H I PROFILE MODELS VERIFIED — 4 FROZEN CALIBRATION GALAXIES  
**Date:** 2026-08-12  
**Scientific boundary:** source acquisition only. `L_A` and `\mathcal C_A` remain locked.

## Public source

Hunter et al. (2021), *The Astronomical Journal* 161, 71, DOI `10.3847/1538-3881/abd089`, arXiv `2012.00146`.

Machine-readable parameters are published through VizieR catalog `J/AJ/161/71`, with the H I Sérsic parameters in `table2` and source-name/distance metadata in `table1`.

## Exact profile convention

The primary arXiv source was inspected directly. The paper states that the H I surface-density profiles are measured from velocity-integrated robust-weighted maps and fit with the Sérsic form

`Sigma_HI(R) = Sigma0 * exp[-(R/R0)^(1/n)]`.

The source explicitly notes that `n=1` is a standard exponential disk. The tabulated H I parameters are the extrapolated central surface mass density, characteristic radius and profile curvature.

The equation is therefore no longer an inferred convention: it is **verified from the primary source**.

The exact helium convention for the Hunter tabulated H I surface-mass-density normalization is kept **explicitly pending** until separately verified. No helium factor or back-conversion is applied to these source parameters during acquisition.

## Frozen Paper I crossmatch

Four of the 40 Hunter/LITTLE THINGS galaxies map to the frozen 149-galaxy stationary master. All four are calibration galaxies:

| Frozen galaxy | Source name / alias | log10 Sigma0 | R0 (kpc) | n_HI | R50_HI (kpc) | Preferred Paper I source disposition |
|---|---|---:|---:|---:|---:|---|
| DDO154 | DDO 154 / NGC 4789A | 0.74 +/- 0.03 | 3.54 +/- 0.13 | 0.73 +/- 0.02 | 3.64 +/- 0.12 | **secondary analytic cross-check**; Leroy 2008 full numerical profile remains preferred |
| DDO168 | DDO 168 / UGC 08320 | 1.25 +/- 0.05 | 1.91 +/- 0.13 | 0.79 +/- 0.03 | 2.09 +/- 0.08 | **secondary analytic cross-check**; Iorio 2017 15-row raw-H I profile remains preferred |
| UGC05918 | DDO 87 / UGC 05918 | 0.33 +/- 0.02 | 6.26 +/- 0.14 | 0.35 +/- 0.01 | 4.65 +/- 0.12 | **new public analytic profile route** |
| UGC07559 | DDO 126 / UGC 07559 | 0.80 +/- 0.04 | 2.59 +/- 0.10 | 0.50 +/- 0.02 | 2.32 +/- 0.06 | **new public analytic profile route** |

Source distances in the Hunter catalog are retained separately from the frozen SPARC distances; no source-to-frozen coordinate scaling is performed here.

## Source hierarchy

The purpose of the Hunter block is to expand public reproducibility, not to replace a higher-information numerical source.

- **DDO154:** Leroy et al. (2008)/THINGS has a machine-readable 7-row radial profile and remains the preferred Paper I public source. Hunter is retained as an independent analytic profile description.
- **DDO168:** Iorio et al. (2017) has a public 15-row raw-H I radial profile and remains the preferred Paper I public source. Hunter is retained as an independent analytic profile description.
- **UGC05918 / DDO87:** Hunter provides a verified analytic H I profile model and becomes the current preferred public source route.
- **UGC07559 / DDO126:** Hunter provides a verified analytic H I profile model and becomes the current preferred public source route.

This hierarchy prevents lower-information analytic fits from overwriting already recovered numerical profiles while still allowing the analytic models to serve as QC/cross-source checks.

## Canonical machine-readable artifact

`data/stationary/source_reconstruction/hunter2021_littlethings_hi_sersic_parameters_v1.csv`

Reproducible builder:

`scripts/stationary/ingest_hunter2021_littlethings_hi_sersic.py`

Workflow:

`.github/workflows/ingest_hunter2021_littlethings_hi_sersic.yml`

## Transformations deliberately not performed

No:

- helium correction or back-conversion;
- source-to-frozen distance rescaling;
- inclination-amplitude correction;
- common-grid interpolation;
- extrapolation/taper;
- persistence fitting;
- blind-set evaluation.

## Database disposition

This source block adds **two new preferred public analytic-profile galaxies** to the stationary acquisition layer:

- UGC05918 — calibration
- UGC07559 — calibration

DDO154 and DDO168 remain recovered through their higher-information Leroy and Iorio numerical sources, respectively, with Hunter retained as an independent analytic source check.
