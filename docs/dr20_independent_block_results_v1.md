# SDSS DR20 independent current-field block v1 — results

Status: **complete on `agent/dr20-young-old-current-field-v1`**. Protocol ID: `sdss-dr20-independent-current-field-v1`.

The protocol, thresholds, estimands, random seeds, and interpretation lock were frozen before real-outcome evaluation. This block is independent of the stationary/SPARC calibration, locked `L_A` and `C_A`, earlier Milky Way residual maps, and any material requested from Dr. Lelli.

## Field result

Exact Gaia DR3 matching and the frozen quality cuts retained 6,843 stars: 2,848 in the uncertainty-separated young cohort and 956 in the old cohort. Thirteen spatial voxels met the minimum of ten stars from each cohort, exceeding the preregistered power floor of twelve voxels.

The equal-voxel mean Mahalanobis current/velocity contrast was `T = 28.8914277`. In 2,000 within-voxel label permutations (seed `20260814`), the greater-or-equal p-value was `0.0004997501`, below the frozen `alpha = 0.01`. The field verdict is therefore `reject_within_voxel_exchangeability`.

The secondary signed old-minus-young velocity contrasts were dominated by the azimuthal component: equal-voxel means `(v_R, v_phi, v_z) = (0.457, -20.527, 0.321) km/s`. These component summaries are descriptive and do not replace the omnibus statistic.

## Open-cluster control

The frozen control retained 111 BOSS OCCAM clusters. Spearman correlation between cluster age and `|R_Guide - R_now|` was `rho = 0.1423854`. Its positive-tail p-value from 2,000 age permutations (seed `20260815`) was `0.0659670`, above the frozen `alpha = 0.05`; the positive conventional-dynamics confound flag was therefore not triggered.

## Locked interpretation

The preregistered classification is **`persistence_compatible_not_a_detection`**. The field result establishes an age-conditioned tracer-kinematic difference after the frozen spatial matching. The null control means this particular cluster displacement diagnostic did not independently flag a conventional age-dependent orbital confound at its preregistered threshold. It does not rule out asymmetric drift, disk heating, selection effects, population chemistry, or other conventional mechanisms.

This block measures a matched catalog-tracer current/velocity contrast—not a calibrated stellar-mass current, gravitational acceleration, or causal memory term. Neither the significant field statistic nor the null control is a detection of gravitational persistence.

Machine-readable authorities:

- `data/persistence_history/dr20_independent/field_v1/field_summary.json`
- `data/persistence_history/dr20_independent/open_cluster_control_v1/open_cluster_summary.json`
- `data/persistence_history/dr20_independent/block_verdict_v1.json`
