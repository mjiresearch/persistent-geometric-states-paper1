# Persistence Framework — Paper I Project Ledger

**Canonical cross-session checkpoint**  
**Repository:** `mjiresearch/persistent-geometric-states-paper1`  
**Ledger established:** 2026-08-12  
**Purpose:** preserve the scientific and operational state of Paper I across ChatGPT sessions so completed work is not repeatedly reopened, frozen boundaries are not accidentally violated, and the next live branch is always explicit.

> **Authority rule:** this ledger summarizes the project state. It does **not** supersede frozen protocol, data, provenance, validation, or manuscript artifacts. If this ledger conflicts with a frozen artifact, the frozen artifact controls and the ledger must be corrected.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| **FROZEN** | Predeclared boundary or artifact that must not be altered after the fact. |
| **COMPLETE** | Implemented and durable in the repository's canonical scientific record. |
| **COMPLETE (PR)** | Implemented and validated on a durable GitHub branch/PR but not yet merged to `main`. |
| **IN PROGRESS** | Current active work branch. |
| **NEXT** | Queued immediately after the active branch. |
| **LOCKED** | Must not be opened, fit, tuned, or evaluated until stated prerequisites are met. |
| **BLOCKED** | Waiting on a prerequisite or missing public source. |
| **SUPERSEDED** | Historical work retained for auditability but no longer canonical. |

---

## 2. North star and current scientific state

Paper I is an **independent empirical test of the Persistence Framework** under a predeclared calibration/blind-validation discipline. The central working idea is that a persistent/hereditary geometric response associated with prior baryonic stress-energy and mass-current history may contribute to the gravitational field normally attributed phenomenologically to a dark-matter halo. The paper must test that possibility rather than assume it.

Current scientific posture:

- There is **no final empirical conclusion yet** for the stationary SPARC test.
- A substantial baryons-only gravitational deficit is robust in the Milky Way work examined so far, but the historical proxies tested through Stage 8 have **not yet produced accepted evidence** that persistence explains that deficit.
- Negative or null intermediate tests are preserved and used to constrain the next test; they are not repaired through post-hoc threshold, sign, subset, or kernel tuning.
- The stationary SPARC source/profile construction must be frozen **before** `L_A` and `\mathcal C_A` are calibrated.
- The blind SPARC set is reserved for the final pre-frozen evaluation. There is no blind-set refitting.
- The canonical `main` branch currently contains the Milky Way scientific record through Stage 7. Stage 8 is completed and validated in draft PR #2 but is not yet merged to `main`.

---

## 3. Canonical locked/frozen boundaries

| ID | Status | Boundary / decision | Canonical detail |
|---|---|---|---|
| B01 | **FROZEN** | Stationary observational master | `data/stationary/frozen/stationary_master_v1.csv`; **149 galaxies, 3,152 radial measurements**; SHA-256 `254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f`. Selection: `Q <= 2`, inclination `>=30 deg`, at least 5 valid radial points. |
| B02 | **FROZEN** | Canonical calibration/blind split | **104 calibration / 45 blind** galaxies, deterministic SHA-256 assignment, frozen before source-profile fitting. Earlier 124/25 exploratory audit split is **SUPERSEDED** and must not be confused with the canonical split. |
| B03 | **LOCKED** | Stationary source current | Use `J(R) = Sigma_b(R) V(R)` with the **self-consistent model velocity**. `Vobs` is the target observable only and must not be used as the source velocity. |
| B04 | **LOCKED** | Stellar source basis | `Sigma_disk = Upsilon_d * SBdisk`, `Sigma_bulge = Upsilon_b * SBbulge`; retain unit-M/L basis so stellar M/L remains a declared nuisance parameter rather than being silently fixed early. |
| B05 | **LOCKED** | Gas sign convention | Preserve signed gas contribution using `Vgas * abs(Vgas)`; do not replace it with `Vgas**2`. |
| B06 | **LOCKED** | Primary H I source data | The primary source is **direct radial H I surface-density profiles with provenance**. SPARC `Vgas` is not a substitute for `Sigma_HI(R)`. |
| B07 | **LOCKED** | Stationary memory time | `tau_A` is not inferable from the stationary `m=0` problem and must not be fit from the stationary sample as if it were independently constrained. |
| B08 | **LOCKED** | Persistence calibration | `L_A` and `\mathcal C_A` remain locked until the radial H I/source-profile package is complete, validated, and frozen. |
| B09 | **FROZEN** | Blind-test discipline | No blind refit, blind-informed selection, parameter rescue, or source-profile rule change. Source availability does not change a galaxy's frozen calibration/blind role. |
| B10 | **LOCKED** | Public/private provenance | Publicly redistributable products may be archived with provenance. Restricted/private profiles must not be redistributed without authorization. |
| B11 | **LOCKED** | Milky Way stop rules | No repeated post-hoc threshold/sign/kernel/subset mining on failed proxy families; no use of present mono-age density as if it were a formation profile; no fitting kernel lifetimes to the existing pulsar sample after seeing the result. |

