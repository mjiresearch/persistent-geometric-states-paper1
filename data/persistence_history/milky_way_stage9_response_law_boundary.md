# Milky Way Stage 9 response-law boundary

Date: 2026-08-10

## Result of theory audit

The checked-in persistence manuscript supplies the conceptual weak-field decomposition

\[
\mathbf a_{\rm dyn}=\mathbf a_b+\mathbf a_H+\mathbf a_{\rm int}+\cdots
\]

and requires causal evolution, independent initial data, finite relaxation, universal interaction structure, and continuous recovery of GR. It also explicitly rules out interpreting the persistent state as a second instantaneous Poisson field sourced by the same static baryonic density.

## Candidate progression

Stage 9 has now tested several minimal effective closures while preserving the halo-blind guardrail:

- L0: causal damped hyperbolic control, later recognized to factorize to a light-cone-only response and retained as a null/control candidate;
- L1: two-rate causal transport with genuine interior-cone support;
- L2: L1 transport with local curvature-change deposition, S_H = 4 pi G c_H^2 tau D_H rho_b, avoiding deposition throughout the long-range Newtonian potential.

## Critical speed-unit correction

A subsequent characteristic-speed audit found that the original code constant `C_KPC_PER_GYR = 306.60139378555056` was mislabeled: that value is c in kpc/Myr, not kpc/Gyr. The correct value is approximately 306601.39378555055 kpc/Gyr.

The constant has been corrected and protected by regression tests. All Candidate L2 field products and comparisons produced with the old constant are invalid and must be regenerated. The earlier provisional numerical statement that L2 was roughly nine orders of magnitude too small is therefore withdrawn pending the corrected rerun.

## Characteristic-speed boundary

The checked-in manuscript still does not derive the persistence-mode characteristic speed from a completed quadratic parent action/principal symbol. A strongly subluminal c_H therefore may not be introduced post hoc to improve the Milky Way comparison.

The repository now allows the preregistered c_H=c case, but blocks c_H<c unless a provenance record demonstrates all of the following before halo comparison:

1. parent-action derivation;
2. documented principal symbol/characteristic speed;
3. stability analysis;
4. gravitational-Cherenkov consistency audit;
5. observational-coupling audit;
6. speed prior frozen before target comparison.

With the corrected c, making c_H tau a 5--20 kpc Galactic scale over tau=1--16 Gyr would require an extreme c_H/c of roughly 10^-6--10^-4, not a modest subluminal correction. Such a mode is therefore not treated as an available tuning direction.

## Current Stage 9 status

Available/frozen:

- 0--180 degree orientation-history operator;
- 1--16 Gyr relaxation-time sensitivity grid;
- Ratcliffe-2026 Table A.1 provisional radial history;
- historical ordinary baryonic-potential diagnostics;
- L0/L1/L2 response-law implementations and theory tests;
- corrected luminal characteristic speed;
- guardrail against post-hoc subluminal speed sweeps.

Still provisional:

- the Ratcliffe Table A.1 source history is not the unique physical formation-site history;
- L2 is an effective weak-field closure, not yet derived from the completed covariant parent action;
- the corrected c_H=c L2 numerical field must be regenerated before any amplitude/shape verdict is retained.

The scientific protocol remains: generate the corrected halo-blind field first, freeze it, then compare against the already archived Milky Way residuals and orbit-weight benchmarks without renormalization or target-selected speed changes.
