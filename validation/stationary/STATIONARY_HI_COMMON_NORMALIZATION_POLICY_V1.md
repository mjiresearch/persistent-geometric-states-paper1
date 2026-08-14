# Stationary H I common-normalization policy v1

**Status:** FROZEN BEFORE ANY EVALUATION OF `L_A`, `C_A`, `tau_A`, PERSISTENCE PREDICTIONS, OR BLIND OUTCOMES.

This policy converts certified source-level radial H I profiles to one common Paper-I source convention while retaining the original source values and provenance.

## 1. Frozen radial coordinate

The authoritative galaxy distance is the frozen distance in `data/stationary/frozen/stationary_master_v1.csv`.

- If an acquisition product already contains a verified `radius_kpc_frozen`, retain it unchanged.
- If a profile is expressed in angular radius, convert angle to physical radius using the frozen distance.
- If a profile is expressed in source-paper kpc, use

  `R_frozen = R_source * D_frozen / D_source`.

- For analytic profile parameters expressed in source-paper kpc, apply the same multiplicative radius scale to every radial length/location parameter before evaluating the analytic profile.

Source distances are provenance data, never fitted or adjusted to improve a rotation-curve or persistence result.

## 2. Surface-density geometry / inclination

Do **not** rescale H I surface-density amplitudes from the source-paper inclination to the frozen SPARC inclination.

The certified radial profiles were already constructed/deprojected by their source analyses. Re-applying a `cos(i)` correction would risk double-deprojection and would mix heterogeneous reconstruction assumptions into the source amplitudes. Source inclination and frozen inclination are retained as QC/sensitivity metadata only.

## 3. Common neutral-gas helium convention

The Paper-I common source convention is

`Sigma_neutral_1p33 = 1.33 * Sigma_HI_raw`.

This matches the SPARC mass-model convention in Lelli et al. (2016), where the atomic-gas mass is multiplied by 1.33 for helium.

Each certified profile is first interpreted according to its documented source convention and then mapped exactly once:

- source is raw atomic H I / H I column density: multiply by `1.33`;
- Leroy et al. (2008) THINGS profiles: source values already include a `1.36` helium factor, so multiply the published values and their uncertainties by `1.33/1.36`;
- Westmeier et al. (2011) NGC300 profile: published gas profile includes `x1.4`, so multiply published values by `1.33/1.4`;
- Allaert et al. (2015) / HEROES NGC5907: Figure 29 `Sigma_HI` is atomic H I derived from 21-cm surface brightness/column density, so treat it as raw H I and multiply by `1.33`.

No galaxy-specific helium factor may be tuned to improve the persistence fit.

## 4. Analytic source profiles

Certified analytic profiles are source representations, not fitted by Paper I. Their published amplitudes and shapes remain fixed. Only their radial length/location parameters are moved to the frozen distance scale and their surface-density amplitude is converted to the common helium convention above.

## 5. Interpolation / continuation

The candidate numerical rule that passed synthetic validation is:

- piecewise-linear interpolation in `Sigma(R)` between measured radial samples;
- constant inward continuation equal to the innermost measured value down to `R=0`;
- zero beyond the outermost measured H I radius;
- reject negative surface-density inputs.

This rule is **validated but not yet promoted as the final galaxy-data rule**. It becomes final only after the full 31-galaxy normalized radial-coverage audit shows that no additional source-independent numerical rule is required.

Analytic profiles are evaluated directly and do not require tabulated interpolation within their defined analytic domain.

## 6. Provenance and fail-closed rule

Every normalized row/value must retain the source artifact, source convention, source/frozen distance information, radial transform, helium transform, and stationary role. If any required transform cannot be established from durable provenance, that galaxy fails closed and is not supplied to the stationary source-current builder.

## 7. Scientific boundary

This normalization policy is an observational-data construction rule only. It does not evaluate `L_A`, `C_A`, `tau_A`, persistence accelerations, blind residuals, or model preference. `L_A` and `C_A` remain locked until the complete source-profile package is validated and frozen.
