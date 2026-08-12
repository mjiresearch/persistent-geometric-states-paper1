# Persistence Framework — Paper I Project Ledger

**Canonical cross-session checkpoint**  
**Repository:** `mjiresearch/persistent-geometric-states-paper1`  
**Established:** 2026-08-12  
**Last reconciled:** 2026-08-12 — stationary H I galaxy-database branch

> **Authority rule:** this ledger summarizes project state. Frozen protocol/data/provenance/validation artifacts remain authoritative if any discrepancy is found.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| **FROZEN** | Predeclared boundary; do not change after the fact. |
| **COMPLETE** | Finished and durably represented in GitHub. |
| **COMPLETE (PR)** | Finished/validated on a GitHub PR/branch but not merged to `main`. |
| **CHAT-COMPLETE / RECOVER** | Prior session completed the work, but the claimed artifact is not presently found on canonical GitHub and must be recovered/recreated before relying on it as durable. |
| **IN PROGRESS** | Current live work. |
| **NEXT** | Immediate queued work. |
| **LOCKED** | Must not be fit/opened/evaluated until prerequisites are met. |
| **BLOCKED** | Waiting on a required source/prerequisite. |
| **SUPERSEDED** | Historical work retained for auditability but no longer canonical. |

---

## 2. North star

Paper I is an **independent empirical test of the Persistence Framework** under a predeclared calibration/blind-validation discipline. The working hypothesis is that a hereditary/persistent geometric response associated with prior baryonic stress-energy and mass-current history may contribute to the field normally represented phenomenologically by a dark-matter halo. The paper must test this rather than assume it.

Current posture:

- No final stationary SPARC empirical conclusion exists yet.
- Milky Way work establishes a robust baryons-only gravitational deficit in the tested observables, but the historical proxies tested through Stage 8 have not yet produced accepted evidence that persistence explains it.
- Null/negative results are preserved; failed proxies are not repaired by post-hoc tuning.
- The stationary baryonic source/profile construction must be complete and frozen **before** `L_A` and `\mathcal C_A` are calibrated.
- The blind sample is inspected only under the final frozen model; there is no blind refit.

---

## 3. Frozen / locked boundaries

| ID | Status | Boundary |
|---|---|---|
| B01 | **FROZEN** | Stationary observational master: `data/stationary/frozen/stationary_master_v1.csv`, **149 galaxies / 3,152 radial measurements**, SHA-256 `254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f`; `Q <= 2`, inclination `>=30 deg`, >=5 valid radial points. |
| B02 | **FROZEN** | Canonical split: **104 calibration / 45 blind**, deterministic SHA-256 assignment. The earlier 124/25 exploratory split is **SUPERSEDED**. |
| B03 | **LOCKED** | Stationary source current: `J(R)=Sigma_b(R)V(R)` using the self-consistent model velocity. `Vobs` is target data, not the source velocity. |
| B04 | **LOCKED** | Stellar basis: `Sigma_disk=Upsilon_d SBdisk`, `Sigma_bulge=Upsilon_b SBbulge`; retain unit-M/L basis and declared nuisance treatment. |
| B05 | **LOCKED** | Signed gas gravitational contribution: use `Vgas*abs(Vgas)`, never silently replace with `Vgas**2`. |
| B06 | **LOCKED** | Primary gas-source route: independently sourced **direct radial H I surface-density profiles** with provenance. SPARC `Vgas(R)` is not `Sigma_HI(R)`. |
| B07 | **LOCKED** | `tau_A` is not independently inferable from the stationary `m=0` problem and is not a stationary-fit parameter. |
| B08 | **LOCKED** | **`L_A` and `\mathcal C_A` remain locked until the radial H I/source-profile package is complete, validated and frozen.** |
| B09 | **FROZEN** | No blind refit, blind-informed source selection, parameter rescue, or split reshuffling due to profile availability. |
| B10 | **LOCKED** | Public-data-first provenance and redistribution policy. Restricted/private source files are not redistributed without authorization. |
| B11 | **LOCKED** | Milky Way stop rules: no repeated post-hoc threshold/sign/kernel/subset mining; present mono-age density is not a formation profile; do not fit kernel lifetime to a sample after seeing its residual result. |

---

## 4. Achievement ledger

### A01 — Reproducible repository infrastructure
**Status: COMPLETE**

Scripts, workflows, frozen data, validation records, provenance products, manuscript-method artifacts and staged Milky Way analyses are maintained in the repository.

