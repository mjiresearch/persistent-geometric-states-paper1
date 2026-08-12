# Iorio et al. (2017) — DDO168 radial H I profile audit v1

**Status:** RAW PUBLIC SOURCE PROFILE INGESTED  
**Date:** 2026-08-12  
**Scientific boundary:** source acquisition only. `L_A` and `\mathcal C_A` remain locked.

## Source

G. Iorio et al. (2017), *MNRAS* **466**, 4159–4192, DOI `10.1093/mnras/stw3285`.

The public OUP supporting-material archive contains the nested source member:

`results.zip::finalrot/ddo168_onlinetab.txt`

The source member SHA-256 is:

`b6616306fd12e01c56d87a8d50ef1fe57d94e817c01adb616d19b24c8aba11fc`

The full publisher supplement is not redistributed in the repository. Only the Paper-I-relevant radial H I columns are extracted into a provenance-preserving source CSV.

## Frozen Paper I target

- galaxy: **DDO168**
- frozen role: **calibration**
- frozen distance: **4.25 Mpc**
- frozen inclination: **63 deg**
- frozen SPARC radial domain: **0.41–4.12 kpc**

The frozen role and metadata are not modified by the source acquisition.

## Source metadata

The Iorio online table records:

- source distance: **4.3 Mpc**
- mean H I inclination: **62.0 deg**
- mean position angle: **272.7 deg**

The source and frozen values are retained separately. No radius or surface-density rescaling is applied at acquisition time.

## Numerical H I profile

The source table contains **15** strictly increasing radial samples:

- radius: **15–225 arcsec**
- source physical radius: **0.31–4.69 kpc**
- H I surface density `Sdens`: **0.86–16.43 Msun pc^-2**

The table definition states that `Sdens` is the H I surface density in `Msun pc^-2`, corrected for primary-beam attenuation. The Iorio paper's figure-layout description identifies the intrinsic H I surface density as **not corrected for helium**.

Therefore:

- the ingested values are **raw H I** for the Paper I source-convention audit;
- `helium_already_included = 0`;
- no helium factor is applied in the raw-source product;
- any later helium convention is applied once, globally, only after the common source-profile normalization rules are frozen.

## Reproducible ingestion

Script:

`scripts/stationary/ingest_iorio2017_ddo168_hi_profile.py`

Workflow:

`.github/workflows/ingest_iorio2017_ddo168_hi.yml`

Raw-source output:

`data/stationary/source_reconstruction/iorio2017_ddo168_hi_profile_v1.csv`

Machine-generated summary:

`validation/stationary/iorio2017_ddo168_hi_profile_v1_summary.json`

Output SHA-256:

`37dea9a3b5d42cb8a2a976e8a9e42ff75f36a6f4fdefeb7730ef3de804053953`

## Transformations deliberately not performed

The acquisition product applies no:

- source-to-frozen distance rescaling;
- inclination-amplitude rescaling;
- helium correction;
- interpolation or common-grid resampling;
- extrapolation or taper;
- persistence parameter evaluation;
- blind-set inspection.

## Database disposition

DDO168 moves from `available_nonpublic_request_required` to:

**`raw_source_profile_ingested`**

under the public Iorio/LITTLE THINGS source block.

The next relevant operation is common source-metadata/radial-coverage QC, not persistence fitting.
