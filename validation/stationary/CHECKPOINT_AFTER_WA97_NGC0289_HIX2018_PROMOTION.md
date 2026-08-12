# Post-Wa97 / NGC0289 stationary H I checkpoint

Status: **NGC0289 EXACT PUBLIC LATER-DIRECT H I PROFILE PROMOTED; RECONCILE/RERANK NEXT**

- Frozen target: NGC0289 — calibration.
- Lelli/SPARC source code: Wa97, Walsh et al. (1997). Original Figure 6 is a direct deprojected radial H I surface-density profile, but the public ADS article is raster-only.
- Rescue source: Lutz et al. (2018), HIX survey II, new/direct ATCA H I observations.
- Exact asset: arXiv source `Images/app-fig3.pdf`, Figure A3 panel (b), 52 native filled vector markers.
- Semantics: radial H I column density measured from elliptical annuli in the non-clipped moment-0 map; TiRiFiC inclination/PA set annulus geometry.
- Source distance: 23.06 Mpc; source radius range 0.830-85.459 kpc.
- Frozen SPARC distance: 20.8 Mpc; corresponding frozen radius range 0.748-77.084 kpc.
- Sigma_HI range: 1.249-6.337 Msun pc^-2; helium not applied.
- Independent QC: outer-bin linear crossing at Sigma_HI=1 gives 87.456 kpc vs published R_HI=86.9 kpc (0.64% difference before small beam correction).
- Profile: `data/stationary/source_reconstruction/hix2018_ngc0289_hi_profile_v1.csv`.
- No OCR, raster digitization, profile fitting, persistence fitting, or blind-outcome inspection.
- `L_A` and `C_A` remain locked.

## Resume point
Reconcile/rerank and continue the new highest-ranked actionable Lelli family. Do not repeat the Wa97 raster route unless its reopen rule is satisfied.
