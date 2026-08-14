# Frozen protocol: SDSS DR20 young–old current field v1

Status: **frozen before real-outcome evaluation** on 2026-08-14. Protocol ID: `sdss-dr20-independent-current-field-v1`.

## Question and independence boundary

This block asks whether age-separated stellar tracers occupy measurably different present-day three-dimensional current fields after exact matching in narrow Galactic volume elements. It uses the SDSS DR20 gyrochronology dwarf VAC for **both** age cohorts and exact Gaia DR3 `source_id` phase space. The DR20 BOSS OCCAM cluster catalog is an orthogonal control for ordinary age-dependent orbital displacement.

The block cannot read stationary-calibration products, SPARC data or fits, locked `L_A`/`C_A` values, earlier Milky Way residual maps, or private source-history data. The public OB-star kinematics VAC is restricted to a coverage/coordinate audit and cannot enter the primary statistic. This keeps the test independent of the stationary branch and of any result from Dr. Lelli’s requested profile material.

## Primary stellar-field sample

Both cohorts come from `gyro_age_dwarf-1.0.0.fits`:

- young: upper one-sigma age bound at or below 1.0 Gyr;
- old: lower one-sigma age bound at or above 4.0 Gyr;
- finite non-negative lower and upper age errors are required;
- intermediate-age objects are excluded rather than reassigned.

The gyro rows are joined to `gaiadr3.gaia_source` by exact integer `source_id`. Required Gaia quantities are sky position, positive parallax, proper motion, and radial velocity. The frozen quality cuts are parallax-over-error ≥ 10, RUWE ≤ 1.4, no duplicated source, and complete six-dimensional phase space. Distance is the inverse-parallax estimate; its use is limited to this high-S/N local sample.

The Galactocentric transform is fixed at `R0=8.2 kpc`, `z_sun=0.025 kpc`, and solar Cartesian velocity `[11.0, 232.24, 7.25] km/s`. Cylindrical velocity is reported as `(v_R,v_phi,v_z)`, with the sign of `v_phi` standardized so the median prograde disk is positive.

## Frozen 3D matching and current statistic

Galactocentric `(X,Y,Z)` is assigned to a zero-anchored Cartesian grid of `0.25 × 0.25 × 0.10 kpc`. A voxel is supported only with at least 10 young and 10 old stars; the block is powered only with at least 12 supported voxels. These dimensions and thresholds were selected from cohort/coverage counts alone, before inspecting a real velocity or current contrast.

For cohort `c` in a voxel of volume `V`, the audit products include the raw catalog-tracer density and current,

\[
\rho_c=n_c/V, \qquad \mathbf J_c=\rho_c\,\bar{\mathbf v}_c.
\]

Because catalog counts are shaped by the selection function and are not a calibrated mass density, inference uses a symmetric matched density—the harmonic mean of the two cohort counts divided by `V`—for both cohort currents. The old-minus-young mean-current contrast then has the same local density factor on each side.

The primary statistic is the equal-voxel mean of the squared Mahalanobis distance between the old and young mean three-velocity (equivalently, matched-current) vectors. Each voxel covariance is the sum of the two cohort mean-covariance matrices with a frozen `10^-6` trace-scaled ridge. The null permutes young/old labels **inside each supported voxel**, preserving its observed cohort counts. There are 2,000 permutations with seed `20260814`; the one-sided p-value is `(1 + # permuted T >= observed T)/2001`. The frozen field threshold is `p ≤ 0.01`.

Signed component contrasts and raw currents are secondary descriptive outputs. They cannot replace the primary omnibus statistic.

## Open-cluster control

The control uses the DR20 BOSS OCCAM cluster VAC, never to tune the field analysis. Cluster age is `10^Cav_logAge/10^9` Gyr, present radius is `R_GC_Cav`, and guiding radius is `R_Guide`. Rows require finite values and at least three full members when that count is available.

The control statistic is the Spearman correlation between age and `|R_Guide-R_now|`. Its positive-tail p-value comes from 2,000 global age permutations with seed `20260815`. It needs at least 20 clusters and uses `p ≤ 0.05` only as a confound flag: a positive result shows that ordinary age-dependent orbital dynamics remain capable of producing a young–old contrast.

## Interpretation lock

- A non-significant or underpowered field test supplies no support from this block.
- A significant field statistic plus a positive cluster control remains conventionally confounded and is **not** promoted as persistence evidence.
- A significant field statistic with a null cluster control is persistence-compatible, but still is not a direct acceleration measurement and cannot establish the framework alone.
- No result from this block may be called a detection of gravitational persistence.

The machine-readable authority is [`data/persistence_history/dr20_independent/protocol_v1.json`](../data/persistence_history/dr20_independent/protocol_v1.json). Any schema-only adapter required by an upstream file must be recorded without changing cuts, statistics, or interpretation rules.
