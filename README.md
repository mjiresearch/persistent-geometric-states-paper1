# Persistent Geometric States — Paper I

Data, analysis code, validation products, and reproducibility materials for Paper I of the **Persistent Geometric States** framework.

## Purpose

This repository is the external reproducibility archive accompanying Paper I. Large observational tables, machine-readable data products, validation outputs, and analysis code are maintained here rather than embedded directly in the manuscript appendices.

The manuscript appendices describe the methods, definitions, selection rules, validation tests, and principal results. Where appropriate, each appendix links to the corresponding version-controlled material in this repository.

## Repository structure

```text
persistent-geometric-states-paper1/
├── README.md
├── data/
│   ├── stationary/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── frozen/
│   ├── longitudinal/
│   └── cross-sectional/
├── validation/
│   └── stationary/
├── analysis/
│   └── stationary/
├── scripts/
│   └── stationary/
├── figures/
├── tables/
├── appendices/
└── docs/
```

Git does not preserve empty directories. Directory placeholder files are included until scientific products are committed.

## Stationary SPARC data product

The first frozen observational product is intended to be:

`data/stationary/frozen/stationary_master_v1.csv`

Before a dataset is designated **frozen**, its construction and audit must establish, at minimum:

- provenance against authoritative SPARC source material;
- column definitions and physical units;
- galaxy and radial-point counts;
- duplicate handling;
- missing-value / NaN handling;
- signed-gas treatment;
- radial ordering within each galaxy;
- explicit selection and exclusion criteria; and
- reproducible checks against the authoritative observational data.

A frozen product must not be silently overwritten. Subsequent substantive changes receive a new version identifier.

## Data-status terminology

- **raw** — source or source-derived material retained for provenance;
- **processed** — intermediate/reconstructed products still subject to validation;
- **frozen** — audited version used for reported manuscript results;
- **validation** — machine-readable audit and comparison products.

## Reproducibility principle

Numerical values reported in Paper I should be traceable to a frozen input dataset, a versioned analysis procedure, and a reproducible output. Placeholder or illustrative values are not treated as empirical results.

## Appendices

The manuscript appendices should remain readable scientific documents rather than repositories for thousands of machine-readable rows. Appendix sections will therefore summarize methods and results and link to the corresponding repository directories/files when the underlying tables, diagnostics, or code are too large for the manuscript.

## Citation and provenance

Formal citation information, source-data acknowledgements, release/version identifiers, and a repository snapshot corresponding to the submitted manuscript will be added before archival release.
