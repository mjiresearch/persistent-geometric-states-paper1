# Persistence Framework — Research Ledger

## Purpose

This is the standing project-control document for the persistence framework. It exists to prevent circular work, rediscovery of already-settled issues, and drift away from the canonical manuscripts and validation plan.

**Rule:** Before beginning a new theory branch, numerical experiment, or interpretive change, check this ledger. Update the ledger when a major result changes project status.

## Canonical references

1. **Current Paper — _Persistent Geometric States in General Relativity: A Hereditary Framework for Galactic Rotation Curves_**
   - Canonical theory document.
   - New work must agree with it or explicitly identify and justify a proposed extension/revision.
2. **Earlier Paper — _Finite-Memory Gravitational Response from Retarded Green's Function Tails_**
   - Historical/theoretical foundation for causal hereditary motivation.
   - GR Green-function tails motivate the effective hereditary sector; they are not presently a quantitative derivation of the phenomenological kernel.
3. **Referee report on the earlier paper**
   - Permanent conceptual checklist: effective modification vs exact GR reformulation; correct GR limit; auxiliary-sector state/DOF accounting; quantitative tail derivation; quantitative cosmology/GW claims.
4. **Stage 9 Milky Way validation framework**
   - Primary halo-blind empirical test.
5. **SPARC validation framework**
   - Independent galaxy-population validation after the Milky Way test is frozen.

## Standing scientific interpretation

- The framework is treated as a **covariant, strictly retarded effective extension of gravitational response**, not an exact reformulation of GR if it changes observables.
- The ordinary Einstein response remains explicit. The persistence contribution must vanish continuously in the GR limit.
- GR Hadamard tails are motivation for causal hereditary structure; an exponential/Gyr/kpc effective kernel is not claimed to be quantitatively derived from the exact tail operator unless that derivation is supplied.
- The hereditary sector may contain independent state variables/initial data. Do not equate “no new propagating spin-2 metric pole” with “no additional state degrees of freedom.”
- The current paper’s dynamical state-frame/moving-background construction remains central.
- Rotation, lensing, and cosmological expansion/growth are linked tests of one framework, not independent opportunities for parameter fitting.

## Achievement and decision ledger