### A02 — Stationary observational sample freeze
**Status: FROZEN / COMPLETE**

149 galaxies / 3,152 measurements with documented QC and immutable frozen membership.

Canonical artifact: `data/stationary/frozen/STATIONARY_OBSERVATIONAL_FREEZE_V1.md`.

### A03 — Calibration/blind split freeze
**Status: FROZEN / COMPLETE**

104 calibration / 45 blind. Earlier 124/25 audit split is superseded.

Canonical artifact: `validation/stationary/STATIONARY_SPLIT_FREEZE_V1.md`.

### A04 — Operator reconstruction audit
**Status: COMPLETE**

Early literal/scalar reconstruction exposed missing executable operator choices and non-identifiability. This motivated explicit source definitions, numerical rules and predeclared stationary/blind boundaries. Missing operator choices may not be filled in after seeing outcomes.

### A05 — Stationary source-basis machinery
**Status: COMPLETE**

Stellar unit-M/L basis, signed-gas guard, model-velocity source rule and associated validation machinery are established.

### A06 — Direct-H I profile policy and provenance inventory
**Status: COMPLETE as policy/inventory; profile build IN PROGRESS**

The public SPARC mass-model tables do not supply the needed azimuthally averaged radial H I surface-density profiles. The project therefore uses direct literature/archive profiles with explicit provenance.

Canonical provenance inventory:  
`data/stationary/source_reconstruction/stationary_hi_profile_provenance_v1.csv`

Current four systems known absent from the target 169-profile compilation at the frozen audit boundary:

- D564-8 — calibration
- D631-7 — calibration
- NGC4138 — blind
- NGC5907 — calibration

If unresolved, the direct-profile primary subset is 145 galaxies = 101 calibration + 44 blind, preserving the original roles.

### A07 — Appendix I stationary build protocol
**Status: COMPLETE as protocol/build-status document**

Canonical artifact: `validation/stationary/APPENDIX_I_BUILD_STATUS_V1.md`.

### A08 — Milky Way Stages 1–3
**Status: COMPLETE / ARCHIVED**

Initial diagnostics and staged workflows archived; not to be repeatedly reopened because later tests are null.

### A09 — Milky Way Stage 4 migration/history proxy replication
**Status: COMPLETE**

Exploratory migration correlations did not survive model/tracer/grid changes. Baryonic deficit remained robust; age alone was not an accepted explanatory variable. Stop rule: do not significance-mine the same migration-proxy family.

Canonical artifact: `data/persistence_history/milky_way_stage4_history_verdict.md`.

### A10 — Milky Way Stage 5 Jeans/history tests
**Status: COMPLETE**

No stable history predictor survived the homogeneous-cohort/coverage checks. No further threshold/bin/grid scanning of this same family.

Canonical artifact: `data/persistence_history/milky_way_stage5_force_verdict.md`.

### A11 — Milky Way Stage 6 direct pulsar acceleration
**Status: COMPLETE**

A baryons-only residual remained, but the frozen static local displacement proxy failed independent replication. Primary 1.0-kpc new-system result: `rho=+0.1923`, one-sided `p=0.7014`; 1.5-kpc robustness `rho=+0.0498`, `p=0.3000`.

Verdict: reject the **static local `R_now-Rbirth_proxy` predictor**, not the entire hereditary framework.

Canonical artifact: `data/persistence_history/milky_way_stage6_direct_acceleration_verdict.md`.

### A12 — Milky Way Stage 7 source-history boundary
**Status: COMPLETE**

Public summary products do not provide the full machine-readable radial formation/SFH history needed by the source-history operator. A minimum-information mass/size reconstruction produced an unphysical negative inner component in one interval, demonstrating that aggregate mass/size evolution cannot simply be promoted to the required radial formation field.

Verdict: the public Milky Way branch is **source-history limited**.

Canonical artifact: `data/persistence_history/milky_way_stage7_source_history_boundary.md`.

### A13 — Milky Way Stage 8 age-dependent validation pilot
**Status: COMPLETE (validated work; repository merge state requires separate hygiene review)**

DistMass asymmetric `AGE_ERR` handling was corrected by reducing the two-sided uncertainty conservatively to the larger absolute side. The Stage 8A pilot completed successfully. No statistically significant old/young difference was found at the current sample size:

- `tau_int_old=4.2763`
- `tau_int_young=3.5118`
- `Delta tau_int=0.7645`
- bootstrap `p=0.3173`
- young-variability robustness `p=0.331`
- global-control `p=0.3535`

