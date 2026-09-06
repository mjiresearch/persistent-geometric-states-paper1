# mwsuperpos — Stage 8 working copy

Independent reimplementation of the Khoperskov et al. Milky Way orbit-superposition method, adapted here for controlled persistence-framework tests.

This copy is **not** treated as a literal reconstruction of the Galaxy's past 5 Gyr. The stored orbit libraries are integrations in fixed rotating potentials and are used as phase-space reconstruction machinery only.

## Source papers

- Khoperskov et al. Paper I — method validation, arXiv:2411.15062
- Khoperskov et al. Paper II — disc chrono-chemo-kinematics and method reference, arXiv:2411.16866
- Khoperskov et al. Paper III — bulge, arXiv:2411.18182
- Ratcliffe et al. Paper IV/V — birth radius and SFH, arXiv:2509.02691

## Installation

AGAMA needs GSL and a non-isolated build. On Debian/Ubuntu:

```bash
sudo apt-get install -y libgsl-dev libeigen3-dev
pip install numpy scipy astropy
pip install agama --no-build-isolation --config-settings="--build-option=--yes"
```

## Public input data

- `allStar-dr17-synspec_rev1.fits` from APOGEE DR17; this contains the Gaia EDR3 astrometry cross-match in `GAIAEDR3_*` columns.
- APOGEE DistMass VAC (Stone-Martinez et al. 2024), keyed on `APOGEE_ID`.

The multi-GB source catalogs are not committed to this repository.

## Standard run

```bash
python run_pipeline.py \
  --allstar allStar-dr17-synspec_rev1.fits \
  --distmass apogee_distmass-dr17.fits \
  --outdir results/
```

Main outputs:

- `sample.fits` — selected APOGEE × DistMass sample;
- `orbits.npy` — `(N,500,6)` unmirrored bar-frame trajectories;
- `weights.npz` — normalized mean weights, all realizations, IDs, chemistry, ages, approximate birth radii, ICs and diagnostics;
- exported AGAMA potential definition for the selected force model.

## Persistence-specific corrections and controls

### Saved-weight normalization

The source implementation fit each of five orbit subsets independently to the full target density, then renormalized only the reconstructed map. That can leave the saved orbit weights over-normalized by approximately the number of subsets.

This working copy defaults to fitting each subset to `rho/n_sub` and then explicitly mass-normalizes every realization and the final mean weight vector inside the fitted volume. `combine()` no longer silently rescales the reconstruction by default.

The legacy full-target subset convention remains selectable with `--subsample-target full`, but saved weights are still normalized before use.

### Controlled force models

`run_pipeline.py` accepts:

- `--potential portail17` or `--potential hunter24`;
- `--baryons-only` to remove the dark halo;
- `--target-density portail17|hunter24`.

For the primary robustness experiment the target density should remain fixed while the force model changes, so a target change cannot masquerade as a potential effect.

### Four-way comparison

```bash
python compare_potentials.py \
  --allstar allStar-dr17-synspec_rev1.fits \
  --distmass apogee_distmass-dr17.fits \
  --outdir comparison_results/
```

This runs the same selected stars through:

1. Portail17 + halo;
2. Portail17 baryons only;
3. Hunter24 + halo;
4. Hunter24 baryons only.

It writes `comparison_summary.csv` and `persistence_replacement_target.npz`.

The replacement target contains

`delta_a_halo(R) = a_full(R) - a_baryons(R)`

for the Portail and Hunter families. This is only the conventional acceleration contribution a successful persistence model would need to replace; it is **not evidence for persistence**.

## Mock validation

```bash
python validate_mock.py 2500
```

The mock validation now explicitly uses the production absolute-residual convention and the corrected fractional-subset/mass-normalized solver.

## Important caveats

- The 5-Gyr trajectories are phase-space samples in a stationary model, not measured historical paths.
- Full-halo orbit libraries are dark-matter-conditioned by construction; they cannot be used as independent hereditary-source histories without controlling that dependence.
- The Paper II solar-motion choice is not fully specified in the source paper.
- The source-paper bar pattern speed is reported as 37.5 km/s/kpc in Paper II and 37 in later papers.
- `rbirth.py` is an approximate auxiliary reconstruction, not the full Ratcliffe gradient-history inference, and `R_now-R_birth` must not be resurrected as a persistence state variable after the frozen Stage 6 replication failure.
- Weight-realization scatter is a numerical stability diagnostic, not a posterior uncertainty.

## Layout

```text
potential.py          Portail/Hunter force models with optional halo removal
orbits.py             coordinate transforms and rotating-frame integration
superposition.py      grid, sparse design matrix, normalized NNLS solver
 ingest.py            APOGEE DR17 × DistMass selection and IC construction
rbirth.py             approximate birth-radius helper
run_pipeline.py       one-model end-to-end run
compare_potentials.py controlled four-way persistence comparison
validate_mock.py      data-free machinery validation
PROVENANCE.md         received-package and review-artifact checksums
CHANGES_PERSISTENCE.md project-specific modifications
```

See `docs/milky_way_stage8_orbit_superposition.md` for the scientific interpretation rules and guardrails for Stage 8.
