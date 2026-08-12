# Iorio et al. (2017) — DDO87 / DDO126 radial H I profile audit v1

**Status:** TWO RAW PUBLIC SOURCE PROFILES INGESTED  
**Date:** 2026-08-12  
**Scientific boundary:** source acquisition only. `L_A` and `\mathcal C_A` remain locked.

## Source

G. Iorio et al. (2017), *MNRAS* **466**, 4159–4192, DOI `10.1093/mnras/stw3285`.

The public OUP supporting-material archive contains the machine-readable online tables:

- `results.zip::finalrot/ddo87_onlinetab.txt`
- `results.zip::finalrot/ddo126_onlinetab.txt`

The publisher archive is not redistributed wholesale. The repository stores only the Paper-I-relevant radial H I columns with the source member checksums and metadata needed for reproducibility.

## Frozen alias reconciliation

| Iorio source alias | Frozen Paper I galaxy | Frozen role |
|---|---|---|
| DDO87 | UGC05918 | calibration |
| DDO126 | UGC07559 | calibration |

These alias identifications are independently consistent with the Hunter et al. (2021) LITTLE THINGS catalog, which lists DDO87 with NED name UGC05918 and DDO126 with NED name UGC07559.

## UGC05918 / DDO87

The public source table contributes **12** strictly increasing radial H I samples:

- angular radius: **12–144 arcsec**
- source physical radius: **0.43–5.17 kpc**
- source H I surface density: **0.97–2.79 Msun pc^-2**
- source distance: **7.4 Mpc**
- source mean inclination: **42.7 deg**
- source mean PA: **238.6 deg**
- source-member SHA-256: `4460a564a3e6c290f2f0722ca29df8fa7b6878c715dec2b0469647edaf0b61d9`

## UGC07559 / DDO126

The public source table contributes **13** strictly increasing radial H I samples:

- angular radius: **20–140 arcsec**
- source physical radius: **0.48–3.33 kpc**
- source H I surface density: **1.29–5.06 Msun pc^-2**
- source distance: **4.9 Mpc**
- source mean inclination: **62.2 deg**
- source mean PA: **140.7 deg**
- source-member SHA-256: `bb8291ce9751e0642dc74e61f79e0be44c2ca316da01c1635a35feef1b0ef8f2`

## H I / helium convention

The Iorio online-table `Sdens` quantity is the intrinsic H I surface density in `Msun pc^-2`, corrected for primary-beam attenuation. The Iorio paper identifies the intrinsic H I surface-density profiles as not corrected for helium.

Therefore for both galaxies:

- `helium_already_included = 0`;
- the ingested source values are treated as **raw H I**;
- no helium factor is applied in the acquisition product;
- any later helium correction is applied once and globally only after the Paper I source-profile convention is frozen.

## Preferred-source hierarchy

Hunter et al. (2021) independently provides a verified Sérsic H I model for both systems,

`Sigma_HI(R) = Sigma0 exp[-(R/R0)^(1/n)]`.

However, the Iorio online tables contain the higher-information numerical radial profiles. Therefore:

- **Iorio 2017 is the preferred Paper I public source** for UGC05918 and UGC07559;
- Hunter 2021 is retained as an independent analytic cross-check/QC model;
- the analytic Hunter model must not overwrite or replace the numerical Iorio measurements.

## Reproducible ingestion

Script:
` scripts/stationary/ingest_iorio2017_ddo87_ddo126_hi_profiles.py `

Workflow:
` .github/workflows/ingest_iorio2017_ddo87_ddo126_hi.yml `

Raw-source output:
` data/stationary/source_reconstruction/iorio2017_ddo87_ddo126_hi_profiles_v1.csv `

Machine summary:
` validation/stationary/iorio2017_ddo87_ddo126_hi_profiles_v1_summary.json `

Combined output:

- galaxies: **2**
- source rows: **25**
- output SHA-256: `639717da95d78ff1002a4e16b73e4d221d963404e052c08b4986a7c14b6289df`

## Transformations deliberately not performed

No:

- source-to-frozen distance rescaling;
- inclination-amplitude rescaling;
- helium correction;
- interpolation/common-grid resampling;
- extrapolation/taper;
- persistence fitting;
- blind-set evaluation.

## Database disposition

UGC05918 and UGC07559 move to **`raw_source_profile_ingested`** in the public-source acquisition layer. The next operation for these profiles is common source-metadata/radial-coverage QC, not persistence fitting.
