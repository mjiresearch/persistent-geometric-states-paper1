# Milky Way Stage 5 force-residual verdict

Date: 2026-08-08

## Purpose

Stage 5 asked whether the source-history screen could be upgraded from rotation/streaming proxies to a more direct dynamical-force estimate without relaxing the Stage 4 stop rule against further significance mining.

## Stage 4G independent tracer arbitration

A radial rotation proxy was constructed directly from the independent BOSSNet hot-star population over 12 bins from 5.0 to 10.5 kpc and compared with both McMillan17 and McGaugh2019 baryonic decompositions.

The baryonic deficit was positive in all 12 bins under both decompositions.

General young-star sample:

- median Vphi = 225.52 km/s;
- McMillan17 median chi_young = 0.6252;
- McGaugh2019 median chi_young = 0.3114.

The strong Stage 4B guiding-migration signal did not independently replicate after detrending and family-wise correction:

- McMillan17 general: outward >1 kpc rho = +0.6713, maxT p = 0.1021; inward >1 kpc rho = -0.6783, maxT p = 0.0929.
- McGaugh2019 general: outward rho = -0.4545, maxT p = 0.4538; inward rho = +0.3636, maxT p = 0.6647.
- McMillan17 cold: outward rho = +0.6084, maxT p about 0.17; inward rho = -0.5734, maxT p about 0.22.
- McGaugh2019 cold: outward rho = -0.5524, maxT p about 0.26; inward rho = +0.4895, maxT p about 0.39.

Thus the halo-like baryonic deficit survives the independent tracer, while the migration-direction explanation does not.

## Stage 5A axisymmetric Jeans sensitivity screen

A radial Jeans estimate was constructed from the 30,495-star MWM history sample using

\[
V_c^2 = \langle V_\phi\rangle^2 + \sigma_\phi^2 - \sigma_R^2\left[1+\frac{\partial\ln(\nu\sigma_R^2)}{\partial\ln R}\right].
\]

The tracer density was not inferred from raw MWM counts. Instead, an exponential tracer-density scale-length envelope h_nu = 2.0, 2.5, 3.0, 3.5 kpc was imposed. Multiple vertical cuts were tested, and both baryonic decompositions were retained.

Across 32 scenario/decomposition tests per predictor:

- Rbirth: 0 tests with maxT p < 0.05;
- delta Rguide: 0;
- |delta Rguide|: 0;
- history-distance/time proxy: 0;
- inner-born fraction: 0;
- age: 0 below 0.05 and only 1 below 0.10;
- outward >1 kpc: 3 below 0.05, but positive/negative sign fraction = 0.50/0.50;
- inward >1 kpc: 3 below 0.05, but sign is likewise not stable across scenarios.

Therefore no history variable satisfies the pre-specified stability rule.

More importantly, the mixed MWM tracer population fails a stronger methodological sanity check. The radial velocity-dispersion profile changes abruptly with radius because the spectroscopic footprint samples different stellar populations at different R and |z|. For example, a representative z < 1 kpc profile has sigma_R roughly 50--85 km/s inside 7.5 kpc but about 11--20 km/s around 8--9 kpc. A single mixed-population Jeans equation should therefore not be treated as a clean force reconstruction even when its inferred Vc is numerically near the Eilers scale.

Stage 5A is retained as a sensitivity diagnostic, not as an accepted force measurement.

## Stage 5B homogeneous-cohort Jeans screen

To remove the population-mixing problem, three tracer cohorts were fixed before re-running the Jeans screen:

1. low-alpha disk;
2. intermediate-age low-alpha disk;
3. narrower solar-metallicity low-alpha disk.

The acceptance rule required at least 8 radial bins plus a smooth sigma_R profile before any history significance was evaluated.

Coverage failed before the significance stage:

- low-alpha: 6 usable radial bins for both |z| < 1.0 and 1.5 kpc;
- intermediate-age low-alpha: 6 bins for both cuts;
- solar-metallicity low-alpha: 4 bins for both cuts.

Therefore no homogeneous-cohort Jeans history result is accepted. This is a footprint/coverage limitation, not evidence for or against the persistence mechanism.

## Scientific conclusion after Stages 1--5

1. A substantial Milky Way baryonic gravitational deficit is robust to multiple baryonic decompositions and an independent BOSSNet young-star tracer population.
2. Age alone does not robustly predict that residual after present-state controls.
3. Birth-radius and guiding-migration proxies contain real Galactic dynamical information and can produce strong correlations in particular residual constructions.
4. Those migration correlations do not remain stable when the baryonic decomposition, tracer population, spatial grid, or force-estimation assumptions are changed.
5. The public MWM footprint does not support a sufficiently homogeneous, radially extended tracer sample for a clean selection-light Jeans force test using the current derived sample.
6. Therefore no present public-data result is accepted as evidence that inherited geometric persistence explains the halo-like residual.
7. The persistence framework remains testable, but the next decisive experiment requires genuinely new information rather than another threshold/grid scan.

## Required next experiment

The preferred sequence is now:

\[
\text{time-resolved baryonic source history}
\rightarrow H[\rho_b,J_b]
\rightarrow \text{independent spatial force residual}
\rightarrow \text{frozen interaction law}
\rightarrow \text{external-galaxy validation}.
\]

Highest-value missing source-history product:

- probabilistic birth radius joined to Gaia DR3 ID;
- time-resolved guiding-center history Rguide(t), ideally with phi(t), z(t), and velocity history;
- migration epoch/direction probability;
- bar/spiral resonance history;
- accreted versus in-situ probability.

Highest-value missing dynamical product:

- a selection-function-corrected 3D Galactic force/acceleration map, or a sufficiently complete tracer catalog to construct one without mixing different populations across radius.

## Stop rule

Do not continue scanning new migration thresholds, radial bin definitions, or azimuth grids with the same public proxy data. The next progress should come from a new source-history observable or a genuinely stronger force reconstruction.
