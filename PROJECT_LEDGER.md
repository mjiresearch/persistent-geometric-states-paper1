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
| **SOURCE RECOVERED** | Direct public profile/analytic representation is durably recovered; common downstream normalization may still be pending. |
| **COMPLETE (PR)** | Finished/validated on a GitHub PR/branch but not merged to `main`. |
| **RECOVER** | Scientific choice/result was completed previously but its exact durable artifact must still be restored. |
| **IN PROGRESS** | Current live work. |
| **NEXT** | Immediate queued work. |
| **LOCKED** | Must not be fit/opened/evaluated until prerequisites are met. |
| **BLOCKED** | Waiting on a required source/prerequisite. |
| **SUPERSEDED** | Historical work retained for auditability but no longer canonical. |

---

## 2. North star and current scientific posture

Paper I is an **independent empirical test of the Persistence Framework** under a predeclared calibration/blind-validation discipline. The working hypothesis is that a hereditary/persistent geometric response associated with prior baryonic stress-energy and mass-current history may contribute to the gravitational field normally represented phenomenologically by a dark-matter halo. The paper must test this rather than assume it.

Current posture:

- No final stationary SPARC empirical conclusion exists yet.
- Milky Way work establishes a robust baryons-only gravitational deficit in the tested observables, but historical proxies tested through Stage 8 have not produced accepted evidence that persistence explains it.
- Null/negative intermediate tests are preserved and are not repaired through post-hoc tuning.
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
| B11 | **LOCKED** | When a public numerical route fails at sufficient fidelity, mark it pending and move to another source block rather than repeatedly searching the same inaccessible artifact. |

---

## 4. Achievement ledger

| ID | Status | Achievement / scientific consequence |
|---|---|---|
| A01 | **COMPLETE** | Reproducible GitHub infrastructure: scripts, workflows, frozen data, provenance, validation and manuscript-method artifacts. |
| A02 | **FROZEN / COMPLETE** | Stationary observational sample frozen at **149 galaxies / 3,152 measurements**. |
| A03 | **FROZEN / COMPLETE** | Canonical **104 calibration / 45 blind** split frozen independently of persistence results. |
| A04 | **COMPLETE** | Early operator reconstruction audit exposed missing executable choices/non-identifiability and motivated explicit source/numerical/blind rules. |
| A05 | **COMPLETE** | Stationary source-basis machinery established: unit-M/L stellar basis, signed gas guard, model-velocity source rule. |
| A06 | **COMPLETE as policy/inventory** | Direct-H I profile policy/provenance inventory established. Public SPARC mass-model tables do not supply required radial `Sigma_HI`. |
| A07 | **COMPLETE** | Appendix I stationary build protocol established. |
| A08 | **COMPLETE / ARCHIVED** | Milky Way Stages 1–3 completed and archived. |
| A09 | **COMPLETE** | Stage 4 migration/history proxy correlations did not survive robustness tests; stop significance-mining that proxy family. |
| A10 | **COMPLETE** | Stage 5 Jeans/history tests yielded no stable accepted history predictor; no further threshold/bin/grid scanning of the same family. |
| A11 | **COMPLETE** | Stage 6 direct pulsar acceleration: baryonic deficit persists, but static local `R_now-Rbirth_proxy` failed independent replication; predictor rejected without tuning rescue. |
| A12 | **COMPLETE** | Stage 7 source-history boundary: public aggregate Galactic mass/size history cannot substitute for a full radial formation/SFH field. |
| A13 | **COMPLETE (PR)** | Stage 8 asymmetric `AGE_ERR` fix and age-dependent validation pilot completed; no significant old/young signal at current sample size (`Delta tau_int=0.7645`, bootstrap `p=0.3173`). |
| A14 | **COMPLETE as infrastructure** | Current manuscript/method scaffolding records source construction, calibration and blind-test separation. |
| A15 | **RECOVER** | NGC1090 source/extraction choice is settled: original `fig2.eps`, filled-circle average series. Restore exact extracted coordinates/QC artifact before final source freeze; do not redo source selection. |
| A16 | **COMPLETE source/convention audit** | Côté et al. (2000) frozen family = **UGCA442 (blind), DDO161 (calibration), ESO444-G084 (blind)**. Figure 3 direct gas profiles already include 4/3 helium; numerical curves remain pending. |
| A17 | **COMPLETE crossmatch audit** | van Zee et al. (1997) Paper I overlap = **five**: UGC00191, UGC00891, UGC05716, UGC05764, UGC11820. “Six-profile” shorthand refers to the source paper's six-LSBDG subgroup, not six frozen overlaps. |
| A18 | **COMPLETE correction** | `UGC05829` is **not** van Zee 1997; correct H I source family is Taylor et al. (1994). |
| A19 | **SOURCE RECOVERED** | **KK98-251** (calibration): exact public analytic raw-H I radial profile recovered from Begum & Chengalur. |
| A20 | **SOURCE RECOVERED** | **CamB / KK44** (calibration): exact public analytic raw-H I radial profile recovered from Begum, Chengalur & Hopp. |
| A21 | **COMPLETE source/convention audit** | **NGC3741** (calibration): Figure 5 direct radial gas profile identified; published profile already includes helium `x1.3`, so never double-correct. Numerical curve remains pending. |
| A22 | **COMPLETE alias audit** | FIGGS aliases fixed: **CamB = KK44**, **KK98-251 = KK251**, NGC3741 direct. All three are public Begum/FIGGS-block calibration targets. |
| A23 | **COMPLETE source audit** | **UGC05829** (blind): Taylor et al. (1994) public VLA H I synthesis source confirmed; later compilation gives ~20x20 arcsec beam and ~6.0x5.3 arcmin H I extent. Direct azimuthally averaged radial profile remains unverified, so it is not marked ingested. |