---

## 4. Achievement ledger

### A01 — Repository and reproducibility infrastructure
**Status: COMPLETE**

The repository now contains reproducible scripts, GitHub Actions workflows, archived outputs, provenance tables, validation documents, frozen stationary data, manuscript-method artifacts, and Milky Way staged analyses. The project is no longer dependent on an undocumented local analysis path.

### A02 — Stationary observational sample freeze
**Status: FROZEN / COMPLETE**

The stationary SPARC observational master is frozen at **149 galaxies / 3,152 radial measurements** with documented quality and inclination cuts, signed gas preservation, duplicate checks, and no use of persistence parameters or model predictions in constructing the sample.

Canonical artifact: `data/stationary/frozen/STATIONARY_OBSERVATIONAL_FREEZE_V1.md`.

### A03 — Stationary calibration/blind split freeze
**Status: FROZEN / COMPLETE**

The canonical split is **104 calibration / 45 blind** galaxies. Assignment is deterministic from the galaxy name using the frozen hash rule and was performed before source-profile fitting or persistence-parameter evaluation.

Canonical artifact: `validation/stationary/STATIONARY_SPLIT_FREEZE_V1.md`.

**Historical note:** an earlier 124/25 train/blind division was used during operator-reconstruction/exploratory audit work. It is retained only as historical diagnostic work and is **not** the Paper I canonical split.

### A04 — Operator reconstruction audit and method clarification
**Status: COMPLETE**

An early reconstruction audit established that the advertised persistence operator could not be uniquely reconstructed from the manuscript description alone without explicit choices for items such as projector definitions, normalization, stationary temporal treatment, boundary handling, and parameterization. Literal/scalar analogue reconstructions did not provide a satisfactory blind result and exposed non-identifiability.

This directly motivated the explicit Paper I stationary method, source definition, numerical procedure, frozen boundaries, and calibration/blind protocol now present in the repository. The lesson is retained: **do not infer missing operator choices after seeing the data.**

### A05 — Stationary source-basis machinery and operator guards
**Status: COMPLETE**

The source-reconstruction machinery defines the baryonic source basis, preserves signed gas, separates the target observable from the model source velocity, and keeps stellar mass-to-light contributions in a form suitable for declared nuisance treatment. Reproducible builders/workflows and validation guards are present.

Canonical area: `data/stationary/source_reconstruction/` and associated stationary scripts/workflows.

### A06 — H I provenance audit and direct-profile policy
**Status: COMPLETE as policy/inventory; profile freeze still IN PROGRESS**

The project established that public SPARC mass-model tables do **not** contain the required radial H I surface-density profiles and that `Vgas(R)` cannot be treated as `Sigma_HI(R)`. The primary route is therefore direct radial H I profiles from public source papers/data with explicit provenance.

A provenance inventory exists at `validation/stationary/stationary_hi_profile_provenance_v1.csv`.

Four frozen-sample systems were identified as unresolved in the direct-profile route at the current audit boundary:

- D564-8
- D631-7
- NGC4138
- NGC5907

If they remain unresolved, the direct-profile target is **145 galaxies**, preserving the frozen roles: **101 calibration + 44 blind** among the directly profiled subset. Their absence must not be used to reshuffle the frozen split.

### A07 — Appendix I stationary build protocol
**Status: COMPLETE as protocol/build-status document**

The stationary Appendix I build protocol records the frozen master, split, source conventions, missing-profile handling, source-basis builder, and the remaining pre-`L_A`/`\mathcal C_A` gates.

Canonical artifact: `validation/stationary/APPENDIX_I_BUILD_STATUS_V1.md`.

### A08 — Milky Way Stages 1–3
**Status: COMPLETE / ARCHIVED**

The initial Milky Way staged diagnostics, workflows, and outputs are archived in the repository and established the foundation for the later history/force/source-history branches. They are retained as completed stages rather than rerun opportunistically when a later test is null.

### A09 — Milky Way Stage 4: migration/history proxy replication
**Status: COMPLETE**

Exploratory migration correlations seen under one modeling choice did **not** survive changes of Galactic potential/tracer/grid and therefore were not accepted as evidence for persistence. The robust feature remained the baryonic gravitational deficit; age by itself was not a useful explanatory variable and the migration proxy family was unstable.

