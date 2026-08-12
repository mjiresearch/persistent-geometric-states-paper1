# Post-CP90 stationary H I checkpoint

Status: **CP90 NGC0300 PROMOTED; RECONCILE/RERANK NEXT**

- NGC0300 — calibration — 20 exact native Westmeier et al. 2011 Table-2 rows.
- Radius: 100-2000 arcsec; 0.92-18.42 kpc on source-paper scale.
- Quantity: face-on gas mass surface density derived from H I column density; helium x1.4 already included.
- This is a later deeper ATCA public replacement for the CP90/Lelli branch, not a numeric recovery of Puche et al. 1990.
- Profile artifact: `data/stationary/source_reconstruction/westmeier2011_ngc300_gas_profile_v1.csv`
- Other CP90 frozen members were verified as already resolved and left unchanged: `[{"existing_rows": "38", "existing_source": "Leroy et al. 2008 / THINGS", "galaxy": "NGC7793", "role": "blind"}]`
- `L_A` and `C_A` remain locked.

## Resume point
Run reconciliation/ranking and continue the new highest-ranked actionable Lelli family. Do not restart CP90 unless its reopen rule is satisfied.

## Reranked live queue
Next actionable family: **Ca88** — 1 untouched frozen galaxies (1 calibration, 0 blind). Galaxies: UGC02259.

Untouched frozen galaxies remaining: 92.
