# Milky Way Stage 8 — orbit-superposition source reconstruction and potential controls

Date: 2026-08-08

## Purpose

Stage 8 introduces an independent reimplementation of the Khoperskov et al. APOGEE orbit-superposition reconstruction as a new Milky Way source-reconstruction layer for the persistence program.

This stage is intentionally separated from the earlier Stage 6 direct-pulsar-acceleration branch and Stage 7 global source-history summaries. It is not treated as evidence for persistence by itself.

## Why this stage is needed

The frozen Stage 6 out-of-sample test rejected the simple local `R_now - R_birth` proxy as a demonstrated universal history-force variable. Stage 7 then showed that global `Mstar(t) + Reff(t)` summaries are insufficient to reconstruct a unique physical spatial star-formation/current history.

The orbit-superposition package adds substantially richer present-day information: selection-corrected stellar weights, full 6D phase-space initial conditions, orbit families in controlled potentials, ages, chemistry, and approximate birth radii.

## Source package provenance

The package was supplied to this project as `mwsuperpos.tar.gz` and reviewed as a complete codebase before modification.

Original archive SHA-256:

`a664c481f4fcb1e503186ebd4a27d438ffd9663d1aa7eb3b10014c175b96a8bb`

Supplied `Portail17.ini` SHA-256:

`280cf91f942fd04787483403b6846f261bd34b038f8caff5651f9b16a5dab036`

The repository stores the working source code and provenance record rather than the original archive binary.

## Changes made for the persistence analysis

### 1. Weight normalization correction

The original implementation solved each of five subsamples against the full target density and only renormalized the reconstructed map afterward. That can leave saved orbit weights over-normalized by approximately the number of subsamples.

The corrected implementation:

- fits each subset to `rho / n_sub` by default;
- explicitly mass-normalizes every completed realization inside the fitted volume;
- mass-normalizes the mean saved weight vector;
- disables silent post-hoc map renormalization by default.

This ensures that `weights.npz` contains physically normalized weights rather than relying on a plotting-stage scale factor.

### 2. Controlled potential comparison

The working package exposes four force-model cases:

- Portail17 + halo;
- Portail17 baryons only;
- Hunter24 + halo;
- Hunter24 baryons only.

The primary comparison holds the reconstruction target density fixed while changing the force field. This avoids conflating a change in potential with a simultaneous change in the density being fitted.

### 3. Persistence replacement target

For each potential family, the comparison records

`delta_a_halo(R) = a_full(R) - a_baryons(R)`.

This quantity is interpreted only as the radial acceleration contribution that a successful persistence model would need to replace if the conventional dark halo were removed. It is not itself evidence for persistence.

## Guardrail: orbit library is not literal Galactic history

The 5-Gyr, 500-point trajectories are integrations in a fixed rotating potential. They are phase-space orbit-library samples under an assumed present-day force model, not measured historical trajectories of individual baryons.

Therefore they must not be inserted directly into a hereditary kernel as if they were the true past 5 Gyr of Galactic matter/current history.

The full-halo trajectories are additionally dark-matter-conditioned by construction. Demonstrating that a hereditary operator can reproduce a feature of those same trajectories would be circular unless the halo dependence is explicitly controlled.

## Primary Stage 8 diagnostics

The first real-data comparison should report:

1. reconstruction residuals for all four potential cases;
2. mass ratios before any optional visualization scaling;
3. Portail-vs-Hunter normalized weight correlation and rank correlation;
4. full-vs-baryons-only weight changes within each potential family;
5. orbit-library displacement statistics under force-model changes;
6. radial `delta_a_halo(R)` agreement between Portail and Hunter;
7. sensitivity to bar pattern speed, solar-motion assumptions, and absolute-vs-relative row weighting.

## Interpretation rule

- If Portail and Hunter yield similar normalized stellar reconstructions and similar `delta_a_halo(R)`, the missing-acceleration target is comparatively robust to this potential choice.
- If baryons-only orbit libraries reconstruct the stellar target nearly as well as the halo-conditioned libraries, the density reconstruction itself is weakly diagnostic of a halo and should not be used as a dark-matter detection.
- If baryons-only reconstructions degrade materially while both halo models perform well, conventional halo dynamics are strongly encoded in the orbital support.
- None of these outcomes alone establishes persistence. A persistence claim requires an independently specified hereditary source operator and out-of-sample force/acceleration prediction.

## Repository locations

Working code:

`scripts/milky_way/mwsuperpos/`

Stage 8 outputs when generated:

`data/persistence_history/milky_way_orbit_superposition/`

This document records the scientific interpretation boundary for the stage.
