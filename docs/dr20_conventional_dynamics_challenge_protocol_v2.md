# Frozen protocol: SDSS DR20 conventional-dynamics challenge v2

Status: **frozen before any v2 outcome calculation** on 2026-08-21. Protocol ID: `sdss-dr20-conventional-dynamics-challenge-v2`.

## Purpose and evidential posture

Version 1 produced a significant matched young–old three-dimensional velocity/current contrast, but the signed difference was overwhelmingly azimuthal: old minus young `(v_R,v_phi,v_z) = (0.457,-20.527,0.321) km/s`. This is exactly the direction in which ordinary asymmetric drift and age-dependent disk heating are expected to act. The v1 open-cluster control (`p=0.065967`) did not trigger its preregistered confound flag, but it did not test or exclude asymmetric drift, disk heating, chemistry, vertical structure, or survey selection.

The v2 question is therefore deliberately adversarial: **can conventional Galactic dynamics and population/selection structure account for the v1 young–old contrast without invoking persistence?** No v2 threshold or decision rule may be changed after any v2 outcome statistic is inspected.

The v1 result remains immutable and is not recomputed or overwritten. All v2 products are additive.

## Fixed inputs and frame

The primary challenge uses the same v1 DR20 gyrochronology dwarf VAC and exact Gaia DR3 `source_id` matches. The v1 age cuts, astrometric quality cuts, Galactocentric frame, and base spatial grid remain unchanged unless a stress test below explicitly defines an additional restriction.

For chemistry, the preferred DR20 source is BOSS-CLAM stellar labels `[Fe/H]` and `[alpha/M]` joined by a unique stellar identifier/source mapping. Only rows with finite, unflagged/recommended-quality values may enter chemistry-conditioned analyses. If one of the two chemistry labels is unavailable for a star, that star is excluded from the chemistry-complete subset; missing chemistry is never imputed from age or velocity.

Gaia DR3 photometry (`phot_g_mean_mag`, `bp_rp`) and astrometric-quality quantities may be used only for the frozen selection-balance tests below.

## Test A — measured asymmetric-drift expectation

### A1. Measured kinematic moments

Inside each supported v1 voxel and each cohort, compute the mean cylindrical velocities and unbiased sample dispersions `sigma_R`, `sigma_phi`, and `sigma_z`. The primary drift variable is `sigma_R^2`. Uncertainties are obtained by a fixed 2,000-resample within-voxel nonparametric bootstrap with seed `20260821`.

### A2. Axisymmetric Jeans asymmetric-drift prediction

Use the radial Jeans relation

`V_c^2 - mean(v_phi)^2 = sigma_phi^2 - sigma_R^2 * [1 + d ln(nu sigma_R^2)/d ln R] - (R/nu) d(nu <v_R v_z>)/dz`.

The baseline circular speed is fixed at `V_c = 232.24 km/s`, matching the azimuthal frame constant already used by v1. `nu` is a **tracer** density, not a stellar mass density.

To reduce selection sensitivity in the derivative, estimate `d ln(nu sigma_R^2)/d ln R` from the pooled young+old sample in cylindrical radial bins of width `0.5 kpc`, separately within `|z|<0.25 kpc` and `0.25<=|z|<0.5 kpc` when each fit has at least four populated radial bins. Fit a straight line to `ln(nu sigma_R^2)` versus `ln R` with equal radial-bin weight. The derivative is evaluated from that slope and then held common to young and old stars at the same `(R,|z|)` stratum so that age-dependent survey density gradients cannot by themselves manufacture the predicted age contrast.

The baseline tilt term is set to zero. A mandatory sensitivity calculation includes the directly measured covariance `<v_R v_z>` and a centered finite-difference vertical derivative wherever both adjacent `0.1 kpc` vertical layers are populated. Baseline and tilt-inclusive results must both be reported; neither may be chosen post hoc.

For each supported voxel, solve the Jeans equation for the expected cohort `mean(v_phi)` using the measured dispersions and common local gradient, then form the predicted old-minus-young `Delta v_phi_AD`. The primary asymmetric-drift estimand is the equal-voxel mean of `Delta v_phi_observed - Delta v_phi_AD`.

### A3. Drift decision rule

Conventional asymmetric drift is considered quantitatively sufficient for the v1 azimuthal contrast if **both** conditions hold:

1. the observed equal-voxel `Delta v_phi` lies inside the two-sided 95% bootstrap prediction interval of the Jeans-predicted `Delta v_phi_AD`; and
2. after subtracting the voxel-level Jeans prediction, a within-voxel age-label permutation test of the residual azimuthal contrast has `p > 0.01`.

If either condition fails, asymmetric drift alone is insufficient under this frozen implementation; that failure is not by itself evidence for persistence.

## Test B — chemistry, vertical height, and selection balance

### B1. Chemistry-complete matched subset

Construct a chemistry-complete subset requiring finite recommended-quality `[Fe/H]` and `[alpha/M]`. Within each original spatial voxel, perform coarsened exact matching using fixed bins:

- `[Fe/H]`: width `0.10 dex`;
- `[alpha/M]`: width `0.05 dex`;
- `|z|`: width `0.05 kpc`;
- Gaia `G`: width `0.50 mag`;
- Gaia `BP-RP`: width `0.20 mag`.

Bin origins are zero for all quantities except `[Fe/H]`, whose origin is `-3.0 dex`. A matched cell is retained only if it contains at least five young and five old stars. Each matched cell receives equal weight; within a cell, young and old are weighted to equal total weight.

