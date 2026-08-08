# Stage 7 source-history acquisition manifest

Date: 2026-08-08

## Scientific purpose

Stages 1--6 showed that static age/birth-radius/migration surrogates do not robustly explain the Milky Way gravitational residual, including a failed frozen out-of-sample test against direct pulsar accelerations. Stage 7 therefore changes the source variable rather than re-tuning the residual or the proxy.

The target is an explicitly time-dependent baryonic source history suitable for constructing at least the scalar part of a hereditary source functional,

\[
H_\rho(\mathbf x,t_0)=\int K(t_0-t)\,S_\rho[\rho_b(\mathbf x,t)]\,dt,
\]

and, if velocity/current information is supplied,

\[
H_J(\mathbf x,t_0)=\int K(t_0-t)\,S_J[\mathbf J_b(\mathbf x,t)]\,dt,
\qquad \mathbf J_b=\rho_b\mathbf v_b.
\]

## Priority public/collaborator source

Ratcliffe et al. 2026, A&A 706, A103,
*Rediscovering the Milky Way with an orbit superposition approach and APOGEE data: IV. The disc growth and history of star formation*,
DOI 10.1051/0004-6361/202557057, arXiv:2509.02691.

Why this is materially different from the rejected Stage-6 proxy:

- the paper reconstructs the **spatially resolved star-formation history** of the Milky Way;
- it combines stellar birth-radius estimates with **orbit-superposition mass weights** that reconstruct the full stellar disc rather than using the raw APOGEE footprint;
- it traces stellar mass formation at the inferred formation sites while accounting for stellar mass loss;
- the paper explicitly reports radial migration biases between present-radius age distributions and true formation-site SFHs;
- the result is a time-dependent mass-formation field, not merely a present-day star-by-star displacement statistic.

The paper uses roughly 80,000 APOGEE DR17 giants with Gaia DR3 astrometry and distmass ages. The orbit-superposition method originates in Khoperskov et al. 2025, A&A 695, A220.

## Publicly located components

Available now:

1. `BridgetRatcliffe/Rbirth` — public birth-radius package.
2. Ratcliffe et al. Table A.1 — global history calibration, archived here as
   `ratcliffe2026_tableA1_global_disc_history.csv`.
3. Published figures showing the spatial history products, including:
   - Fig. 3: mass/birth-radius distribution versus lookback time;
   - Fig. 5: spatially resolved SFH by formation radius;
   - Fig. 8: migration-induced differences between true formation-site SFR and present-radius age distributions;
   - Fig. A.7: SFH versus birth radius per unit area;
   - Figs. A.8/A.10: spatial SFR of alpha sequences with chemistry/eccentricity overlays.

Not located in public repositories as of the search date:

- the numerical R_birth x lookback-time SFH array;
- star/orbit mass weights from the orbit-superposition reconstruction;
- a reconstructed present-disc stellar mass grid with orbit IDs;
- per-orbit propagated age PDFs or R_birth PDFs;
- time-sampled orbit/current arrays associated with the weighted orbit library.

Searches covered the paper/arXiv record, A&A indexing, author public GitHub repositories, and general web/code-repository search. The only directly relevant Ratcliffe analysis repository found was `Rbirth`.

## Minimum Stage-7 dataset

A minimally useful numeric product would contain a grid such as:

- `lookback_time_gyr` or age-bin edges;
- `Rbirth_bin_kpc` or formation-radius bin edges;
- `formed_initial_mass_msun` or `SFR_msun_per_yr`;
- surface-density-normalized equivalent if available;
- lower/upper uncertainty or posterior percentiles;
- high-alpha / low-alpha label if the published decomposition is available.

This would support a **time-resolved scalar source-density history**. It would not yet provide the baryonic current history.

## Preferred orbit-level dataset

For a substantially stronger test, request one row per APOGEE orbit/star with:

- stable source ID: Gaia DR3 source_id and/or APOGEE_ID;
- orbit-superposition mass weight and its normalization;
- present `(R,phi,z,v_R,v_phi,v_z)`;
- stellar age PDF or samples;
- R_birth PDF or samples;
- orbit family/component label;
- alpha-sequence label;
- initial/current stellar mass correction used in the SFH;
- selection/reconstruction weight metadata.

If the orbit library itself is available, additionally request sampled orbit arrays:

- `orbit_id`;
- sample time or orbital phase;
- `R,phi,z`;
- `v_R,v_phi,v_z`;
- integration potential/version and units.

These orbit samples are **not automatically interpreted as literal historical migration trajectories**: in a fixed present-day potential they describe orbit occupancy, not secular churning history. They are nevertheless useful for reconstructing present baryonic density/current and for separating that from the formation-site history.

## Gold-standard history product

The decisive source-side product remains a probabilistic secular history rather than a fixed-potential orbit:

- `R_guide(t)` posterior or samples;
- migration/churning epoch and direction probability;
- `phi(t), z(t)` where defensible;
- `v_R(t), v_phi(t), v_z(t)` or current-history moments;
- bar/spiral resonance encounter/history probabilities;
- accreted versus in-situ probability;
- covariance/uncertainty information.

## Stage-7 analysis rule

The direct pulsar acceleration observable from Stage 6 is retained unchanged. No pulsar residual threshold, sign, or source-field kernel will be selected using the new source history.

The first Stage-7 test will be preregistered **after inspecting only the structure/units/coverage of the new source-history product, not its correlation with pulsar residuals**. Candidate kernel families will be fixed before evaluating the acceleration association.

The failed Stage-6 displacement surrogate remains rejected and will not be reintroduced as a tuning variable.
