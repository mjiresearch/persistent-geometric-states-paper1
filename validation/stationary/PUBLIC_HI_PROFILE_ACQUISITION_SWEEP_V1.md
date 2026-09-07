# Public H I profile acquisition sweep v1

## Goal

Recover the radial H I surface-density profiles needed by the frozen stationary SPARC analysis from public, independently reproducible sources before requesting the private compilation used in later SPARC work.

## Scientific rule

The calibration/blind split remains frozen. No acquisition decision may depend on persistence-model performance. `Vgas(R)` is never inverted or substituted for `Sigma_HI(R)` in the primary analysis.

## Master literature map

Hua et al. (2025, A&A 703, A223), Appendix A, Table A.1 identifies 32 source-family entries for the 169 available SPARC H I surface-density profiles. The source-family registry is stored at:

`data/stationary/source_reconstruction/hua2025_hi_source_family_registry_v1.csv`

Table A.1 provides source-family counts, not a galaxy-by-galaxy mapping. Therefore the public sweep requires a separate galaxy/reference crosswalk.

## Acquisition hierarchy

For every retained stationary galaxy, use the first available route in this order:

1. author/journal/CDS/VizieR machine-readable radial `Sigma_HI(R)` table;
2. public calibrated H I moment-0 map or cube from the original survey/archive, reduced with a frozen tilted-annulus extraction procedure;
3. numerical table embedded in an openly licensed/public article if redistribution rights permit extraction and republication;
4. otherwise mark `public_profile_unresolved`.

No digitization of plotted curves is part of the primary freeze unless it is separately preregistered, uncertainty-validated against galaxies with machine-readable profiles, and clearly labeled as digitized data.

## Publication / redistribution policy

A file being publicly downloadable does not automatically mean that we may relicense or redistribute it. The final public profile package must carry, per source and per galaxy:

- original citation and DOI/bibcode;
- source URL/archive identifier in the acquisition log;
- acquisition date and checksum where feasible;
- data-product type (`published_table`, `survey_map_reduction`, etc.);
- original license/rights statement;
- whether raw redistribution is permitted;
- whether only derived radial profiles may be redistributed;
- transformation code/version and unit conventions;
- attribution text required by the source.

Where redistribution rights are unclear, the repository may publish scripts, checksums, provenance and derived products only when legally justified; it must not mirror restricted raw data.

## Public routes confirmed at sweep start

- **Verheijen & Sancisi (2001):** public A&A/VizieR catalogue `J/A+A/370/765`; the data paper explicitly includes radial H I surface-density profiles and H I atlas products.
- **Noordermeer et al. (2005):** public WHISP VizieR catalogue `J/A+A/442/137` confirmed; table/map content still requires detailed extraction audit.
- **Swaters et al. (2002):** article/public survey provenance confirmed; the paper reports radial H I surface-density profiles for its WHISP dwarf sample. Exact machine-readable/public-map route remains to be audited.
- **de Blok et al. (1996):** public article/arXiv/author copies confirmed; exact machine-readable/public-map route remains to be audited.

These four source families alone account for the dominant fraction of the Hua compilation and are the first acquisition priority.

## Existing independent public reductions

The project library already contains direct annular H I profiles produced from public H I products for DDO154 and DDO168, plus a prepared LITTLE THINGS FITS-ingestion path for NGC2366 and NGC4214. Those products are validation assets and will only enter the stationary freeze after their provenance, geometry, units, beam masking and radius conventions pass the same QC as the literature-table route.

## Required galaxy-level manifest

Create `stationary_public_hi_acquisition_manifest_v1.csv` with at least:

`galaxy,stationary_role,hi_reference,source_family,public_route,product_id,profile_status,redistribution_status,units_status,distance_status,inclination_status,helium_status,coverage_status,qc_status,notes`

The manifest must contain all 149 frozen stationary galaxies. The four systems known absent from the Hua 169-profile set remain explicit exclusions unless a genuinely independent public profile is found before calibration.

## Completion criterion

The source-profile freeze may be declared complete only after every retained galaxy is either:

- `direct_public_profile_frozen`, or
- `predeclared_exclusion_no_direct_profile`.

Only then may the project build `stationary_hi_profiles_v1.csv`, `stationary_source_profiles_v1.csv`, run interpolation/coverage QC, and fit the global stationary parameters.

## Current status

**IN PROGRESS — public source-family sweep started.**

The private Lelli compilation remains a contingency route, not the primary acquisition path.
