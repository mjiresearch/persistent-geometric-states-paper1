# Post-VM97 / NGC6015 stationary H I checkpoint

Status: **NGC6015 SOURCE-NATIVE PGPLOT H I PROFILE PROMOTED; RECONCILE/RERANK NEXT**

- Frozen target: NGC6015 — calibration.
- Source: Verdes-Montenegro, Bosma & Athanassoula (1997), A&A 321, 754-764.
- Exact source asset: legacy A&A Figure 3 embedded `07540003.eps`, pure PGPLOT vector, zero raster operators.
- Figure 3d: 31 exact H I surface-density samples.
- Source-scale radial range: 14.944-315.080 arcsec = 1.007-21.233 kpc at D=13.9 Mpc.
- Sigma_HI range: 0.390-7.132 Msun pc^-2.
- Independent QC: recovered central/peak = 57.54% vs source ~57%; annular mass scale within 5.81% of paper total H I mass over represented profile coverage.
- Profile: `data/stationary/source_reconstruction/vm97_ngc6015_hi_profile_v1.csv`.
- Validation: `validation/stationary/vm97_ngc6015_native_hi_profile_recovery_v1.json`.
- No PostScript execution, raster digitization, OCR, helium scaling, profile fitting, persistence fitting, or blind-outcome inspection.
- `L_A` and `C_A` remain locked.

## Resume point
Reconcile/rerank and continue the new highest-ranked actionable Lelli family. Do not restart VM97 unless its explicit reopen rule is satisfied.
