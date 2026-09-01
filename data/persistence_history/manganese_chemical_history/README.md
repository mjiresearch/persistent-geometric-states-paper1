# Manganese Chemical-History Test

**Queue position:** immediately after the independent SDSS DR20 young-vs-old current-field block  
**Status:** PUBLIC DATA AVAILABLE / V0 PROTOCOL READY / NO OUTCOME INSPECTED  
**Established:** 2026-09-01

## Scientific purpose

This block tests whether a manganese-based chemical-history coordinate carries reproducible dynamical information after controlling for the present stellar state and conventional population/dynamical effects.

It is a complementary history-sensitive screen, not a substitute for the stationary SPARC H I source package and not a direct acceleration measurement. A positive result is not, by itself, a detection of gravitational persistence.

The motivating atomic-physics result is Samak, Nahar & Pradhan (2026), *Emissivity line ratios for [Mn III] and spectral diagnostics of H II regions*, MNRAS 550, stag1304, DOI 10.1093/mnras/stag1304. The paper gives the first theoretical [Mn III] emission-line diagnostic study and predicts, among other ratios, `I(8213.52 A)/I(8081.28 A)` as a temperature/density-sensitive diagnostic. Detection could also constrain Mn abundance. These newly predicted nebular lines have not yet become a standard survey product.

## Why Mn is useful but must not be called a clock

Mn abundance is shaped by chemical-evolution history, including metallicity-dependent nucleosynthetic yields and the changing contributions of Type Ia and core-collapse supernovae. Therefore `[Mn/Fe]` is treated here as a **chemical-history tag**, not as a one-dimensional age clock and not as the persistence field itself.

The test is deliberately framed as an incremental-information question: after present location, age, metallicity, alpha abundance, stellar-parameter/selection controls, and conventional dynamics are accounted for, does a Mn history coordinate still track a kinematic residual?

## Public-data feasibility — 2026-09-01

### 1. GALAH DR4 — PRIMARY V0 / runnable with existing data

GALAH DR4 is the cleanest first implementation because the public products are internally joinable on `sobject_id`:

- recommended all-star catalogue `galah_dr4_allstar_240705.fits`: one row per star, stellar parameters, `age`, `fe_h`, `mn_fe`, `mg_fe`, errors and quality flags;
- dynamics VAC `galah_dr4_vac_dynamics_240705.fits`: Galactocentric `R_Rzphi`, `z_Rzphi`, `phi_Rzphi`, `vR_Rzphi`, `vz_Rzphi`, `vT_Rzphi`, actions and orbital parameters;
- BSTEP ages/masses VAC `galah_dr4_vac_ages_masses_240705.fits`: `age_bstep` plus 16th/50th/84th-percentile age estimates and associated stellar properties.

GALAH best-practice cuts relevant to the primary test are `flag_sp == 0`, `flag_mn_fe == 0`, and `snr_px_ccd3 > 30`. GALAH explicitly warns that `flag_fe_h` is affected by a DR4 bug and must not be used as a metallicity-quality gate.

Official documentation:
- https://www.galah-survey.org/dr4/the_catalogues/
- https://www.galah-survey.org/dr4/using_the_data/
- https://www.galah-survey.org/dr4/table_schema/

### 2. APOGEE — INDEPENDENT REPLICATION / runnable with existing data

SDSS DR20 is public as of 2026-07-30. DR20 contains no newly reduced/reanalysed APOGEE sample relative to the carried-forward DR19/DR17 products, but public APOGEE products already provide what this test needs:

- AstroNN/Astra: Mn among individual APOGEE abundances;
- legacy APOGEE DR17 astroNN VAC: abundances, distances, ages, stellar/orbital parameters;
- public identifiers such as `gaia_dr3_source_id` / `sdss_id` support joins where required.

This makes APOGEE a strong independent spectroscopic replication after the GALAH protocol is executed, not a reason to wait for DR21.

Official documentation:
- https://www.sdss.org/dr20/mwm/astra/pipelines-in-astra/astronn/
- https://www.sdss.org/dr20/mwm/data/abundances/
- https://www.sdss.org/dr20/data_access/value-added-catalogs/

### 3. MaNGA DR17 — SECONDARY CUSTOM [Mn III] LINE-SEARCH ARM

MaNGA spectra cover approximately 3600–10300 A, so the predicted 8081.28 A and 8213.52 A [Mn III] lines lie inside the observed wavelength range. However, these new [Mn III] lines are not standard DR17 DAP emission-line products. A MaNGA test therefore requires custom work on LOGCUBE/model residual spectra:

1. select star-forming/H II-dominated spaxels or annuli;
2. shift to the local rest frame using DAP gas kinematics;
3. subtract the best-fit stellar+known-emission model or construct a controlled residual spectrum;
4. stack spectra/radial annuli to gain sensitivity;
5. fit both 8081.28 and 8213.52 A with predeclared sky/telluric/artifact masks and common kinematic constraints;
6. require reproducible paired-line evidence and a physically plausible ratio before interpreting any candidate as [Mn III].

This is scientifically interesting but should not block the GALAH/APOGEE stellar-abundance test.

Official documentation:
- https://www.sdss4.org/dr17/manga/manga-analysis-pipeline/
- https://www.sdss4.org/dr17/manga/manga-data/data-model/

## V0 hierarchy

1. **GALAH DR4 primary screen** — execute the frozen pre-outcome protocol in `protocol_v0.json`.
2. **Conventional challenge** — asymmetric drift / disk heating, population chemistry, vertical structure, selection and migration diagnostics are required before interpretation.
3. **APOGEE independent replication** — same scientific estimand, independently measured Mn abundances and survey selection.
4. **MaNGA [Mn III] search** — separate observational line-search arm; no claim may depend on those lines until an actual robust detection/calibration exists.

## Interpretation guardrail

Allowed positive language for v0 is **`manganese_history_sensitive`** or, after all conventional challenges and independent replication, **`persistence_compatible_chemical_history_signal`**. The phrase **`persistence detection`** is prohibited for this block.

## Execution note

The present ChatGPT execution environment can verify the public catalogues and their schemas but cannot resolve the Data Central host from its code runtime, so the GALAH FITS rows were not downloaded or numerically inspected during protocol construction. This is advantageous for preregistration: the protocol is committed before any manganese-dynamical outcome is seen.
