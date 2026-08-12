# Le14 upstream H I source split checkpoint

Status: **LE14 SPLIT RESOLVED; UGC4483 FIGURE-6 VECTOR GATE LIVE**

Lelli/SPARC family: `Le14` = Lelli, Verheijen & Fraternali 2014, A&A 566 A71.
Frozen targets: `NGC4068` and `UGC04483`, both calibration.

## NGC4068

- Le14 Table B.1 identifies the original H I cube as **Swaters et al. 2002 (WHISP)**.
- The Sw02 family has already been audited in the stationary acquisition ledger: the historical atlas was recovered but target profile figures are raster-dominant and no exact numeric/vector radial profile route was found.
- Do **not** reopen Sw02 absent its explicit reopen condition.

## UGC04483 / UGC 4483

- Le14 Table B.1 points to **Lelli et al. 2012b, A&A 544 A145** as the dedicated H I analysis.
- That paper analyses archival VLA B+C observations originally described by van Zee et al. 1998.
- Lelli et al. 2012b Figure 6 explicitly publishes inclination-corrected H I surface-density profiles for the northern side, southern side, and entire galaxy.
- The whole-galaxy azimuthally averaged profile is the gas profile used for the mass model.
- Live gate: inspect the arXiv source asset for Figure 6 and recover the whole-galaxy radial H I profile **only if exact source-native vector geometry/numeric arrays are present**.

## Boundary

No raster digitization, map-to-profile reconstruction, profile fitting, persistence fitting, normalization, or blind-outcome inspection. `L_A` and `C_A` remain locked.

## Resume point

If interrupted, **do not restart Le14 or Ha14**. Continue at `UGC04483 -> Lelli et al. 2012b -> Figure 6 source-native vector/numeric audit`. If recovered, ingest/promote UGC04483; NGC4068 remains on the already-audited Sw02 disposition unless a genuinely new public mechanism is found.
