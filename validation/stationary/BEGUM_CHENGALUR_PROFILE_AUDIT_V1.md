# Begum / Chengalur direct H I profile audit v1

**Status:** THREE FROZEN TARGETS CONFIRMED; **CamB AND KK98-251 ANALYTIC H I PROFILES RECOVERED**; NGC3741 NUMERICAL CURVE PENDING  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `C_A` remain locked.

## 1. Frozen-master targets and FIGGS aliases

| Frozen galaxy | Frozen role | FIGGS identity | Frozen distance (Mpc) | Frozen inclination (deg) | Direct source status |
|---|---|---|---:|---:|---|
| CamB | calibration | KK 44 | 3.36 | 65 | **exact analytic raw-H I radial profile recovered** |
| KK98-251 | calibration | KK 251 | 6.80 | 59 | **exact analytic raw-H I radial profile recovered** |
| NGC3741 | calibration | NGC 3741 | 3.21 | 70 | direct gas profile/conventions recovered; numerical Figure 5 curve pending |

FIGGS confirms all three once aliases are reconciled. No galaxy membership or frozen role changes were made.

---

## 2. CamB / KK 44 — exact analytic H I profile recovered

### Primary source

A. Begum, J. N. Chengalur & U. Hopp, **“The little galaxy that could: kinematics of Camelopardalis B,”** *New Astronomy* 8, 267–281; DOI `10.1016/S1384-1076(02)00238-5`; arXiv `astro-ph/0301194`.

The source adopts **2.2 Mpc**. The frozen Paper I distance is **3.36 Mpc**.

### Profile construction

Section 3.2 and Figure 4 state that the deprojected radial H I surface-density profile was obtained by fitting elliptical annuli to the GMRT H I moment-0 image. The profile is well represented by the zero-centered Gaussian

`Sigma_HI(r) = Sigma0 * exp[-r^2/(2 r0^2)]`

with

- `r0 = 40.7 +/- 1.6 arcsec`
- `Sigma0 = 5.9 +/- 0.2 Msun pc^-2`
- H I inclination `65 +/- 5 deg`
- H I position angle `215 +/- 5 deg`
- profile map resolution approximately `40 x 38 arcsec`

The frozen inclination is also 65 deg, so the source central inclination and frozen central inclination agree.

### Helium convention

The analytic Figure 4/Equation 1 quantity is **raw H I surface density**. In the mass-model section the paper explicitly says primordial helium is included later by multiplying H I densities by **1.4**. Therefore:

- archive the analytic profile as raw `Sigma_HI`;
- do **not** apply helium during source ingestion;
- apply the single globally frozen Paper I helium convention downstream.

### Distance conversion QC

At the source distance 2.2 Mpc, `r0` corresponds to about **0.4341 kpc**, consistent with the paper's rounded 0.43 kpc statement.

At the frozen 3.36 Mpc distance, preserving the observed angular profile:

- `1 arcsec = 0.0162897 kpc`
- `r0_frozenD = 0.662992 kpc`
- `sigma(r0_frozenD) = 0.026064 kpc`

These are coordinate-conversion checks only; the native angular parameters remain the provenance authority.

### Promotion state

CamB is now **analytic_source_recovered**. No plot digitization is required for its primary analytic representation. It is not yet globally resampled or helium-corrected because those common normalization rules remain frozen-gate work.

---

## 3. KK98-251 / KK 251 — exact analytic H I profile recovered

### Primary source

A. Begum & J. N. Chengalur, **“Kinematics of two dwarf galaxies in the NGC 6946 group,”** A&A 424, 509–517; DOI `10.1051/0004-6361:20041210`; arXiv `astro-ph/0406211`.

The deprojected raw H I profile is

`Sigma_HI(r) = Sigma0 * exp[-(r-c)^2/(2 r0^2)]`

with

- `r0 = 34.2 +/- 0.7 arcsec`
- `c = 19.2 +/- 0.8 arcsec`
- `Sigma0 = 7.8 +/- 0.1 Msun pc^-2`
- source distance 5.6 Mpc
- source H I inclination `62 +/- 5 deg`
- FIGGS H I inclination `59 +/- 5 deg`
- frozen inclination 59 deg

The source mass model applies helium `x1.4` separately, so the analytic equation is preserved as raw H I.

At the frozen 6.8 Mpc distance, `r0 = 1.12748 kpc` and `c = 0.632972 kpc` as coordinate-conversion QC only.

### Promotion state

KK98-251 is **analytic_source_recovered**. No digitization is required for its primary analytic representation.

---

## 4. NGC3741 — direct radial gas profile; numerical curve pending

Primary sources include Begum, Chengalur & Karachentsev, **“A dwarf galaxy with a giant HI disk,”** A&A 433, L1–L4, and Begum et al., **“Life in the last lane…”**, MNRAS 383, 809–816; DOI `10.1111/j.1365-2966.2007.12592.x`.

The latter provides **Figure 5**, a radial gas surface-mass-density profile derived from the **11 x 9 arcsec** H I map. Its H I profile is already scaled by **1.3** for primordial helium.

**Critical rule:** never apply helium a second time. If a raw-H I intermediate is required, use

`Sigma_HI = Sigma_gas_Fig5 / 1.3`

while retaining the published source values unchanged.

Source distance is 3.03 Mpc; frozen distance is 3.21 Mpc. The disk is warped, with source kinematic inclination varying roughly 58–70 deg; frozen inclination is 70 deg.

A high-resolution publisher Figure 5 route was attempted but did not yield machine-readable/vector data in the current environment. Under the anti-loop rule, NGC3741 remains `figure_curve_pending` until a genuinely new high-fidelity route appears. No points are fabricated from axis ticks or SPARC `Vgas`.

---

## 5. Durable source products

- `data/stationary/source_reconstruction/begum_chengalur_profile_source_audit_v1.csv`
- `data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv`

The analytic parameter file now contains both **CamB** and **KK98-251** as recovered raw-H I models.

---

## 6. Current disposition

- CamB: **ANALYTIC RAW-H I PROFILE RECOVERED**.
- KK98-251: **ANALYTIC RAW-H I PROFILE RECOVERED**.
- NGC3741: **SOURCE/CONVENTION RECOVERED; NUMERICAL CURVE PENDING**.
- FIGGS aliases CamB=KK44 and KK98-251=KK251: **CONFIRMED**.
- Global radius resampling, helium application, inclination normalization and interpolation rules: **NOT YET APPLIED / remain source-freeze work**.
- `L_A` and `\mathcal C_A`: **LOCKED**.

No persistence parameter or blind-set outcome was inspected while building this source audit.
