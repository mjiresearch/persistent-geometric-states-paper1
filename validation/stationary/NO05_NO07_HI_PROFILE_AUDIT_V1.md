# Noordermeer 2005 / 2007 — early-type disk H I profile provenance audit v1

**Status:** DIRECT `No05` RADIAL H I ATLAS CONFIRMED; FULL NUMERICAL ATLAS CURRENTLY UNAVAILABLE; `No07` IS DOWNSTREAM USE OF THE SAME H I DATA  
**Date:** 2026-08-12  
**SPARC/Lelli reference IDs:** `No05`, `No07`  
**Scientific boundary:** acquisition/provenance only. `L_A` and `\mathcal C_A` remain locked.

## Frozen Paper I overlap

Both Lelli reference IDs map to the same **12 still-untouched frozen galaxies = 10 calibration + 2 blind**:

`UGC02487, UGC02916, UGC02953, UGC03205, UGC03546, UGC03580, UGC05253, UGC06786, UGC06787, UGC08699, UGC09133, UGC11914`.

## No05 — direct observing source

E. Noordermeer et al. (2005), **“The Westerbork HI survey of spiral and irregular galaxies. III. HI observations of early-type disk galaxies,”** A&A 442, 137–157; arXiv `astro-ph/0508319`; VizieR `J/A+A/442/137`.

This is a direct WSRT/WHISP H I survey of **68 early-type disk galaxies**. The paper explicitly states that its appendix atlas shows, for all galaxies:

- H I surface-density maps;
- global H I profiles;
- velocity fields; and
- **radial H I surface-density profiles**.

Thus `No05` is a valid original direct-profile source family for Paper I.

### Public CDS state

The public VizieR catalog `J/A+A/442/137` contains:

- a 68-row H I-properties table;
- a 68-row observing-parameters table; and
- a 31-row table of references to earlier 21-cm synthesis observations.

No machine-readable radial `Sigma_HI(R)` table is exposed in the catalog.

### arXiv asset state

A bounded audit of the public arXiv source package found 14 files, including:

- `noordermeer.tex`;
- `noordermeer_A1.eps`;
- `noordermeer_A2.eps`;
- nine main-paper EPS figures.

No `.dat`, `.tbl`, `.tab` or `.csv` radial-profile asset is present.

The two appendix EPS files are flattened image-like PostScript assets rather than separable profile geometry:

- `noordermeer_A1.eps`: 193,778 bytes; 0 `moveto`; 0 `lineto`; 1 `show`; 2 literal strings;
- `noordermeer_A2.eps`: 193,809 bytes; 0 `moveto`; 0 `lineto`; 1 `show`; 2 literal strings.

They cannot supply publication-grade individual curve coordinates as native vectors.

### Separate full atlas

The arXiv record explicitly says the submission is 24 pages / 11 figures and that a **version with the full atlas** was distributed separately as a **9.3-MB gzipped PostScript** file at:

`https://www.astro.rug.nl/~edo/WHISPIII.ps.gz`

A single bounded check of that exact author-hosted path returned **404 Not Found**. A targeted search for the exact historical file did not locate another live public copy during this pass.

Per the project anti-loop rule, that dead atlas URL is not retried.

## No07 — downstream analysis, not a second H I acquisition source

E. Noordermeer et al. (2007), **“The mass distribution in early-type disk galaxies: declining rotation curves and correlations with optical properties,”** MNRAS 376, 1513–1546, uses rotation curves assembled from the same WHISP/WSRT H I observations together with optical spectroscopy.

For source acquisition, `No07` therefore does **not** constitute a second independent radial H I profile data source for these same 12 galaxies. The direct H I provenance remains `No05` / WHISP.

## Quantity/convention boundary

The primary paper calls the atlas quantity **H I surface density**. No global helium factor is introduced into Paper I at acquisition time unless an exact source statement requires it. Any later helium convention remains a separate, once-only normalization rule before source-profile freeze.

## Current disposition

- 12-galaxy frozen overlap: **COMPLETE**
- `No05` direct H I observing source: **CONFIRMED**
- radial H I profiles published: **CONFIRMED**
- CDS radial numerical table: **ABSENT**
- arXiv full atlas: **ABSENT; two flattened sample pages only**
- historical full-atlas URL: **DEAD / 404; NO RETRY**
- `No07`: **DOWNSTREAM SAME-DATA ANALYSIS; NOT A NEW PROFILE ACQUISITION ROUTE**
- numerical Paper I ingestion: **PENDING A GENUINELY NEW PUBLIC ATLAS/MAP/TABLE MECHANISM**

## Anti-loop decision

Do not repeat the historical `WHISPIII.ps.gz` request, search for the same dead link, or inspect the two flattened arXiv appendix pages again. Reopen only if a new archive, original WHISP map product, full atlas mirror, or machine-readable republication becomes available.

The Lelli-directed queue advances to the next genuinely distinct direct H I observing source rather than duplicating the `No05`/`No07` same-data chain.
