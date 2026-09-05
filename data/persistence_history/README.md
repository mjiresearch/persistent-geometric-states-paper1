# Persistence-history data workspace

This directory is the staging area for Milky Way source-history tests of the persistence framework.

## Current public-data status

As checked on 2026-08-07, the official SDSS public site still identifies **DR19** as the latest live public release and states that DR20 is scheduled for 2026. Therefore, this repository does **not** label unverified DR20 products as downloaded public data.

Confirmed public DR19 products relevant to the test include:

- **APOGEE OCCAM**: cluster and member catalogs. The current documented cluster file is `occam_cluster-DR19-v2.fits`; the VAC includes Gaia DR3/SDSS-V identifiers, membership information, positions, kinematics, metallicity, bulk cluster motions, chemical abundances, and orbital parameters.
- **MWM MINESweeper**: BOSS halo-star stellar parameters, metallicities, alpha abundances, isochrone distances, and kinematic/orbital parameters with propagated uncertainties.

## Files

- `persistence_history_master_template.csv`: canonical one-row-per-star schema. It reserves fields for future email-authorized history products (birth radius, migration, perturbation, accretion, etc.).
- `persistence_dataset_manifest.csv`: public/restricted source inventory and intended persistence use.
- `hi4pi_grb_geometric_distance/`: reproducibility package for the geometric-distance / H I kinematic-residual test using the three GRB sightlines. It contains the public HI4PI cube downloader/extractor, the frozen target-coordinate manifest, and retrieval notes.

## Raw-data policy

Raw SDSS FITS files should be retained separately from derived tables and should not be silently converted into claims about source history. The master table should record provenance for every imported or derived field.

For the HI4PI GRB test, the large public FITS spectral cubes are not vendored into GitHub. The repository stores the retrieval code and frozen sightline definitions; extracted one-dimensional spectra and derived component fits should retain the originating HI4PI tile name and archive provenance.

## Pending ingestion

The current execution environment could verify the SDSS catalog documentation but could not retrieve the SAS FITS bytes because direct access to `data.sdss.org` was unavailable from the download runtime. The next successful ingestion should preserve the original FITS files, generate normalized CSV/Parquet derivatives, and join primarily through Gaia DR3 source IDs and SDSS-V identifiers.