Interpretation: **validation pilot; no significant age-linked signal at current sample size**.

### A14 — Manuscript/method scaffolding
**Status: COMPLETE as current infrastructure; manuscript IN PROGRESS**

Current method/Appendix scaffolding records the separation between source construction, persistence calibration and blind validation. Final empirical claims remain gated by the stationary freeze and blind test.

### A15 — NGC1090 direct-profile extraction branch
**Status: CHAT-COMPLETE / RECOVER**

Prior project work records that the **NGC1090 extraction was completed** and that the original **`fig2.eps` vector source** was selected for numerical extraction/QC, using the **filled-circle average series** rather than a raster approximation. The prior session then moved into Côté/van Zee auditing.

However, a current repository search does not locate the claimed NGC1090 extraction artifact or a commit containing `NGC1090` / `fig2.eps`. Therefore:

- do **not** redo the scientific choice;
- do **recover/recreate and commit** the exact extracted coordinates/QC artifact before the final source-profile freeze;
- until then, count NGC1090 as a **durability gap**, not a new unresolved source-identification problem.

### A16 — Côté et al. (2000) three-profile source family
**Status: SOURCE/CONVENTION AUDIT COMPLETE; NUMERICAL DIGITIZATION IN PROGRESS**

The correct three frozen-sample overlaps are now durably identified:

| Galaxy | Frozen role | Côté source inclination | Frozen inclination |
|---|---|---:|---:|
| UGCA442 | blind | 64° | 64° |
| DDO161 | calibration | 70° | 70° |
| ESO444-G084 | blind | 32° | 32° |

Canonical audit artifacts:

- `validation/stationary/COTE2000_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/cote2000_profile_source_audit_v1.csv`

Key source conventions now frozen for ingestion:

- Côté et al. 2000 Figure 3 is a **direct radial gas-surface-density profile source**, not a `Vgas` reconstruction.
- Published Figure 3 profiles were multiplied by **4/3 for primordial helium** and deprojected by `cos(i)` in the source paper.
- Therefore the plotted source values must **not receive a second helium correction**.
- If a raw-H I intermediate is required, use `Sigma_HI = (3/4) Sigma_gas,Cote` while retaining the original plotted quantity for provenance.
- Source-paper distances (UGCA442 2.5 Mpc; DDO161 and ESO444-G084 3.5 Mpc) are stored separately from the frozen SPARC distances and must not silently replace them.
- Central source inclinations agree with the frozen inclinations for all three, so no inclination-amplitude rescaling is currently warranted.

Current numerical state: the public article/Figure 3 is identified, but publication-grade curve coordinates have **not yet been committed**. No caption/axis approximation, `Vgas` substitution or fabricated point set is permitted.

---

## 5. Current live branch — stationary radial H I galaxy database

**`L_A` and `\mathcal C_A` remain LOCKED.**

| Order | Status | Work item | Exact state / completion condition |
|---:|---|---|---|
| 0 | **RECOVER before final freeze** | NGC1090 extraction artifact | Scientific extraction choice is already settled (`fig2.eps`, filled-circle average series). Recover/recreate exact coordinates and QC artifact in GitHub; do not restart source-selection reasoning. |
| 1 | **IN PROGRESS** | Côté 2000 three-profile family | Source/crossmatch/convention audit COMPLETE for UGCA442, DDO161, ESO444-G084. Recover publication-grade numerical Figure 3 curves and commit normalized/provenance-preserving profile points. If the archival scan route does not yield sufficient fidelity, mark numerical extraction pending and proceed rather than looping. |
| 2 | **NEXT** | van Zee 1997 profile family | Audit the direct radial H I profiles in van Zee et al., AJ 113, 1618 (“A Comparative Study of Star Formation Thresholds in Gas-Rich Low Surface Brightness Dwarf Galaxies”), determine exact frozen-master overlaps and recover the six intended profile series with equivalent units/distance/inclination/helium/QC controls. |
| 3 | **NEXT** | Begum/Chengalur family | Recover exact frozen overlaps and public direct profiles with equivalent provenance/QC. |
| 4 | **NEXT** | Remaining public direct-profile blocks | Exhaust public literature/archive/supplement/vector-figure routes before any private request. |
| 5 | **NEXT** | Full provenance reconciliation | Reconcile all acquired profiles against the immutable 149-galaxy membership and 104/45 roles. |
| 6 | **NEXT** | Build `stationary_hi_profiles_v1.csv` | Normalized H I profile product with raw-source columns/conventions preserved. |
| 7 | **NEXT** | Build `stationary_source_profiles_v1.csv` | Frozen stellar basis + normalized gas profiles under locked source rules. |
| 8 | **NEXT** | Interpolation/coverage QC | Freeze units, radius conversion, interpolation, extrapolation/taper, duplicate handling and coverage rules. |
| 9 | **NEXT** | Resolved-profile validation report | Validate source machinery without persistence-success inspection of the blind set. |
| 10 | **BLOCKED until 0–9 resolved** | `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` | Record hashes, exact profile membership, exclusions, provenance and source-builder rules. |
| 11 | **LOCKED** | Calibrate `L_A`, `\mathcal C_A` | Calibration set only, after source freeze. |
| 12 | **LOCKED** | Final model freeze | Freeze nuisance/solver/scoring/convergence/failure rules before blind evaluation. |
| 13 | **LOCKED final test** | 45-galaxy blind evaluation | One pre-frozen evaluation; no refit/rule change after inspection. |

