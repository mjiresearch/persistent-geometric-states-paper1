# Persistence Framework — Paper I Project Ledger

**Canonical cross-session checkpoint**  
**Repository:** `mjiresearch/persistent-geometric-states-paper1`  
**Established:** 2026-08-12  
**Last reconciled:** 2026-08-12 — stationary radial H I galaxy-database build

> **Authority rule:** this ledger summarizes project state. Frozen protocol/data/provenance/validation artifacts remain authoritative if any discrepancy is found.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| **FROZEN** | Predeclared boundary; do not change after the fact. |
| **COMPLETE** | Finished and durably represented in GitHub. |
| **COMPLETE (PR)** | Finished/validated on a GitHub PR/branch but not merged to `main`. |
| **RECOVER** | Scientific choice/result was completed previously but the durable artifact still must be restored to canonical GitHub. |
| **IN PROGRESS** | Current live work. |
| **NEXT** | Immediate queued work. |
| **LOCKED** | Must not be fit/opened/evaluated until prerequisites are met. |
| **BLOCKED** | Waiting on a required source/prerequisite. |
| **SUPERSEDED** | Historical work retained for auditability but no longer canonical. |

---

## 2. North star

Paper I is an **independent empirical test of the Persistence Framework** under a predeclared calibration/blind-validation discipline. The working hypothesis is that a hereditary/persistent geometric response associated with prior baryonic stress-energy and mass-current history may contribute to the gravitational field normally represented phenomenologically by a dark-matter halo. The paper must test this rather than assume it.

Current posture:

- No final stationary SPARC empirical conclusion exists yet.
- Milky Way work establishes a robust baryons-only gravitational deficit in the tested observables, but historical proxies tested through Stage 8 have not yet produced accepted evidence that persistence explains it.
- Null/negative intermediate tests are preserved and are not repaired by post-hoc tuning.
- The stationary baryonic source/profile construction must be complete and frozen **before** `L_A` and `\mathcal C_A` are calibrated.
- The blind sample is inspected only under the final frozen model; there is no blind refit.

---

## 3. Frozen / locked boundaries

| ID | Status | Boundary |
|---|---|---|
| B01 | **FROZEN** | Stationary observational master: `data/stationary/frozen/stationary_master_v1.csv`, **149 galaxies / 3,152 radial measurements**, SHA-256 `254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f`; `Q <= 2`, inclination `>=30 deg`, >=5 valid radial points. |
| B02 | **FROZEN** | Canonical split: **104 calibration / 45 blind**. Earlier 124/25 exploratory split is **SUPERSEDED**. |
| B03 | **LOCKED** | Stationary source current: `J(R)=Sigma_b(R)V(R)` using self-consistent model velocity. `Vobs` is target data, not source velocity. |
| B04 | **LOCKED** | Stellar basis: `Sigma_disk=Upsilon_d SBdisk`, `Sigma_bulge=Upsilon_b SBbulge`; retain unit-M/L basis and declared nuisance treatment. |
| B05 | **LOCKED** | Signed gas gravitational contribution: use `Vgas*abs(Vgas)`, not `Vgas**2`. |
| B06 | **LOCKED** | Primary gas-source route: independently sourced **direct radial H I surface-density profiles** with provenance. SPARC `Vgas(R)` is not `Sigma_HI(R)`. |
| B07 | **LOCKED** | `tau_A` is not independently inferable from stationary `m=0` and is not a stationary-fit parameter. |
| B08 | **LOCKED** | **`L_A` and `\mathcal C_A` remain locked until the radial H I/source-profile package is complete, validated and frozen.** |
| B09 | **FROZEN** | No blind refit, blind-informed source selection, parameter rescue, or split reshuffling due to profile availability. |
| B10 | **LOCKED** | Public-data-first provenance/redistribution rule. Restricted/private files are not redistributed without authorization. |
| B11 | **LOCKED** | Milky Way stop rules: no repeated post-hoc threshold/sign/kernel/subset mining; present mono-age density is not a formation profile; do not fit kernel lifetime after seeing residual results. |

