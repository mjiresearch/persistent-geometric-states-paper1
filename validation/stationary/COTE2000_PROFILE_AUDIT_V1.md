# Côté et al. (2000) direct radial gas-profile audit v1

**Status:** SOURCE FAMILY IDENTIFIED; NUMERICAL DIGITIZATION PENDING  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `C_A` remain locked.

## Source

S. Côté, C. Carignan & K. C. Freeman (2000), **“The Various Kinematics of Dwarf Irregular Galaxies in Nearby Groups and Their Dark Matter Distributions,”** *The Astronomical Journal* **120**, 3027–3059. DOI: `10.1086/316883`.

The paper presents H I imaging of eight dwarf irregular galaxies. Section 5.2 explicitly states that total H I distributions were integrated along ellipses using the orientation parameters derived from the velocity-field analysis to produce the radial surface-density distributions shown in **Figure 3**.

## Exact crossmatch to the frozen 149-galaxy stationary master

The Côté et al. (2000) eight-object sample is:

- UGCA 442
- SDIG
- NGC 625
- ESO 245-G05
- ESO 381-G20
- DDO 161
- ESO 444-G84
- ESO 325-G11

Exactly three objects overlap the frozen Paper I stationary master:

| Paper identifier | Frozen SPARC identifier | Frozen role | Frozen distance (Mpc) | Frozen inclination (deg) |
|---|---|---:|---:|---:|
| UGCA 442 | UGCA442 | blind | 4.35 | 64 |
| DDO 161 | DDO161 | calibration | 7.50 | 70 |
| ESO 444-G84 | ESO444-G084 | blind | 4.83 | 32 |

These are the **Côté 2000 three-profile family** for the stationary source-profile build. No other Côté 2000 object is to be promoted into the frozen 149-galaxy sample.

## Figure/profile construction in the source paper

Section 5.2 states that the plotted radial profiles were constructed by:

1. integrating the total H I distributions along ellipses using the adopted orientation parameters;
2. multiplying the radial profiles by **4/3** to account for primordial helium; and
3. multiplying by the cosine of the inclination angle for deprojection.

The mass-model discussion further states that the gas distribution uses the H I radial surface-density profiles, with the **high-resolution profile at small radius combined with the low-resolution profile at large radius**.

Therefore Figure 3 is a direct observational radial gas-surface-density source, not a reconstruction from the SPARC `Vgas` curve.

### Critical helium rule

The Figure 3 ordinate is **not raw H I alone**: the paper has already applied a 4/3 primordial-helium correction. A digitized Figure 3 value must therefore be archived as the source-paper gas quantity and **must not receive another helium multiplication**.

For a canonical raw-H-I intermediate product, use

`Sigma_HI = Sigma_gas_Cote2000 * 3/4`

before applying the single globally frozen Paper I helium convention. The source value itself must also be retained unchanged for provenance/QC.

## Inclination/deprojection compatibility

The source-paper central inclinations for the three overlaps are:

| Galaxy | Côté 2000 inclination | Frozen SPARC inclination | Central-value mismatch |
|---|---:|---:|---:|
| UGCA442 | 64 deg | 64 deg | 0 deg |
| DDO161 | 70 deg | 70 deg | 0 deg |
| ESO444-G084 | 32 deg | 32 deg | 0 deg |

Thus the central inclination convention used to deproject the published profiles agrees with the frozen stationary metadata for all three galaxies. No inclination-amplitude rescaling is warranted at this stage.

The paper notes a substantial inclination uncertainty for DDO161 and correspondingly large uncertainty in its peak surface density; that uncertainty must be retained in the profile QC/provenance record rather than silently suppressed.

## Source distance convention

Côté et al. (2000) used group distances of:

- Sculptor group: **2.5 Mpc**;
- Centaurus A group: **3.5 Mpc**.

For this three-profile family that means:

| Galaxy | Source distance convention (Mpc) | Frozen stationary distance (Mpc) |
|---|---:|---:|
| UGCA442 | 2.5 | 4.35 |
| DDO161 | 3.5 | 7.50 |
| ESO444-G084 | 3.5 | 4.83 |

The numerical ingestion must preserve the source angular-radius coordinate when available and store the source-distance conversion separately from the canonical frozen-distance conversion. The source paper's old group distance must not silently overwrite the frozen stationary distance.

## Observational resolution / beam

The observing log gives the following synthesized beams for the relevant H I data:

| Galaxy | Instrument/configuration context | Beam |
|---|---|---:|
| UGCA442 | ATCA | 40 x 40 arcsec |
| DDO161 | VLA | 13 x 13 arcsec |
| ESO444-G084 | ATCA | 22 x 22 arcsec |

The paper specifically notes that DDO161 has the highest spatial resolution of the sample (about 0.22 kpc per beam under its source-distance convention) and reports a peak gas/H I surface-density scale near 21 `Msun pc^-2`, with large inclination-driven uncertainty. This is a useful future digitization QC anchor, not a substitute for the radial data points.

## Figure 3 digitization status

The full article text and Figure 3 caption are publicly discoverable and identify the correct direct-profile figure. The search-index rendering also exposes the plotting-axis tick sequences, but it does **not** provide the curve coordinates with sufficient fidelity for scientific ingestion.

Accordingly:

- source/article match: **COMPLETE**;
- frozen-master crossmatch: **COMPLETE**;
- source quantity/convention audit: **COMPLETE**;
- numerical radial-profile extraction: **PENDING**;
- profile ingestion into `stationary_hi_profiles_v1.csv`: **PENDING**;
- source-profile freeze: **NOT OPEN**.

No point values will be fabricated from the caption, mass model, Figure 13 ratios, `Vgas`, or approximate axis ranges.

## Acceptance criteria for promotion to the galaxy database

Each of the three Côté profiles may be promoted only after the Figure 3 curve is recovered at sufficient graphical/data fidelity and the following are stored:

1. galaxy identifier and frozen stationary role;
2. raw source radial coordinate and units;
3. raw digitized source surface-density quantity and units;
4. explicit marker that the source curve already includes the 4/3 helium correction;
5. canonical raw-H-I intermediate (`3/4` of the plotted source quantity), if used;
6. source and frozen distance conventions separately;
7. inclination/deprojection convention;
8. beam/resolution metadata;
9. digitization method/version and QC residuals/anchors; and
10. full citation/DOI/Figure 3 provenance.

Until those conditions are met, these three galaxies remain **source identified / digitization pending**, not “profile ingested.”