---

## 5. Recovered analytic H I models

### CamB / KK44 — calibration

Primary: Begum, Chengalur & Hopp, *New Astronomy* 8, 267–281; DOI `10.1016/S1384-1076(02)00238-5`; arXiv `astro-ph/0301194`.

`Sigma_HI(r) = Sigma0 exp[-r^2/(2 r0^2)]`

- `Sigma0 = 5.9 +/- 0.2 Msun pc^-2`
- `r0 = 40.7 +/- 1.6 arcsec`
- source distance = 2.2 Mpc
- frozen distance = 3.36 Mpc
- source H I inclination = `65 +/- 5 deg`
- frozen inclination = 65 deg
- source profile is **raw H I**; paper applies primordial helium `x1.4` separately in mass modelling
- source profile resolution ~`40 x 38 arcsec`
- frozen-distance QC: `r0 = 0.662992 kpc`, `sigma(r0)=0.026064 kpc`

### KK98-251 / KK251 — calibration

Primary: Begum & Chengalur, A&A 424, 509–517; DOI `10.1051/0004-6361:20041210`.

`Sigma_HI(r) = Sigma0 exp[-(r-c)^2/(2 r0^2)]`

- `Sigma0 = 7.8 +/- 0.1 Msun pc^-2`
- `r0 = 34.2 +/- 0.7 arcsec`
- `c = 19.2 +/- 0.8 arcsec`
- source distance = 5.6 Mpc
- frozen distance = 6.8 Mpc
- source H I inclination = `62 +/- 5 deg`; FIGGS H I inclination = `59 +/- 5 deg`; frozen inclination = 59 deg
- source profile is **raw H I**; paper applies helium `x1.4` separately
- frozen-distance QC: `r0 = 1.12748 kpc`, `c = 0.632972 kpc`

Canonical analytic table:

`data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv`

Native angular parameters remain the provenance authority. No common grid resampling, inclination-amplitude renormalization or helium application occurs until those global rules are frozen.

---

## 6. Current source-family acquisition matrix

| Source block | Frozen targets | Durable state | Next action |
|---|---|---|---|
| NGC1090 | NGC1090 — calibration | extraction choice settled; coordinate/QC artifact missing | **RECOVER before final freeze** |
| Côté 2000 | UGCA442 — blind; DDO161 — calibration; ESO444-G084 — blind | source/crossmatch/conventions complete | numerical Figure 3 curves pending; revisit only through a new defensible vector/data route |
| van Zee 1997 | UGC00191 — calibration; UGC00891 — calibration; UGC05716 — blind; UGC05764 — calibration; UGC11820 — blind | crossmatch/alias audit complete | primary numerical profiles/conventions pending; no invented sixth overlap |
| Begum/Chengalur — CamB | CamB — calibration | **analytic raw-H I profile recovered** | retain native analytic model; downstream normalization later |
| Begum/Chengalur — KK98-251 | KK98-251 — calibration | **analytic raw-H I profile recovered** | retain native analytic model; downstream normalization later |
| Begum/Chengalur — NGC3741 | NGC3741 — calibration | profile/convention complete | numerical Figure 5 remains pending; do not loop unless a new high-fidelity route appears |
| Taylor 1994 | UGC05829 — blind | public VLA H I map source confirmed | bounded search for direct radial profile or reusable map/cube; otherwise leave numeric pending |
| Remaining public blocks | pending | **IN PROGRESS** | continue systematic literature/archive/table/vector-source sweep |

