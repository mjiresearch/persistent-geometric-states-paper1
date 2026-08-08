# Milky Way Stage 6 direct-acceleration verdict

Date: 2026-08-08

## Why Stage 6 mattered

Stages 1--5 relied on stellar rotation, streaming, or Jeans-derived force proxies. Stage 6 replaced those with direct Earth-to-pulsar differential Galactic accelerations from pulsar timing, while keeping the source-history population independent in the MWM/SDSS stellar sample.

This is the cleanest empirical branch attempted so far because the dynamical observable does not require a steady-state tracer-density model.

## Stage 6A: direct pulsar acceleration residual

The Moran et al. (2024) 29-pulsar catalog was ingested with the published Galactocentric positions, line-of-sight Galactic accelerations, uncertainties, five published >=3-sigma local-model outlier flags, and the three systems used in the authors' modified-catalog sensitivity check.

The instantaneous baryonic prediction was computed with exactly the same McMillan17 component rule used in Stage 3:

- galpy `McMillan17`;
- all components except `NFWPotential` treated as baryonic;
- McMillan17's own natural `ro=8.21 kpc`, `vo=233.1 km/s` scaling.

The line-of-sight prediction was

\[
a_{\rm LOS,b}=\left[\mathbf a_b(\mathbf x_{\rm PSR})-\mathbf a_b(\mathbf x_\odot)\right]\cdot\hat{\mathbf d}.
\]

The sign and coordinate construction passed an internal sanity check against Moran et al.'s published local linear acceleration model. After removing their five published local-model outliers, the local-model residual has a reduced chi-square of order 1.5 and no remaining >3-sigma standardized residuals.

On the most conservative 21-pulsar sample excluding both published flag sets, the baryons-only residual has a stable positive median of roughly +0.16 to +0.19 x 10^-10 m s^-2 across plausible Sun-position assumptions. Individual pulsars scatter on both sides, so this is not interpreted as a simple missing-gravity detection.

## Coordinate mapping resolved before replication

Stage 6B initially carried both signs of the Moran y coordinate because the accessible Moran text explicitly defined only +x and +z.

The ambiguity was subsequently resolved independently of the acceleration-history result:

- Astropy/MWM has the Sun at negative X and +Y approximately toward Galactic longitude l=90 degrees;
- Moran +x points away from the Galactic center, so `X_MWM=-x_Moran`;
- the published Moran y signs for J0437-4715, J0613-0200, J1713+0747, and J1909-3744 match +y toward l=90 degrees.

Therefore the physical mapping is

\[
X_{\rm MWM}=-x_{\rm Moran},\qquad
Y_{\rm MWM}=+y_{\rm Moran},\qquad
Z_{\rm MWM}=+z_{\rm Moran}.
\]

The old reflected-y branch remains archived only as an intentionally conservative sensitivity experiment.

## Stage 6B: discovery-screen spatial alignment

For each Moran pulsar, the MWM source-history field was sampled at the same present location using fixed Gaussian kernels of 1.0 and 1.5 kpc. The primary history proxy was the local weighted mean

\[
\Delta R_{\rm proxy}=R_{\rm now}-R_{\rm birth,proxy}.
\]

The null rotated the complete pulsar configuration around the Galaxy while preserving each pulsar's R and z, so radial and vertical gradients were retained and only the azimuthal alignment with the source-history field was broken.

In the physical coordinate branch, the most interesting result occurred after excluding Moran et al.'s five published local-model outliers. At sigma=1.0 kpc, the source displacement proxy versus baryons-only acceleration residual gave approximately

\[
\rho\simeq-0.62,
\]

with an azimuth-rotation/family-wise probability of about 0.008. The negative sign was also seen at sigma=1.5 kpc.

However the significance depended on the pulsar sample definition. Stage 6B was therefore classified only as a direct-acceleration precursor, not evidence for persistence.

## Frozen replication rule

Before inspecting the expanded Donlon et al. (2025) catalog, the following were frozen in `docs/stage6_coordinate_mapping_resolution.md`:

- predictor: local source mean `deltaR_present_birth_kpc`;
- predicted sign: larger positive source displacement -> more negative baryons-only LOS residual;
- primary source-field scale: 1.0 kpc;
- robustness scale: 1.5 kpc;
- fixed physical coordinate mapping above;
- primary replication sample: pulsar systems absent from the Moran 2024 discovery catalog.

No new migration threshold, predictor, sign, or kernel scale was allowed to be selected from the replication catalog.

## Donlon et al. 2025 expanded catalog

The authors' public final `v3/data.csv` was ingested directly from

