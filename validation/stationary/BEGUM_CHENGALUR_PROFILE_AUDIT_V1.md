# Begum / Chengalur direct H I profile audit v1

**Status:** THREE FROZEN TARGETS IDENTIFIED; KK98-251 ANALYTIC PROFILE RECOVERED; NGC3741 AND CamB NUMERICAL/PROFILE REPRESENTATIONS PENDING  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `C_A` remain locked.

## 1. Frozen-master matches / targets

The Begum/Chengalur literature supplies three confirmed frozen Paper I targets worth pursuing through public primary H I sources:

| Frozen galaxy | Frozen role | Frozen distance (Mpc) | Frozen inclination (deg) | Direct source status |
|---|---|---:|---:|---|
| CamB | calibration | 3.36 | 65 | dedicated public GMRT H I paper identified; exact radial surface-density representation pending |
| KK98-251 | calibration | 6.80 | 59 | **exact analytic H I radial profile recovered** |
| NGC3741 | calibration | 3.21 | 70 | direct radial gas profile identified; numerical curve recovery pending |

The FIGGS overview contains 65 dwarf galaxies. Direct-name comparison identifies NGC3741 as the immediate exact frozen-master overlap in that survey table; a final catalogue-alias reconciliation remains part of the later full provenance audit. No extra galaxy is promoted merely from a similar catalogue number.

---

## 2. KK98-251 — exact analytic direct H I profile

### Primary source

A. Begum & J. N. Chengalur, **“Kinematics of two dwarf galaxies in the NGC 6946 group,”** Astronomy & Astrophysics 424, 509–517; DOI `10.1051/0004-6361:20041210`; arXiv `astro-ph/0406211`.

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

The profile equation is explicitly `Sigma_HI`, not helium-corrected total gas. In the paper's mass modelling section the authors calculate the gaseous contribution from the **observed H I surface-mass-density profiles** and then scale H I by **1.4** to account for helium. Therefore the analytic parameters above are archived as **raw H I** and receive no helium factor at source-ingestion time.

The final Paper I global helium convention is applied exactly once downstream after the global source-profile convention is frozen.

### Distance/inclination handling

- source distance: 5.6 Mpc
- frozen Paper I distance: 6.80 Mpc
- source H I inclination: 62 +/- 5 deg
- frozen Paper I inclination: 59 deg

The analytic source is preserved in its native angular-radius form so no source-distance assumption is baked into the radial coordinate. For QC only, the frozen-distance conversion is `1 arcsec = 0.0329673 kpc`, giving `r0 = 1.12748 kpc` and `c = 0.632972 kpc` at 6.8 Mpc. These are derived checks, not replacements for the native angular parameters.

No inclination-amplitude rescaling is applied ad hoc here; source and frozen inclinations are both retained for the later single global normalization rule.

### Promotion state

KK98-251 is **source-data recovered** at the analytic-profile level. It is not yet resampled onto any Paper I radial grid because interpolation/resampling rules are deliberately not frozen yet. The exact Gaussian parameters are stored in:

`data/stationary/source_reconstruction/begum_chengalur_analytic_profile_parameters_v1.csv`.

---

## 3. NGC3741 — direct radial gas profile

### Primary sources

A. Begum, J. N. Chengalur & I. D. Karachentsev, **“A dwarf galaxy with a giant HI disk,”** A&A 433, L1–L4; arXiv `astro-ph/0502307`.

A. Begum, J. N. Chengalur, R. C. Kennicutt, I. D. Karachentsev & J. C. Lee, **“Life in the last lane: star formation and chemical evolution in an extremely gas rich dwarf,”** MNRAS 383, 809–816; DOI `10.1111/j.1365-2966.2007.12592.x`; arXiv `0711.1588`.

### Profile identification

The 2008 paper provides **Figure 5**, explicitly described as the radial **gas surface-mass-density profile** for NGC3741 derived from the **11 x 9 arcsec** H I map.

The paper states that the H I surface-density profile plotted/used for this gas profile is scaled by **1.3** to account for primordial helium. Therefore Figure 5 is already a helium-corrected gas profile.

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

The publisher exposes the Figure 5 image, but the current retrieval path has not provided a machine-readable/vector point table. No points are inferred from axis ranges, a later reconstruction, or SPARC `Vgas`.

---

## 4. CamB — dedicated public GMRT route

### Primary source

A. Begum, J. N. Chengalur & U. Hopp, **“The little galaxy that could: kinematics of Camelopardalis B,”** *New Astronomy* 8, 267–280; DOI `10.1016/S1384-1076(02)00238-5`; arXiv `astro-ph/0301194`.

The paper presents deep high-velocity-resolution GMRT H I imaging of CamB and adopts a source distance of **2.2 Mpc**. The frozen Paper I values are **3.36 Mpc** and **65 deg**.

This establishes a public primary H I route for a frozen calibration galaxy that had previously remained listed as requiring nonpublic profile acquisition.

### Current profile status

The paper clearly contains the H I imaging and mass-model inputs, but in this audit pass the exact radial H I surface-density representation, its helium treatment, profile radius coordinate, and source deprojection convention have **not yet been verified to the standard required for numerical promotion**.

Therefore CamB is currently:

`primary_public_HI_paper_identified / radial_profile_representation_pending`.

This is a real public-source upgrade, but it is intentionally not mislabeled as `profile_data_ingested` yet.

---

## 5. FIGGS context / alias control

The FIGGS overview (Begum et al. 2008, MNRAS 386, 1667–1682; arXiv `0802.3982`) defines a 65-galaxy sample and supplies an authoritative public sample table. It provides useful acquisition inventory but is not treated as proof that every FIGGS galaxy belongs to the frozen SPARC sample.

Direct canonical-name comparison confirms NGC3741. Plausible near-name UGC/DDO systems remain subject to the final global alias sweep; no alias is accepted without a positive catalogue identity match.

---

## 6. Acceptance / next actions

### KK98-251

**Recovered source profile:** yes, analytically.  
**Safe next action:** preserve analytic parameters/native angular radius; defer common kpc normalization, any inclination rescaling, helium scaling and radial resampling until the global rules are frozen.

### NGC3741

**Recovered source profile:** source/convention yes; numerical curve no.  
**Safe next action:** pursue public Figure 5/vector/data recovery once, then park as numerical-pending if unavailable rather than looping.

### CamB

**Recovered source profile:** public primary H I paper yes; exact radial representation no.  
**Safe next action:** inspect the primary text/figures for a direct radial surface-density representation or analytic fit; if unavailable at sufficient fidelity, retain as public-source identified and continue the larger public-block sweep.

No persistence parameter has been evaluated and no blind-set result was inspected while building this audit.
