# Ge04 stationary H I resume checkpoint

Status: **GE04 LIVE — ORIGINAL-SOURCE PROFILE AUDIT NEXT**

Use this file as the resume point after any interruption. Do not restart Ha14, Le14, Tr09, Sw02, or other disposed families unless their explicit reopen condition is satisfied.

## Locked analysis state
- `L_A` and `C_A` remain locked.
- Continue only the public H I source-profile acquisition/reconstruction freeze.

## Current chain
Lelli/SPARC galaxy -> Lelli Ref -> original observational paper -> exact public radial H I table/vector profile gate -> ingest or disposition -> rerank.

## Current live family from the canonical priority queue
- SPARC Ref: `Ge04`
- Reference: Gentile et al. 2004, MNRAS 351, 903 (`2004MNRAS.351..903G`).
- Frozen targets: `ESO079-G014` (calibration), `ESO116-G012` (blind).
- Priority count: 2 untouched frozen galaxies (1 calibration, 1 blind).

## Exact next action
Determine from Gentile et al. 2004 whether Ge04 is itself the original resolved H I observation/profile source for each target or redirects to earlier 21-cm observations. Then follow only the original observational branch and apply the exact public radius-vs-Sigma_HI table/vector gate.

No raster digitization, no moment-map/cube-to-profile reconstruction, no persistence fitting, and no blind-outcome inspection.