---

## 4. Achievement ledger

| ID | Status | Achievement / scientific consequence |
|---|---|---|
| A01 | **COMPLETE** | Reproducible GitHub infrastructure: scripts, workflows, frozen data, provenance, validation and manuscript-method artifacts. |
| A02 | **FROZEN / COMPLETE** | Stationary observational sample frozen at **149 galaxies / 3,152 measurements**. |
| A03 | **FROZEN / COMPLETE** | Canonical **104 calibration / 45 blind** split frozen independently of persistence results. |
| A04 | **COMPLETE** | Early operator reconstruction audit exposed missing executable choices/non-identifiability and motivated explicit source/numerical/blind rules. |
| A05 | **COMPLETE** | Stationary source-basis machinery established: unit-M/L stellar basis, signed gas guard, model-velocity source rule. |
| A06 | **COMPLETE as policy/inventory** | Direct-H I profile policy/provenance inventory established. Public SPARC mass-model tables do not supply the required radial `Sigma_HI`. |
| A07 | **COMPLETE** | Appendix I stationary build protocol established. |
| A08 | **COMPLETE / ARCHIVED** | Milky Way Stages 1–3 completed and archived. |
| A09 | **COMPLETE** | Stage 4 migration/history proxy correlations did not survive robustness tests; stop significance-mining that proxy family. |
| A10 | **COMPLETE** | Stage 5 Jeans/history tests yielded no stable accepted history predictor; no further threshold/bin/grid scanning of same family. |
| A11 | **COMPLETE** | Stage 6 direct pulsar acceleration: baryonic deficit persists, but static local `R_now-Rbirth_proxy` failed independent replication; predictor rejected without tuning rescue. |
| A12 | **COMPLETE** | Stage 7 source-history boundary: public aggregate Galactic mass/size history cannot substitute for a full radial formation/SFH field. |
| A13 | **COMPLETE (PR)** | Stage 8 asymmetric `AGE_ERR` fix and age-dependent validation pilot completed; no significant old/young signal at current sample size (`Delta tau_int=0.7645`, bootstrap `p=0.3173`). Merge hygiene remains separate. |
| A14 | **COMPLETE as infrastructure** | Current manuscript/method scaffolding records source construction, calibration and blind-test separation. |
| A15 | **RECOVER** | NGC1090 scientific extraction choice settled: original `fig2.eps`, filled-circle average series. Exact extracted coordinate/QC artifact must be restored to GitHub before final source freeze; do not redo source selection. |
| A16 | **COMPLETE source/convention audit** | Côté et al. (2000) frozen family = **UGCA442 (blind), DDO161 (calibration), ESO444-G084 (blind)**. Figure 3 direct gas profiles already include 4/3 helium; numerical curves remain pending. |
| A17 | **COMPLETE crossmatch audit** | van Zee et al. (1997) Paper I overlap is **five**, not six: UGC00191, UGC00891, UGC05716, UGC05764, UGC11820. “Six-profile” shorthand refers to source paper's six LSBDGs. Numerical primary profiles remain pending. |
| A18 | **COMPLETE correction** | `UGC05829` is **not** van Zee 1997; route it to **Taylor et al. (1994)**. False van-Zee attribution removed from durable source audit. |
| A19 | **COMPLETE / SOURCE DATA RECOVERED** | **KK98-251** (calibration) has an exact public analytic raw-H I radial profile from Begum & Chengalur: `Sigma_HI(r)=7.8 exp[-(r-19.2")^2/(2(34.2")^2)] Msun pc^-2`, with quoted parameter uncertainties. No graph digitization required for the primary analytic representation. |
| A20 | **COMPLETE source/convention audit** | **NGC3741** (calibration) direct radial gas profile identified in Begum et al. Figure 5; published profile already includes **x1.3 helium**, so never double-correct. Numerical curve recovery remains pending. |
| A21 | **PUBLIC ROUTE IDENTIFIED** | **CamB** (calibration) dedicated Begum, Chengalur & Hopp GMRT H I paper recovered publicly; exact radial surface-density representation/conventions still under one-pass verification before promotion. |

