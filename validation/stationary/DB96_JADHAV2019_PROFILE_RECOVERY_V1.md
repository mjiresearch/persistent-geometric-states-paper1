# de Blok 1996 source family — public analytic H I recovery via Jadhav & Banerjee 2019

**Status:** FIVE OF EIGHT FROZEN `dB96` TARGETS NOW HAVE PUBLIC ANALYTIC H I PROFILES  
**Date:** 2026-08-12  
**SPARC/Lelli source family:** `dB96`  
**Scientific boundary:** source acquisition only. `L_A` and `\mathcal C_A` remain locked.

## 1. Original dB96 source state

W. J. G. de Blok, S. S. McGaugh & J. M. van der Hulst (1996), *MNRAS* 283, 18–54, presents VLA/WSRT 21-cm H I observations of 19 late-type low-surface-brightness galaxies.

The public arXiv source confirms that the authors derived radial H I column-density profiles from the H I maps and corrected them for inclination to obtain radial **H I surface-density profiles**. No machine-readable radial-profile table is present in the arXiv package.

The arXiv record notes that Figure 2 was omitted from the submission, but the manuscript text identifies Figure 2 as a rotation-curve comparison. Therefore that missing historical figure is **not pursued as an H I-profile recovery route**.

The dB96 paper treats the published quantity as H I surface density. Later mass-modelling papers explicitly multiply the dB96 H I surface densities by about 1.4 to include helium/metals, independently confirming that the source values themselves should be retained as **raw atomic H I** at acquisition.

## 2. New public analytic republication

V. Jadhav Y & A. Banerjee (2019), **“The specific angular momenta of superthin galaxies: Cue to their origin?”**, *MNRAS* 488, 547–556, DOI `10.1093/mnras/stz1680`, arXiv `1906.10039`, uses literature H I surface-density profiles for nine LSB galaxies and publishes best-fitting analytic H I profile parameters in Table 7.

The paper states that for its LSB sample the H I surface-density profiles were available from de Blok et al. (2001). These are the same named LSB systems for which the SPARC/Lelli provenance includes the earlier dB96 H I source family. The 2019 fit is therefore used as a **public analytic representation / republication route**, not as proof that the 1996 arXiv graphics themselves were numerically recoverable.

### Analytic form

The paper gives the off-centred double-Gaussian model

`Sigma_HI(R) = S01 exp[-(R-a1)^2/(2 r01^2)] + S02 exp[-(R-a2)^2/(2 r02^2)]`

where the amplitudes are in `Msun pc^-2` and the offsets/scale lengths are in kpc. The paper explicitly says the gas disc calculation considers **atomic hydrogen (H I) surface density only**; molecular gas is neglected for the LSB systems.

No helium factor is applied to these source-profile parameters in Paper I acquisition.

## 3. Frozen Paper I targets recovered

The SPARC/Lelli `dB96` untouched family contains eight frozen galaxies:

- F565-V2 — blind
- F568-3 — calibration
- F568-V1 — calibration
- F571-8 — calibration
- F571-V1 — calibration
- F574-1 — blind
- F583-1 — calibration
- F583-4 — calibration

Jadhav & Banerjee Table 7 supplies analytic H I fits for five of them:

| Galaxy | Frozen role | Public analytic status |
|---|---|---|
| F568-3 | calibration | recovered; one Gaussian component |
| F568-V1 | calibration | recovered; two Gaussian components |
| F574-1 | blind | recovered; two Gaussian components |
| F583-1 | calibration | recovered; two Gaussian components |
| F583-4 | calibration | recovered; two Gaussian components |

Thus this route adds **5 actual public analytic profiles = 4 calibration + 1 blind**.

The exact parameters and quoted uncertainties are stored in:

`data/stationary/source_reconstruction/jadhav_banerjee2019_lsb_hi_analytic_profiles_v1.csv`

## 4. Still unresolved within the dB96 family

- F565-V2 — blind
- F571-8 — calibration
- F571-V1 — calibration

These remain `direct_HI_source_known / numeric_profile_pending` until a genuinely new public table, map, fit, or republication route is identified.

## 5. Acceptance / normalization boundary

The analytic forms are preserved exactly as published. They are **not yet** resampled onto the Paper I common radial grid, renormalized to SPARC distances/inclinations, or multiplied by a helium factor. Those operations belong to the later globally frozen normalization step.

The second Gaussian component is absent for F568-3 and remains absent rather than being invented. The negative fitted `a1` for F583-4 is retained exactly as published.

## 6. Anti-loop decision

Do not chase the omitted dB96 Figure 2 for H I-profile recovery: source text identifies it with the rotation-curve presentation, and a valid newer public analytic H I route now exists for five of the eight frozen targets.

Continue the Lelli-directed source-family queue for the remaining unresolved galaxies and other high-yield source blocks.

No persistence parameter or blind result was inspected in making this acquisition decision.
