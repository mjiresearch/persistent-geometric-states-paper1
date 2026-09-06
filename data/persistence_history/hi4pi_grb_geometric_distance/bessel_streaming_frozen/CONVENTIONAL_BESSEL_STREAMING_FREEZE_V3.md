# Conventional BeSSeL/Maser Streaming Field — Freeze V3

Freeze date: 2026-09-06
Status: FROZEN BEFORE COMPARISON TO GRB H I OUTCOMES
Parent: V2 remains immutable as the coarse all-arm Cartesian baseline.

## Purpose

V3 addresses three pre-outcome methodological issues identified in the sign/field audit:

1. use the exact historical standard solar motion `(U,V,W)=(10.3,15.3,7.7) km/s` in the catalog `V_LSR -> heliocentric` conversion;
2. estimate in-plane spiral streaming `(U,V)` independently from the vertical/warp component `W`;
3. condition the in-plane interpolation on spiral-arm membership and position along the fitted arm, rather than smoothing all arms together in Cartesian `(x,y)`.

No GRB H I velocity, H I residual, V1/V2 predicted residual, or Persistence prediction may be read by the V3 builder or used for model selection.

## Inputs

- Reid et al. (2019), VizieR `J/ApJ/885/131/table1`.
- Frozen geometry-only target file: `frozen_grb_geometry_only.csv` containing only `(target, arm, l, b, geometric distance)`.
- Reid A5 Galactic constants retained for the Galactocentric transformation and URC: `R0=8.15 kpc`, `Theta0=236 km/s`, `(U_sun,V_sun,W_sun)=(10.6,10.7,7.6) km/s`, `a2=0.96`, `a3=1.62`.

## Maser quality boundary

Inherited from V1/V2 except for the exact standard-LSR correction:

- finite parallax, proper motions and VLSR;
- positive parallax;
- fractional parallax uncertainty <=20%;
- Galactocentric radius `R>=4 kpc`;
- propagated 1-sigma peculiar-velocity uncertainty <=20 km/s in every component;
- no peculiar-velocity clipping by value or sign;
- 256 Monte Carlo draws per source for measurement-error propagation;
- intrinsic velocity floor `sigma_int=7 km/s`.

## Sign convention

- `+U`: radially inward, toward the Galactic center.
- `+V`: direction of Galactic rotation, relative to the Reid A5 circular speed.
- `+W`: toward the North Galactic Pole.
- Positive LOS residual means the source is more positive / less negative in LSR velocity than the axisymmetric Reid prediction.

## V3 in-plane arm model

For each target arm separately:

1. Select only eligible masers with the same Reid spiral-arm designator. Human target label `Outer` maps only to Reid `Out*` designators; `OSC` maps only to Reid `OSC*` designators. No adjacent-arm borrowing is allowed.
2. Require at least 4 eligible same-arm masers before any U/V prediction is possible.
3. Fit a logarithmic spiral using positions only:
   `ln R = alpha + beta * phi`, with azimuth unwrapped around the target azimuth.
4. Define along-arm arc coordinate `s` from the fitted logarithmic spiral and a perpendicular arm-locus offset `d_perp`.
5. Interpolate U and V independently with a Gaussian kernel in along-arm coordinate. Same-arm masers are additionally weighted by their perpendicular consistency with the fitted arm locus. No W information participates in U/V fitting.
6. Candidate along-arm bandwidths are `h={1,2,3,4,5,7,10} kpc`.
7. For each arm, choose the bandwidth with the smallest leave-one-out standardized squared error across U and V among bandwidths that satisfy the target-support requirements below for every frozen target assigned to that arm.

### U/V target-support requirements

A target is support-qualified only when all are true:

- same-arm eligible masers >=4;
- `N_eff_U>=3` and `N_eff_V>=3`;
- nearest same-arm maser along-arm separation <=`2h`;
- target perpendicular offset from the fitted arm locus <= `max(1.0 kpc, 2*sigma_arm)` where `sigma_arm` is the robust same-arm perpendicular scatter.

If no bandwidth qualifies for an arm, every target on that arm receives `NO_INPLANE_PREDICTION`. In particular, sparse OSC sampling must remain unsupported rather than borrowing from Outer/Perseus/Local-arm masers.

## V3 vertical/warp model

`W` is estimated independently of U/V using all eligible masers and no arm labels. The frozen empirical vertical field is a weighted linear model in Galactocentric radius and azimuth:

`W = a0 + aR*dR + a1*sin(phi) + b1*cos(phi) + aR1*dR*sin(phi) + bR1*dR*cos(phi)`,

where `dR=R-R0`. Weights are `1/(sigma_W^2 + sigma_int^2)`. No W-value clipping is allowed.

This is a velocity-field nuisance model, not a geometric warp-height model. It is kept separate because the GRB sightlines have small |b| and therefore weak LOS sensitivity to W.

## Uncertainty

- 2000 bootstrap resamples.
- U/V resampling is within the same target arm only.
- W resampling uses the full eligible maser sample independently.
- Report in-plane LOS, vertical LOS, total LOS, and 16/50/84 percentiles where U/V support exists.
- If U/V support fails, report W separately but total conventional streaming prediction is `NO_PREDICTION`.

## Immutable outputs

V3 outputs are written only to `bessel_streaming_frozen/outputs_v3/` and are never used to alter V2. After successful execution, the V3 protocol and outputs are frozen. Any later change requires V4 with an explicit pre-outcome reason.
