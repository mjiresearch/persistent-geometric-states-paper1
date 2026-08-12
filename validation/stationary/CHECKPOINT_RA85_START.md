# RA85 stationary H I resume checkpoint

Status: **RA85 LIVE — HUNTER 2013 LATER WHISP PROFILE ROUTE NEXT**

Use this as the exact resume point after interruption. Do not restart Ca88, El10, JC90, CP90, Bl04, Ba05, Ge04, or any earlier closed source family.

## Locked state
- `L_A` and `C_A` remain locked.
- Public H I source-profile acquisition only.
- No raster digitization, map/cube-to-profile reconstruction, persistence fitting, or blind-outcome inspection.

## Current Lelli/SPARC family
- Ref: `RA85`
- Target: `UGC02885`
- Frozen role: calibration
- Original source: Roelfsema & Allen 1985, A&A 146, 213-222, *Radio observations of H I in UGC 2885, the largest identified Sc galaxy*.

## Later independent higher-fidelity route
Hunter et al. 2013, AJ 146, 92 (arXiv:1307.7116), *Star Formation in Two Luminous Spiral Galaxies*, explicitly uses H I data for UGC 2885 retrieved from the WHISP archives. Later documentation identifies these as WSRT observations taken in 2004 and reported by Hunter et al. 2013, so this is not treated as a numerical republication of the 1985 RA85 data.

Hunter et al. determine H I surface densities from the integrated H I maps using GIPSY and publish a face-on H I+He surface-density radial profile for UGC 2885 in Figure 14.

## Exact next action
Audit the Hunter et al. 2013 arXiv source (`1307.7116`) for:
1. a machine-readable radial H I/H I+He profile table or numeric sidecar;
2. the exact Figure-14 profile asset and whether it contains source-native vector profile geometry;
3. explicit helium treatment and source distance/radius units.
If exact numeric/vector values are recoverable, ingest them as a later independent WHISP replacement for the RA85/Lelli branch. If raster-only/no table, record the public-route boundary and rerank.
