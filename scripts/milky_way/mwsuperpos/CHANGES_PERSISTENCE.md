# Persistence comparison changes

- Fixed orbit-weight mass normalization at the weight-vector level.
- Default subset target is `rho/n_sub`; legacy full-target subset solving remains selectable.
- `combine()` no longer renormalizes reconstructed density by default.
- Added Portail17 and Hunter24 force-model selection.
- Added halo removal (`--baryons-only`) for both force families.
- Added fixed-target-density control to avoid conflating potential and target changes.
- Added `compare_potentials.py` for four-way controlled comparisons and persistence replacement targets.
- Mock validation now explicitly uses the production absolute-residual convention.
