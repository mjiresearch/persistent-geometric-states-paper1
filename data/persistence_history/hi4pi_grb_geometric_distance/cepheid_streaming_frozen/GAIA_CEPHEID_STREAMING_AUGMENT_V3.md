# Gaia-Cepheid streaming augmentation V3 — frozen protocol

Status: **FROZEN BEFORE H I COMPARISON**

V3 preserves all frozen V3 arm geometry/support rules and the V1 generic-Gaia sample while adding independent systemic-RV information only for otherwise unsupported Cepheids.

## Unchanged rules
- Same 3306-star period-Wesenheit distance catalog.
- Same Reid+2019 A5 Galactic constants/sign convention.
- Same frozen Outer and OSC arm loci.
- Same bandwidth grid h={1,2,3,4,5,7,10} kpc.
- Same support requirement: N_eff>=3 independently in U and V, nearest phase tracer<=2h, target within frozen arm width.
- RUWE<1.4, fractional distance error<=20%, R>=4 kpc, propagated U/V uncertainty<=20 km/s.
- No velocity clipping.
- GRB031203 remains excluded.

## Frozen RV hierarchy
For each Cepheid, select the first available source in this order:
1. VELOCE DR1 vgamma, only Binflag=F and NRV>=8; RV uncertainty floor=1.0 km/s.
2. Gaia DR3 vari_cepheid.average_rv, num_clean_epochs_rv>=8 and error<=5 km/s.
3. Gaia DR3 gaia_source.radial_velocity, rv_nb_transits>=8 and error<=5 km/s (the original V1 rule; retained so the original OSC support is not discarded).
4. Mel'nik et al. 2015 J/AN/336/70 heliocentric RV, coordinate-matched within 2 arcsec, e_HRV<=5 km/s.

No source is selected based on agreement with another RV catalog or with any GRB outcome.

## Prediction
Use the unchanged arm-conditioned kernel, leave-one-out U+V cross-validation, target-support qualification, LOS projection, and 2000-draw bootstrap from frozen V1.

## Outcome firewall
The builder must not read any H I spectrum, H I velocity, H I residual, previous GRB comparison outcome, or Persistence prediction.
