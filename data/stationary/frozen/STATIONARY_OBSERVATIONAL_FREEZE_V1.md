# Stationary observational freeze record v1

**Freeze status:** FROZEN

This record freezes the observational input boundary only. No value of `L_A`,
`C_A`, `tau_A`, or any persistence-model prediction was used to construct or
audit this dataset.

## Frozen products

- `data/stationary/frozen/stationary_master_v1.csv`
  - SHA-256: `254e17dbe22eb8371384e3c7f301f9936181b99384518e772be861567e4e896f`
  - 149 galaxies
  - 3,152 radial measurements
- `validation/stationary/stationary_sample_manifest_v1.csv`
  - SHA-256: `de5ee5a85c65be60f73239ccc4712333523fbfd06acd90c03db53512a0c02629`
- authoritative SPARC catalog used for metadata verification
  - `SPARC_Lelli2016c.mrt`
  - SHA-256: `5aa0501f6b0d881fa579030e315e7b5b6ef561a5bd3a07472f9929c7e5728243`

## Freeze conditions verified

1. All 149 eligible galaxies exist in the authoritative 175-galaxy SPARC catalog.
2. Quality flag, inclination, and adopted distance match the authoritative catalog.
3. Each galaxy satisfies `Q <= 2`, `i >= 30 deg`, and at least five valid radial points.
4. Galaxy membership and per-galaxy point counts match between manifest and master.
5. No duplicate galaxy-radius keys or duplicate observational rows are present.
6. Radial ordering, positive radii, and positive velocity uncertainties are preserved.
7. Signed gas values are retained without clipping or absolute-value replacement.

Any future change to the frozen observational master requires a new versioned
file and a new freeze record; `stationary_master_v1.csv` must not be silently
overwritten.
