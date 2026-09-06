# Conventional BeSSeL/Maser Streaming Field — Freeze V1

Freeze date: 2026-09-06
Status: FROZEN BEFORE EVALUATION AGAINST THE GRB H I RESIDUALS

## Purpose

Construct a spatially predictive conventional non-circular velocity field from the Reid et al. (2019) VLBI maser catalog and evaluate it at the four geometrically located GRB dust structures. The fit must not use the GRB H I velocities or their residuals at any stage.

## Source catalog

CDS/VizieR J/ApJ/885/131/table1, Reid et al. (2019), 199 high-mass star-forming regions with trigonometric parallax, east/north proper motions, LSR radial velocity, and spiral-arm labels.

Raw catalog URL:
https://cdsarc.cds.unistra.fr/ftp/J/ApJ/885/131/table1.dat

## Galactic constants

Use Reid et al. (2019) fit A5:

- R0 = 8.15 kpc
- z_sun = 0.0055 kpc
- U_sun = +10.6 km/s toward the Galactic center
- V_sun = +10.7 km/s in the direction of Galactic rotation
- W_sun = +7.6 km/s toward the north Galactic pole
- Theta0 = 236 km/s
- Universal Rotation Curve parameters a2 = 0.96, a3 = 1.62

The catalog V_LSR values use the standard LSR solar motion (U,V,W)=(10,15,7) km/s; convert them to heliocentric radial velocities before the Galactocentric transform.

## Target geometry only

The prediction code may read only the frozen GRB coordinates and X-ray geometric distances:

- GRB 221009A Outer: l=52.96 deg, b=+4.32 deg, d=13.9 kpc
- GRB 221009A OSC:   l=52.96 deg, b=+4.32 deg, d=19.0 kpc
- GRB 160623A Outer: l=84.17 deg, b=-2.69 deg, d=9.9 kpc
- GRB 031203 Outer:  l=255.74 deg, b=-4.80 deg, d=9.7 kpc

No H I velocity, Reid residual, residual sign, or persistence prediction is permitted as an input to field construction, bandwidth choice, clipping, or weighting.

## Maser eligibility

A maser enters the streaming-field sample iff:

1. parallax > 0;
2. fractional parallax uncertainty e_plx/plx <= 0.20;
3. Galactocentric radius R >= 4.0 kpc;
4. all required phase-space observables are finite;
5. Monte-Carlo propagated 1-sigma uncertainties in each peculiar-velocity component U_s, V_s, W_s are <= 20 km/s.

No source is removed because its peculiar velocity is large. No GRB-dependent spatial or arm selection is allowed.

## Phase-space transform

For each source, use d=1/plx (valid under the <=20% fractional-parallax cut), catalog proper motions, and heliocentric radial velocity. Transform to a Galactocentric Cartesian frame with the constants above. Define:

- U_s: peculiar velocity toward the Galactic center;
- V_s: peculiar velocity in the direction of rotation relative to the A5 URC;
- W_s: peculiar velocity toward the north Galactic pole.

Propagate catalog parallax, proper-motion, and radial-velocity uncertainties with 256 Gaussian Monte-Carlo draws per source, deterministic seed 20260906.

## Spatial field model

Primary model: non-parametric Gaussian-kernel local-constant vector field in Galactocentric (x,y), fitted to (U_s,V_s,W_s).

For a target position x_t and maser i,

w_i(h) = exp[-D_i^2/(2 h^2)] / (sigma_i^2 + sigma_int^2),

where D_i is planar Galactocentric separation, sigma_i is the propagated uncertainty for the component being predicted, and sigma_int=7 km/s is fixed before evaluation.

Candidate bandwidths are frozen to:

h in {1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0} kpc.

Select one global h by leave-one-out cross-validation on the maser sample only, minimizing the summed squared standardized prediction error across U_s,V_s,W_s. GRB data play no role in bandwidth selection.

## Target prediction and uncertainty

At each GRB geometry, predict U_s,V_s,W_s with the selected h. Report:

- predicted U_s,V_s,W_s;
- kernel effective sample size N_eff=(sum w)^2/sum(w^2), component-wise and minimum;
- nearest eligible maser distance;
- predicted line-of-sight streaming correction;
- bootstrap 16/50/84 percentiles using 2000 source-resampling realizations, seed 20260907.

Project the vector prediction to the line of sight using geometry only. If c_R is the line-of-sight projection coefficient for radial-outward velocity, c_phi for tangential velocity, and c_z for vertical velocity, then because U_s is positive inward,

Delta v_LOS,stream = -c_R U_s + c_phi V_s + c_z W_s.

## Support flag

Flag a target as weakly supported if either:

- minimum component N_eff < 3, or
- nearest eligible maser is farther than 2h.

Do not alter h or the sample in response to this flag.

## Locked comparison rule

This file freezes only the conventional prediction. After the prediction products are committed, they may be compared with the already measured GRB H I residuals. No refitting after that comparison is permitted under V1. Any later model must be labeled V2 and justified independently.