Known systems absent from the target 169-profile private compilation at the frozen audit boundary remain:

- D564-8 — calibration
- D631-7 — calibration
- NGC4138 — blind
- NGC5907 — calibration

Their roles never change. Independent public direct profiles may still rescue them before source freeze.

---

## 7. Durable source-audit artifacts

- `validation/stationary/COTE2000_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/cote2000_profile_source_audit_v1.csv`
- `validation/stationary/VANZEE1997_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/vanzee1997_profile_source_audit_v1.csv`
- `validation/stationary/BEGUM_CHENGALUR_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/begum_chengalur_profile_source_audit_v1.csv`
- `data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv`
- `validation/stationary/TAYLOR1994_UGC05829_AUDIT_V1.md`
- `data/stationary/source_reconstruction/taylor1994_ugc05829_source_audit_v1.csv`
- `data/stationary/source_reconstruction/stationary_hi_profile_provenance_v1.csv`

The master provenance inventory predates some of the public-source recoveries above and still requires a later global reconciliation; per-family audit files are currently the more specific authority for these newly recovered routes.

---

## 8. H I/source-profile gate products

| Product | Status |
|---|---|
| master stationary H I provenance inventory | **EXISTS; global reconciliation pending** |
| Côté source audit | **COMPLETE; numerical points pending** |
| van Zee source audit | **COMPLETE; numerical points/conventions pending** |
| Begum/Chengalur source audit | **COMPLETE for current three targets; CamB + KK98-251 analytic profiles recovered** |
| Taylor/UGC05829 source audit | **COMPLETE at public-map level; direct profile pending** |
| NGC1090 extraction artifact | **RECOVER** |
| `stationary_hi_profiles_v1.csv` | **NOT YET COMPLETE/FROZEN** |
| `stationary_source_profiles_v1.csv` | **NOT YET COMPLETE/FROZEN** |
| common radius/helium/inclination/interpolation/coverage rules | **NOT YET FROZEN** |
| resolved-profile validation report | **NOT YET COMPLETE** |
| `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` | **NOT YET CREATED/FROZEN** |
| `L_A`, `\mathcal C_A` calibration | **LOCKED** |
| final 45-galaxy blind evaluation | **LOCKED** |

---

## 9. Decision register — do not reopen without new evidence

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
| D11 | Côté family = UGCA442, DDO161, ESO444-G084. Figure 3 already contains 4/3 helium; never double-correct. |
| D12 | van Zee 1997 Paper I overlap = five. Old “six-profile” wording is source-subsample shorthand. |
| D13 | UGC05829 belongs to Taylor et al. (1994), not van Zee 1997. |
| D14 | KK98-251 analytic equation is raw H I; source mass model applies helium later. |
| D15 | CamB analytic equation is raw H I; source mass model applies helium `x1.4` later. |
| D16 | NGC3741 Figure 5 already includes helium `x1.3`; divide by 1.3 only if a raw-H I intermediate is required while preserving original source values. |
| D17 | If a public numerical route stalls, record `numeric_pending` and move on unless a genuinely new high-fidelity route appears. |

---

## 10. Current live queue

1. **IN PROGRESS — remaining public H I source blocks:** continue systematic frozen-master source-family acquisition and seek analytic/table/vector profiles first.
2. **BOUNDED FOLLOW-UP — Taylor 1994 UGC05829:** check once for direct radial profile or publicly reusable VLA map/cube; otherwise retain `public_map_source_confirmed / numeric_pending`.
3. **PENDING NUMERICAL:** Côté three curves, van Zee five curves, NGC3741 Figure 5; revisit only through a new defensible data/vector route.
4. **RECOVER before source freeze:** NGC1090 `fig2.eps` filled-circle extraction/QC artifact.
5. Reconcile all family audits into the master H I provenance inventory.
6. Build `stationary_hi_profiles_v1.csv` from recovered public source products under one frozen normalization schema.
7. Build `stationary_source_profiles_v1.csv` under locked source rules.
8. Freeze common radius conversion, helium convention, inclination/deprojection handling, interpolation/extrapolation/taper, duplicate and coverage rules.
9. Complete resolved-profile validation report.
10. Create `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` with hashes and exact membership.
11. **Only then** unlock `L_A` and `\mathcal C_A` calibration on calibration galaxies.
12. Freeze final model/nuisance/solver/scoring specification.
13. Run the frozen 45-galaxy blind evaluation once, with no refit.

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

**Current resume point:** continue the remaining public radial-H I source blocks, prioritizing analytic/tabulated profiles. CamB and KK98-251 are now source-recovered analytic calibration profiles. `L_A` and `\mathcal C_A` remain locked.