---

## 5. Stationary H I galaxy-database state

### Known four systems absent from the target 169-profile compilation at the frozen audit boundary

- D564-8 — calibration
- D631-7 — calibration
- NGC4138 — blind
- NGC5907 — calibration

If no independent direct public profile is recovered for them before source freeze, the directly profiled primary subset is 145 galaxies = 101 calibration + 44 blind. Frozen roles never change.

### Source-family acquisition matrix

| Source block | Frozen targets established | Durable state | Next action |
|---|---|---|---|
| NGC1090 | NGC1090 — calibration | scientific extraction choice complete; artifact missing | **RECOVER before final freeze**: exact `fig2.eps` filled-circle coordinates + QC |
| Côté 2000 | UGCA442 — blind; DDO161 — calibration; ESO444-G084 — blind | source/crossmatch/conventions complete | publication-grade Figure 3 numerical extraction still pending; do one defensible public recovery pass, then park rather than loop |
| van Zee 1997 | UGC00191 — calibration; UGC00891 — calibration; UGC05716 — blind; UGC05764 — calibration; UGC11820 — blind | exact crossmatch/alias audit complete | recover original profile figure/table quantities/conventions and numbers; no invented sixth overlap |
| Taylor 1994 | UGC05829 — blind | correct source family identified | acquire its direct public profile under Taylor source block |
| Begum/Chengalur — KK98-251 | KK98-251 — calibration | **analytic raw-H I profile recovered** | retain native angular analytic model; normalize/resample only under later global rules |
| Begum/Chengalur — NGC3741 | NGC3741 — calibration | source/profile/helium convention complete | recover Figure 5 numerical curve/vector/data once; park if unavailable |
| Begum/Chengalur — CamB | CamB — calibration | dedicated public primary H I paper identified | verify exact radial H I surface-density representation/helium/deprojection once; promote only if defensible |
| Remaining public blocks | pending | **NEXT** | continue literature/archive/supplement/vector sweep without reopening completed source-family decisions |

Canonical source-audit artifacts now include:

- `validation/stationary/COTE2000_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/cote2000_profile_source_audit_v1.csv`
- `validation/stationary/VANZEE1997_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/vanzee1997_profile_source_audit_v1.csv`
- `validation/stationary/BEGUM_CHENGALUR_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/begum_chengalur_profile_source_audit_v1.csv`
- `data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv`
- `data/stationary/source_reconstruction/stationary_hi_profile_provenance_v1.csv`

---

## 6. Recovered analytic source profile — KK98-251

Primary source: Begum & Chengalur, A&A 424, 509–517, DOI `10.1051/0004-6361:20041210`, arXiv `astro-ph/0406211`.

Source equation:

`Sigma_HI(r) = Sigma0 exp[-(r-c)^2/(2 r0^2)]`

with:

- `Sigma0 = 7.8 +/- 0.1 Msun pc^-2`
- `r0 = 34.2 +/- 0.7 arcsec`
- `c = 19.2 +/- 0.8 arcsec`
- source distance = 5.6 Mpc
- frozen distance = 6.8 Mpc
- source H I morphology inclination = 62 +/- 5 deg
- frozen inclination = 59 deg
- raw profile quantity = **H I only**; paper applies helium x1.4 separately in gas mass modelling

Frozen-distance QC conversion only:

- `1 arcsec = 0.0329673 kpc`
- `r0 = 1.12748 kpc`
- `c = 0.632972 kpc`

Native angular parameters remain the provenance authority. No global radius resampling or inclination-amplitude normalization is applied until those common rules are frozen.

---

