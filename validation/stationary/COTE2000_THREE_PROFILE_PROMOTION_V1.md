# Cote, Carignan & Freeman (2000) three-profile promotion — V1

## Status

PROMOTED: DDO161, ESO444-G084, and UGCA442.

## Public source

Cote, Carignan & Freeman (2000), AJ 120, 3027, public IOP PDF. Figure 3 gives gas radial surface-density distributions. Section 5.2 states that the H I radial distributions were integrated in ellipses and then scaled by 4/3 for primordial helium and by cos(i) for deprojection.

## Numerical extraction

The public PDF preserves the Figure 3 axes and filled profile markers as vector objects. Marker centers were recovered from the PDF drawing geometry and calibrated from the vector tick marks. The committed table is `data/stationary/source_reconstruction/cote2000_vector_profiles_v1.csv`.

For the persistence-source dataset, the plotted gas surface densities are divided by 4/3 to restore hydrogen-only Sigma_HI. The plotted gas values are retained in a separate column for provenance/QC.

## Independent radius QC

The source-figure plotted-gas Sigma=1 crossings are:

- UGCA442: 4.341 kpc; SPARC R_HI = 4.37 kpc; difference -0.66%.
- DDO161: 10.727 kpc; SPARC R_HI = 10.69 kpc; difference +0.35%.
- ESO444-G084: 2.918 kpc; SPARC R_HI = 2.95 kpc; difference -1.08%.

This near-identity is an external check on the axis calibration and galaxy assignment. The hydrogen-only profiles used by the source model are the same vector measurements after removal of the documented 4/3 helium factor.

## Frozen distances and coverage

- UGCA442: D=4.35 Mpc; vector profile extends to 6.327 kpc; frozen SPARC radii extend to 6.33 kpc (rounding-equivalent endpoint).
- DDO161: D=7.50 Mpc; vector profile extends to 16.90 kpc; frozen SPARC radii extend to 13.37 kpc.
- ESO444-G084: D=4.83 Mpc; vector profile extends to 5.79 kpc; frozen SPARC radii extend to 4.44 kpc.

No H I extrapolation is introduced.

## Guardrail

No SPARC Vgas value was inverted or used to determine any profile point. SPARC R_HI was used only as an external post-extraction QC diagnostic.
