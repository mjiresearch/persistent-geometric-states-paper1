# Persistence Framework — Paper I Project Ledger

**Canonical cross-session checkpoint**  
**Repository:** `mjiresearch/persistent-geometric-states-paper1`  
**Established:** 2026-08-12  
**Last reconciled:** 2026-08-12 — public radial H I database build through Leroy/THINGS ingestion and 149-galaxy provenance reconciliation

> **Authority rule:** this ledger summarizes project state. Frozen protocol/data/provenance/validation artifacts remain authoritative if any discrepancy is found. The original H I provenance inventory is retained unchanged for auditability; the versioned reconciled provenance view is the current acquisition-status view.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| **FROZEN** | Predeclared boundary; do not change after the fact. |
| **COMPLETE** | Finished and durably represented in GitHub. |
| **SOURCE RECOVERED** | Direct public profile/analytic representation is durably recovered; common downstream normalization may still be pending. |
| **RAW PROFILE INGESTED** | Machine-readable radial source values are durably ingested with source conventions preserved. |
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
| A23 | **COMPLETE source audit** | **UGC05829** (blind): Taylor et al. (1994) public VLA H I synthesis source confirmed. Direct azimuthally averaged radial profile remains unverified, so it is not marked ingested. |
| A24 | **RAW PROFILE INGESTED** | **Leroy et al. (2008) / THINGS:** public VizieR `J/AJ/136/2782/table7` ingested for **11 frozen galaxies = 6 calibration + 5 blind**, yielding **369 radial H I rows** with source radius, helium-inclusive `SigmaHI`, and uncertainties preserved. Output SHA-256 `d0cc498aaf7b378bf9affe19f0ca5ea7f638622e23517986ee2ee6477d7ddc75`. |
| A25 | **COMPLETE** | Public-source overlay and reconciled **149-galaxy acquisition-status view** created. Overlay covers **24 frozen galaxies = 14 calibration + 10 blind**. **13 galaxies = 8 calibration + 5 blind** now have a recovered analytic or ingested numerical public profile. Original provenance inventory remains unchanged for auditability. |

---

## 5. Recovered / ingested public H I profile set

### A. Analytic profiles recovered

#### CamB / KK44 — calibration

Primary: Begum, Chengalur & Hopp, *New Astronomy* 8, 267–281; DOI `10.1016/S1384-1076(02)00238-5`; arXiv `astro-ph/0301194`.

`Sigma_HI(r) = Sigma0 exp[-r^2/(2 r0^2)]`

- `Sigma0 = 5.9 +/- 0.2 Msun pc^-2`
- `r0 = 40.7 +/- 1.6 arcsec`
- source distance = 2.2 Mpc; frozen distance = 3.36 Mpc
- source H I inclination = `65 +/- 5 deg`; frozen inclination = 65 deg
- source profile is **raw H I**; paper applies primordial helium `x1.4` separately in mass modelling
- source profile resolution ~`40 x 38 arcsec`
- frozen-distance QC only: `r0 = 0.662992 kpc`

#### KK98-251 / KK251 — calibration

Primary: Begum & Chengalur, A&A 424, 509–517; DOI `10.1051/0004-6361:20041210`.

`Sigma_HI(r) = Sigma0 exp[-(r-c)^2/(2 r0^2)]`

- `Sigma0 = 7.8 +/- 0.1 Msun pc^-2`
- `r0 = 34.2 +/- 0.7 arcsec`
- `c = 19.2 +/- 0.8 arcsec`
- source distance = 5.6 Mpc; frozen distance = 6.8 Mpc
- source H I inclination = `62 +/- 5 deg`; FIGGS/frozen inclination = 59 deg
- source profile is **raw H I**; paper applies helium `x1.4` separately
- frozen-distance QC only: `r0 = 1.12748 kpc`, `c = 0.632972 kpc`

Canonical analytic table:
`data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv`

### B. Leroy/THINGS machine-readable profiles ingested

Canonical raw-source file:
`data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv`

| Galaxy | Role | Source rows |
|---|---|---:|
| DDO154 | calibration | 7 |
| IC2574 | calibration | 46 |
| NGC2403 | blind | 57 |
| NGC2841 | calibration | 25 |
| NGC2976 | calibration | 26 |
| NGC3198 | calibration | 23 |
| NGC3521 | blind | 30 |
| NGC5055 | blind | 43 |
| NGC6946 | blind | 41 |
| NGC7331 | calibration | 33 |
| NGC7793 | blind | 38 |

**Total: 369 rows.** Leroy `SigmaHI` is source-published **including helium**. Values are preserved unchanged. No second helium correction, assumed raw-H-I back-conversion, distance rescaling, inclination rescaling, interpolation, extrapolation or taper has been applied.

