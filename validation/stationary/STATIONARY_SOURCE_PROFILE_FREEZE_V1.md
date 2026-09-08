# Stationary source-profile freeze v1 — certified 34-profile subset

**Status: FROZEN CERTIFIED SUBSET; GLOBAL 149-GALAXY SOURCE GATE REMAINS LOCKED.**

- **Freeze date:** 2026-08-14
- **Scope:** 34 galaxies = 25 calibration + 9 blind
- **Grid rows:** 905 frozen rotation radii
- **Common gas convention:** `Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw`

## Frozen numerical rule

- measured tabulated nodes are retained exactly;
- interior samples use piecewise-linear `Sigma(R)` interpolation;
- radii inside the first measured node use the first measured value;
- radii beyond the last measured node use zero, without an inferred taper;
- analytic profiles are evaluated directly from their frozen source functions;
- invalid, negative, nonfinite, duplicate-radius, or interior-gap inputs fail closed.

The authoritative rule is `validation/stationary/STATIONARY_HI_INTERPOLATION_CONTINUATION_POLICY_V1.md`. It was promoted from the predeclared candidate only after the complete 34-profile support audit showed that no galaxy-specific numerical rule was required.

## Exact membership

**Calibration (25):** CamB, DDO154, DDO168, ESO079-G014, F568-3, F568-V1, F583-1, F583-4, IC2574, KK98-251, NGC0289, NGC0300, NGC2841, NGC2903, NGC2976, NGC3198, NGC4559, NGC5907, NGC6015, NGC7331, UGC04483, UGC05918, UGC07559, UGC09037, UGC12506

**Blind (9):** ESO116-G012, F574-1, NGC0024, NGC2403, NGC3521, NGC5033, NGC5055, NGC6946, NGC7793

## Frozen products

| Product | SHA-256 |
|---|---|
| `data/stationary/processed/stationary_hi_profiles_v1.csv` | `e8498b95378aadc99d8679b7b17012993a0e947893bef9e45e323263caac36ef` |
| `data/stationary/processed/stationary_source_profiles_v1.csv` | `ac13746a691b9f32da5cca4b955e2933d631d7294a41b7806f24b3599aeab155` |

The H I product contains one common-normalized central surface density at every frozen rotation radius for each certified galaxy. The source product adds the unit-`Upsilon` disk and bulge bases and retains the symbolic rules `Sigma_b = Sigma_gas + Upsilon_d Sigma_disk,1 + Upsilon_b Sigma_bulge,1` and `J = Sigma_b V_model`.

No observed velocity is present in either frozen product. The self-consistent source-current velocity is deliberately unevaluated.

## Evaluation accounting

- analytic evaluations: **108**
- exact measured nodes: **3**
- piecewise-linear samples: **629**
- constant-inner continuation samples: **23**
- zero-outer continuation samples: **142**
- tabulated galaxies requiring inner continuation: **11**
- tabulated galaxies requiring outer continuation: **11**

## Scientific and versioning boundary

This is an immutable freeze of the currently certified public 34-profile subset. It is **not** the final 149-galaxy source package and does not unlock `L_A`, `C_A`, `tau_A`, source-current evaluation, calibration fitting, or blind evaluation. The current 112-galaxy author request remains pending.

Later profiles must pass provenance, schema, normalization, missing-value, and support QC and enter a new version under the same source-independent numerical rule. Version 1 is not rewritten to improve a fit or accommodate a blind result.
