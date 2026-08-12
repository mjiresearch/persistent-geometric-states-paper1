# van Zee et al. (1997) H I profile-family audit v1

**Status:** FAMILY/CROSSMATCH AUDIT COMPLETE; ORIGINAL-PAPER PROFILE-CONVENTION AND NUMERICAL EXTRACTION PENDING  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `C_A` remain locked.

## Primary publication identity

L. van Zee, M. P. Haynes, J. J. Salzer & A. H. Broeils (1997), **“A Comparative Study of Star Formation Thresholds in Gas-Rich Low Surface Brightness Dwarf Galaxies,”** *The Astronomical Journal* **113**, 1618–1637. DOI `10.1086/118379`. ADS bibcode `1997AJ....113.1618V`.

The primary abstract describes **six low-surface-brightness dwarf galaxies (LSBDGs) plus four “normal” gas-rich dwarf comparison galaxies**. This resolves an important project-language ambiguity: the prior shorthand **“van Zee six-profile family” refers to the six-object LSB subsample, not to six members of the frozen Paper I stationary master.**

## 1997 sample membership

A later published literature compilation explicitly labels a “van Zee sample” and lists UGCA 20 followed by ten UGC systems. UGCA 20 is tied to the separate van Zee et al. (1996) AJ 112, 129 study, leaving the following ten as the 1997 AJ 113 working sample reconstruction:

### Six LSB dwarfs

- UGC 2684
- UGC 2984
- UGC 3174
- UGC 5716
- UGC 7178
- UGC 11820

### Four normal gas-rich dwarf comparisons

- UGC 191
- UGC 634
- UGC 891
- UGC 5764

This ten-object partition is consistent with the 1997 abstract's 6+4 design and with later literature repeatedly attributing H I/rotation data for these systems to van Zee et al. (1997). Final original-paper table verification remains required before the source-profile freeze, but the membership is sufficient for acquisition/crossmatch control.

## Exact crossmatch to the frozen 149-galaxy stationary master

Canonical-name and alias checking yields **five** Paper I overlaps:

| van Zee identifier | Frozen SPARC identifier | Frozen role | Source subsample |
|---|---|---|---|
| UGC 191 | UGC00191 | calibration | normal comparison dwarf |
| UGC 891 | UGC00891 | calibration | normal comparison dwarf |
| UGC 5716 | UGC05716 | blind | LSBDG |
| UGC 5764 | UGC05764 | calibration | normal comparison dwarf |
| UGC 11820 | UGC11820 | blind | LSBDG |

The five remaining van Zee identifiers do not map to a frozen member:

- UGC 2684 — catalog identifiers include LEDA 12514 / TC 47 / [MI94] Im 25; no frozen-master alias match found.
- UGC 2984 — no frozen-master canonical/alias match identified.
- UGC 3174 — no frozen-master canonical/alias match identified.
- UGC 634 = **DDO 7** — neither UGC00634 nor DDO7 is in the frozen master.
- UGC 7178 = **DDO 110 / LEDA 38793 / MCG+00-31-036** — none is a frozen-master member.

Therefore the Paper I target from this source family is **five frozen galaxies: three calibration + two blind**. No sixth target is to be invented to satisfy the old shorthand.

## Important source correction: UGC05829

A live-session provisional crossmatch incorrectly included `UGC05829` in the van Zee family. That is now rejected.

A published H I compilation attributes:

- UGC 5716 -> van Zee et al. (1997)
- UGC 5764 -> van Zee et al. (1997)
- UGC 7178 -> van Zee et al. (1997)
- **UGC 5829 -> Taylor et al. (1994)**

Accordingly, frozen galaxy `UGC05829` remains a valid stationary galaxy but must be acquired under its correct Taylor et al. source family, not van Zee 1997.

## Why the six-profile wording arose

The paper itself is explicitly a study of **six LSBDGs** plus four normal comparison dwarfs. Thus “six-profile family” is a source-paper/subsample description. For the stationary Paper I database, every valid direct H I profile is considered only if its galaxy actually belongs to the frozen 149-member master.

This prevents two errors:

1. extracting a sixth nonexistent SPARC target merely because the source paper has six LSB dwarfs; and
2. discarding the three normal-comparison galaxies that do overlap the frozen master and can supply valid direct H I profiles.

## Current public-access state

Public discovery routes verify the publication, DOI and ADS bibcode. The original historical AJ article remains the required authority for profile-level conventions. In the current browser environment the original scan/vector/table data have not yet been recovered at sufficient fidelity for numerical ingestion.

Accordingly, this audit does **not** fabricate the following still-needed source conventions:

- exact radial H I/gas surface-density figure/table number;
- whether the plotted radial ordinate is raw H I or helium-corrected gas;
- exact deprojection/inclination convention;
- angular versus physical radial coordinate in each published profile;
- source distances and inclinations used in the plotted radial profiles;
- beam/resolution for each relevant map/profile;
- numerical radial profile points.

Those items remain **PRIMARY-SCAN VERIFICATION PENDING**.

## Acquisition/QC rule

For each of the five frozen overlaps, promotion to `stationary_hi_profiles_v1.csv` requires:

1. primary-paper profile identification;
2. raw radial coordinate and units;
3. raw H I or gas surface-density ordinate and units;
4. helium-treatment flag;
5. inclination/deprojection convention;
6. source distance stored separately from the frozen SPARC distance;
7. beam/resolution metadata;
8. digitization/data-table provenance and method;
9. profile-level QC before normalization; and
10. exact source citation.

If the original vector/table/scan route remains inaccessible, the five objects stay `source_family_identified / numeric_profile_pending` and work proceeds to the next public source family rather than looping.

## Current disposition

- publication identity / DOI / ADS bibcode: **COMPLETE**
- 6+4 study design: **COMPLETE**
- source-family membership reconstruction: **COMPLETE for acquisition control; primary-paper table recheck retained as final-freeze QC**
- frozen canonical-name crossmatch: **COMPLETE**
- alias check of five direct-name nonmatches: **COMPLETE — no hidden frozen sixth overlap found**
- `UGC05829` false van-Zee attribution: **CORRECTED; route to Taylor et al. (1994)**
- Paper I overlap: **5 galaxies = 3 calibration + 2 blind**
- original-paper profile figure/table and quantity-convention audit: **PENDING**
- numerical profile extraction: **PENDING**
- ingestion into stationary database: **PENDING**

No persistence parameter has been evaluated in performing this source audit.
