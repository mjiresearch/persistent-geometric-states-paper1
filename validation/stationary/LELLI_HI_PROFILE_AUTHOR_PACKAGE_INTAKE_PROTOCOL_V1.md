# Lelli H I profile author-package intake protocol v1

**Status: FROZEN BEFORE RECEIPT OR INSPECTION OF AUTHOR-SUPPLIED NUMERICAL CONTENT.**

- **Freeze date:** 2026-08-14
- **Current request authority:** 112 galaxies = 77 calibration + 35 blind
- **Request-manifest SHA-256:** `fb85c40db51782ff13367084b6bffc5517e8e60291ec427cced343639f394f6a`
- **Existing source freeze:** immutable certified public subset v1, 34 galaxies

This protocol defines the permission, storage, membership, metadata, and source-only numerical gates that must pass before an author-supplied radial H I profile can enter a version-2 staging package. It does not authorize receipt, use, redistribution, or publication by itself.

## 1. Permission and storage boundary

The permission record is the first file read. Numerical and profile-metadata files are not opened unless all of the following are true:

1. the record is not a template;
2. the provider and receipt date are recorded;
3. data use is explicitly authorized;
4. citation, acknowledgement, conditions, and the private location of permission evidence are recorded; and
5. the authorization state is internally consistent.

The supported states are:

| State | Numerical use | Public source-file redistribution |
|---|---:|---:|
| `permission_pending` | no | no |
| `use_not_authorized` | no | no |
| `authorized_restricted` | yes | no |
| `authorized_public_redistribution` | yes | yes |

Restricted packages and actual permission records must remain outside this public repository. The repository defensively ignores `data/stationary/restricted_author_inputs/` and `validation/stationary/private_permission_records/`, but an external access-controlled directory is the required default. A repository-contained package is rejected unless public source-file redistribution is authorized **and** the operator supplies the explicit repository-contained-public-data override.

Permission evidence is never copied into a validation report. Package hashes and membership are omitted from a restricted report unless their disclosure is separately authorized.

## 2. Canonical local staging envelope

The validator consumes three local files. The author may supply a different layout; any mechanical staging into this envelope must preserve source values exactly and be documented outside the public repository until publication permission is clear.

| File | Purpose | Public template |
|---|---|---|
| `permission_record.json` | use, redistribution, derivative, metadata, and hash permissions | `validation/stationary/lelli_hi_author_package_permission_record_template_v1.json` |
| `metadata.csv` | one provenance/convention row per profile | `validation/stationary/lelli_hi_author_package_metadata_template_v1.csv` |
| `profiles.csv` | long-form unmodified source samples | `validation/stationary/lelli_hi_author_package_profiles_template_v1.csv` |

The machine-readable authority for exact headers, enumerations, and validation rules is `validation/stationary/lelli_hi_author_package_intake_schema_v1.json`.

The `--synthetic-fixture` switch is reserved for the bundled test harness and is accepted only with its exact synthetic permission markers. It must never be applied to an author package.

## 3. Fail-closed gate order

The gates run in this exact order:

1. **permission** — stop without opening metadata or profile values if use is not authorized;
2. **storage** — stop if restricted content resolves inside the public repository;
3. **request-manifest integrity** — require the frozen manifest hash and 112 = 77 calibration + 35 blind boundary;
4. **metadata schema and membership** — require exact canonical identifiers, roles, units, helium convention, adopted distance, inclination treatment, beam/sampling information, uncertainty convention, and citation;
5. **numerical schema** — allow only the six declared source-profile columns and reject velocity, residual, persistence, fit, and outcome fields;
6. **profile geometry** — require contiguous zero-based sample indices, finite nonnegative radii, strictly increasing radii, finite nonnegative source surface densities, and internally consistent uncertainties.

Failure at a gate prevents later content from being opened. No fuzzy identifier match, implicit alias, silent unit conversion, row sorting, deduplication, interpolation, continuation, taper, helium transformation, distance rescaling, inclination rescaling, or missing-value imputation is performed at intake.

## 4. Membership and versioning

Only exact canonical identifiers carrying `request_from_lelli=1` in the frozen 112-profile request manifest are eligible for version-2 candidate staging. The source identifier is retained separately in `source_galaxy_id`; it does not replace the canonical identifier.

- A partial authorized package may pass intake, but `request_complete` remains false.
- The 34 already-certified public profiles are rejected from this intake route rather than duplicated or used to rewrite version 1.
- D564-8, D631-7, and NGC4138 remain ineligible under this version because the current manifest records them as unavailable/no-request. A genuinely new availability statement requires a documented manifest/protocol version change before numerical intake.
- Frozen calibration/blind roles cannot change in response to availability or model performance.

## 5. Source metadata and values

Every profile must document its source radius unit, `Msun_pc^-2` surface-density unit, exact helium multiplier relative to raw H I, adopted source distance, source inclination, deprojection/face-on treatment, beam, radial sampling, uncertainty convention, citation, and source-profile reference.

Accepted helium states are raw H I and source values already including 1.33, 1.36, or 1.4. An unknown or different convention fails closed and requires a new documented rule. Accepted radial units are arcseconds, arcminutes, or kpc at the source-adopted distance.

The intake table stores `sigma_source_msun_pc2`, not the Paper-I common 1.33-helium quantity. Common normalization, frozen-distance radius mapping, support audit, interpolation/continuation, and source-grid construction occur only in the later versioned build under the already-frozen Paper-I rules.

## 6. Reports and scientific boundary

The validator report contains gate states and, when permitted, aggregate membership and file hashes. It never contains numerical profile values or permission evidence. Passing intake means only that an authorized source package is structurally eligible for version-2 staging.

Passing intake does **not**:

- rewrite or supersede the certified 34-profile v1 freeze;
- mark the 112-profile request complete unless all exact members are present;
- apply normalization, interpolation, continuation, or a source current;
- unlock `L_A`, `C_A`, or `tau_A`; or
- authorize inspection of velocities, residuals, persistence predictions, model preference, or blind outcomes.

## 7. Local invocation after receipt

Keep the package and its first report outside the repository:

```bash
python scripts/stationary/validate_lelli_hi_author_package_v1.py \
  --package-root /secure/path/lelli-hi-package \
  --permission-record /secure/path/lelli-hi-package/permission_record.json \
  --metadata /secure/path/lelli-hi-package/metadata.csv \
  --profiles /secure/path/lelli-hi-package/profiles.csv \
  --report /secure/path/lelli-hi-package/intake_report_v1.json
```

Do not use the repository-contained-public-data override unless the permission record explicitly authorizes public redistribution of the source files. Do not commit an actual permission record, correspondence, or source profile merely because the structural validator passes.
