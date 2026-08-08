# Milky Way Stage 4 source-history verdict

Date: 2026-08-08

## Question

Does a source-history variable substantially closer to baryonic history than stellar age—specifically inferred birth radius and radial/guiding-center migration—robustly predict the Milky Way dark-matter-like gravitational residual under the revised inherited-state + contemporary-curvature interaction picture?

The simplest interaction-normalized observable screened was

\[
\chi_{\rm int}=\frac{\Delta g}{g_b}.
\]

## Data and tests

- Dantas et al. 2025 public birth-radius catalogue: 1,190 rows. Exact Gaia overlap with DR20 MINESweeper was zero.
- Ratcliffe public `Rbirth` APOGEE sample: 143,307 rows; 120,987 usable over the main radial range.
- Stage 4A: present radius minus inferred birth radius.
- Stage 4B: guiding radius minus inferred birth radius; preferred migration definition.
- Stage 4C: exact Ratcliffe APOGEE ↔ MWM Gaia crossmatch; only 45 stars / 2 viable spatial cells, therefore underpowered.
- Stage 4D: exploratory transfer of the Ratcliffe birth-radius relation to the full MWM MINESweeper age/[Fe/H] sample; 30,495 stars and 237 spatial cells.
- BOSSNet independent young/hot tracer sample: 15,660 hot stars, 8,995 with finite BOSS radial velocity; 7,110 pass the initial 6D disk-quality selection.
- Stage 4E/F: source-history map from MWM versus independent young-star kinematics on matched spatial cells.
- Stage 4G: independent BOSSNet young-star radial rotation proxy versus the Stage 4B guiding-migration history profile and two baryonic decompositions.

## Strong Stage 4B exploratory result

With the Eilers circular-speed summary plus McMillan17 baryons, guiding-center migration direction was very strongly associated with the interaction-normalized residual over 12 supported radial bins:

- outward migration >1 kpc: detrended Spearman rho = -0.9371, family-wise maxT p = 0.00020;
- inward migration >1 kpc: detrended Spearman rho = +0.8951, family-wise maxT p = 0.00155.

The independent McGaugh 2019 baryonic decomposition did not reproduce these directional relationships.

Therefore the Stage 4B signal was not accepted as persistence evidence.

## Spatial independent-tracer test

On a 1.0 kpc x 0.5 kpc x 30 degree common grid, the general young-star sample had 16 source-history/tracer cells. After adjusting source-history variables for source age, [Fe/H], and alpha abundance, inferred birth radius versus young-star radial streaming gave:

- rho = +0.7211;
- within-R-|z| permutation p = 0.0320;
- family-wise maxT p = 0.0320.

However, the signal disappeared in the cold near-circular young-star subset and on the 45 degree robustness grid. Migration-direction predictors also failed the pre-specified cross-sample/grid replication requirement.

Therefore the spatial independent-tracer decision rule failed.

## Independent young-star radial residual arbitration

Stage 4G built a radial rotation proxy directly from BOSSNet young-star Vphi over 12 bins from 5.0 to 10.5 kpc.

The baryonic deficit was positive in all 12 bins under both baryonic decompositions.

General young-star profile:

- median Vphi = 225.52 km/s;
- McMillan17 median chi_young = 0.6252;
- McGaugh median chi_young = 0.3114.

For McMillan17 baryons:

- outward migration >1 kpc: detrended rho = +0.6713, uncorrected p = 0.0168, permutation p = 0.0195, maxT p = 0.1021;
- inward migration >1 kpc: detrended rho = -0.6783, uncorrected p = 0.0153, permutation p = 0.0182, maxT p = 0.0929.

For McGaugh baryons:

- outward migration >1 kpc: detrended rho = -0.4545, maxT p = 0.4538;
- inward migration >1 kpc: detrended rho = +0.3636, maxT p = 0.6647.

Cold young-star profile:

- McMillan outward >1 kpc: detrended rho = +0.6084, maxT p = 0.1739;
- McMillan inward >1 kpc: detrended rho = -0.5734, maxT p = 0.2209;
- McGaugh outward >1 kpc: detrended rho = -0.5524, maxT p = 0.2619;
- McGaugh inward >1 kpc: detrended rho = +0.4895, maxT p = 0.3911.

Thus the young-star rotation arbitration does not independently replicate the original Stage 4B migration-direction signal. The sign depends on the baryonic decomposition, and none of the directional migration variables survives the family-wise correction in both decompositions and both tracer cuts.

## Current scientific conclusion

1. The Milky Way baryonic gravitational deficit remains robust in these screens. It is seen with the independent BOSSNet young-star rotation proxy as well as the earlier Eilers/McGaugh analyses.
2. Age alone is not a useful persistence predictor after appropriate controls.
3. Inferred birth radius and migration history contain substantially more Galactic dynamical information than age alone.
4. Migration direction can generate very strong correlations with a particular residual construction, but those correlations are not stable to changing the baryonic decomposition, tracer population, or spatial grid.
5. Therefore no current public-data result is accepted as evidence that persistence explains the halo-like residual.
6. The public-data tests do, however, sharpen the next decisive experiment: use independently reconstructed, preferably probabilistic/time-resolved source trajectories or guiding-center histories to construct a predicted hereditary state H, then compare that prediction with a spatial gravitational force residual under a frozen interaction law.

## Stop rule

Do not continue scanning additional radial bins, grid choices, or migration thresholds for significance with the current public proxy data. Further significance mining would weaken the inference.

The next advancement should come from new information or a stronger observable:

- time-resolved source-history data (birth radius probability + Rguide(t), migration epoch/direction, bar/spiral interaction history, accretion labels), or
- a properly reconstructed local gravitational-force residual with an independently specified source-history functional.

The current Stage 4 result is therefore a scientifically useful null/constraint on simple migration-proxy versions of the persistence hypothesis, not a detection.
