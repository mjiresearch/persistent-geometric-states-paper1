# THINGS public MOM0 radial H I reconstruction protocol v2

**Status: FROZEN BEFORE ANY PERSISTENCE EVALUATION OR BLIND-OUTCOME INSPECTION.**

Protocol v2 retains the complete science-pixel reconstruction algorithm, geometry rules, mask rules, annular sampling, unit conversion, and numerical thresholds of `THINGS_MOM0_PROFILE_RECONSTRUCTION_PROTOCOL_V1.md`. It changes only the pre-persistence hierarchy used for the independent H I radial-extent QC after a source-domain discrepancy was discovered in the first calibration galaxy, DDO154.

The original v1 DDO154 validation result is retained unchanged and remains part of the audit trail.

## 1. Unchanged reconstruction rules

The following v1 rules remain frozen without modification:

- primary product = public THINGS natural-weighted blanked MOM0 FITS map;
- source center, inclination, and position angle fixed from the THINGS observational data family;
- exact-zero floating MOM0 values are source blanks under the separately frozen zero-blank policy; finite nonzero values, including negative values, are retained;
- raw atomic H I is reconstructed first;
- line-of-sight H I column surface density is converted once to disk-plane surface density with the fixed source inclination;
- no helium factor is applied during map reconstruction;
- elliptical annuli use one natural-weighted beam geometric-mean FWHM in width, with centers at half-beam increments;
- annular statistic = mean over valid source pixels;
- valid-area gate = at least 50% of the geometrical annulus area;
- interior missing annuli fail closed;
- no profile continuation is used to rescue map coverage;
- no galaxy-specific tuning is permitted.

The common downstream convention remains `Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw` only after source-level validation.

## 2. Unchanged quantitative validation gates

The numerical thresholds remain exactly those declared in protocol v1:

1. overlap-profile median absolute fractional difference <= 15%;
2. overlap-integrated H I mass difference <= 10%;
3. global H I mass/flux difference <= 10%;
4. independent H I radial extent agreement within the larger of one natural-weighted beam FWHM or 10% in radius;
5. difference between inner- and outer-half median reconstructed/published profile ratios <= 15%.

No threshold is relaxed in v2.

## 3. Radial-extent comparator hierarchy

For gate 4, use the most product-matched independent published size measurement available under this fixed hierarchy:

### Priority 1 — Wang et al. (2016) product-matched survey row
Use Wang et al. (2016), VizieR `J/MNRAS/460/2143/table2`, when the catalogue contains a row that matches the same H I survey/product family being reconstructed.

For a THINGS MOM0 reconstruction, require `Sample=THINGS`. If the same galaxy also appears under another survey (for example LITTLE THINGS), that other row is explicitly excluded.

This source is preferred because Wang et al. define `D_HI` from natural-weighted H I images where possible, at the azimuthally averaged raw-H I threshold `Sigma_HI=1 Msun pc^-2`, and report a beam-smearing-corrected H I diameter. The same-survey row must also be checked for consistency of the adopted distance before use.

### Priority 2 — another explicitly product-matched published H I size
If no Wang THINGS row exists, use an independent published measurement only if its survey/data product, H I threshold convention, distance scale, and size definition can be documented well enough to compare to the reconstructed profile.

### Priority 3 — fail closed
If no product-matched independent radial-extent comparator exists, gate 4 is not silently dropped or replaced by a heterogeneous value. The target fails the radial-extent validation pending a separately documented source-domain comparator.

## 4. Why v2 was required

DDO154 was the first calibration-only science-pixel validation under protocol v1. The reconstruction passed four independent gates strongly:

- overlap-profile median absolute fractional difference: 1.53%;
- overlap annular H I mass difference: 1.48%;
- total THINGS H I flux difference: 0.106%;
- inner-versus-outer profile-ratio drift: 3.56%.

The sole v1 failure was comparison to Oman et al. (2019), which listed `R_HI=4.5 kpc` for DDO154.

A source-domain audit then found the product-matched Wang et al. (2016) THINGS row at the same 4.3 Mpc distance, with `D_HI=11.97 kpc`, or `R_HI=5.985 kpc`. Wang's definition explicitly uses the azimuthally averaged `Sigma_HI=1 Msun pc^-2` threshold and the THINGS interferometric data family. The unchanged reconstruction gives an annular crossing of `R_HI=5.63045 kpc`, a 5.93% difference.

The discrepancy was therefore adjudicated by product provenance and matched size definition, not by persistence behavior. Oman remains recorded as a discrepant secondary comparison; its value is not deleted or altered.

## 5. Scope

The comparator hierarchy above applies unchanged to every subsequent THINGS target, including calibration and blind-role galaxies. Source-domain metadata may be acquired for blind-role galaxies, but their rotation residuals, persistence predictions, and model outcomes remain sealed.

## 6. Scientific boundary

Protocol v2 was frozen entirely from observational product provenance and source-domain validation before any `L_A`, `C_A`, `tau_A`, persistence acceleration, blind residual, or model-preference evaluation. `L_A` and `C_A` remain locked.