`thomasdonlon/Empirical_Model_MSP_Spindown_Accels`.

The final file contains:

- 53 usable pulsar rows;
- 27 binary-orbital acceleration rows;
- 26 spin-inferred-only acceleration rows;
- one duplicated physical location, J0737-3039A/B;
- 52 independent sky positions after avoiding double weighting of that binary system.

Following the authors' README, the binary-orbital `ALOS_PB` acceleration is used whenever available; otherwise the empirically calibrated spin acceleration `ALOS_PS` is used.

The binary acceleration channel overlaps 24 Moran systems and has the expected positive correspondence with the Moran accelerations (Spearman rho about +0.707, p about 1.1e-4), providing a useful unit/sign validation.

## Stage 6C: frozen out-of-sample result

There are 28 independent Donlon systems absent from the Moran discovery catalog. Of these, 26 use the new spin-inferred acceleration channel and two use the binary-orbital channel.

### Primary 1.0-kpc kernel

For the 28 new systems, 27 have finite source-field coverage:

\[
\rho(\Delta R_{\rm proxy},\Delta a_{\rm LOS,b})=+0.1923,
\]

with frozen one-sided negative-sign azimuth-rotation probability

\[
p_{1s}=0.7014.
\]

This is opposite to the predicted sign.

The 26 spin-inferred-only systems give essentially the same result:

\[
\rho=+0.1846,\qquad p_{1s}=0.7222.
\]

### 1.5-kpc robustness kernel

All 28 new systems have finite coverage:

\[
\rho=+0.0498,\qquad p_{1s}=0.3000.
\]

The spin-inferred-only sample is effectively null:

\[
\rho\simeq-0.0010,\qquad p_{1s}=0.2889.
\]

### Overlapping binary systems

The 26 independent binary-orbital positions retain a negative tendency:

- sigma=1.0 kpc: rho about -0.317, p_one-sided about 0.286;
- sigma=1.5 kpc: rho about -0.396, p_one-sided about 0.200.

These systems substantially overlap the discovery data and do not independently reproduce the significance.

### Combined 52 independent positions

The combined catalog is weak/null:

- sigma=1.0 kpc: rho about -0.060, p_one-sided about 0.451;
- sigma=1.5 kpc: rho about -0.154, p_one-sided about 0.311.

## Verdict

**The frozen Stage 6B source-displacement hypothesis fails independent replication.**

This is a stronger conclusion than saying that a significance threshold was missed. The genuinely new systems do not preserve the predicted negative direction at the primary scale, and the robustness scale is essentially null.

Therefore:

1. the Stage 6B Moran correlation should be interpreted as sample-specific, nuisance-sensitive, or a feature of the age/metallicity-derived birth-radius proxy rather than a demonstrated universal history-force relation;
2. the local `R_now - Rbirth_proxy` field is not accepted as the persistence state variable;
3. no sign flip, new migration threshold, alternative kernel scale, or replacement history proxy should be selected from the Donlon replication data;
4. the direct pulsar acceleration observable remains highly valuable, but it should next be paired with genuinely time-resolved baryonic source trajectories/current histories rather than another static birth-radius proxy.

## What this does and does not falsify

The result **does falsify the specific tested empirical surrogate**

\[
H_{\rm proxy}\propto\langle R_{\rm now}-R_{\rm birth,proxy}\rangle_{\rm local}
\]

with the frozen negative LOS-residual prediction used in Stage 6C.

It does **not** test the full persistence framework, whose proposed source variable is a hereditary functional of the baryonic stress-energy/current history,

\[
H[\rho_b,J_b](\mathbf x,t_0)
=\int K(t_0-t)\,S[\rho_b(\mathbf x,t),J_b(\mathbf x,t)]\,dt,
\]

because the current public proxy contains no time-resolved guiding-center history, azimuthal history, velocity/current history, resonance history, or migration epoch information.

## Stop rule after Stage 6

Do not continue mining the Moran/Donlon acceleration catalogs with alternative birth-radius thresholds, kernel scales, signs, or chemistry-derived history functions.

The next valid advance requires a **new source-history observable**:

- probabilistic R_birth with uncertainty joined to Gaia IDs is useful but insufficient by itself;
- preferred: R_guide(t), migration time/epoch, phi(t), z(t), and velocity/current history;
- resonance/bar/spiral interaction history;
- accreted versus in-situ probability;
- ultimately a reconstruction of rho_b(x,t) and J_b(x,t).

The empirical target remains the direct pulsar acceleration residual, or a future machine-readable 3D Gaia force grid, but the source side of the test must now improve rather than the residual side being re-tuned.
