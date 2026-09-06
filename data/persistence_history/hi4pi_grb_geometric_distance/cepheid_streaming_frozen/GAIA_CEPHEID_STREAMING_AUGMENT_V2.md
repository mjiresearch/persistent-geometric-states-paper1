# Gaia-Cepheid streaming augmentation V2 — frozen protocol

Status: **FROZEN BEFORE H I COMPARISON**

Purpose: attempt to recover an arm-conditioned in-plane streaming prediction at the support-qualified GRB locations, especially the OSC point, without changing the frozen V3 geometry/support rules and without reading any GRB H I outcome.

## Immutable geometry/model rules

- Keep the V3 Galactic constants and sign convention unchanged.
- Keep the frozen Outer-arm locus unchanged.
- Keep the frozen OSC locus anchored by G007.47+00.05 unchanged.
- Keep the arm-phase bandwidth grid unchanged: h = {1,2,3,4,5,7,10} kpc.
- Keep the target support rule unchanged: N_eff >= 3 independently for U and V, nearest phase tracer <= 2h, and target within the frozen arm perpendicular-width limit.
- Keep GRB 031203 excluded because it failed the frozen arm-geometry support audit.
- No peculiar-velocity clipping or tuning to the GRB outcomes is allowed.

## Distance and astrometry

- Use the same 3306-star public classical-Cepheid catalog and period-Wesenheit distances used in the frozen geometry audit.
- Use Gaia DR3 source_id-matched proper motions and RUWE.
- Require RUWE < 1.4, fractional distance uncertainty <= 20%, R >= 4 kpc, and propagated U/V uncertainty <= 20 km/s.

## Radial-velocity hierarchy

1. Primary: Gaia DR3 `gaiadr3.vari_cepheid.average_rv`, which is the Cepheid-specific radial-velocity model output. Require `num_clean_epochs_rv >= 8` and `average_rv_error <= 5 km/s`.
2. Fallback only when the Gaia Cepheid-specific RV above is unavailable or fails those RV-quality cuts: VELOCE DR1 systemic velocity `vgamma`, matched by Gaia DR3 source_id through VELOCE table A.1. Require VELOCE `Binflag = F` and `NRV >= 8`.
3. VELOCE fallback RV uncertainty is fixed at 1.0 km/s, conservatively covering the reported ~0.65 km/s Gaia–VELOCE systemic zero-point difference.
4. The generic Gaia `gaia_source.radial_velocity` is not used in V2.

## Prediction

- Transform each eligible 6D Cepheid into Galactocentric peculiar U,V using the same Reid+2019 A5 constants as V3.
- Fit no H I information.
- For each arm, choose the bandwidth with minimum leave-one-out standardized U+V prediction error among bandwidths that satisfy the frozen support rule at all support-qualified targets of that arm.
- Bootstrap the final LOS in-plane streaming prediction with 2000 resamples.

## Outcome firewall

The V2 builder is forbidden from reading any H I spectrum, H I velocity, H I residual, V1/V2/V3 GRB comparison result, or Persistence prediction. Only Cepheid positions/distances, Gaia astrometry/Cepheid-specific RVs, VELOCE systemic RV information, frozen target geometry, and frozen arm geometry may be used.
