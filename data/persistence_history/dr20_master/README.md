# DR20 persistence master

Generated reproducibly from public SDSS DR20 VACs.

- MINESweeper rows: 56,104
- GravPot16 rows: 1,515,648
- Verified MINESweeper↔orbit join key: `None`
- Orbital matches: 0 / 56,104
- BOSS OCCAM verified join key: `None`
- BOSS OCCAM matched master rows: 0

The master intentionally reserves direct source-history fields (birth radius, migration, bar/spiral interaction, perturbation/accretion and disk rebuilding) for the permissioned email dataset. No positional/fuzzy star matching is used. See `join_report.json` for full schemas and overlap diagnostics.
