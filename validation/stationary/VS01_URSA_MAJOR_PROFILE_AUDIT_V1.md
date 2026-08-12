# Verheijen & Sancisi 2001 / Sanders & Verheijen 1998 — Ursa Major H I profile audit v1

**Status:** PUBLIC RADIAL H I PROFILE ATLAS CONFIRMED; CURRENT NUMERICAL ASSET ROUTE PENDING / CLOSED FOR THIS PASS  
**Date:** 2026-08-12  
**SPARC/Lelli reference IDs:** `VS01`, `SV98`  
**Scientific boundary:** acquisition/provenance only. `L_A` and `\mathcal C_A` remain locked.

## Why this source family was audited

The frozen-sample SPARC/Lelli reference map ranks `VS01` and `SV98` as the highest-yield untouched source family. Each maps to **27 frozen Paper I galaxies = 19 calibration + 8 blind**.

The 27 frozen galaxies are:

`NGC3726, NGC3769, NGC3877, NGC3893, NGC3917, NGC3949, NGC3953, NGC3972, NGC3992, NGC4010, NGC4013, NGC4051, NGC4085, NGC4088, NGC4100, NGC4138, NGC4157, NGC4183, NGC4217, UGC06399, UGC06667, UGC06818, UGC06917, UGC06923, UGC06930, UGC06983, UGC07089`.

## Primary source

M. A. W. Verheijen & R. Sancisi (2001), **“The Ursa Major cluster of galaxies. IV. H I synthesis observations,”** *Astronomy & Astrophysics* 370, 765–867, DOI `10.1051/0004-6361:20010090`, arXiv `astro-ph/0101404`.

The paper reports a WSRT synthesis survey of **43 spiral galaxies** and explicitly states that its atlas contains **radial H I surface-density profiles** in addition to H I channel maps, global H I profiles, integrated H I column-density maps, velocity fields, position-velocity diagrams, and rotation curves.

This is therefore a valid original public source family for the Paper I direct-H I acquisition program.

## Public machine-readable catalog state

The CDS/VizieR catalog `J/A+A/370/765` is public and contains:

- table 1: 52-galaxy sample inventory;
- table 2: photometry;
- table 3: H I widths / integrated flux comparison;
- table 4: rotation curves (437 rows);
- table 5: synthesis-observation results (43 rows).

**The CDS release does not expose a numerical radial H I surface-density table.** Rotation-curve radii/velocities are not substituted for `Sigma_HI(R)`.

## arXiv source-package audit

The public arXiv source package was successfully downloaded in a bounded GitHub Actions audit. It contains **12 files**, including:

- `paper.tex`;
- `UMaHImap.ps`;
- `fig1.ps` through `fig8.ps`;
- `figA01a.ps`;
- `figA01b.ps`.

The arXiv record itself states that the submission is **32 pages including only 2 sample pages of the H I atlas**. It points to a separate **104-page, ~11 MB full atlas** at the historical NRAO URL:

`http://www.nrao.edu/library/preprints/00173.ps.gz`

The current NRAO URL returns **404 Not Found**. A targeted web search for that exact historical file did not locate a live public copy during this pass.

Thus `figA01a.ps` / `figA01b.ps` are sample atlas pages only and cannot supply the full 27-galaxy frozen overlap.

## Publisher state

The A&A publication is 103 journal pages (765–867), and the publisher index advertises a roughly 15.4 MB full article/PDF containing the atlas. The GitHub runner's direct A&A PostScript request returned **HTTP 403** on the first bounded attempt. Per the project's anti-loop rule, that endpoint was **not retried**.

The existence of the published atlas is not in doubt; the unresolved issue is a reproducible numerical/vector retrieval route from the current environment.

## Quantity convention

The source publication consistently describes the plotted quantity as **H I surface density**, not total gas. No helium scaling is introduced during source acquisition. Any global Paper I helium convention remains a later explicit normalization step and may be applied only once after the source-profile rules are frozen.

## Current disposition

- source-family identity: **COMPLETE**
- frozen 27-galaxy overlap: **COMPLETE**
- direct radial H I profiles published: **CONFIRMED**
- CDS numerical radial H I table: **ABSENT**
- arXiv full 43-galaxy atlas: **ABSENT; only two sample atlas pages included**
- historical NRAO full-atlas link: **DEAD / 404**
- A&A GitHub-runner PostScript route: **CLOSED AFTER FIRST HTTP 403; NO RETRY**
- numerical Paper I profile ingestion from this family: **PENDING A GENUINELY NEW PUBLIC ASSET MECHANISM**

## Anti-loop decision

Do **not** repeat the NRAO URL search, A&A GitHub-runner request, or arXiv sample-page audit. Reopen this family only if a genuinely new mechanism becomes available, such as a directly retrievable full publisher PDF/vector atlas, institutional archive copy, or machine-readable republication of the radial H I profiles.

The acquisition queue now advances to the next Lelli-ranked untouched family: **Swaters et al. 2002 (`Sw02`) — 13 frozen galaxies (7 calibration + 6 blind)**.

No persistence parameter or blind outcome was inspected in making this provenance decision.
