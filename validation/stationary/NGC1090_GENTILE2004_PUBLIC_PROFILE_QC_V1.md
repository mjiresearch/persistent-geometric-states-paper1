# NGC1090 Gentile et al. 2004 public H I profile QC v1

## Source
Public arXiv source package for Gentile et al. (2004), astro-ph/0403154. Figure 2 explicitly shows the radial neutral-hydrogen surface-density distribution. Filled triangles are the approaching side, open triangles the receding side, and filled circles the average. The source text states that NGC1090's radial distribution was computed by integrating the total-intensity map over concentric ellipses.

## Frozen-distance conversion
The published panel uses angular radius in arcsec, so no source-distance inference is needed. The digitized angular coordinates are converted directly with the frozen SPARC distance D=37.0 Mpc.

## Digitization
The average filled-circle marker was template-matched in the NGC1090 panel after an exact linear axis calibration. The retained series has 20 securely matched average points. A conservative 2-pixel coordinate uncertainty is carried into radius and surface-density digitization errors. No profile value was derived from SPARC Vobs or Vgas.

## Coverage
Digitized profile range on the frozen distance: 1.293--31.423 kpc. The frozen SPARC rotation-curve range is 0.35--30.09 kpc. Therefore 22/24 frozen source radii (1.60--30.09 kpc) are covered by interpolation inside the measured H I range. The two inner points at 0.35 and 1.07 kpc remain uncovered; no inward extrapolation is allowed.

## Independent physical QC
The paper independently tabulates r_HI/r_d=8.8 and r_opt=10.9 kpc, with r_opt=3.2 r_d, implying r_HI≈29.98 kpc on the paper's adopted scale. The digitized averaged profile crosses Sigma_HI=1 Msun pc^-2 at roughly 29--30 kpc on the frozen SPARC distance. This is consistent at the few-percent level and is independent of the persistence model.

## Decision
**PROMOTE.** NGC1090 is accepted as a public publication-figure radial H I profile. It may enter the stationary source build only at frozen SPARC radii lying inside the digitized profile's measured radial range. No extrapolation is permitted.
