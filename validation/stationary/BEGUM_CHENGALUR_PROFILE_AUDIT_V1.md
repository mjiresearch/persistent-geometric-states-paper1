# Begum / Chengalur direct H I profile audit v1

**Status:** TWO FROZEN-SAMPLE DIRECT-PROFILE SOURCES CONFIRMED; KK98-251 ANALYTIC PROFILE RECOVERED; NGC3741 NUMERICAL CURVE PENDING  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `C_A` remain locked.

## 1. Frozen-master matches

The Begum/Chengalur/FIGGS literature supplies two confirmed direct-name matches to the frozen 149-galaxy Paper I stationary master:

| Frozen galaxy | Frozen role | Frozen distance (Mpc) | Frozen inclination (deg) | Direct source status |
|---|---|---:|---:|---|
| KK98-251 | calibration | 6.80 | 59 | exact analytic H I radial profile recovered |
| NGC3741 | calibration | 3.21 | 70 | direct radial gas profile identified; numerical curve recovery pending |

The FIGGS overview contains 65 dwarf galaxies. A direct-name crossmatch plus targeted checks of plausible near-name UGC/DDO candidates did not reveal another frozen-master match in this block. A final global alias reconciliation remains part of the later full provenance audit; no extra galaxy is promoted merely from a similar catalogue number.

---

## 2. KK98-251 — exact analytic direct H I profile

### Primary source

A. Begum & J. N. Chengalur, **“Kinematics of two dwarf galaxies in the NGC 6946 group,”** Astronomy & Astrophysics 424 (2004/2005), 509–517; DOI `10.1051/0004-6361:20041210`; arXiv `astro-ph/0406211`.

The observations cover KK98 250 and KK98 251 with the GMRT. The paper adopts a group distance of **5.6 Mpc** for both galaxies.

### Profile construction

For KK98-251, the paper states that the H I surface-density profile was obtained by fitting elliptical annuli to the integrated H I column-density image at approximately **26 x 21 arcsec** resolution. The H I disk inclination and position angle inferred from the outer contours are **62 +/- 5 deg** and **220 +/- 5 deg**, respectively.

The deprojected **raw H I** surface-density profile is represented by the Gaussian

`Sigma_HI(r) = Sigma0 * exp[-(r-c)^2 / (2 r0^2)]`

with

- `r0 = 34.2 +/- 0.7 arcsec`
- `c = 19.2 +/- 0.8 arcsec`
- `Sigma0 = 7.8 +/- 0.1 Msun pc^-2`

The source Figure 3 caption describes the profile points and adopted Gaussian fit. The body text says 26 x 21 arcsec resolution, while the figure caption reports 26 x 23 arcsec; this minor source-text discrepancy is retained explicitly rather than silently resolved.

### Helium convention

The profile equation is explicitly `Sigma_HI`, not helium-corrected total gas. In the paper's mass modelling section the authors state that they calculate the gaseous contribution from the **observed H I surface-mass-density profiles** and then scale H I by **1.4** to account for helium. Therefore the analytic parameters above are archived as **raw H I** and receive no helium factor at source-ingestion time.

The final Paper I global helium convention is applied exactly once downstream after the global source-profile convention is frozen.

### Distance/inclination handling

- source distance: 5.6 Mpc
- frozen Paper I distance: 6.80 Mpc
- source H I inclination: 62 +/- 5 deg
- frozen Paper I inclination: 59 deg

The analytic source is preserved in its native angular-radius form so no source-distance assumption is baked into the radial coordinate. Physical-kpc conversion under the frozen Paper I distance is deferred to the common normalization step. No inclination-amplitude rescaling is applied ad hoc here; the source inclination and frozen inclination are both retained for the later single global normalization rule.

### Promotion state

KK98-251 is **source-data recovered** at the analytic-profile level. It is not yet resampled onto any Paper I radial grid because interpolation/resampling rules are deliberately not frozen yet. The exact Gaussian parameters are stored separately in `begum_chengalur_analytic_profile_parameters_v1.csv`.

---

## 3. NGC3741 — direct radial gas profile

### Primary sources

A. Begum, J. N. Chengalur & I. D. Karachentsev, **“A dwarf galaxy with a giant HI disk,”** A&A 433 (2005), L1–L4; arXiv `astro-ph/0502307`.

A. Begum, J. N. Chengalur, R. C. Kennicutt, I. D. Karachentsev & J. C. Lee, **“Life in the last lane: star formation and chemical evolution in an extremely gas rich dwarf,”** MNRAS 383 (2008), 809–816; DOI `10.1111/j.1365-2966.2007.12592.x`; arXiv `0711.1588`.

### Profile identification

The 2008 paper provides **Figure 5**, explicitly described as the radial **gas surface-mass-density profile** for NGC3741 derived from the **11 x 9 arcsec** H I map.

The paper explicitly states that the H I surface-density profile plotted/used for this gas profile is scaled by **1.3** to account for primordial helium. Therefore Figure 5 is already a helium-corrected gas profile.

**Critical ingestion rule:** a digitized Figure 5 value must not receive a second helium correction. If a raw-H I intermediate is needed, use

`Sigma_HI = Sigma_gas_Fig5 / 1.3`

while preserving the original plotted gas quantity unchanged for provenance/QC.

### Source geometry / distance

The 2008 paper adopts **3.03 Mpc**, with 1 arcsec = 14.7 pc. The 2005 GMRT paper reports a kinematic inclination varying from about **58 to 70 deg** across the warped disk. The frozen Paper I values are 3.21 Mpc and 70 deg.

Because NGC3741 is warped and the source geometry is radius-dependent, no single inclination rescaling is imposed during acquisition. The profile's source geometry is retained and any normalization rule must be global and frozen before source-profile production.

### Numerical status

- primary radial profile source: **confirmed**
- helium convention: **confirmed (x1.3 already applied in Figure 5)**
- map resolution: **confirmed (11 x 9 arcsec)**
- source distance: **confirmed (3.03 Mpc)**
- numerical Figure 5 curve coordinates: **pending**

The publisher exposes the Figure 5 image, but the current retrieval path did not provide a machine-readable/vector point table. No points are inferred from axis ranges, a later reconstruction, or SPARC `Vgas`.

---

## 4. FIGGS context / alias control

The FIGGS overview (Begum et al. 2008, MNRAS 386, 1667–1682; arXiv `0802.3982`) defines a 65-galaxy sample and lists both NGC3741 and KK251. It provides a useful public source inventory but is not treated as proof that every FIGGS galaxy belongs to the frozen SPARC sample.

Targeted exact-name checks against the frozen stationary manifest confirmed NGC3741 and KK98-251. Plausible FIGGS near-name candidates including UGC6456, UGC7298, UGC8508, UGC8638, DDO187 and UGC11583 do not occur in the frozen 149 under those canonical identifiers. A final catalogue-alias sweep is retained as a later global provenance task.

---

## 5. Acceptance / next actions

### KK98-251

**Recovered source profile:** yes, analytically.  
**Safe next action:** preserve analytic parameters and native angular radius; defer common kpc conversion, helium scaling and resampling until global normalization rules are frozen.

### NGC3741

**Recovered source profile:** source/convention yes; numerical curve no.  
**Safe next action:** pursue public Figure 5/vector/data recovery once, then park as numerical-pending if unavailable rather than looping.

No persistence parameter has been evaluated and no blind-set result was inspected while building this audit.
