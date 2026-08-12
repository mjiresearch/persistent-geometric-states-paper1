# CP90 stationary H I resume checkpoint

Status: **CP90 LIVE — WESTMEIER 2011 MACHINE-READABLE SOURCE-TABLE ROUTE NEXT**

Use this as the exact resume point after interruption. Do not restart Bl04, Ba05, Ge04, dB97/dB96, Ha14, Le14, or Tr09.

## Locked state
- `L_A` and `C_A` remain locked.
- Public H I source acquisition only; no blind-outcome inspection.

## Current Lelli/SPARC family
- Ref: `CP90`
- Current untouched target: `NGC0300`
- Frozen role from reranked queue: calibration
- Original observing paper: Puche, Carignan & Bosma 1990, AJ 100, 1468, *H I Studies of the Sculptor Group Galaxies. VI. NGC 300* (VLA 21-cm observations; bibcode 1990AJ....100.1468P).

## Higher-fidelity public replacement route
Westmeier, Braun & Koribalski 2011, MNRAS 410, 2217 (arXiv:1009.0317) obtained deeper ATCA H I observations over the full NGC300 H I disk. The paper explicitly derives the radial H I column-density profile with GIPSY ELLINT and converts it to face-on gas mass surface density with a factor 1.4 for helium. The resulting radial `Sigma_gas(r)` values are published in Table 2.

This is a later independent, higher-fidelity public profile route, analogous to the later public-source replacements already permitted in the stationary overlay. It does not claim to numerically recover the CP90 VLA profile itself.

## Exact next action
Inspect the authors' arXiv source (`1009.0317`) for Table 2 numeric rows. If the table is present in TeX/source form, ingest the exact published radius and Sigma_gas values unchanged with helium status explicitly recorded; validate row/radius endpoints against the paper and promote NGC0300. If the source table is not machine-readable, audit the public HTML table route next.

No raster digitization, no map/cube-to-profile reconstruction, no persistence fitting.
