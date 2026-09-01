# Persistence-history data workspace

This directory is the staging area for Milky Way source-history tests of the Persistence Framework.

## Current public-data status

Updated 2026-09-01. **SDSS DR20 is now publicly available** (released 2026-07-30). The earlier 2026-08-07 note that DR19 was still the latest live release is superseded.

Relevant current public resources include:

- **SDSS DR20 / DR20-carried APOGEE products:** APOGEE spectra and products in DR20 are unchanged from DR19/DR17 where documented; Astra/ASPCAP/AstroNN provide stellar parameters and individual abundances including Mn. The legacy APOGEE DR17 astroNN VAC provides abundances, distances, ages, and orbital parameters and is suitable for an independent manganese-history replication.
- **GALAH DR4:** the recommended all-star catalog contains stellar ages and elemental abundances including `mn_fe`; public value-added catalogs provide Gaia crossmatches, Galactocentric phase space/orbits, and BSTEP ages/masses. This is the preferred public-data route for a first manganese chemical-history test.
- **MaNGA DR17:** resolved spectra span the optical range containing the newly predicted [Mn III] 8081.28 and 8213.52 Angstrom diagnostics. These lines are not a standard MaNGA DAP product, so any test requires custom residual-spectrum fitting/stacking and is a secondary line-search arm rather than the primary v0 test.

## Observational queue

1. **SDSS DR20 young-vs-old current-field test + open-cluster control** — COMPLETE on `agent/dr20-young-old-current-field-v1`; conventional-dynamics challenge v2 remains the required interpretation gate. The v1 result is persistence-compatible, not a detection.
2. **Manganese Chemical-History Test** — NEXT / PUBLIC DATA AVAILABLE. Run GALAH DR4 first; use APOGEE as an independent replication; retain MaNGA as a custom [Mn III] emission-line search arm. The test asks whether a manganese-based chemical-history coordinate adds dynamical information after present-position, metallicity, alpha-abundance, age, selection, and conventional-dynamics controls. Manganese abundance is a history tracer, not a simple clock and not a direct persistence observable.

The manganese block is intentionally adjacent to the DR20 young-vs-old block because it is a complementary history-sensitive test that does not depend on receipt of the requested Lelli H I package.

## Files

- `persistence_history_master_template.csv`: canonical one-row-per-star schema. It reserves fields for future email-authorized history products (birth radius, migration, perturbation, accretion, etc.).
- `persistence_dataset_manifest.csv`: public/restricted source inventory and intended persistence use.
- `dr20_independent/`: frozen DR20 young-vs-old protocols, results, open-cluster control, and conventional-dynamics challenge.
- `manganese_chemical_history/`: public-data feasibility note and pre-outcome v0 protocol for the manganese chemical-history block.

## Raw-data policy

Raw survey files should be retained separately from derived tables and should not be silently converted into claims about source history. Every imported or derived field must retain provenance. New history proxies must be protocol-frozen before their dynamical outcomes are inspected; null/negative results are retained without threshold rescue.
