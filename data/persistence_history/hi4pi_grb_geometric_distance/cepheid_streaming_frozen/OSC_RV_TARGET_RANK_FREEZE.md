# Frozen OSC systemic-RV target ranking

Purpose: rank geometry-qualified classical Cepheids near the frozen GRB 221009A OSC arm phase that are excluded from the frozen multi-catalog streaming field solely because they lack an acceptable systemic radial velocity, and determine whether one or two new systemic-RV measurements would satisfy the predeclared V3 support threshold.

## Outcome firewall
This ranking MUST NOT read any GRB H I spectrum, H I velocity, H I residual, conventional-vs-HI comparison, or Persistence prediction. It uses only the already-frozen Cepheid position/distance/astrometry catalogs, frozen OSC arm geometry, and frozen V3 support rules.

## Frozen rules
- Galactic constants, transformations, OSC logarithmic-arm locus, arm width, target geometry, sign conventions, intrinsic dispersion sigma_int=7 km/s, and candidate bandwidth grid h={1,2,3,4,5,7,10} kpc are inherited unchanged from the frozen Gaia-Cepheid V3 field.
- Geometry-qualified OSC candidates must satisfy |d_perp| <= 2 sigma_arm at the GRB 221009A OSC phase.
- Non-RV quality requirements remain RUWE < 1.4, fractional Cepheid distance error <= 20%, finite proper motions/errors, and R >= 4 kpc.
- Existing frozen V3 eligible OSC 6D Cepheids remain fixed and unmodified.
- A candidate enters this target list only if it passes the non-RV/geometry rules but is absent from the frozen V3 eligible 6D sample because no systemic RV passes the V3 hierarchy/quality gate.

## Hypothetical RV precision for support-only ranking
Primary: sigma_RV = 2.0 km/s.
Sensitivity: sigma_RV = 1.0 and 5.0 km/s.
The hypothetical RV central value is not used to rank support. Only propagated U/V uncertainty and the resulting kernel weight matter.

For each candidate and each frozen bandwidth, calculate the candidate's hypothetical U/V uncertainty and the updated effective sample sizes
N_eff=(sum w)^2/sum(w^2)
for U and V after adding that star to the immutable V3 OSC support set. Rank candidates by whether a single addition makes both N_eff,U >= 3 and N_eff,V >= 3 at any frozen bandwidth, then by the maximum achieved min(N_eff,U,N_eff,V). Evaluate all candidate pairs under the same rule.

No bandwidth, quality threshold, arm width, intrinsic dispersion, or target position may be changed after the ranking is generated.
