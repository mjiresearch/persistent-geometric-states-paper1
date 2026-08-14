# Current stationary H I acquisition resume point

Status: **PUBLIC EXACT-SOURCE QUEUE EXHAUSTED; AUTHOR REQUEST PENDING; 34-PROFILE NORMALIZATION COMPLETE**.

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

The completed support audit has **7 analytic-defined**, **7 full-measured-support**, **2 inner-and-outer-continuation**, **9 inner-only**, and **9 outer-only** profiles. Across the 27 tabulated profiles, **11 require inner continuation** and **11 require outer continuation**. No continuation has yet been applied.

NGC5033 is a blind galaxy. Its FEASTS profile was acquired and promoted only under the pre-frozen blind source-acquisition protocol; its 50 source rows passed locked source-only QC. Its normalized support requires inner continuation only. No blind residual, persistence prediction, or model preference was inspected.

## Exact next action

1. Promote one source-independent interpolation/continuation rule against the completed 34-profile support audit. The validated candidate is piecewise-linear interpolation between measurements, constant inward continuation to `R=0`, and zero beyond the measured outer edge; do not add galaxy-specific rescue rules.
2. Build and validate the versioned source-profile freeze package under that rule.
3. Keep the source-profile package fail-closed for any later author-supplied profiles and reconcile them against the 112-galaxy manifest before use.

Do not reopen a dispositioned public route unless its explicit `reopen_rule` is satisfied by a genuinely new mechanism. Do not inspect persistence outcomes or blind residuals. `L_A` and `C_A` remain locked until the complete source-profile package is validated and frozen.
