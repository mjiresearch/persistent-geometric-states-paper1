# V2 frozen coarse baseline

Date marked: 2026-09-06

`CONVENTIONAL_BESSEL_STREAMING_FREEZE_V2.md` and every product under `outputs_v2/` are immutable historical baseline products. They must not be edited, regenerated with changed conventions, or silently replaced.

Scientific status: V2 is the support-qualified **coarse all-arm Cartesian baseline**. It uses a 5 kpc global Gaussian kernel in Galactocentric `(x,y)` and therefore mixes spiral-arm membership and arm phase. It is retained for auditability and sensitivity comparison only.

V3 is a new, separately frozen model. V3 must not read any GRB H I velocity, H I residual, V1/V2 predicted residual, or Persistence prediction during construction or hyperparameter selection.
