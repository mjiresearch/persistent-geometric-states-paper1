# Current stationary H I acquisition resume point

Status: **CERTIFIED 34-PROFILE SOURCE SUBSET FROZEN; AUTHOR REQUEST PENDING; GLOBAL SOURCE GATE LOCKED**.

Reconciled: **2026-08-14**.

## Current counts

- Frozen sample: **149 galaxies = 104 calibration + 45 blind**.
- Public-source overlay: **62 galaxies = 45 calibration + 17 blind**.
- Recovered/ingested and certified common-normalized profiles: **34 = 25 calibration + 9 blind**.
- Certified representation: **27 tabulated profiles / 781 rows + 7 analytic profiles**.
- Current actionable public reference families: **0**.
- Current author/private-compilation request manifest: **112 = 77 calibration + 35 blind**.
- Reported unavailable in the 169-profile compilation: **D564-8, D631-7, NGC4138**.

The request to Dr. Federico Lelli was sent on 2026-08-14 when the request set was **115 = 79 calibration + 36 blind**. NGC2903, NGC4559, and NGC5033 were subsequently promoted from the public FEASTS 2025 release, reducing the current outstanding manifest to 112. Do not resend the request merely to remove those three systems; reconcile any received package against the current manifest at ingestion time.

## Certified package

- Manifest: `data/stationary/source_reconstruction/certified_hi_normalization_manifest_v3.csv`.
- Common tabulated profiles: `data/stationary/source_reconstruction/certified_hi_common_tabulated_v5.csv`.
- Common analytic profiles: `data/stationary/source_reconstruction/certified_hi_common_analytic_v5.csv`.
- Normalization summary: `validation/stationary/certified_hi_common_normalized_v5_summary.json`.
- Radial-support audit: `validation/stationary/certified_hi_full_radial_coverage_v3.csv` and `validation/stationary/certified_hi_full_radial_coverage_v3_summary.json`.

The completed support audit has **7 analytic-defined**, **7 full-measured-support**, **2 inner-and-outer-continuation**, **9 inner-only**, and **9 outer-only** profiles. Across the 27 tabulated profiles, **11 require inner continuation** and **11 require outer continuation**. The common-normalized source artifacts remain unchanged; continuation is applied only in the separately versioned processed v1 grid below.

NGC5033 is a blind galaxy. Its FEASTS profile was acquired and promoted only under the pre-frozen blind source-acquisition protocol; its 50 source rows passed locked source-only QC. Its normalized support requires inner continuation only. No blind residual, persistence prediction, or model preference was inspected.

## Frozen certified-subset source package

- Numerical authority: `validation/stationary/STATIONARY_HI_INTERPOLATION_CONTINUATION_POLICY_V1.md`.
- H I grid: `data/stationary/processed/stationary_hi_profiles_v1.csv`.
- Source basis: `data/stationary/processed/stationary_source_profiles_v1.csv`.
- Machine-readable summary: `validation/stationary/stationary_source_profile_freeze_v1_summary.json`.
- Independent validation: `validation/stationary/stationary_source_profile_freeze_v1_validation.json` — **14/14 gates pass**.
- Freeze record: `validation/stationary/STATIONARY_SOURCE_PROFILE_FREEZE_V1.md`.

The frozen rule retains measured nodes, uses piecewise-linear interpolation between measured samples, continues the first measured value inward to `R=0`, sets the profile to zero strictly beyond the last measured radius, and evaluates analytic source functions directly. Invalid inputs fail closed; no galaxy-specific rescue rule exists.

The v1 products contain **905 frozen rotation-grid rows**: **108 analytic evaluations, 3 exact measured nodes, 629 piecewise-linear samples, 23 inner-constant samples, and 142 outer-zero samples**. They contain the common gas source and unit-`Upsilon` stellar bases but no observed velocity. The self-consistent source current remains unevaluated.

## Exact next action

1. Preserve the certified 34-profile v1 freeze unchanged; do not rewrite it when additional profiles arrive.
2. Await the author response for the current **112 = 77 calibration + 35 blind** request manifest. Do not resend merely because three FEASTS systems were removed after the original request.
3. On receipt, establish redistribution/derivative permissions and reconcile exact membership against the current manifest before reading numerical profile content into the pipeline.
4. Apply the same frozen radius, helium, missing-value, interpolation, and continuation rules; fail closed on any new source condition not already covered.
5. Build a new versioned normalization, support audit, and source-profile freeze. Version 1 remains immutable audit history.

Do not reopen a dispositioned public route unless its explicit `reopen_rule` is satisfied by a genuinely new mechanism. Do not inspect persistence outcomes or blind residuals. `L_A` and `C_A` remain locked until the global source-profile package is complete, validated, and frozen.
