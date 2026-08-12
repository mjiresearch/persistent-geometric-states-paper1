# van Zee et al. (1997) H I profile-family audit v1

**Status:** FAMILY/CROSSMATCH AUDIT COMPLETE; ORIGINAL-PAPER PROFILE-CONVENTION AND NUMERICAL EXTRACTION PENDING  
**Date:** 2026-08-12  
**Scientific boundary:** pre-fit source acquisition only. `L_A` and `C_A` remain locked.

## Primary publication identity

L. van Zee, M. P. Haynes, J. J. Salzer & A. H. Broeils (1997), **“A Comparative Study of Star Formation Thresholds in Gas-Rich Low Surface Brightness Dwarf Galaxies,”** *The Astronomical Journal* **113**, 1618–1637. ADS bibcode `1997AJ....113.1618V` (NED index displays the first-author suffix in lower case). The Cornell ExtraGalactic Group publication page confirms the title, authors, journal, volume, year and first page.

The primary abstract describes **six low-surface-brightness dwarf galaxies (LSBDGs) plus four “normal” gas-rich dwarf comparison galaxies**. This resolves an important project-language ambiguity: the prior shorthand **“van Zee six-profile family” refers to the six-object LSB subsample, not to six members of the frozen Paper I stationary master.**

## Candidate 1997 sample membership

A later published literature compilation explicitly labels a “van Zee sample” and lists UGCA 20 followed by ten UGC systems. UGCA 20 is tied to the separate van Zee et al. (1996) paper, leaving the following ten as the working 1997 sample reconstruction:

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

This ten-object partition is consistent with the 1997 abstract's 6+4 design and with later literature repeatedly attributing H I/rotation data for these systems to van Zee et al. (1997). **Because the accessible original ADS scan has not yet been retrieved in this work session, the individual ten-name membership/partition remains flagged for final primary-paper table verification before source-profile freeze.** It is adequate for acquisition triage but is not being promoted as a frozen source convention on secondary evidence alone.

## Crossmatch to the frozen 149-galaxy stationary master

Exact canonical-name matching against `validation/stationary/stationary_sample_manifest_v1.csv` yields five obvious overlaps:

| van Zee identifier | Frozen SPARC identifier | Frozen role | In six-LSB subset? |
|---|---|---|---|
| UGC 191 | UGC00191 | calibration | no — comparison dwarf |
| UGC 891 | UGC00891 | calibration | no — comparison dwarf |
| UGC 5716 | UGC05716 | blind | yes |
| UGC 5764 | UGC05764 | calibration | no — comparison dwarf |
| UGC 11820 | UGC11820 | blind | yes |

The following working 1997 identifiers do not occur under the corresponding zero-padded UGC names in the frozen master:

- UGC 2684 -> no `UGC02684`
- UGC 2984 -> no `UGC02984`
- UGC 3174 -> no `UGC03174`
- UGC 634 -> no `UGC00634`
- UGC 7178 -> no `UGC07178`

Therefore **there is not a six-galaxy frozen-master overlap from this paper under direct UGC naming**. The current Paper I target from this source family is five frozen galaxies, pending a final alias check of the five nonmatches. No sixth galaxy will be invented to satisfy the old shorthand.

### Frozen roles of the five current overlaps

- calibration: UGC00191, UGC00891, UGC05764
- blind: UGC05716, UGC11820

These roles are immutable and are not changed by source availability.

## Why the six-profile wording arose

The paper itself is explicitly a study of **six LSBDGs** plus four normal comparison dwarfs. Thus “six-profile family” should be interpreted as a source-paper/subsample description. For the stationary Paper I database, only galaxies that actually crossmatch the frozen 149-member master are promoted.

This correction prevents two errors:

1. extracting a sixth nonexistent SPARC target merely because the source paper has six LSB dwarfs; and
2. ignoring the three normal-comparison galaxies that do overlap the frozen master and may supply valid direct H I radial profiles.

## Current public-access state

Public authoritative discovery routes confirm the publication and ADS bibcode, and ADS documents that scanned historical AJ articles are available through its Article Service. In this work session, the modern ADS abstract endpoint returned rate-limit/access failures and the legacy scanned-PDF endpoint could not be retrieved through the available browser transport.

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
9. alias verification; and
10. profile-level QC before normalization.

If the original vector/table/scan route remains inaccessible, the five objects stay `source_family_identified / numeric_profile_pending` and work proceeds to the next public source family rather than looping.

## Current disposition

- publication identity: **COMPLETE**
- 6+4 study design: **COMPLETE**
- explanation of old “six-profile” shorthand: **COMPLETE**
- exact frozen direct-name crossmatch: **COMPLETE — five current overlaps**
- alias check of five direct-name nonmatches: **PENDING**
- original-paper ten-object table verification: **PENDING**
- profile figure/table and quantity-convention audit: **PENDING**
- numerical profile extraction: **PENDING**
- ingestion into stationary database: **PENDING**

No persistence parameter has been evaluated in performing this source audit.