| ID | Investigation / achievement | Result / decision | Status | Reopen only if… |
|---|---|---|---|---|
| L-001 | Exact-GR-reformulation interpretation | Rejected for any version that changes physical observables. Treat persistence as an effective extension. | **CLOSED** | A mathematically exact equivalence proof also demonstrates identical observables. |
| L-002 | GR limit | Einstein source must remain explicit; hereditary correction tends to zero. Never let memory-amplitude → 0 imply `G_mn = 0`. | **CLOSED** | Parent equations are fundamentally replaced. |
| L-003 | GR tail interpretation | Exact Hadamard tails motivate causality/heredity but do not presently derive the adopted exponential/Gyr/kpc response. | **CLOSED as wording rule / OPEN as derivation problem** | A quantitative coarse-graining of the tail operator is completed. |
| L-004 | Auxiliary-sector degrees of freedom | Independent relaxational/state variables must be acknowledged and constraint/mode structure stated explicitly. | **ACTIVE GUARDRAIL** | Full constraint analysis proves a stronger statement. |
| L-005 | Current paper vs earlier tail paper | Current paper is canonical; earlier paper is an ancestral/motivating model and referee-history reference. | **CLOSED** | A deliberate manuscript-level theory revision is approved. |
| L-006 | Moving-background / state-frame concept | Physical motion relative to a dynamical timelike state frame is central; coordinate motion alone is not persistence. | **ESTABLISHED** | Covariant parent theory rules it out. |
| L-007 | Milky Way historical orientation | Keep 0° as canonical Stage 9A and a preregistered 0–180° sensitivity suite. Do not assume a 90° flip as fact. | **OPEN / DESIGNED** | New Galactic-archaeology evidence materially changes the prior. |
| L-008 | Halo-blind Stage 9 principle | Persistence shape/normalization/history parameters may not be chosen from Portail17+halo, Hunter24+halo, orbit weights, SPARC, or Δa targets. | **PERMANENT GUARDRAIL** | Never for confirmatory Stage 9. |
| L-009 | Provisional Ratcliffe baryonic history | Useful as a bracketed source-history reconstruction but not a complete formation-site history. Signed and clipped envelopes retained. | **OPEN / INPUT-LIMITED** | Better resolved baryonic history becomes available. |
| L-010 | Candidate L0 telegraph response | Factorizes to a damped massless-wave form with light-cone-only response; inadequate as the desired hereditary-tail mechanism. | **CLOSED CONTROL** | New mathematics shows an omitted tail-producing term. |
| L-011 | Candidate L2 luminal local-curvature-change response | Corrected `c` run gives an extremely small, wrong-shaped Galactic acceleration for the tested unit-normalized additive linear channel. | **FALSIFIED FOR TESTED FORMULATION** | The theory—not the halo data—derives materially different coupling/source structure. |
| L-012 | Slow-`c_H` rescue | Not allowed as an empirical rescue. Strongly subluminal gravitational modes require parent-action, stability, Cherenkov, coupling and GW audits. | **BLOCKED** | Parent theory independently derives such a mode. |
| L-013 | Weak bilinear interaction rescue of L2 | Perturbative interaction would require an enormous effective coupling in the tested L2 branch; not a credible weak-coupling rescue. | **CLOSED FOR PERTURBATIVE L2** | A nonperturbative interaction is derived from the parent theory. |
| L-014 | A0–A4 exploratory scaffolding | Useful for rediscovering state-frame, metric-coupling, deposition and normalization issues, but must not supersede or duplicate the current paper without explicit justification. | **REFERENCE / NOT CANONICAL** | A component is shown to improve the canonical theory and is deliberately incorporated. |
| L-015 | Referee report | Converted into permanent theory-admissibility guardrails. | **INCORPORATED** | A new referee/theory result supersedes a specific point. |
| L-016 | Rotation–lensing–cosmology triangle | Reconfirmed as the natural cross-scale validation structure already present in the early work and current framework. | **ESTABLISHED** | Theory predicts a demonstrably different observable structure. |
| L-017 | Canonical weak-field Stage 9 bridge | Derived directly from the current paper. Stationary disks are vector-current dominated; historical evolution adds the canonical scalar/history source. The observable force follows from `g_obs = g + epsilon_H H`. | **ESTABLISHED** | Canonical manuscript equations are deliberately revised. |

## Current achievements

### Theory

| Goal | Status | Notes |
|---|---|---|
| Effective-extension interpretation | ✅ | Referee ambiguity resolved. |
| Correct GR recovery | ✅ | Persistence correction vanishes; Einstein response remains. |
| Independent hereditary state | ✅ | Current paper explicitly treats persistent state as additional effective structure. |
| Dynamical state frame | ✅ | Covariant moving-background concept present. |
| Parent field content | ✅ | Current paper contains scalar/vector/state-frame construction. |
| Stability/dispersion framework | ✅ | Present in current manuscript; precision claims must stay within what is actually derived. |
| Canonical weak-field source-to-force mapping | ✅ | Documented in `docs/theory/stage9_canonical_weak_field_bridge.md`. |
| Explicit constraint/mode-counting presentation | 🟡 | Strengthen for referee-proof exposition. |
| Quantitative GR-tail → effective-kernel derivation | ⏳ | Major open theoretical goal. |
| Observable coupling/parameter values frozen independent of galaxy targets | 🟡 | Structure is known; numerical provenance for universal combinations still required. |

### Milky Way / Stage 9

