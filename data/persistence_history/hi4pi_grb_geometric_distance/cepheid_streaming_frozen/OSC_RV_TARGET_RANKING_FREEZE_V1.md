# OSC systemic-RV target ranking — frozen protocol V1

Purpose: identify which geometry-qualified classical Cepheids would most efficiently raise the frozen V3 Outer-Scutum–Centaurus (OSC) streaming-field support above the predeclared threshold, without using any GRB H I outcome or Persistence prediction.

## Frozen inputs

- Gaia DR3 classical-Cepheid position/distance catalog already cached in this directory.
- Gaia DR3 astrometry already cached in `gaia_dr3_6d_join.csv`.
- Gaia DR3 Cepheid-specific RV join already cached in `gaia_dr3_cepheid_specific_rv_join_v2.csv`.
- Frozen V3 multi-catalog eligible 6D sample in `outputs_v3/eligible_6d_cepheids_v3.csv`.
- Frozen OSC logarithmic-arm geometry, A5 Galactic constants, intrinsic velocity dispersion, and candidate bandwidth grid inherited unchanged from `build_gaia_cepheid_streaming_v1.py` / V3.

## Candidate definition

A candidate must:

1. pass every V3 non-RV quality cut: finite Gaia proper motions/errors and RUWE, RUWE < 1.4, fractional Cepheid distance error <= 20%, R >= 4 kpc;
2. lie within the frozen OSC geometric membership window |d_perp| <= 2 sigma_arm;
3. not already appear in the frozen V3 eligible 6D sample;
4. fail V3 only because no acceptable systemic/radial velocity is available under the frozen hierarchy.

No H I spectrum, H I velocity, H I residual, conventional GRB outcome, or Persistence prediction may be read.

## Hypothetical RV measurement

Primary assumed systemic-RV uncertainty: **2.0 km/s**.
Sensitivity checks: **1.0 and 5.0 km/s**.

For each candidate, propagate its existing distance/proper-motion uncertainties plus the hypothetical RV uncertainty into eU and eV using the same Galactocentric transformation as V3. The central hypothetical RV may be set to 0 km/s because the covariance propagation is linear to excellent approximation and the support statistic depends on uncertainty/geometry weights, not the unknown velocity value.

Keep the frozen intrinsic dispersion sigma_int = 7 km/s and bandwidth grid h = {1,2,3,4,5,7,10} kpc.

## Ranking statistic

At each h, compute the existing frozen V3 OSC weights in U and V and the new effective sample sizes after adding:

- each missing-RV candidate singly;
- every pair of missing-RV candidates.

A support-qualified augmentation requires both N_eff,U >= 3 and N_eff,V >= 3, with the existing V3 nearest-phase condition unchanged.

Primary ranking: maximum over the frozen bandwidth grid of min(N_eff,U, N_eff,V) after augmentation. Report the smallest bandwidth that reaches the threshold, if any. Ties are resolved by smaller along-arm phase distance to the GRB target and then Gaia source_id.

This exercise ranks observing/data-recovery leverage only. It does **not** generate a streaming velocity prediction because the candidate systemic velocities are unknown.
