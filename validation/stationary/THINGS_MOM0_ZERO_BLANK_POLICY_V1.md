# THINGS MOM0 exact-zero blank policy v1

**Status: FROZEN BEFORE ANY RADIAL PROFILE VALIDATION, PERSISTENCE EVALUATION, OR BLIND-OUTCOME INSPECTION.**

This policy resolves the finite blank/mask encoding in the public THINGS floating-point MOM0 products.

## Source/product evidence

Walter et al. (2008) describe constructing a master emission mask, blanking noise regions in the residual-rescaled cubes, and calculating moment maps from the blanked cubes. The public DDO154 natural-weighted MOM0 FITS product is entirely finite and therefore does not use FITS NaN/BLANK as its blank sentinel.

The durable pixel-topology audit `validation/stationary/things_ddo154_zero_blank_semantics_v1.json` finds:

- 1,048,576 total pixels, all finite;
- 825,109 exact-zero pixels (78.69% of the image);
- every image-border pixel is exactly zero;
- 824,304 of 825,109 zero pixels (99.902%) belong to the boundary-connected zero region;
- 223,467 finite nonzero pixels remain;
- 402 of those nonzero pixels are negative and are therefore real finite moment-map values/noise residuals rather than a blank sentinel.

## Frozen rule

1. In the public THINGS natural-weighted floating MOM0 product, **exact floating-point zero is treated as the source blank/mask sentinel and is excluded from valid annular pixels**.
2. Every finite **nonzero** MOM0 pixel is retained as a valid source-map value, including negative values.
3. Negative finite nonzero pixels are never clipped to zero before annular averaging or integrated-flux calculation.
4. The exact-zero rule must be topology-checked on each additional THINGS target before promotion. If another product uses NaN, FITS BLANK, or a materially different sentinel encoding, that target fails closed until its product-specific mask encoding is documented.
5. Interior exact-zero holes remain masked rather than converted to measured zero H I emission.
6. This policy does not alter the predeclared >=50% valid-area annulus gate in `THINGS_MOM0_PROFILE_RECONSTRUCTION_PROTOCOL_V1.md`.

## Scientific boundary

This rule is based only on THINGS source-product construction and pixel-mask topology. It was frozen without evaluating rotation velocities, persistence parameters, persistence predictions, blind residuals, or model preference. `L_A` and `C_A` remain locked.
