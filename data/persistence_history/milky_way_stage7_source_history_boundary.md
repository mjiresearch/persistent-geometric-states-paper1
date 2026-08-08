# Milky Way Stage 7 source-history boundary

Date: 2026-08-08

## Why Stage 7 exists

The frozen Stage 6 direct-pulsar replication rejected the tested static source-displacement surrogate. Stage 7 therefore changes the **source-side observable** rather than re-tuning the force residual, kernel scale, migration threshold, or sign.

The intended physical object remains a time-dependent baryonic source history,

\[
H[\rho_b,J_b](\mathbf x,t_0)
=\int K(t_0-t)\,S[\rho_b(\mathbf x,t),J_b(\mathbf x,t)]\,dt,
\]

not a static star-by-star birth-radius displacement.

## Public source-side products tested

### Ratcliffe et al. 2026

The strongest Milky Way-specific reconstruction located is Ratcliffe et al. 2026, A&A 706 A103. It reconstructs a spatially resolved, orbit-mass-weighted star-formation history at inferred formation radii using APOGEE, Gaia, the public `Rbirth` method, and orbit-superposition mass weights.

Publicly recoverable now:

- the paper and figures;
- public `Rbirth` code;
- global Table A.1 with ten epochs of total stellar mass, current-radius effective size, birth-radius effective size, SFR, and ISM metallicity gradient.

Not located as a public numerical product:

- the R_birth x lookback-time mass/SFR array underlying the spatial SFH figures;
- orbit-superposition mass weights;
- orbit-level age/R_birth posterior products;
- sampled orbit library with IDs and weights;
- time-resolved secular guiding-centre/migration histories.

The arXiv page exposes a TeX Source link, but the binary source bundle could not be retrieved through the current archive interface. This specific source-bundle inspection therefore remains unresolved rather than being treated as proof that no auxiliary files exist.

### Frankel 2019/2020

The Frankel low-alpha models provide reproducible statistical radial redistribution operators and inside-out growth prescriptions.

Stage 7A fixed the published Frankel 2019 parameters and compared the source-side model to Ratcliffe Table A.1 without using any force or pulsar data.

The implementation reproduces Frankel's own published size evolution:

- present migrated half-mass radius: 5.887 kpc versus about 5.9 kpc published;
- 7.4-Gyr lookback half-mass radius: 4.218 kpc versus about 4.2 kpc published;
- reconstructed size growth: 39.6% versus about 43% published.

However, the model cannot serve as a whole-Milky-Way history operator. At the oldest common Ratcliffe epoch, 6.76 Gyr lookback:

- Frankel low-alpha cumulative mass relative to its 0.7-Gyr value: 0.151;
- Ratcliffe all-disc cumulative mass relative to its 0.7-Gyr value: 0.667.

The recent specific-SFR mismatch is also large. Frankel is therefore retained only as a possible late low-alpha redistribution component, not as the total source history.

### Ratcliffe Table A.1 minimum-information reconstruction

Stage 7B asked whether the global Table A.1 summaries alone could be converted into a physical spatial history without using any force data.

At each epoch the cumulative birth-radius mass distribution was approximated by the minimum-information 2D exponential disk having the published Mstar(t) and Reff_birth(t). Adjacent cumulative profiles were differenced to infer the newly assembled radial mass profile.

Result:

- 10 epochs / 9 intervals;
- 8 intervals are nonnegative or nearly so under this compression;
- the 3.03 -> 0.70 Gyr interval requires a negative inner component;
- negative mass is 6.83% of the absolute profile change and 7.91% of the net interval mass growth;
- the sign change occurs near R = 2.08 kpc.

This does **not** imply negative star formation. It demonstrates that Mstar(t)+one effective radius per epoch do not uniquely encode the actual spatial SFH. The authors' underlying R_birth-by-time mass arrays are required for a defensible source field.

## Independent early-disc constraints

Other public work constrains the old/high-alpha component but does not replace the missing formation-site history:

- Khoperskov et al. 2025 orbit-superposition reconstruction finds high-alpha populations comprise roughly 40--44% of the total stellar mass and are centrally concentrated.
- Mackereth et al. mono-age/mono-metallicity APOGEE reconstructions find high-alpha populations dominate old ages and have short radial scale lengths, while low-alpha mono-age profiles broaden with age.
- Lian et al. 2022 provides selection-corrected present-day mono-abundance density profiles.
- Xiang & Rix 2022 precisely constrains the chronology of the early thick-disc/halo assembly.

These are valuable priors and cross-checks, but they describe present-day density by age/chemistry or global chronology. They cannot be substituted for a mass-weighted **formation-site** distribution without reintroducing radial-migration bias.

## Current scientific boundary

The public-data branch is now **source-history limited**, not force-residual limited.

We already have:

1. robust rotation-based evidence for a Milky Way baryonic gravitational deficit under multiple baryonic decompositions;
2. a direct binary-pulsar acceleration observable independent of the MWM source population;
3. a larger Donlon pulsar catalog that falsified the frozen static displacement proxy out of sample;
4. source-side validation showing that available summary models cannot be promoted to the full baryonic history without unsupported assumptions.

We do **not** yet have the numerical source history required by the theory.

## Reopening condition for a Stage 7 force test

Do not evaluate another pulsar/source-history correlation until at least one of the following is obtained:

### Preferred minimum

A machine-readable Ratcliffe-style grid with

- lookback-time bin edges;
- R_birth bin edges;
- initial mass formed or SFR per bin;
- uncertainty/posterior interval;
- high-alpha / low-alpha split if available.

This is enough for a time-resolved **axisymmetric scalar density-history** test, but not a baryonic-current-history test.

### Stronger

Orbit-level products containing

- Gaia DR3 / APOGEE stable IDs;
- orbit-superposition mass weights;
- age and R_birth posterior samples;
- present phase space;
- population labels;
- sampled orbit phase-space arrays with orbit IDs and adopted potential.

These permit a much better present density/current reconstruction, though fixed-potential orbit samples are not automatically literal secular histories.

### Decisive

A probabilistic secular history containing

- R_guide(t);
- migration/churning epoch and direction probability;
- phi(t), z(t) where defensible;
- velocity/current history;
- bar/spiral resonance history;
- accreted versus in-situ probability.

That would finally permit the intended history functional to be evaluated rather than proxied.

## Stop rule

Until a new source-history product is obtained:

- do not scan new R_birth thresholds;
- do not flip the failed Stage 6C sign;
- do not select a new pulsar subset because it restores the Moran correlation;
- do not select new Gaussian source-field scales;
- do not treat present-day mono-age density profiles as formation-site profiles;
- do not fit persistence kernel lifetimes to the existing pulsar catalog.

The next scientifically valid progress is **new source data**, not more significance searches in the existing proxy data.