**Decision:** stop significance-mining the same migration-proxy data. Move to a stronger force observable or genuinely time-resolved source history.

Canonical artifact: `data/persistence_history/milky_way_stage4_history_verdict.md`.

### A10 — Milky Way Stage 5: Jeans/history tests
**Status: COMPLETE**

The Jeans-based screens did not produce a stable history variable. The mixed Milky Way Mapper sample failed homogeneity sanity checks; more homogeneous cohorts were underpowered or coverage-limited. The baryonic deficit remained, but there was no robust accepted persistence-history predictor.

**Decision:** no further migration threshold/bin/grid scanning on the same family.

Canonical artifact: `data/persistence_history/milky_way_stage5_force_verdict.md`.

### A11 — Milky Way Stage 6: direct pulsar acceleration test
**Status: COMPLETE**

The analysis moved to direct pulsar accelerations. A baryons-only residual remained positive in the conservative sample, but the proposed static local source-displacement predictor failed independent replication on the expanded Donlon sample.

Frozen mapping used in the comparison:

- `X_MWM = -x_Moran`
- `Y_MWM = +y_Moran`
- `Z_MWM = +z_Moran`

The independent new-system replication did not recover the predicted sign (primary 1.0-kpc new-system result `rho = +0.1923`, one-sided `p = 0.7014`; 1.5-kpc robustness `rho = +0.0498`, `p = 0.3000`).

**Verdict:** the **static local `R_now - Rbirth_proxy` predictor is rejected**. This is not treated as falsification of the entire hereditary framework; it specifically redirects work to the source-history side rather than allowing residual tuning.

Canonical artifact: `data/persistence_history/milky_way_stage6_direct_acceleration_verdict.md`.

### A12 — Milky Way Stage 7: source-history boundary
**Status: COMPLETE**

The project deliberately changed the source observable instead of tuning the residual model. Public Ratcliffe 2026 summary products provide age/time information but not the machine-readable `R_birth x lookback-time` mass/SFR grid and orbit weights needed for the full source-history operator. Frankel migration products constrain statistical migration/size evolution but are not a complete whole-Milky-Way source history.

A minimum-information reconstruction using `Mstar(t)` and birth effective radius demonstrated the limitation: of the reconstructed intervals, one interval required a negative inner component, with a sign change near `R ~ 2.08 kpc` and a non-negligible negative-mass contribution. This showed that aggregate size/mass summaries cannot simply be promoted to the required physical formation-history field.

**Verdict:** the public-data Milky Way branch is **source-history limited**, not merely force-residual limited.

Canonical artifact: `data/persistence_history/milky_way_stage7_source_history_boundary.md`.

