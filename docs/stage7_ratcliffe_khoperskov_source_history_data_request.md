# Draft data request — Ratcliffe/Khoperskov Milky Way source-history products

**Status:** draft only; not sent.

**Target work:** Ratcliffe et al. 2026, A&A 706, A103, DOI 10.1051/0004-6361/202557057, together with the orbit-superposition products introduced in Khoperskov et al. 2025, A&A 695, A220.

## Proposed message

Subject: Machine-readable Milky Way orbit-weighted spatial SFH / orbit-superposition products

Dear Dr. Ratcliffe and Dr. Khoperskov,

I am working on an independent Galactic-dynamics analysis that compares direct gravitational-acceleration measurements with reconstructions of the Milky Way's prior baryonic source distribution.

Your 2026 A&A paper is particularly valuable because it combines birth-radius estimates with the orbit-superposition reconstruction of the full APOGEE stellar disc, producing a spatially resolved, mass-weighted star-formation history at formation sites rather than relying on the present-day survey footprint.

Would you be willing to share the machine-readable numerical products underlying the spatial SFH figures, or point me to a public archive if they are already available?

### Minimum product that would be immediately useful

A table/grid underlying Figs. 3, 5 and/or A.7 with, ideally:

- lookback-time / age-bin edges;
- R_birth bin edges;
- initial stellar mass formed, SFR, or surface SFR in each bin;
- uncertainty / 16--84% interval where available;
- high-alpha / low-alpha split if stored separately;
- the mass-loss convention used to convert initial to surviving mass.

### Orbit-level product, if shareable

The strongest version of the analysis would use the orbit-superposition catalogue itself. Useful fields would be:

- Gaia DR3 source_id and/or APOGEE_ID;
- orbit ID;
- orbit-superposition stellar mass weight;
- present R, phi, z, v_R, v_phi, v_z;
- age and age uncertainty/posterior samples;
- R_birth and uncertainty/posterior samples;
- alpha-sequence / population label;
- initial-mass or mass-loss correction;
- any selection-function/reconstruction metadata attached to the orbit weight.

If sampled orbit libraries are available, the orbit phase-space samples and the potential/version used for integration would also be valuable. I would treat those samples as present-day orbit occupancy in the adopted potential, not automatically as literal secular migration trajectories.

### Longer-term history product

If your group has an internal product that goes beyond fixed-potential orbit occupancy—for example probabilistic guiding-centre histories R_guide(t), migration/churning epochs, or resonance histories—that would be especially relevant. Even a subset with Gaia IDs would be scientifically useful.

The intended comparison uses an independent direct-acceleration observable from pulsar timing, so the source-history reconstruction would not be fitted from the dynamical residual itself. Any shared data would be cited directly and used with the caveats/uncertainties you recommend.

Thank you for considering the request.

Best regards,
[Name]

## Internal rationale

The minimum R_birth x lookback-time mass grid allows a first scalar hereditary source-density test,

\[
H_\rho(R,t_0)=\int K(t_0-t)\,S_\rho[\Sigma_b(R,t)]\,dt.
\]

Orbit-level weights would additionally permit an independent present-day density/current reconstruction. A genuine secular trajectory/history product would enable the intended current-history term

\[
H_J(\mathbf x,t_0)=\int K(t_0-t)\,S_J[\rho_b\mathbf v_b]\,dt,
\]

which cannot be inferred from static R_birth alone.
