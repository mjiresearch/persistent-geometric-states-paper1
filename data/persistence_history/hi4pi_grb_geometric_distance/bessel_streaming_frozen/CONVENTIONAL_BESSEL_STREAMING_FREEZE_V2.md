# Conventional BeSSeL/Maser Streaming Field — Freeze V2

Freeze date: 2026-09-06
Status: FROZEN BEFORE COMPARISON TO GRB H I OUTCOMES
Reason for V2: V1 failed its own predeclared spatial-support guardrail at all four target geometries. This is a geometry/catalog support failure, not an outcome-based failure. V1 remains immutable.

## Inherited, unchanged from V1

- Reid et al. (2019) VizieR catalog J/ApJ/885/131/table1.
- A5 Galactic constants and URC.
- V_LSR-to-heliocentric conversion.
- 20% fractional-parallax limit, R>=4 kpc, finite phase space, <=20 km/s propagated component uncertainties.
- No peculiar-velocity clipping.
- 256-draw measurement-error propagation.
- Gaussian-kernel local-constant vector field in Galactocentric (x,y).
- sigma_int=7 km/s.
- Candidate global bandwidths h={1.0,1.5,2.0,2.5,3.0,4.0,5.0} kpc.
- Same geometry-only GRB target file.
- No GRB H I velocity/residual or persistence prediction may be read.

## V2 bandwidth rule

For every candidate h, evaluate the field support at each of the four frozen target geometries using the catalog only. A bandwidth is support-qualified iff at every target:

1. min(N_eff_U,N_eff_V,N_eff_W) >= 3; and
2. nearest eligible maser distance <= 2h.

Among support-qualified bandwidths, select the one with the smallest V1 leave-one-out mean standardized squared error on the maser sample. If no bandwidth qualifies, V2 returns NO_PREDICTION and the BeSSeL catalog is declared insufficient for this head-to-head.

This rule is frozen before any comparison with the H I residuals. No target residual value or sign participates in qualification or bandwidth selection.

## Output status

V2 predictions are labeled support-qualified, but their spatial resolution is the selected global h and must be reported. V1 predictions remain available as the higher-resolution but unsupported baseline.
