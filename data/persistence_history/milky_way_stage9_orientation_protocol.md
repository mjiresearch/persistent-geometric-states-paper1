# Milky Way Stage 9 orientation-history protocol

Date: 2026-08-09

## Purpose

Stage 9 will test whether a persistence field derived from baryonic history can move the Milky Way orbit-weight solution toward the conventional full-potential solutions without using those halo solutions to determine the free shape of the persistence field.

The present-day, non-flipped Galactic frame remains the canonical primary case. A possible historical reorientation is introduced only as a predeclared sensitivity dimension.

## Primary and sensitivity cases

The orientation amplitude is frozen to the following grid before any comparison with Portail17+halo, Hunter24+halo, or the required acceleration residual:

- Stage 9A: 0 degrees — canonical baseline
- Stage 9B: 30 degrees
- Stage 9C: 60 degrees
- Stage 9D: 90 degrees
- Stage 9E: 120 degrees
- Stage 9F: 150 degrees
- Stage 9G: 180 degrees

The historical orientation is represented by a time-dependent rotation operator R(t). The initial implementation uses a fixed rotation axis, a transition centre in lookback time, and a finite transition duration. These are source-history descriptors and must not be chosen by maximizing agreement with halo-derived orbit weights or force residuals.

## Memory-time sensitivity

The initial predeclared memory-time grid is 1, 2, 4, 8, and 16 Gyr. These values are sensitivity cases, not fit parameters.

Do not select a preferred memory time by maximizing agreement with the existing pulsar residual catalog, Portail17+halo, Hunter24+halo, or Delta a(R). If later Galactic-archaeology evidence provides an independent prior on a characteristic persistence timescale, that prior must be documented before force comparison.

## Required source-side operation

For each historical baryonic source snapshot:

1. reconstruct the source in its historical frame;
2. apply the time-dependent orientation operator to positions;
3. rotate vector/current quantities consistently;
4. apply the persistence temporal kernel;
5. accumulate the present persistence field;
6. freeze the resulting field before comparing it with halo-based targets.

The 0-degree case must reduce exactly to the original non-flipped Stage 9 construction.

## Comparison protocol

For every predeclared orientation/memory case, use the same stellar sample, initial conditions, integration time, orbit gridding, mirroring, NNLS procedure, and diagnostics.

Compare each persistence result against both Portail17+halo and Hunter24+halo using at minimum:

- Pearson correlation of orbit weights;
- Spearman correlation of orbit weights;
- cosine similarity of orbit-weight vectors;
- weighted RMS orbit-weight difference;
- spatial density reconstruction residuals;
- orbital-family fractions where available;
- radial Delta a(R) error;
- three-dimensional acceleration residual maps.

The 0-degree result remains the primary reported test. The orientation sweep is a sensitivity analysis unless an independent observational prior is frozen in advance.

## Interpretation of 180 degrees

A 180-degree case is retained deliberately. Scalar density geometry may become approximately degenerate with the 0-degree case for symmetric components, while vector/current terms can reverse sign or direction. The 0-versus-180 comparison is therefore a diagnostic of whether the implemented persistence source is effectively scalar-only or contains physically meaningful current/vector memory.

## Guardrails

- Do not optimize orientation angle against Portail17+halo or Hunter24+halo.
- Do not optimize orientation angle against Delta a(R).
- Do not optimize memory time against the halo orbit weights or the existing pulsar residual catalog.
- Do not replace Stage 9A with a 90-degree baseline solely because a flip has been proposed in the literature.
- Do not interpret a high-correlation sensitivity point as confirmation unless it also approaches the independently required acceleration field and survives the full three-dimensional diagnostics.
- Any later narrowing of angle, transition epoch, transition duration, or rotation axis must be justified by independent Galactic-archaeology observations and frozen before force comparison.

## Current scientific boundary

The Stage 7 archive established that the project remains source-history limited: global stellar-mass and effective-radius summaries are not sufficient to reconstruct a unique physical spatial star-formation history. This Stage 9 orientation scaffold does not override that boundary. It makes the geometry ready so that a sufficiently resolved baryonic-history product can be inserted without redesigning the analysis after the halo comparison is visible.
