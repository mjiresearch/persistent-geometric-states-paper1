# Public radial-HI build checkpoint — 17 galaxies v1

**Status:** acquisition checkpoint only; **not** the stationary source-profile freeze.

No value of `L_A`, `C_A`, a halo model, `Vobs` as source velocity, or any persistence residual was used to select or construct these profiles.

## Active harmonized build

- Frozen stationary galaxies represented: **17**
- Direct public radial H I measurements: **898**
- Frozen-SPARC source rows covered without H I extrapolation: **496**
- H I interpolation policy: linear, **inside the measured radial range only**
- Stored H I convention: hydrogen-only `Sigma_HI` in `Msun pc^-2`
- Downstream atomic-gas correction: one common factor `1.33`
- Stellar reference M/L: disk `0.5`, bulge `0.7`
- Source-current velocity policy: self-consistent model velocity; never `Vobs`

The 17 systems are DDO154, DDO168, IC2574, NGC1003, NGC2403, NGC2841, NGC2903, NGC2976, NGC3198, NGC3521, NGC4559, NGC5033, NGC5055, NGC5585, NGC6946, NGC7331, and NGC7793.

## Source families

- THINGS/LITTLE THINGS direct public map extraction: DDO154, DDO168
- FEASTS direct public radial profiles: NGC2841, NGC2903, NGC3198, NGC3521, NGC4559, NGC5033, NGC5055
- Leroy et al. (2008) / THINGS machine-readable CDS radial profiles: IC2574, NGC2403, NGC2976, NGC6946, NGC7331, NGC7793
- HALOGAS DR1 v2 public H I column-density maps: NGC1003, NGC5585

## Build hashes

The current working build produced these exact files:

- `stationary_hi_profiles_public_harmonized_v1.csv`
  - rows: 898
  - bytes: 182817
  - SHA-256: `df28e67df758b6f7dc95ec15ba9d18e689c87226013a1c3775cc1b46109d778e`
- `stationary_source_profiles_public_seed_v1.csv`
  - rows: 496
  - bytes: 90133
  - SHA-256: `26d5220cbe9f9f6dd7afad6b65d8b431175b540d9815ec467134f98722b395c3`
- `stationary_public_harmonized_summary_v1.csv`
  - rows: 17
  - bytes: 2000
  - SHA-256: `1b6ba39261cd1dde944e89b9d14b297189f90559da98ac60bb3bebbf251cdaf2`

The compact 17-row summary is committed under `data/stationary/source_reconstruction/stationary_public_harmonized_summary_v1.csv`. The two larger working CSVs remain acquisition products until their full provenance/standardization validation is finished; their hashes are frozen here so subsequent promotion can be checked byte-for-byte.

## HALOGAS QC

HALOGAS DR1 v2 has eight overlaps with the frozen 149-galaxy master. Four overlap systems were already represented by independent public profiles and are retained as cross-survey validation opportunities: NGC2403, NGC3198, NGC4559, NGC5055.

Four were initially new candidates:

- NGC1003 — accepted by the common thin-annulus extraction; 78 clean annuli, 2.044746–37.941398 kpc.
- NGC5585 — accepted; 80 clean annuli, 1.148710–21.314946 kpc.
- NGC0891 — **not** extracted by this method because the frozen SPARC inclination is 90 deg; thin elliptical deprojection is singular.
- UGC04278 — same edge-on exclusion at frozen inclination 90 deg.

NGC0891 and UGC04278 remain acquisition targets; they are not removed from the project. They require a separately preregistered edge-on surface-density reconstruction or an independent published radial profile.

HALOGAS `*_coldens.fits` products contain values on the physical H I column-density scale (~10^20–10^22 atoms cm^-2) while retaining a stale/inherited `BUNIT='JY/BEAM.km/s'` header. This mismatch is preserved as a QC/provenance flag. Zero-valued image background is excluded, matching the pre-existing frozen public-map reduction rule.

## Availability ceiling correction

Hua et al. identify six SPARC galaxies without published direct H I profiles. Five, not four, are in the frozen 149-galaxy stationary master:

- D564-8 — calibration
- D631-7 — calibration
- NGC4138 — blind
- NGC5907 — calibration
- UGC06818 — calibration

D512-2 is not in the frozen stationary sample. Therefore, if none of the five are independently recovered before fitting, the maximum direct-profile retained set is **144 = 100 calibration + 44 blind**. Original roles remain unchanged.

## Next acquisition order

1. Recover NGC4068 and UGC04483 from the public Lelli et al. (2014) products without inventing a new source mask or galaxy-specific threshold.
2. Continue the high-yield Verheijen & Sancisi / WHISP block (up to 26 non-Hua-missing frozen candidates after excluding NGC4138 and UGC06818 from any assumed-profile count).
3. Maintain NGC0891 and UGC04278 on a separate edge-on recovery track.
4. Continue lower-yield public source families only after these bulk routes are exhausted.

**Guardrail:** no `L_A` or `C_A` fitting until the full source-profile standardization, provenance, coverage, and rights audit is frozen.
