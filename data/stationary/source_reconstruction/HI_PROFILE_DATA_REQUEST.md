# Request for SPARC radial HI surface-density profiles

## Target dataset

The primary Appendix I source reconstruction requires the azimuthally averaged
SPARC HI surface-density profiles used by Yasin & Desmond (2025, MNRAS 539,
2110; DOI 10.1093/mnras/staf453). Their paper states that profiles were
available for 169 SPARC galaxies and were supplied by Federico Lelli by private
communication. The paper's Data Availability statement says that other data
will be made available on reasonable request to the corresponding author.

Corresponding author listed by the journal:

Tariq Yasin  
University of Oxford  
`tariq.yasin@physics.ox.ac.uk`

## Requested content

Please provide the machine-readable azimuthally averaged HI surface-density
profiles used in the paper for the SPARC galaxies, preferably with:

- galaxy identifier;
- radius and radius units;
- Sigma_HI and units;
- whether Sigma_HI is face-on / inclination corrected;
- adopted distance used to convert angular radius to physical radius;
- any quoted measurement uncertainties;
- any flags for interpolation, extrapolation, beam correction, or missing
  radial bins;
- provenance/reference to the original HI data when available.

## Suggested request text

> Dear Dr. Yasin,
>
> I am preparing a reproducibility analysis of baryonic source profiles for a
> manuscript using the SPARC rotation-curve sample. Your 2025 MNRAS paper
> reports using azimuthally averaged HI surface-density profiles for 169 SPARC
> galaxies, supplied by Federico Lelli, and notes that nonpublic data are
> available on reasonable request.
>
> Would you be willing to share the machine-readable radial HI
> surface-density profiles used in that work, including any available radius,
> surface-density, uncertainty, and provenance metadata? The data will be used
> only as observational input to a predeclared analysis, with full citation to
> your paper and the original SPARC/source references.
>
> Thank you,
> Michael J. Iuliano

## Freeze rule

Receipt of these data may populate `stationary_hi_profile_provenance_v1.csv`
and the direct-profile tables, but may not alter the already-frozen stationary
calibration/blind roles. No persistence parameter fit is permitted before the
profile ingestion and validation audit are frozen.