| Goal | Status | Notes |
|---|---|---|
| Baryons-only baseline | ✅ | Existing control. |
| Conventional full-potential benchmark | ✅ | Portail17/Hunter24 comparison framework exists. |
| Halo-blind methodology | ✅ | Hard guardrails implemented. |
| Historical orientation operator | ✅ | 0° baseline + 30° increments through 180°. |
| Memory-time sensitivity architecture | ✅ | Frozen grid architecture exists. |
| Provisional baryonic-history adapter | ✅ / 🟡 | Operational but source-history limited. |
| Canonical-theory weak-field mapping | ✅ | Derived from current paper. |
| Canonical stationary disk equation reproduction | **NEXT** | Reproduce Sec. 10 numerically before historical Stage 9A. |
| Universal parameter provenance table | **NEXT** | Determine source for `L_A`, `C_A`, scalar/history parameters, state-frame assumptions. |
| 0° canonical persistence prediction | ⏳ | After stationary reproduction and parameter freeze. |
| 0–180° orientation suite | ⏳ | Run only after 0° theory and normalization are frozen. |
| Orbit-weight comparison | ⏳ | After persistence field is frozen. |
| Δa comparison | ⏳ | Downstream diagnostic only; never calibration. |
| SPARC external validation | ⏳ | After Milky Way pipeline is frozen. |

## Canonical weak-field bridge summary

The current paper supplies the Stage 9 chain directly:

1. baryonic energy/current relative to the state frame:
   - `epsilon ~ rho_b c^2`
   - `q_i ~ rho_b c v_i^rel`;
2. scalar history invariant:
   - `I_phi = tau_* (dot epsilon_M + chi_q c D_mu q^mu)`;
3. source maps:
   - `J_phi = -(g_phi/M_*) I_phi`
   - `J_A_mu = -(g_A/M_*) q_mu`;
4. retarded scalar/vector propagation;
5. composite inherited perturbation `H_mn(phi,A,n)`;
6. observable metric `g_obs = g + epsilon_H H`;
7. stellar acceleration from `H_00`, `H_0i`, and retained `H_ij` terms.

For the minimal stationary axisymmetric pressureless disk, the scalar dust source vanishes and the baseline extra radial force is the canonical vector-current term

`a_R^(A) = zeta_A v_c B_P,z`,

with the nonlocal disk kernel and universal theory-level combinations given in Sec. 10 of the current paper.

## Highest-priority open goals

1. **Canonical stationary reproduction:** implement/reproduce Sec. 10 with the exact paper equations before historical generalization.
2. **Parameter provenance:** identify which universal combinations are already fixed/calibrated in the current paper and which remain open; none may be chosen from Stage 9 halo targets.
3. **Historical source implementation:** extend the canonical scalar/vector source maps to the Milky Way history and orientation operator.
4. **Constraint/mode accounting:** make the additional state content and constraints explicit enough to answer the referee’s DOF objection without overclaiming.
5. **Kernel provenance:** either quantitatively derive the effective hereditary kernel from coarse-grained GR-tail physics or state clearly that it is an effective ansatz and seek an independent microscopic origin.
6. **Stage 9A prediction:** freeze the 0° Milky Way persistence field before opening halo/Δa/orbit-weight comparisons.
7. **Orientation sensitivity:** only after Stage 9A is frozen, run 30°, 60°, 90°, 120°, 150°, 180° with identical physics.
8. **Cross-observable validation:** use the same universal theory for dynamics, lensing and cosmology; no sector-specific retuning.
9. **SPARC:** apply the frozen framework to the broader galaxy population after Milky Way validation.

## Do-not-digress rules

Before pursuing a new idea, answer all four questions:

1. **Is this already contained in the current canonical paper?** If yes, use the existing formulation rather than reinventing it.
2. **Does it resolve an open ledger item or referee criticism?** If not, deprioritize it.
3. **Does it advance a halo-blind prediction or independent falsification?** If not, justify why it is necessary.
4. **Is it a derivation or a new assumption?** New assumptions must be labeled, preregistered where appropriate, and never chosen because they improve the Galactic target.

If a proposed path contradicts a CLOSED or PERMANENT-GUARDRAIL item, stop and explicitly justify reopening that item before doing new work.

## Immediate next action

**Reproduce the canonical Section 10 stationary rotating-disk equation numerically, using the current paper’s exact vector-current source and force mapping, and build a parameter-provenance table before any new Milky Way halo comparison.**
