# Stage 9 canonical stationary parameter provenance

This document records where each quantity in the canonical Section 10 stationary vector-current model is allowed to come from.

## Canonical stationary equation

The current manuscript defines

    V^2(R) = V_b^2(R) + R C_A V(R) B_A[V](R),

with

    B_A[V](R) = integral dR' R' Sigma_b(R') V(R') K_A(R,R';L_A).

The primary universal stationary parameter pair is

    {L_A, C_A}.

## Provenance classes

| Quantity | Role | Allowed provenance | Stage 9 rule |
|---|---|---|---|
| `L_A` | stationary vector correlation length | Universal parameter of current paper; numerical value is **not presently derived uniquely from the action**. Section 12 treats it as a global stationary-calibration parameter subject to theory-health priors. | Must be frozen before Milky Way history/orientation comparison. No Milky-Way-specific tuning. |
| `C_A` | universal stationary force amplitude | Combination of source coupling, embedding map and force convention. Sign is action/convention-fixed; numerical magnitude is **not presently uniquely derived**. Section 12 treats it as a global stationary-calibration parameter. | Sign cannot change by galaxy. Magnitude must be frozen before Milky Way history/orientation comparison. |
| `tau_A` | vector relaxation time | Time-dependent/history sector only. It does not enter the stationary m=0 equation. | Do not infer it from stationary rotation curves. Infer/constrain only with independent history/time-dependent information under a predeclared protocol. |
| `c_A` | vector characteristic speed | Parent-theory/stability quantity. | Must satisfy theoretical causal/stability constraints; not a stationary rotation-fit parameter. |
| `Sigma_b(R)` | baryonic surface density | Measured/reconstructed from baryonic data. | No residual-driven reshaping. |
| baryonic streaming velocity | source current | Prefer independently measured component-resolved streaming; cold closure uses the self-consistent V only as the manuscript's declared approximation. | Source prescription must be frozen before target comparison. |
| `Upsilon_d`, `Upsilon_b` | stellar M/L nuisance | Fixed external priors. | May not absorb persistence-model freedom. |
| vertical scale height/profile | UV/finite-thickness physics | Independently measured or a single predeclared common prescription used for controlled numerical validation. | Never tune per galaxy from rotation residuals. |
| spectral grid, taper, under-relaxation, tolerances | numerics | Convergence studies only. | One declared algorithm/settings family; changes justified by numerical error, not fit quality. |

## Sequencing consequence

The current manuscript's own empirical protocol implies the following order if the theory does not independently derive numerical `L_A` and `C_A`:

1. implement and validate the Section 10 solver on synthetic/analytic controls;
2. define the stationary-galaxy calibration and blind split before fitting;
3. infer one global `{L_A, C_A}` pair from the stationary calibration sample subject to the theoretical-health priors;
4. freeze that pair and all numerical/source rules;
5. evaluate the stationary blind sample;
6. carry the frozen stationary pair into Milky Way Stage 9/history work;
7. introduce `tau_A` only through independent history-sensitive calibration/data;
8. run the Milky Way 0-degree baseline and then the predeclared orientation sensitivity suite;
9. compare downstream to halo/Delta-a/orbit-weight benchmarks without refitting.

If instead a parent-theory derivation fixes `L_A` and `C_A` before empirical calibration, that derivation supersedes steps 2-3 for those parameters.

## Important correction to the earlier project ordering

The earlier ledger placed SPARC after Milky Way validation. The canonical paper shows that this is too coarse if SPARC (or another stationary galaxy sample) is the source of the universal stationary calibration. In that case a **stationary calibration subset must precede Milky Way Stage 9**, while the **frozen stationary blind validation and broader SPARC population test remain independent validation steps**.

The Milky Way must never be used to choose `L_A` or `C_A` if it is intended to test the hereditary/orientation prediction.
