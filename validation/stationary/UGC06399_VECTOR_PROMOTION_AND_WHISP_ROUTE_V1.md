# UGC06399 vector-profile promotion + WHISP route audit v1

## UGC06399 — PROMOTED

Source: Verheijen & Sancisi (2001), public arXiv source archive `astro-ph/0101404`, appendix PostScript `figA01b.ps`.

The radial H I surface-density panel is true vector PostScript. Axis calibration was recovered from vector tick geometry, not raster digitization:

- radial major ticks: 0, 1, 2 arcmin;
- H I surface-density major ticks: 0, 1, 2, 3, 4, 5 Msun pc^-2;
- solid radial profile: one continuous 13-segment / 14-vertex vector chain.

The profile is stored at:

`data/stationary/source_reconstruction/ugc06399_verheijen2001_vector_profile_v1.csv`

Frozen SPARC distance: 18.0 Mpc. The vector profile crosses Sigma_HI = 1 Msun pc^-2 at R ~= 8.72 kpc, compared with the independently tabulated SPARC R_HI = 8.80 kpc. This approximately 1% agreement is the independent physical QC used for promotion.

The measured profile spans 0.0--11.362 kpc and covers all 9 frozen SPARC stationary radii for UGC06399 (0.87--7.85 kpc), so no radial H I extrapolation is required.

Promotion changes the public-data checkpoint from 17 galaxies / 898 H I bins / 496 source rows to:

**18 galaxies / 912 H I bins / 505 source rows.**

No observational rotation velocity was used to construct the H I profile.

## WHISP / remaining Verheijen systems — NOT YET PROMOTED

The completed public-route artifact confirms:

- the WHISP homepage is reachable;
- `Database/database_top.html` is reachable;
- the Overview Catalog and Database Status infrastructure remain reachable;
- the historical A&A PostScript/PDF endpoints return HTTP 403 to automated CI;
- the arXiv paper/source archive remains reachable and is the successful route used for UGC06399.

The live WHISP database pages currently expose catalog/navigation/status infrastructure, but the audited route has not yet produced a stable direct public cube, moment map, or numerical radial-profile URL for the remaining Verheijen candidates. Therefore none of those systems is promoted on the basis of this audit alone.

### Frozen interpretation

1. UGC06399 is a valid direct public radial H I profile and is now part of the harmonized public source set.
2. Do not infer that the remaining Verheijen galaxies are recovered because their catalog pages are reachable.
3. Continue from the WHISP Overview Catalog toward individual galaxy/product records and modern WSRT public archive mirrors.
4. If only atlas graphics are available, recover identifiable vector/map products galaxy-by-galaxy; do not assign anonymous Figure-8 curves.
5. `L_A` and `C_A` remain locked until the stationary source-profile freeze is complete.
