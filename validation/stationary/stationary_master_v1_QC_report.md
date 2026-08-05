# stationary_master_v1 build and QC report

Status: **candidate; no persistence parameters fitted**

## Construction
- Source: archived SPARC per-galaxy `*_rotmod.dat` files.
- Selected galaxy list and quality/inclination metadata: recovered 149-galaxy summary.
- Rows: 3152
- Galaxies: 149
- Old model outputs were excluded.

## Exact comparison to recovered 3,152-point file
- Row-count mismatches: 0
- Numerical mismatches across R, Vobs, eVobs, Vgas, Vdisk, Vbul at tolerance 1e-12: 0
- Maximum absolute differences: {'radius_kpc': 0.0, 'v_obs_kms': 0.0, 'v_err_kms': 0.0, 'v_gas_kms': 0.0, 'v_disk_ml1_kms': 0.0, 'v_bulge_ml1_kms': 0.0}

## QC
- Duplicate `(galaxy, radius)` keys: 0
- Duplicate full observational rows: 0
- Galaxies with non-increasing radial order: 0
- Nonpositive radii: 0
- Nonpositive velocity errors: 0
- Sample-selection violations: 0
- Summary point-count mismatches: 0
- Negative Vgas points preserved: 343 in 41 galaxies
- Zero Vgas points: 88

## Signed gas convention
Negative `Vgas` values are retained exactly. In later baryonic-speed construction use

`Vgas * abs(Vgas)`

for the signed gas contribution to `V_b^2`; do not square away the sign.

## Freeze boundary
This build contains no `L_A`, `C_A`, `tau_A`, or persistence-model predictions.
