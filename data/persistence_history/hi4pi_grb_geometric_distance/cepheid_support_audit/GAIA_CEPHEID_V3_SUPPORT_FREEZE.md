# Gaia–Cepheid V3 Support Audit — Frozen Protocol

Freeze date: 2026-09-06
Status: FROZEN BEFORE ANY H I RESIDUAL READ

## Purpose

Determine whether the full public Gaia DR3 classical-Cepheid position catalogue has sufficient arm-phase support at the four already-frozen GRB geometric locations for a future V3 conventional-streaming model. This stage is geometry-only. It does **not** estimate streaming velocities and it does **not** read any GRB H I velocity/residual product.

## Public Cepheid source

CDS/VizieR J/A+A/674/A37/table2 (Gaia Collaboration et al. 2023), 3306 classical Cepheids. Only `GaiaDR3`, `GLON`, `GLAT`, `Dist`, and `e_mu` are used. No stellar velocities are read or required.

## Frozen Galactic geometry

- R0 = 8.15 kpc.
- GRB target geometry is read only from the existing frozen geometry file `../bessel_streaming_frozen/frozen_grb_geometry_only.csv`.
- Galactocentric planar coordinates use the same convention as the V3 maser audit: x = -R0 + d cos(b) cos(l), y = d cos(b) sin(l), phi = atan2(y,x).

### Outer arm

Reuse the exact frozen V3 Outer-arm logarithmic spiral without refitting:
- alpha = 2.0373888808067595
- beta = 0.15578848229141543
- sigma_arm = 0.8489392303918806 kpc
- ln R = alpha + beta * phi, with phi wrapped about each target as in V3.

### OSC arm

V3 had no support-qualified same-arm maser fit, so this support audit fixes an external geometry *before inspecting Cepheid counts*:
- Reid et al. (2019) identify the OSC as the continuation of the Scutum–Centaurus arm and report an approximately 13 degree pitch over the Scutum–Centaurus segment.
- The OSC branch is anchored to the trigonometric-parallax source G007.47+00.05 in the frozen Reid 2019 table, using only (l,b,parallax), never its velocity.
- pitch = +13.1 degrees in the V3 (x,y,phi) convention, beta = tan(13.1 deg).
- alpha is determined uniquely from the G007.47+00.05 parallax position.

No H I position/velocity information is used to set either arm locus.

## Cepheid arm assignment

For each arm independently:
1. Compute each Cepheid's perpendicular offset `d_perp` from the frozen log spiral using the same V3 approximation `(R - R_arm)/sqrt(1+beta^2)`.
2. Provisional members satisfy |d_perp| <= 1.5 kpc.
3. For OSC only, estimate a robust arm width from provisional Cepheid offsets as sigma = clamp(1.4826*MAD, 0.25, 1.00) kpc. Outer keeps the already-frozen V3 sigma.
4. Final arm members satisfy |d_perp| <= max(1.0, 2*sigma_arm) kpc.
5. `N_arm` is the total final-member count in the full 3306-object catalogue.

This assignment uses positions/distances only.

## Phase support metrics

At each frozen GRB target and for each h in {1,2,3,4,5,7,10} kpc:

- along-arm phase coordinate `s` is computed with the same logarithmic-spiral coordinate formula used in V3;
- weight w = exp[-0.5(s/h)^2] * exp[-0.5(d_perp/sigma_arm)^2];
- N_eff = (sum w)^2 / sum(w^2);
- d_nearest,phase = min |s| among final same-arm Cepheids;
- d_perp,target is the target's perpendicular offset from the frozen arm locus.

A bandwidth is support-qualified iff:
1. N_eff >= 3;
2. d_nearest,phase <= 2h; and
3. |d_perp,target| <= max(1.0, 2*sigma_arm).

For each target the audit reports the **smallest** support-qualified h. If none qualifies, status is `NO_CEPHEID_SUPPORT`.

## Outcome firewall

The audit script is forbidden from reading:
- any HI4PI/Bonn spectrum;
- any GRB H I velocity or residual table;
- any V1/V2/V3 streaming prediction;
- any Persistence prediction.

Only public Cepheid geometry, the frozen GRB geometry file, the frozen Outer-arm parameters above, and the Reid-table astrometry of G007.47+00.05 are permitted.