## 7. H I/source-profile gate products

| Product | Status |
|---|---|
| `stationary_hi_profile_provenance_v1.csv` | **EXISTS; global reconciliation still pending** |
| Côté source audit | **COMPLETE; numbers pending** |
| van Zee source audit | **COMPLETE; numbers/conventions pending** |
| Begum/Chengalur source audit | **IN PROGRESS; KK98-251 analytic profile recovered** |
| NGC1090 extraction artifact | **RECOVER** |
| `stationary_hi_profiles_v1.csv` | **NOT YET COMPLETE/FROZEN** |
| `stationary_source_profiles_v1.csv` | **NOT YET COMPLETE/FROZEN** |
| direct-profile interpolation/coverage QC | **NOT YET COMPLETE** |
| resolved-profile validation report | **NOT YET COMPLETE** |
| `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` | **NOT YET CREATED/FROZEN** |
| `L_A`, `\mathcal C_A` calibration | **LOCKED** |
| final 45-galaxy blind evaluation | **LOCKED** |

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
| D10 | NGC1090 source/extraction choice is settled: original `fig2.eps`, filled-circle average series. Recover artifact; do not redo choice. |
| D11 | Côté family = UGCA442, DDO161, ESO444-G084. Figure 3 already contains a 4/3 helium correction; never apply helium twice. |
| D12 | van Zee 1997 Paper I overlap = five galaxies. Old “six-profile” wording is source-subsample shorthand, not frozen-overlap count. |
| D13 | UGC05829 belongs to Taylor et al. (1994), not van Zee 1997. |
| D14 | KK98-251 analytic equation is raw H I. Preserve native angular model; apply helium only once downstream under the global convention. |
| D15 | NGC3741 Figure 5 already includes helium x1.3. If raw H I is needed, divide the published gas profile by 1.3 while retaining the source values unchanged. |
| D16 | When a public numerical route stalls, record `numeric_pending` and continue to the next source block rather than repeatedly searching the same inaccessible artifact. |

---

## 9. Public-data-first rule

Before requesting nonpublic H I profile data:

1. identify the exact missing product;
2. exhaust public paper tables, electronic supplements, archives, author/institution repositories and defensible vector/figure digitization;
3. document failed public routes;
4. preserve frozen calibration/blind roles regardless of availability; and
5. follow redistribution/citation terms for any private data eventually supplied.

A private-data request is a last acquisition step, not a shortcut around public reproducibility.

---

## 10. Current live queue

1. **IN PROGRESS — Begum/Chengalur:** verify CamB radial H I representation and make one numerical-recovery pass for NGC3741 Figure 5.
2. **NEXT — Taylor 1994:** recover the correct public direct profile for UGC05829.
3. **NEXT — remaining public source blocks:** continue systematic source-family acquisition/crossmatch.
4. **PENDING NUMERICAL:** Côté three curves and van Zee five curves; revisit only through a new defensible data/vector route, not repeated low-fidelity searches.
5. **RECOVER before source freeze:** NGC1090 `fig2.eps` filled-circle extraction/QC artifact.
6. Reconcile all public source audits into the master provenance inventory.
7. Build `stationary_hi_profiles_v1.csv`.
8. Build `stationary_source_profiles_v1.csv` under locked source rules.
9. Freeze common radius conversion, inclination/deprojection handling, helium convention, interpolation/extrapolation/taper and duplicate/coverage rules.
10. Complete resolved-profile validation report.
11. Create `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` with hashes and exact membership.
12. **Only then** unlock `L_A` and `\mathcal C_A` calibration on calibration galaxies.
13. Freeze final model/nuisance/solver/scoring specification.
14. Run the frozen 45-galaxy blind evaluation once, with no refit.

---

## 11. Cross-session operating rule

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

**Current resume point:** Begum/Chengalur public H I block — CamB profile verification + NGC3741 numerical recovery pass. `L_A` and `\mathcal C_A` remain locked.
