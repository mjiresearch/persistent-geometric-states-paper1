# Draft data request — Gaia DR3 off-plane force grid

**Status:** draft only; not sent.

**Target paper:** Francesco Sylos Labini & Roberto Capuzzo-Dolcetta, *Constraining the Geometry of Galactic Dark Matter with Gaia Data Release 3*, ApJ 1005:213 (2026), DOI 10.3847/1538-4357/ae7be7.

## Proposed message

Subject: Machine-readable Gaia DR3 v_c(R,z) and a_z(R,z) values from ApJ 1005:213

Dear Dr. Sylos Labini and Dr. Capuzzo-Dolcetta,

I am working on an independent gravitational-dynamics analysis using Gaia/SDSS data and would like to test a history-dependent gravitational hypothesis against a force observable that is independent of my source-history reconstruction.

Your 2026 ApJ paper is particularly useful because it reports both the off-plane circular-speed field v_c(R,z) and vertical acceleration a_z(R,z) over the region where Gaia DR3 kinematics are well constrained.

Would you be willing to share the machine-readable numerical values underlying Figures 4 and 5, or point me to a public archive if they are already available?

The most useful columns would be:

- R [kpc]
- z or |z| bin/slice [kpc]
- v_c(R,z) [km/s]
- uncertainty on v_c, including the adopted error floor if stored separately
- a_z(R,z) in the units used in the analysis
- statistical uncertainty on a_z
- systematic uncertainty on a_z, if available separately
- number of stars contributing to each bin
- adopted R_d and z_d for each reported curve/value
- any covariance information between neighboring bins, if available

If the plotting tables or analysis outputs contain additional velocity moments or gradient terms used in the Jeans calculation, those would also be valuable for a robustness check.

I would use the values as an independent dynamical observable and would cite the paper and any associated data product directly. I am not asking for proprietary Gaia data—only the derived numerical values underlying the published figures.

Thank you for considering the request.

Best regards,
[Name]

## Why these fields matter for the persistence test

The intended Stage 6 comparison is

\[
\Delta \mathbf{g}(R,z)
=\mathbf{g}_{\rm dyn}(R,z)-\mathbf{g}_{b,\rm inst}(R,z),
\]

followed by a blinded comparison to a source-history prediction

\[
H[\rho_b,J_b](R,z,t_0).
\]

The force residual must be constructed independently of the source-history variables. The numerical grid is therefore much more valuable than another rotation-curve proxy derived from the same MWM stellar sample.