---

## 6. Current public-source acquisition matrix

| Source block | Frozen targets | Durable state | Next action |
|---|---|---|---|
| Leroy 2008 / THINGS | DDO154, IC2574, NGC2403, NGC2841, NGC2976, NGC3198, NGC3521, NGC5055, NGC6946, NGC7331, NGC7793 | **369 raw radial rows ingested / Actions validated** | ingest source metadata needed for common normalization; run radial-coverage QC versus frozen SPARC domains |
| Begum/Chengalur — CamB | CamB — calibration | **analytic raw-H I profile recovered** | retain native analytic model; downstream common normalization later |
| Begum/Chengalur — KK98-251 | KK98-251 — calibration | **analytic raw-H I profile recovered** | retain native analytic model; downstream common normalization later |
| Begum/Chengalur — NGC3741 | NGC3741 — calibration | profile/convention complete | numerical Figure 5 pending; do not loop unless a new high-fidelity route appears |
| Côté 2000 | UGCA442 — blind; DDO161 — calibration; ESO444-G084 — blind | source/crossmatch/conventions complete | numerical Figure 3 curves pending; revisit only through a new defensible vector/data route |
| van Zee 1997 | UGC00191 — calibration; UGC00891 — calibration; UGC05716 — blind; UGC05764 — calibration; UGC11820 — blind | crossmatch/alias audit complete | primary numerical profiles/conventions pending; no invented sixth overlap |
| Taylor 1994 | UGC05829 — blind | public VLA H I map source confirmed | radial profile/map reconstruction remains pending; do not stall here |
| NGC1090 | NGC1090 — calibration | extraction choice settled; coordinate/QC artifact missing | **RECOVER before final freeze** |
| Remaining public blocks | pending | **IN PROGRESS** | prioritize electronic tables, VizieR, public survey profile products and analytic forms before graph digitization |

Known systems absent from the target 169-profile private compilation at the frozen audit boundary remain:

- D564-8 — calibration
- D631-7 — calibration
- NGC4138 — blind
- NGC5907 — calibration

Their roles never change. Independent public direct profiles may still rescue them before source freeze.

---

## 7. Provenance status and current acquisition authority

Original audit inventory retained unchanged:
`data/stationary/source_reconstruction/stationary_hi_profile_provenance_v1.csv`

Current public-source overlay:
`data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv`

Current reconciled 149-galaxy acquisition view:
`data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv`

Reconciliation summary:
`validation/stationary/stationary_hi_profile_provenance_reconciled_v1_summary.json`

Current reconciled counts:

- frozen galaxies: **149**
- public-overlay galaxies: **24 = 14 calibration + 10 blind**
- recovered/ingested profiles: **13 = 8 calibration + 5 blind**
- analytic profiles recovered: **2**
- raw machine-readable profiles ingested: **11**
- direct profiles identified but numerical data pending: **4**
- source-family identified/numeric pending: **5**
- public H I map confirmed/profile pending: **1**
- exact extraction artifact to recover: **1**
- known unavailable in the private 169 compilation: **4**
- still listed as nonpublic-request-required with no superseding public overlay yet: **121**

Reconciled output SHA-256:
`3fc42939b0ef40877aa66e712d80987e695b37ac32a448f3f4bc98be8f9d5203`

The reconciled view changes **acquisition/source-status metadata only**. It does not alter frozen membership, roles, source equations, model parameters or blind-test rules.

---

## 8. Durable source/database artifacts

- `validation/stationary/COTE2000_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/cote2000_profile_source_audit_v1.csv`
- `validation/stationary/VANZEE1997_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/vanzee1997_profile_source_audit_v1.csv`
- `validation/stationary/BEGUM_CHENGALUR_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/begum_chengalur_profile_source_audit_v1.csv`
- `data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv`
- `validation/stationary/TAYLOR1994_UGC05829_AUDIT_V1.md`
- `data/stationary/source_reconstruction/taylor1994_ugc05829_source_audit_v1.csv`
- `validation/stationary/LEROY2008_THINGS_PROFILE_AUDIT_V1.md`
- `data/stationary/source_reconstruction/leroy2008_things_profile_source_audit_v1.csv`
- `data/stationary/source_reconstruction/leroy2008_things_hi_profiles_v1.csv`
- `validation/stationary/leroy2008_things_hi_profiles_v1_summary.json`
- `scripts/stationary/ingest_leroy2008_things_hi_profiles.py`
- `.github/workflows/ingest_leroy2008_things_hi.yml`
- `data/stationary/source_reconstruction/stationary_public_hi_source_overlay_v1.csv`
- `scripts/stationary/reconcile_public_hi_source_overlay_v1.py`
- `.github/workflows/reconcile_public_hi_source_overlay.yml`
- `data/stationary/source_reconstruction/stationary_hi_profile_provenance_reconciled_v1.csv`
- `validation/stationary/stationary_hi_profile_provenance_reconciled_v1_summary.json`

