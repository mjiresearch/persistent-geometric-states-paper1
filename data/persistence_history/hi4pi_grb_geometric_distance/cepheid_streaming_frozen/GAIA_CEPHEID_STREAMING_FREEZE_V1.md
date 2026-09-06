# Gaia-Cepheid Arm-Conditioned Streaming Field — Freeze V1

Freeze date: 2026-09-06
Status: FROZEN BEFORE ANY H I RESIDUAL COMPARISON

## Purpose
Construct a conventional in-plane (U,V) streaming prediction at the three GRB arm locations that passed the frozen Gaia-Cepheid V3 geometry-only support audit:

- GRB 221009A — Outer
- GRB 221009A — OSC
- GRB 160623A — Outer

GRB 031203 remains excluded because the frozen V3 Outer-arm locus misses its geometric location by ~8.72 kpc.

## Outcome firewall
The builder may read only:
1. CDS/VizieR J/A+A/674/A37/table2 (3306 classical Cepheids; Gaia source_id, Galactic position, period-Wesenheit distance and distance-modulus uncertainty);
2. Gaia DR3 source rows for those source_ids (proper motions, observed radial velocity and associated uncertainties/quality metadata);
3. the frozen geometry constants from the completed Gaia-Cepheid V3 support audit;
4. the three frozen GRB geometries (l,b,d).

It MUST NOT read any H I spectrum, H I velocity, H I residual, V1/V2/V3 conventional prediction, or Persistence prediction.

## Galactic constants and velocity convention
Use Reid et al. (2019) A5 values:
- R0 = 8.15 kpc
- z_sun = 5.5 pc
- (U_sun,V_sun,W_sun) = (10.6,10.7,7.6) km/s
- Theta0 = 236 km/s
- A5 universal rotation curve parameters a2=0.96, a3=1.62

Gaia DR3 radial_velocity is heliocentric, so no LSR conversion is applied.
Positive U is radially inward toward the Galactic center. Positive V is in the direction of Galactic rotation after subtraction of the A5 circular speed.

## Predeclared 6D quality cuts
A Cepheid is eligible for the velocity field iff:
- finite Gaia DR3 pmra, pmdec, radial_velocity and their errors;
- RUWE < 1.4;
- rv_nb_transits >= 8;
- radial_velocity_error <= 5 km/s;
- fractional period-Wesenheit distance uncertainty <= 0.20, using sigma_d/d = ln(10)/5 * sigma_mu;
- Galactocentric R >= 4 kpc;
- Monte-Carlo propagated uncertainty in each of U and V <= 20 km/s.

No clipping on the measured peculiar U or V value is permitted.

## Frozen arm geometry
Outer arm: reuse the immutable V3 BeSSeL fit exactly:
- alpha = 2.0373888808067595
- beta = 0.15578848229141543
- sigma_arm = 0.8489392303918806 kpc
- membership/support perpendicular limit = 2 sigma_arm = 1.6978784607837611 kpc

OSC: reuse the independent support-audit continuation anchored by the trigonometric-parallax source G007.47+00.05:
- alpha = 2.4652064775186884
- beta = 0.23270728955462788
- sigma_arm = 1.0 kpc
- membership/support perpendicular limit = 2.0 kpc

Arm assignment uses position only and is fixed before any velocity interpolation.

## Streaming estimator
For U and V separately, use the V3 arm-coordinate kernel:

w_i = exp[-0.5 (s_i/h)^2] exp[-0.5 (d_perp,i/sigma_arm)^2] / (sigma_i^2 + sigma_int^2)

with sigma_int = 7 km/s and candidate along-arm bandwidths h={1,2,3,4,5,7,10} kpc.

For each arm, choose the bandwidth with the lowest leave-one-out mean standardized squared error among bandwidths that provide N_eff >= 3 at every support-qualified target for that arm and nearest along-arm tracer distance <= 2h. If no bandwidth qualifies, return NO_PREDICTION for that arm.

## Uncertainty
Propagate Gaia proper-motion/RV errors and Cepheid distance-modulus uncertainty by 256 Monte-Carlo draws per source. Report weighted local scatter and 2000 bootstrap draws of the final line-of-sight in-plane prediction.

## Output
For each of the three targets report:
- number of eligible same-arm 6D Cepheids;
- selected h;
- U_pred, V_pred;
- N_eff,U and N_eff,V;
- nearest same-arm phase distance;
- target d_perp;
- projected in-plane delta v_LOS;
- bootstrap p16/p50/p84.

This freeze is immutable once committed. Any later model variant must be versioned separately.