No caliper/bin width may be widened after outcome inspection. If fewer than eight matched cells survive, this stress test is labeled `underpowered` rather than relaxed.

### B2. Vertical-height stress tests

Repeat the component contrasts and drift-corrected azimuthal contrast in two fixed slabs: `|z| < 0.20 kpc` and `0.20 <= |z| < 0.50 kpc`. Stars at `|z| >= 0.50 kpc` are excluded from this specific test. A slab requires at least eight supported matched cells/voxels; otherwise it is `underpowered`.

### B3. Selection-only balance

Independently of chemistry availability, coarsened-exact-match young and old stars inside each original voxel on `|z|`, Gaia `G`, Gaia `BP-RP`, parallax-over-error, and RUWE using fixed bin widths `0.05 kpc`, `0.50 mag`, `0.20 mag`, `10`, and `0.10`, respectively. Require at least five stars from each cohort per matched cell and eight matched cells overall.

The chemistry-complete and selection-only analyses are separate mandatory stress tests. A favorable result in one cannot replace failure or underpowering in the other.

## Test C — identify how much of the omnibus result is specifically v_phi

For every supported v1 voxel compute component-wise standardized squared mean differences

`Q_k = (Delta mean(v_k))^2 / Var[Delta mean(v_k)]`, for `k in {R,phi,z}`,

using the same covariance-of-the-mean estimates and ridge convention as v1. Define

`f_phi = sum(Q_phi) / sum(Q_R + Q_phi + Q_z)`

with sums over equally weighted supported voxels.

Mandatory statistics are:

- original 3-D Mahalanobis `T_3D`;
- one-dimensional `T_R`, `T_phi`, and `T_z` built from the corresponding `Q_k`;
- two-dimensional `T_Rz` using only `(v_R,v_z)` and their covariance;
- leave-phi-out `T_-phi = T_Rz`;
- `f_phi`.

All p-values use the same within-voxel label permutation scheme, 2,000 permutations, seed `20260822`, and `alpha=0.01`.

The v1 omnibus signal is classified `vphi_dominated` if `f_phi >= 0.80` **and** `p(T_Rz) > 0.01`. This classification is descriptive of the signal geometry and explicitly increases the weight assigned to conventional asymmetric-drift explanations.

After Test A, the same decomposition is repeated with `v_phi` replaced by the Jeans drift residual. The drift-corrected 3-D statistic is the main v2 residual statistic.

## Test D — replication in an independent stellar-age catalog

The replication catalog is fixed to **Gaia DR3 FLAME** ages from `gaiadr3.astrophysical_parameters`, using `age_flame`, `age_flame_lower`, and `age_flame_upper`. To make the replication star sample disjoint from v1, exclude every Gaia `source_id` appearing anywhere in the DR20 gyrochronology VAC before defining age cohorts.

Require finite FLAME age bounds and a highest-quality FLAME age flag (`flags_flame` first character `0`), plus the same Gaia six-dimensional phase-space and astrometric quality requirements as v1.

Replication cohorts use the same uncertainty-separated boundaries but directly on FLAME percentile bounds:

- young: `age_flame_upper <= 1.0 Gyr`;
- old: `age_flame_lower >= 4.0 Gyr`;
- all others excluded.

Use the same Galactocentric frame and base voxel dimensions as v1. A voxel requires at least ten stars per cohort; the replication requires at least twelve supported voxels. If those criteria fail, the replication is `underpowered`; thresholds are not relaxed.

The replication reports the same component decomposition and the same Jeans asymmetric-drift challenge. Permutation count is 2,000 with seed `20260823`; `alpha=0.01`.

Replication is considered successful only if the **drift-corrected** 3-D statistic rejects at `p<=0.01` and the direction of the equal-voxel old-minus-young residual vector agrees component-by-component with the v2 primary sample for every component whose absolute primary residual exceeds `2 km/s`. A raw, uncorrected FLAME young–old difference does not count as replication.

## Frozen interpretation matrix

1. **Asymmetric drift sufficient:** if Test A meets both sufficiency conditions, the original `~20.5 km/s` azimuthal difference is treated as conventionally explained unless a separate non-azimuthal and replicated residual survives.
2. **v_phi-dominated:** if `f_phi>=0.80` and `T_Rz` is null, the v1 omnibus rejection is not treated as independent support for persistence even if the raw 3-D p-value remains small.
3. **Chemistry/selection sensitivity:** if significance disappears after either adequately powered chemistry-complete or selection-only matching, the result is classified as population/selection-confounded.
4. **No independent replication:** failure or underpowering of the FLAME replication prevents promotion beyond `unresolved_after_conventional_challenge`.
5. **Survival criterion:** the strongest permitted v2 label is `persistence_compatible_after_conventional_challenge`, and only if (a) asymmetric drift is insufficient by Test A, (b) the drift-corrected 3-D residual has `p<=0.01`, (c) no adequately powered chemistry or selection stress test eliminates the residual, and (d) the disjoint FLAME replication succeeds.
6. **Prohibited claim:** no v2 outcome is a detection of gravitational persistence. Surviving these tests would establish only that this specific set of conventional explanations failed to account for a replicated age-conditioned kinematic residual.

## Execution lock

No v2 outcome calculation may begin until this protocol and its machine-readable authority are committed. Any implementation detail not specified here must be resolved from schema/coverage information without inspecting young–old outcome contrasts and must be documented in a schema-only adapter. Any scientifically material change creates a new protocol version rather than silently editing v2.

Machine-readable authority: `data/persistence_history/dr20_independent/protocol_v2_conventional_challenge.json`.
