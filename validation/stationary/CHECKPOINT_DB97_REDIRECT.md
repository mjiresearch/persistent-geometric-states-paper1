# dB97 stationary H I provenance checkpoint

Status: **DB97 DOWNSTREAM — REDIRECT TO EXISTING DB96 STATE; DO NOT RESTART DB96**

## Locked state
- `L_A` and `C_A` remain locked.
- Continue only Lelli-directed public H I source acquisition.

## Lelli/SPARC targets in dB97
- F565-V2 — calibration in the current dB97 queue entry.
- F571-V1 — blind in the current dB97 queue entry.

## Provenance decision
`dB97` is de Blok & McGaugh (1997), MNRAS 290, 533, *The dark and baryonic matter content of low surface brightness disk galaxies* (arXiv:astro-ph/9704274). It is a mass-model analysis, not the original 21-cm observing paper.

The original resolved H I observations for these systems are in de Blok, McGaugh & van der Hulst (1996), MNRAS 283, 18-54 (`dB96`), *H I observations of low surface brightness galaxies: Probing low-density galaxies*. That source explicitly derives radial H I surface-density profiles from elliptical annuli in the H I maps.

The existing repository dB96 recovery state already lists **F565-V2 and F571-V1 as unresolved public numerical profiles**. Do not rerun or reopen the exhausted dB96 routes merely because dB97 appears separately in the SPARC/Lelli reference list.

Relevant existing checkpoint: `validation/stationary/DB96_JADHAV2019_PROFILE_RECOVERY_V1.md`.

## Exact next action
Mark `dB97` as a downstream redirect to the existing dB96 unresolved state, with reopen only for a genuinely new public numerical/vector/republication route for F565-V2 or F571-V1. Reconcile/rerank and continue the new highest-ranked actionable family.

No raster digitization, moment-map reconstruction, persistence fitting, or blind-outcome inspection.
