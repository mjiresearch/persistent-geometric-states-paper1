# DR20 gyro-age schema adapter v1

The frozen protocol names uncertainty-separated young and old cohorts from the same official DR20 gyrochronology VAC. The released FITS schema supplies two complementary estimators rather than one generic `age` column:

- `gyrointerp_age`, with `gyrointerp_age_m` and `gyrointerp_age_p`, is used for the young upper-bound cut;
- `GPgyro_age`, with `GPgyro_age_m` and `GPgyro_age_p`, is used for the old lower-bound cut.

All six quantities are interpreted in Gyr; `_m` and `_p` are the lower and upper errors. A source meeting both cohort definitions is excluded. Rows meeting neither definition cannot enter inference. Both cohorts therefore remain exact-`source_id` subsets of `gyro_age_dwarf-1.0.0.fits`, while each cohort uses the estimator appropriate to its age regime.

This is a schema-only adapter. It was fixed after checking the released column names, age-domain coverage, exact-match counts, and voxel support, but before calculating or viewing a Gaia velocity/current contrast. The authoritative machine record is `data/persistence_history/dr20_independent/schema_adapter_v1.json`.
