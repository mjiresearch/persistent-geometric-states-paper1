# FEASTS 2025 blind H I source-acquisition protocol v1

**Frozen before inspecting the numerical NGC5033 radial-profile values or any blind rotation/persistence outcome.**

This protocol applies the already-established FEASTS 2025 machine-readable source QC unchanged to the frozen blind galaxy **NGC5033**.

## Public source

Use the official FEASTS password-free release file `HIprof_wang25.ecsv` (Wang et al. 2025, ApJ 980:25, DOI `10.3847/1538-4357/ada95a`, arXiv `2501.01289`). The repository-preserved source file and SHA-256 remain the authoritative acquisition artifact.

The published `SigmaHI_Msunpc2` values are treated as raw atomic H I with no helium factor. The FEASTS source analysis has already deprojected the surface-density profile using its H I disk geometry. Do not rescale surface-density amplitude to the frozen SPARC inclination.

## Locked source-only QC

Apply exactly the same checks already used for the calibration galaxies NGC2903 and NGC4559:

1. exactly one machine-readable source row for the target;
2. equal array lengths for angular radius, source physical radius, and H I surface density;
3. at least three finite measured profile points;
4. positive finite radii;
5. strictly increasing angular radius;
6. strictly increasing source physical radius;
7. non-negative finite H I surface density;
8. the distance implied by `(radius_arcsec, radius_kpc)` must agree with the displayed one-decimal `Dist` value within half of the displayed 0.1-Mpc unit (`0.05 Mpc`);
9. the distance implied by the radial pairs must be constant across the profile to numerical precision;
10. an outer downward `Sigma_HI = 1 M_sun pc^-2` crossing must be present;
11. that crossing must agree with the ECSV tabulated `R_1` within one native profile radial step.

Angular radius is converted separately to the frozen SPARC distance and retained alongside the source-distance radius. The measured inner/outer support relative to the frozen rotation grid is recorded, but missing support is **not** filled during acquisition; continuation is a separate frozen stage.

## Blind firewall

During source acquisition/QC and any profile promotion:

- do not read `Vobs`, residual accelerations, persistence predictions, model preference, `L_A`, `C_A`, or `tau_A`;
- do not compare NGC5033 with any blind-fit outcome;
- do not tune source choice, thresholds, radii, amplitude, or continuation using blind performance.

If all source-only checks pass, NGC5033 may be promoted to `raw_source_profile_ingested` and the certified blind count may increase. If any locked source check fails for a genuine data reason, the profile fails closed. Coding/provenance defects may be corrected only with a documented reason independent of blind outcomes.

`L_A` and `C_A` remain locked.