---

## 6. H I gate products

1. `data/stationary/source_reconstruction/stationary_hi_profile_provenance_v1.csv` — **EXISTS**.
2. Côté 2000 source-family audit — **EXISTS / COMPLETE**.
3. Côté numerical profile points — **PENDING**.
4. NGC1090 extraction/QC artifact — **RECOVER TO GITHUB**.
5. `stationary_hi_profiles_v1.csv` — **NOT YET COMPLETE/FROZEN**.
6. `stationary_source_profiles_v1.csv` — **NOT YET COMPLETE/FROZEN**.
7. Direct-profile interpolation/coverage QC — **NOT YET COMPLETE**.
8. Resolved-profile validation report — **NOT YET COMPLETE**.
9. `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` — **NOT YET CREATED/FROZEN**.

**Hard rule:** no `L_A` / `\mathcal C_A` evaluation before this gate closes.

---

## 7. Public-data-first rule

Before requesting nonpublic H I profile data:

1. identify the exact missing product;
2. exhaust public paper tables, electronic supplements, archives, author/institution repositories and defensible vector/figure digitization;
3. document failed public routes;
4. preserve frozen calibration/blind roles regardless of availability; and
5. follow redistribution/citation terms for any private data eventually supplied.

A private-data request is a last acquisition step, not a shortcut around public reproducibility.

---

## 8. Decision register — do not reopen without new evidence

| ID | Decision |
|---|---|
| D01 | 104/45 is the canonical stationary split; 124/25 is superseded. |
| D02 | Direct radial H I surface-density profiles are the primary gas-source route; `Vgas` is not `Sigma_HI`. |
| D03 | Stage 6 static displacement proxy is rejected and is not to be rescued by tuning. |
| D04 | Aggregate Galactic mass/size history is not a substitute for a full radial formation/SFH field. |
| D05 | Stage 8 is a null-significance validation pilot at current sample size. |
| D06 | `tau_A` is not a stationary `m=0` fit parameter. |
| D07 | `L_A` and `\mathcal C_A` stay locked until source-profile freeze. |
| D08 | Blind roles never change due to missing/recovered profiles. |
| D09 | Exhaust public mechanisms before private requests. |
| D10 | NGC1090 source/extraction choice is settled: original `fig2.eps`, filled-circle average series. Recover the artifact; do not redo the choice. |
| D11 | Côté family = UGCA442, DDO161, ESO444-G084. Figure 3 already contains a 4/3 helium correction; never apply helium twice. |

---

## 9. Cross-session operating rule

At the start of every Paper I work session:

1. read this ledger;
2. inspect current GitHub state;
3. read the frozen artifact controlling the live branch;
4. resume the first **IN PROGRESS** item without reopening settled decisions.

At every meaningful milestone:

1. commit data/code/provenance/QC artifacts;
2. update this ledger in the same session;
3. record failures/blockers/nulls as well as successes; and
4. establish the exact next resume point.

---

## 10. Current resume point

**Now:** finish the **Côté 2000 numerical profile acquisition** without looping on low-fidelity sources.  
**Then immediately:** **van Zee 1997 profile family → Begum/Chengalur → remaining public blocks**.  
**Before final source freeze:** recover/commit the already-decided **NGC1090 `fig2.eps` filled-circle extraction/QC artifact**.  
**Throughout:** **`L_A` and `\mathcal C_A` remain locked.**
