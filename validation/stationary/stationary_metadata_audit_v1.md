# Stationary metadata audit v1

**Status:** PASS

- Authoritative SPARC catalog galaxies: 175
- Frozen eligible galaxies: 149
- Frozen master galaxies: 149
- Frozen radial measurements: 3152
- Galaxies passing all catalog/manifest/master checks: 149 / 149
- Duplicate galaxy-radius keys: 0
- Duplicate full rows: 0
- Negative signed gas rows preserved: 343 across 41 galaxies
- Zero gas rows: 88

## Verified metadata

For every eligible galaxy the audit compares the frozen manifest/master against
`SPARC_Lelli2016c.mrt` for the adopted distance, inclination, and quality flag,
and verifies the radial-point count and frozen selection rules.

## Selection boundary

- SPARC quality flag `Q <= 2`
- inclination `i >= 30 deg`
- at least 5 valid radial measurements

## Hashes

- `stationary_master_v1.csv`: `254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f`
- `stationary_sample_manifest_v1.csv`: `de5ee5a85c65be60f73239ccc4712333523fbfd06acd90c03db53512a0c02629`
- authoritative `SPARC_Lelli2016c.mrt`: `5aa0501f6b0d881fa579030e315e7b5b6ef561a5bd3a07472f9929c7e5728243`

## Failures

- None.
