# Checkpoint — THINGS MOM0 validation closure and FEASTS public-release continuation v1

## Status

The generic fixed-geometry reconstruction from the public THINGS natural-weighted blanked MOM0 FITS maps is **not globally promotable** under the predeclared `THINGS_MOM0_PROFILE_RECONSTRUCTION_PROTOCOL_V1/V2` gates.

This is a source-acquisition/QC conclusion only. No persistence parameters, model residuals, or blind outcomes were used.

## Calibration-only validation outcomes

- **DDO154:** passes all five frozen gates without tuning. This validates that the mechanics can work for an individual system, but DDO154 was already certified from the Leroy et al. numerical profile and does not increment the certified count.
- **NGC2976:** four of five gates pass. Gate 4 (`R_HI`) fails: reconstructed `R_HI = 2.96522 kpc` versus the frozen Wang-THINGS comparator `2.64 kpc`, a `12.3189%` difference beyond the frozen tolerance. The failure remains intact; no threshold adjustment is allowed.
- **NGC2841:** the fixed MOM0 extractor fails closed before radial-profile promotion because the source zero-mask topology does not satisfy the frozen exact-zero blank policy (`all_border_zero = false`). The blanking rule is not modified after seeing this outcome.
- **NGC3198:** completes extraction but fails the profile-amplitude, overlap-mass, and global-flux gates. The reconstructed profile is systematically low relative to Leroy, while radial drift is small. The public natural MOM0 map integrates to about `155.68 Jy km/s` versus the Walter et al. THINGS integrated value `227 Jy km/s`. This is consistent with a product/calibration mismatch for this use rather than a reason to tune geometry or thresholds.

Therefore the fixed-geometry MOM0 route is closed as a universal Paper-I reconstruction mechanism. It may remain as a documented systematics/validation route for galaxies where it independently passes, but it must not be selectively substituted to improve outcomes.

## Physical/product interpretation

Walter et al. (2008) measure global THINGS H I fluxes from residual-flux-scaled natural-weighted data. Later THINGS/FEASTS work likewise distinguishes original/reprocessed residual-rescaled THINGS products from generic map products and documents CLEAN/short-spacing systematics. Consequently, a public `*_NA_MOM0_THINGS.FITS` file is not assumed to be interchangeable with the exact residual-rescaled product used to derive every published radial profile.

## Official FEASTS public release found

The FEASTS team maintains the public GitHub repository/wiki `FEASTS/LVgal`. Its `Publication and Data Release` page states that all observed 55-galaxy data cubes and moment maps have been released and provides advanced-data links for the 2024 FEASTS+THINGS papers.

The official combined-I/II advanced-data share is:

`https://disk.pku.edu.cn/link/AAF401EFBFF9A2493CAA7678F24E9BCF28`

The PKU AnyShare public API resolves this link successfully:

- link id: `AAF401EFBFF9A2493CAA7678F24E9BCF28`
- type: anonymous
- title: `diffuseHI(Wang+24)`
- password required: false
- expiry: Unix epoch sentinel used by AnyShare for permanent/no-expiry sharing

Durable resolver artifact: `validation/stationary/feasts_anyshare_link_resolution_v1.json`.

The obsolete/personal FEASTS page `https://kavli.pku.edu.cn/~jwang/FEASTS_data.html` timed out from both normal web access and GitHub Actions and is not the preferred route anymore.

## Next acquisition action

Continue only through the official FEASTS released-data share or another exact source-published numerical/residual-rescaled/tilted-ring product. Specifically:

1. enumerate the files inside the official `diffuseHI(Wang+24)` share;
2. identify numerical radial-profile files and/or the exact residual-rescaled THINGS products for NGC2841 and NGC3198;
3. prefer a directly published numerical `Sigma_HI(R)` profile if present;
4. if only source-published maps/cubes are present, freeze a separate residual-rescaled/tilted-ring/ELLINT reconstruction protocol **before** science-pixel extraction;
5. do not inspect blind rotation residuals or persistence outcomes during this acquisition/validation stage;
6. do not alter the failed fixed-MOM0 thresholds, zero-mask rule, `L_A`, or `C_A`.

## Count / split checkpoint

No newly uncertified galaxy has been promoted by this branch. The official certified running count therefore remains:

- **31 usable H I profiles total**
- **23 calibration**
- **8 blind**

The count changes only when a previously uncertified frozen galaxy is actually recovered, validated, and promoted.
