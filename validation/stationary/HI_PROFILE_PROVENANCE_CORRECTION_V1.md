# H I profile provenance correction v1

**Status:** ACTIVE CORRECTION TO PRE-FIT PROVENANCE BUILD

A source-list transcription error in the earlier stationary H I provenance
scaffold marked `NGC4138` as unavailable and omitted `UGC06818`.

Hua et al. identify the six SPARC galaxies without compiled H I surface-density
profiles as:

- D512-2
- D564-8
- D631-7
- NGC5907
- NGC7339
- UGC06818

Intersecting that list with the frozen 149-galaxy stationary master yields:

- D564-8 — calibration
- D631-7 — calibration
- NGC5907 — calibration
- UGC06818 — blind

`NGC4138` remains in the frozen stationary sample and is eligible for public
profile acquisition.

The retained-profile count remains unchanged at 145 galaxies if none of the
four unavailable systems is independently recovered before fitting:

- 101 calibration
- 44 blind

The source generator `scripts/stationary/build_hi_profile_provenance_v1.py` has
been corrected. Any previously generated
`stationary_hi_profile_provenance_v1.csv` carrying the old NGC4138 flag is
**superseded for availability decisions** and must be regenerated before the
final source-profile freeze.

No persistence-model result was inspected or used in making this correction.
