# THINGS public MOM0 radial H I reconstruction protocol v1

**Status: FROZEN BEFORE ANY SCIENCE-PIXEL PROFILE EXTRACTION, PERSISTENCE EVALUATION, OR BLIND-OUTCOME INSPECTION.**

This protocol defines a public, reproducible fallback for THINGS galaxies whose currently ingested Leroy et al. (2008) Table-7 H I profiles do not extend over the full stationary rotation-curve domain. The public THINGS site still serves the original FITS MOM0 maps and cubes. This route is a new public mechanism and does not relax the no-raster-digitization rule.

## 1. Primary public science product

For each THINGS target, use the original public **natural-weighted, blanked MOM0 FITS map** (`*_NA_MOM0_THINGS.FITS`) from the THINGS data archive as the primary surface-density reconstruction product.

Rationale: natural weighting maximizes surface-brightness sensitivity to extended H I, which is the quantity required for a radial mass-source profile. The robust-weighted MOM0 map is retained only as a secondary spatial-resolution/systematics cross-check and may not be substituted selectively to improve agreement.

The exact archive URL, HTTP retrieval date, file byte count, SHA-256, complete FITS header, and map identifier must be recorded for every reconstructed galaxy. The source FITS file itself need not be committed if repository size policy disfavors it, provided the public URL and cryptographic hash are durable.

## 2. Source geometry

The reconstruction uses source-side observational geometry fixed independently of persistence results.

### 2.1 Center
Use the published THINGS galaxy center/pointing center associated with the public THINGS data product. The preferred machine-readable source is Walter et al. (2008) THINGS catalogue metadata when available; otherwise use the FITS WCS/OBSRA/OBSDEC center only after verifying that it is the published galaxy center. The center is fixed before annular extraction and is not optimized on the radial H I profile.

### 2.2 Inclination and position angle
Use the public THINGS/Leroy source geometry from the same observational data family (Leroy et al. 2008 VizieR `J/AJ/136/2782/table4`: inclination and PA) for the fixed-geometry reconstruction validation.

Do not rescale reconstructed surface-density amplitudes afterward from source inclination to frozen SPARC inclination. The profile is reconstructed in the source geometry; source and frozen inclinations are retained as metadata.

### 2.3 Warp gate
A fixed-geometry reconstruction is not automatically promoted for a galaxy with a materially warped outer H I disk. If the fixed-geometry reconstruction fails the validation gates below, the galaxy fails closed for this protocol version. A radial tilted-ring geometry may be introduced only under a separately frozen, source-published geometry protocol; it may not be tuned against persistence results.

## 3. FITS units and raw H I conversion

No numerical conversion is permitted until the exact FITS `BUNIT`, beam, WCS, and velocity-integral convention have been read from the archived product/header or authoritative THINGS documentation.

The reconstruction must recover **raw atomic H I surface density** first. The conversion from the MOM0 map to H I column density/surface density must use the standard optically thin 21-cm relation appropriate to the verified FITS units and beam. Any beam-area conversion must use the source-product beam, not a fitted effective beam.

No helium factor is applied during map reconstruction. After validation, the recovered raw-H I profile is passed through the already-frozen Paper-I common normalization rule `Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw`.

Negative noise pixels are not blindly clipped before annular averaging. The public THINGS blanking/mask semantics are preserved. Any additional finite-pixel/mask treatment must be deterministic, global, documented, and validated before promotion.

## 4. Annular sampling

Use concentric elliptical annuli in the fixed source geometry.

- Radial coordinate is the semi-major-axis radius in the source galaxy plane.
- The annulus width is **one natural-weighted synthesized-beam FWHM**, using the geometric-mean FWHM `sqrt(BMAJ*BMIN)` expressed in angular units.
- Annulus centers begin at `0.5 * beam_FWHM` and advance by one beam FWHM.
- A final partial annulus is not created solely to reach a desired stationary rotation radius.
- The same beam-tied sampling rule applies to every target.

If the MOM0 header does not contain beam metadata, the beam must be obtained from the corresponding public THINGS cube/header or authoritative THINGS catalogue product before extraction. It may not be guessed.

## 5. Annular statistic and uncertainty

For each annulus, calculate the mean raw-H I surface density over valid source-map pixels after the source blanking/mask semantics are applied.

Record at minimum:
- annulus inner/outer/central radius;
- valid-pixel count and valid-area fraction;
- mean raw `Sigma_HI`;
- within-annulus standard deviation;
- standard error of the mean using an effective independent-sample count based on beam area rather than raw pixel count;
- source beam and pixel scale.

An annulus with insufficient valid area is recorded as missing rather than zero. The valid-area threshold is fixed at **50% of the geometrical annulus area** for protocol v1. Interior missing annuli cause the profile to fail closed; they are not interpolated through during validation.

## 6. Validation subset

The map-to-profile algorithm is validated before it is promoted as a source mechanism. Validation uses THINGS galaxies with independent public radial H I profiles already recovered in the project and prioritizes calibration-role galaxies. Blind rotation velocities/residuals are not inspected.

For each validation galaxy, compare the map-reconstructed profile to the independently published Leroy et al. (2008) Table-7 H I profile **only over their overlapping finite radial support**, after converting both to the same raw-H I convention (undo Leroy's 1.36 helium factor for the comparison).

The validation also compares reconstructed global/outer quantities to published THINGS H I mass/flux and H I radial extent where available.

## 7. Predeclared validation gates

A fixed-geometry reconstruction protocol is promoted only if the validation subset collectively satisfies all of the following without galaxy-specific tuning:

1. **Overlap profile amplitude:** median absolute fractional difference in finite, beam-independent overlap samples <= 15%.
2. **Overlap annular H I mass:** reconstructed versus published overlap-integrated H I mass differs by <= 10%.
3. **Global H I mass/flux:** reconstructed total H I mass/flux agrees with the published THINGS value within <= 10% after putting both on the same distance and helium convention.
4. **H I radial extent:** reconstructed `R_HI` at the published THINGS surface-density convention agrees with an independent published H I radius within the larger of one natural-weighted beam FWHM or 10% in radius.
5. **No systematic radial drift:** residuals against the independent overlap profile may not show a monotonic radial trend large enough that the inner and outer halves differ in median reconstructed/published ratio by > 15%.

The numerical thresholds are acquisition/QC gates and may not be relaxed after seeing persistence results. If the validation subset fails, protocol v1 fails closed; the next route is a separately frozen published tilted-ring/3D reconstruction, not threshold tuning.

## 8. Application to the 11 current THINGS targets

Only after the validation subset passes are the same rules applied unchanged to:

`DDO154, IC2574, NGC2403, NGC2841, NGC2976, NGC3198, NGC3521, NGC5055, NGC6946, NGC7331, NGC7793`.

The resulting full-domain profiles supersede Leroy Table 7 only as the preferred radial source profile where they pass source-level QC. Leroy remains an independent inner-profile validation/cross-check and is never deleted from provenance.

## 9. No continuation rescue during reconstruction

This protocol is intended to recover the measured H I disk from the original public maps. It does not extend the H I profile beyond the measurable map support. No exponential tail, constant tail, zero tail, or other radial continuation is introduced to force coverage of a stationary rotation point.

Any later source-profile continuation rule, if still needed after map reconstruction, must be frozen separately and justified from source-domain considerations before persistence evaluation.

## 10. Scientific boundary

This protocol is frozen using only source-data structure, observational metadata, and independent H I profile/mass/extent validation. It does not read or optimize against persistence accelerations, `L_A`, `C_A`, `tau_A`, blind residuals, or model preference. `L_A` and `C_A` remain locked.