---

## 9. H I/source-profile gate products

| Product | Status |
|---|---|
| original stationary H I provenance inventory | **EXISTS / retained for audit** |
| public-source overlay | **COMPLETE for currently audited/recovered blocks** |
| reconciled 149-galaxy acquisition view | **COMPLETE / current acquisition-status authority** |
| Leroy/THINGS 11-galaxy raw source profiles | **COMPLETE — 369 rows** |
| CamB + KK98-251 analytic profiles | **COMPLETE source recovery** |
| Côté source audit | **COMPLETE; numerical points pending** |
| van Zee source audit | **COMPLETE; numerical points/conventions pending** |
| NGC3741 direct profile | **SOURCE IDENTIFIED; numerical points pending** |
| Taylor/UGC05829 | **PUBLIC MAP CONFIRMED; radial profile pending** |
| NGC1090 extraction artifact | **RECOVER** |
| common source metadata / radial-coverage QC | **IN PROGRESS / NEXT** |
| `stationary_hi_profiles_v1.csv` | **NOT YET COMPLETE/FROZEN** |
| `stationary_source_profiles_v1.csv` | **NOT YET COMPLETE/FROZEN** |
| common radius/helium/inclination/interpolation/coverage rules | **NOT YET FROZEN** |
| resolved-profile validation report | **NOT YET COMPLETE** |
| `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` | **NOT YET CREATED/FROZEN** |
| `L_A`, `\mathcal C_A` calibration | **LOCKED** |
| final 45-galaxy blind evaluation | **LOCKED** |

---

## 10. Decision register — do not reopen without new evidence

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
| D18 | Leroy/THINGS `SigmaHI` is source-published **including helium**. Preserve it unchanged in acquisition products; do not apply another helium factor or assume a back-conversion factor before the global convention is frozen. |
| D19 | The original H I provenance inventory remains immutable audit history. The versioned overlay + reconciled view carry current public-source acquisition status and may be regenerated reproducibly. |

---

## 11. Current live queue

1. **IN PROGRESS — exploit high-yield public machine-readable H I sources:** continue survey/electronic-catalog search beyond Leroy before returning to low-fidelity digitization branches.
2. **NEXT — Leroy/common-source QC:** ingest source distance/inclination metadata and calculate radial coverage of the 11 Leroy profiles against each frozen SPARC rotation-curve domain without resampling or fitting persistence.
3. **NEXT — normalize recovered analytic source metadata:** CamB and KK98-251 remain native angular analytic profiles until the same global conversion rule is declared.
4. **PENDING NUMERICAL:** Côté three curves, van Zee five curves, NGC3741 Figure 5; revisit only through a genuinely new defensible data/vector route.
5. **PENDING MAP ROUTE:** UGC05829/Taylor 1994; do not stall unless a reusable public map/cube or radial table is found.
6. **RECOVER before source freeze:** NGC1090 `fig2.eps` filled-circle extraction/QC artifact.
7. Extend `stationary_public_hi_source_overlay_v1.csv` and regenerate the reconciled 149-galaxy view at every newly cleared source block.
8. Freeze common radius conversion, helium convention, inclination/deprojection handling, interpolation/extrapolation/taper, duplicate and coverage rules.
9. Build `stationary_hi_profiles_v1.csv` from source-recovered/ingested galaxies under that one frozen normalization schema.
10. Build `stationary_source_profiles_v1.csv` under locked source rules.
11. Complete resolved-profile validation report.
12. Create `STATIONARY_SOURCE_PROFILE_FREEZE_V1.md` with hashes and exact membership.
13. **Only then** unlock `L_A` and `\mathcal C_A` calibration on calibration galaxies.
14. Freeze final model/nuisance/solver/scoring specification.
15. Run the frozen 45-galaxy blind evaluation once, with no refit.

---

## 12. Cross-session operating rule

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

**Current resume point:** the galaxy database now has **13 frozen galaxies with actual public analytic or numerical radial H I profiles**, including **369 machine-readable Leroy/THINGS rows for 11 galaxies**. Continue high-yield public machine-readable source blocks, then run common-source metadata and radial-coverage QC. `L_A` and `\mathcal C_A` remain locked.
