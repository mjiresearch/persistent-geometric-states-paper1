# Begum / Chengalur direct H I profile audit v1

**Status:** THREE FROZEN TARGETS CONFIRMED IN THE PUBLIC BEGUM/FIGGS BLOCK; KK98-251 ANALYTIC PROFILE RECOVERED; NGC3741 AND CamB NUMERICAL/PROFILE REPRESENTATIONS PENDING  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `C_A` remain locked.

## 1. Frozen-master matches / targets

The Begum/Chengalur literature supplies three confirmed frozen Paper I targets through public primary H I sources:

| Frozen galaxy | Frozen role | FIGGS identity | Frozen distance (Mpc) | Frozen inclination (deg) | Direct source status |
|---|---|---|---:|---:|---|
| CamB | calibration | **KK 44** | 3.36 | 65 | dedicated public GMRT H I paper identified; exact radial surface-density representation pending |
| KK98-251 | calibration | **KK 251** | 6.80 | 59 | **exact analytic H I radial profile recovered** |
| NGC3741 | calibration | NGC 3741 | 3.21 | 70 | direct radial gas profile identified; numerical curve recovery pending |

The FIGGS overview/sample tables now independently confirm all three targets once catalogue aliases are reconciled. The earlier direct-name-only statement that NGC3741 was the sole obvious FIGGS overlap is superseded.

### Alias reconciliation

- **CamB = KK 44.** FIGGS Table 1 lists KK 44 at RA 04:53:06.90, Dec +67:05:57, matching the CamB identification used in the dedicated Begum, Chengalur & Hopp literature. FIGGS therefore provides an additional public survey-level H I inventory route for CamB.
- **KK98-251 = KK 251.** FIGGS Table 3 explicitly lists KK 251 and gives reference 13, Begum & Chengalur (2004b), matching the dedicated KK98 250/251 GMRT study. This confirms the catalogue mapping used by the Paper I frozen master.
- **NGC3741** appears directly under the same name in FIGGS.

No new galaxy is added to the frozen 149-member sample; this is source/alias reconciliation only.

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
- FIGGS H I inclination: 59 +/- 5 deg
- frozen Paper I inclination: 59 deg

The analytic source is preserved in its native angular-radius form so no source-distance assumption is baked into the radial coordinate. For QC only, the frozen-distance conversion is `1 arcsec = 0.0329673 kpc`, giving `r0 = 1.12748 kpc` and `c = 0.632972 kpc` at 6.8 Mpc. These are derived checks, not replacements for the native angular parameters.

No inclination-amplitude rescaling is applied ad hoc here; source and frozen inclinations are retained for the later single global normalization rule.

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
- FIGGS membership: **confirmed**
- helium convention: **confirmed (x1.3 already applied in Figure 5)**
- map resolution: **confirmed (11 x 9 arcsec)**
- source distance: **confirmed (3.03 Mpc)**
- numerical Figure 5 curve coordinates: **pending**

The publisher exposes the Figure 5 image, but the current retrieval path has not provided a machine-readable/vector point table. A direct high-resolution publisher image route was attempted and did not yield a reusable extraction object in the current environment. Per the project anti-loop rule, the curve remains `numeric_pending` unless a genuinely new high-fidelity route appears; no points are inferred from axis ranges, a later reconstruction, or SPARC `Vgas`.

---

## 4. CamB / KK 44 — dedicated public GMRT route

### Primary source

A. Begum, J. N. Chengalur & U. Hopp, **“The little galaxy that could: kinematics of Camelopardalis B,”** *New Astronomy* 8, 267–280; DOI `10.1016/S1384-1076(02)00238-5`; arXiv `astro-ph/0301194`.

The paper presents deep high-velocity-resolution GMRT H I imaging of CamB and adopts a source distance of **2.2 Mpc**. The frozen Paper I values are **3.36 Mpc** and **65 deg**.

FIGGS independently includes the same object as **KK 44**, providing a public survey-level H I inventory entry for the frozen CamB calibration galaxy.

### Current profile status

The dedicated paper clearly contains the H I imaging and mass-model inputs, but in this audit pass the exact radial H I surface-density representation, its helium treatment, profile radius coordinate, and source deprojection convention have **not yet been verified to the standard required for numerical promotion**.

Therefore CamB is currently:

`primary_public_HI_paper_identified / FIGGS_alias_confirmed / radial_profile_representation_pending`.

This is a real public-source upgrade, but it is intentionally not mislabeled as `profile_data_ingested` yet.

---

## 5. FIGGS context / alias control

Begum et al. (2008), **“FIGGS: Faint Irregular Galaxies GMRT Survey — overview, observations and first results,”** MNRAS 386, 1667–1682; DOI `10.1111/j.1365-2966.2008.13150.x`; arXiv `0802.3982`, supplies a public primary sample/observation inventory.

For this Paper I block, the durable FIGGS crossmatch is:

- KK 44 -> **CamB** -> calibration
- KK 251 -> **KK98-251** -> calibration
- NGC 3741 -> **NGC3741** -> calibration

This alias mapping is now part of the provenance record and must be used in later global source reconciliation.

---

## 6. Acceptance / next actions

### KK98-251

**Recovered source profile:** yes, analytically.  
**Safe next action:** preserve analytic parameters/native angular radius; defer common kpc normalization, any inclination rescaling, helium scaling and radial resampling until the global rules are frozen.

### NGC3741

**Recovered source profile:** source/convention yes; numerical curve no.  
**Safe next action:** retain `numeric_pending` unless a new vector/table/data route appears; do not loop on the failed image route.

### CamB

**Recovered source profile:** public primary H I paper and FIGGS alias yes; exact radial representation no.  
**Safe next action:** one primary-text/figure verification pass for a direct radial surface-density representation or analytic fit; if unavailable at sufficient fidelity, retain as public-source identified and continue the larger public-block sweep.

No persistence parameter has been evaluated and no blind-set result was inspected while building this audit.