### A13 — Milky Way Stage 8: age-dependent persistence validation pilot
**Status: COMPLETE (PR #2; not merged to `main`)**

Draft PR #2, **“Fix DistMass asymmetric AGE_ERR parsing for Stage 8,”** on branch `work` fixes the DistMass age-error parser so asymmetric uncertainties are reduced conservatively to one scalar uncertainty using the larger absolute side while retaining legacy behavior.

The Stage 8A GitHub Actions workflow completed successfully on commit `ea321e4834d361686cf1232e71520c9d53e1408e`.

The frozen old/young pilot did **not** show a statistically significant age-linked difference in the persistence-timescale statistic at the current sample size. Recorded pilot summary:

- primary `tau_int_old = 4.2763`
- primary `tau_int_young = 3.5118`
- `Delta tau_int = 0.7645`
- two-sided bootstrap `p = 0.3173`
- young-variability robustness `p = 0.331`
- global-control `p = 0.3535`

**Allowed manuscript interpretation:** validation pilot; **no significant age-linked signal at current sample size**. Do not promote this null pilot to evidence for or against the full stationary SPARC operator.

**Repository hygiene item:** review/merge PR #2 separately. Its merge must not alter the stationary H I/profile lock or blind protocol.

### A14 — Manuscript/method scaffolding
**Status: COMPLETE as current working manuscript infrastructure; paper remains IN PROGRESS**

Current manuscript-method and Appendix artifacts are present in the repository, including the full-revision and curvature-interaction update files and the compact Appendix I drop-in. They document the increasingly explicit distinction between hereditary reorganization, phenomenological test construction, source definitions, calibration parameters, and blind validation.

No final Paper I empirical conclusion should be written until the stationary source profile is frozen, calibration is completed on the 104-galaxy set, and the 45-galaxy blind evaluation is performed without refitting.

---

## 5. Current live branch — stationary radial H I/source-profile freeze

**Current gate:** complete the radial H I profile/source-profile freeze for the stationary calibration program.  
**`L_A` and `\mathcal C_A`: LOCKED.**

The active acquisition/normalization queue carried forward from the 2026-08-09 through 2026-08-11 work is:

| Order | Status | Work item | Completion condition |
|---:|---|---|---|
| 1 | **IN PROGRESS** | Correct **Côté 2000 three-profile family** | Recover the correct three radial H I profiles, map them unambiguously to frozen-sample galaxies, preserve source provenance, digitization/units/radius conventions, and pass basic profile QC. |
| 2 | **NEXT** | **van Zee six-profile family** | Recover and normalize the six-profile family with equivalent provenance/QC. |
| 3 | **NEXT** | **Begum/Chengalur** family and remaining public blocks | Exhaust public direct-profile routes before considering any private-data request. |
| 4 | **NEXT** | Full provenance/normalization audit | Reconcile every acquired direct profile against the frozen 149-galaxy membership and frozen 104/45 roles; document source, units, radius definition, inclination/distance assumptions where relevant, interpolation domain, and missingness. |
| 5 | **NEXT** | Build `stationary_hi_profiles_v1.csv` | One normalized direct-profile product with provenance-preserving identifiers and no blind-informed fitting choices. |
| 6 | **NEXT** | Build `stationary_source_profiles_v1.csv` | Combine frozen stellar basis + normalized direct H I source profiles under the locked source conventions. |
| 7 | **NEXT** | Direct-profile interpolation/coverage QC | Validate radial coverage, interpolation, units, duplicate handling, extrapolation/taper rules, and source consistency before any persistence fit. |
| 8 | **NEXT** | Resolved-profile validation report | Demonstrate that the reconstruction/source machinery behaves as predeclared on the resolved-profile subset without inspecting persistence success on the blind sample. |
| 9 | **BLOCKED until 1–8 complete** | Write `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` | Record hashes, profile membership, exclusions, provenance, QC results, interpolation/extrapolation rules, and source-builder version. This is the gate that closes source construction. |
| 10 | **LOCKED until source freeze** | Calibrate `L_A` and `\mathcal C_A` | Calibration set only: 104 frozen-role galaxies, or the documented directly profiled calibration subset if unresolved profiles remain. No blind information. |
| 11 | **LOCKED until calibration/model freeze** | Freeze final stationary model | Freeze parameters, nuisance handling, solver rules, convergence/failure rules, likelihood/scoring definition, and exclusions before blind inspection. |
| 12 | **LOCKED final test** | Evaluate the 45-galaxy blind set | Run the pre-frozen evaluation exactly as declared, with **no refit or rule change after seeing blind outcomes**. |

### Current H I gate products

The Appendix I build status requires the following package before persistence calibration:

1. `stationary_hi_profile_provenance_v1.csv` — **EXISTS; continue updating only under provenance rules until source freeze**.
2. `stationary_hi_profiles_v1.csv` — **NOT YET FROZEN/COMPLETE**.
3. `stationary_source_profiles_v1.csv` — **NOT YET FROZEN/COMPLETE**.
4. Direct-profile interpolation/coverage QC — **NOT YET COMPLETE**.
5. Resolved-profile validation report — **NOT YET COMPLETE**.
6. `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` — **NOT YET CREATED/FROZEN**.

**Hard rule:** no `L_A`/`\mathcal C_A` persistence fitting until all required source-profile products are complete and the source-profile freeze is committed.

---

## 6. Public-data-first / private-request rule

The project will exhaust public archival, paper-table, machine-readable supplement, repository, and defensible digitization routes before requesting nonpublic profile data from an author.

A private request is justified only when:

1. the exact missing product is identified;
2. public and archival routes have been exhausted;
3. the request cannot be avoided by a legitimate public source;
4. the requested data can be used under clear provenance/redistribution terms; and
5. the request does not create a blind-selection loophole.

If private data are eventually required, the request should be narrow, reproducible, and made only after the public search is documented. Restricted data must not be published without permission.

---

## 7. Durable-state reconciliation as of 2026-08-12

### Durable on `main`

- Stationary observational master freeze.
- Canonical 104/45 split freeze.
- Source-basis machinery and stationary protocol/validation documents.
- H I provenance inventory and direct-profile policy.
- Milky Way staged scientific record through Stage 7.
- Current manuscript/method scaffolding through the existing `main`-branch revisions.

### Durable in GitHub but not merged to `main`

- **Stage 8A** parser fix, tests/workflow, and age-dependent validation pilot in draft PR #2 on branch `work`; workflow completed successfully.

### Current work carried forward from project/chat and made durable by this ledger

- Radial H I acquisition/source-profile freeze is the live stationary branch.
- The immediate order is: **Côté 2000 three-profile family -> van Zee six-profile family -> Begum/Chengalur -> remaining public blocks -> normalization/QC -> source-profile freeze**.
- `L_A` and `\mathcal C_A` remain locked throughout this work.

### Not yet complete

- Complete normalized radial H I profile file for the stationary sample.
- Complete stationary source-profile file.
- Final direct-profile interpolation/coverage QC.
- Resolved-profile validation report.
- `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md`.
- Stationary `L_A`/`\mathcal C_A` calibration.
- Frozen final stationary model.
- Final 45-galaxy blind evaluation.
- Final Paper I empirical conclusion.

---

## 8. Decision register — do not reopen without new evidence

| ID | Decision | Reason |
|---|---|---|
| D01 | **104/45 is the canonical stationary split.** | It is the frozen pre-source-profile assignment. The earlier 124/25 division was exploratory and is superseded. |
| D02 | **Direct radial H I surface-density profiles are the primary gas-source route.** | `Vgas` does not contain the information required for `Sigma_HI(R)`. |
| D03 | **The failed Stage 6 static displacement proxy is not to be rescued by tuning.** | It failed the frozen independent replication sign test; work moved to better source-history observables. |
| D04 | **Aggregate Galactic size/mass evolution is not a substitute for a full radial formation/SFH field.** | Stage 7 minimum-information reconstruction exposed an unphysical/negative interval and source non-uniqueness. |
| D05 | **Stage 8 is a validation pilot with a null significance result at current sample size.** | Preserve the result; do not reinterpret it as a successful age detection or full-framework falsification. |
| D06 | **`tau_A` is not a stationary `m=0` fit parameter.** | The stationary problem does not independently determine the memory timescale. |
| D07 | **`L_A` and `\mathcal C_A` stay locked until the source-profile freeze.** | Prevents the source reconstruction from being selected or tuned to improve persistence fits. |
| D08 | **Blind roles never change because a profile is missing or later recovered.** | Avoids a data-availability path to blind-set selection bias. |
| D09 | **Exhaust public mechanisms before requesting data privately.** | Maximizes reproducibility and permits publication of the reconstructed public dataset where licensing permits. |

---

## 9. Immediate next actions

Scientific work should resume in this order unless new evidence changes the dependency structure:

1. Finish the **correct Côté 2000 three-profile family**.
2. Process the **van Zee six-profile family**.
3. Process **Begum/Chengalur** and the remaining public direct-profile blocks.
4. Reconcile the full H I provenance table against the frozen 149-galaxy master and 104/45 roles.
5. Build and QC `stationary_hi_profiles_v1.csv`.
6. Build and QC `stationary_source_profiles_v1.csv` under the locked source rules.
7. Complete interpolation/coverage QC and the resolved-profile validation report.
8. Create and commit `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` with hashes and exact membership.
9. **Only then** unlock calibration of `L_A` and `\mathcal C_A` on the calibration set.
10. Freeze the final operator/model/nuisance/solver/scoring specification.
11. Run the final 45-galaxy blind evaluation without refitting.
12. Update the manuscript with the empirical outcome, including null or negative results if that is what the frozen test returns.

Independent repository hygiene item: review and merge Stage 8 draft PR #2 when appropriate; this must not interrupt or relax the stationary source-profile lock.

---

## 10. Cross-session operating rule

At the beginning of a new Paper I work session:

1. Read `PROJECT_LEDGER.md`.
2. Inspect the latest GitHub repository/PR state rather than relying only on chat memory.
3. Read the frozen artifact governing the live branch.
4. Resume the first **IN PROGRESS** item unless explicitly redirected.
5. Do not reinterpret **FROZEN**, **LOCKED**, **COMPLETE**, or **SUPERSEDED** items without concrete new evidence and an explicit recorded decision.

At the end of a significant work block:

1. Commit durable data/code/provenance/validation artifacts where appropriate.
2. Update this ledger's status and exact next action.
3. Record any new blocker, null result, failed route, or decision so it is not rediscovered repeatedly.
4. Preserve unsuccessful tests when scientifically informative; do not silently replace them with a more favorable specification.
5. If work exists only in chat, mark it explicitly as non-durable until it is committed or recorded here.

---

## 11. Current resume point

**Resume here:** radial H I/source-profile freeze -> **correct Côté 2000 three-profile family**.  
Then: **van Zee six-profile family -> Begum/Chengalur -> remaining public blocks**.  
Throughout: **`L_A` and `\mathcal C_A` remain locked.**
