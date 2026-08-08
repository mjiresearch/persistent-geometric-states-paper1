# Stage 6 external Gaia force-data manifest

Date: 2026-08-08

## Objective

Replace the internally reconstructed MWM force proxies with a genuinely independent Galactic dynamical observable before any further persistence-history inference.

The desired observable is a machine-readable grid of the radial and vertical Galactic force over the inner/intermediate disk, ideally

- R,
- z,
- circular speed v_c(R,z) or radial acceleration a_R(R,z) = -v_c^2/R,
- vertical acceleration a_z(R,z),
- statistical uncertainty,
- systematic uncertainty or adopted error floor,
- number of tracer stars in each bin,
- the tracer-density assumptions used in the Jeans conversion.

This observable would be compared with an independently specified baryonic force model to form a spatial gravitational residual before introducing any source-history predictor.

## Priority source: Sylos Labini & Capuzzo-Dolcetta 2026

Paper: *Constraining the Geometry of Galactic Dark Matter with Gaia Data Release 3*

- Francesco Sylos Labini and Roberto Capuzzo-Dolcetta
- The Astrophysical Journal 1005:213 (2026)
- DOI: 10.3847/1538-4357/ae7be7
- arXiv: 2606.12548
- CC BY 4.0

Why it is high priority:

- directly reports off-plane v_c(R,z), not only a mid-plane rotation curve;
- directly estimates a_z(R,z);
- main high-quality range is approximately R = 8.5--14 kpc and |z| < 2 kpc;
- six vertical slices are shown for v_c;
- vertical acceleration is shown at several fixed radii;
- the paper explicitly discusses astrophysical/systematic error floors rather than relying on tiny formal bootstrap errors.

Important methodological metadata from the paper:

- approximately 1.6 million Gaia DR3 stars after selection;
- radial bins of 0.5 kpc for the rotation curves;
- primary modeling uses a double-exponential tracer-density law;
- reported v_c precision is generally better than about 5% in the selected region;
- a_z is more model dependent, with systematic uncertainties up to roughly 20%;
- v_c is only weakly affected by moderate changes of the adopted radial density scale length, whereas a_z is much more sensitive to the vertical scale height;
- the first four |z| slices, up to |z| about 2 kpc, are the primary fitted region.

### Machine-readable-data search status

As of 2026-08-08, searches of the journal/DOI, arXiv indexing, the authors' public page, ResearchGate, Zenodo, GitHub, VizieR/CDS, OSF, and Figshare did not reveal a public numerical table containing the plotted v_c(R,z) and a_z(R,z) measurements.

The publication page and ResearchGate expose the figures and full methodology, but no verified numeric data-behind-the-figure file was located.

**Decision:** do not treat values estimated from plotted pixels as primary measurements. Figure digitization would be acceptable only as a clearly labelled exploratory check, not as the Stage 6 force observable used for inference.

## Methodological calibration: Koop et al. 2024

Paper: *Assessing the robustness of the Galactic rotation curve inferred from the Jeans equations using Gaia DR3 and cosmological simulations*

- Orlin Koop, Teresa Antoja, Amina Helmi, Thomas M. Callingham, Chervin F. P. Laporte
- A&A 692:A50 (2024)
- DOI: 10.1051/0004-6361/202450911
- arXiv: 2405.19028

Role in Stage 6:

- not used as a force grid unless machine-readable measurements are obtained;
- used to define the robustness/error standard for any Jeans-derived force observable.

Their simulation tests show that a steady-state axisymmetric Jeans reconstruction can differ from the true circular-speed curve by as much as about 15%, with roughly 10% considered plausible for the Milky Way, and that tracer-density truncation or disequilibrium can generate misleading rotation-curve behavior.

Therefore Stage 6 should not claim sub-percent or few-percent force discrimination merely because a Gaia sample contains millions of stars.

## Ingested external calibration: Wang et al. 2023

Paper: *Mapping the Milky Way Disk with Gaia DR3: 3D Extended Kinematic Maps and Rotation Curve to approximately 30 kpc*

- Hai-Feng Wang, Zofia Chrobakova, Martin Lopez-Corredoira, Francesco Sylos Labini
- ApJ 942:12 (2023)
- DOI: 10.3847/1538-4357/aca27c

Machine-readable file in this repository:

`data/external/gaia_force/wang2023_rotation_curve.csv`

The published Table 1 contains 19 circular-speed points from R=9.5 to 27.5 kpc in the Galactic anticenter selection 160 deg < l < 200 deg and |Z| < 3 kpc.

Role:

- independent radial calibration/validation only;
- not sufficient for the persistence test because it does not provide the required off-plane spatial force grid and overlaps the current 5--10.5 kpc source-history profile in only a very small number of radial bins.

## Stage 6 acceptance rule

A force product becomes suitable for the persistence test only if:

1. numerical values are directly supplied by the authors/archive or reproducibly derived from a documented public catalogue;
2. spatial coordinates and bin definitions are explicit;
3. statistical and dominant systematic uncertainties are represented;
4. the force estimate is independent of the MWM source-history variables used as persistence predictors;
5. the residual is constructed against a baryonic model before the history law is fit;
6. the history functional/kernel is then frozen before holdout or external-galaxy testing.

## Current status

The external-force branch is scientifically promising but **data limited, not significance limited**.

The next highest-value action is to obtain the numerical 2026 v_c(R,z)/a_z(R,z) grid from the authors or a future public supplement. Until then, the Wang 2023 table is retained as an independent radial calibration set and the Stage 4/5 stop rule remains in force.
