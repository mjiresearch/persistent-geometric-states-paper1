# Stage 6 pulsar-to-MWM coordinate mapping resolution

Date: 2026-08-08

## Question

Stage 6B conservatively tested both signs for the Moran-catalog Galactocentric y coordinate because the accessible text of Moran et al. (2024) explicitly defined only +x and +z. The history-alignment result was stronger in the `Ysame` branch than in the reflected-y branch, so the physical convention must be fixed from external coordinate information rather than selected from the result.

## Astropy/MWM convention

The Astropy `Galactocentric` frame used for the BOSSNet/MWM phase-space work is right-handed. Its x axis points from the Sun projected onto the Galactic plane toward the Galactic center, so the Sun lies at negative x. For zero roll, +y points approximately toward Galactic longitude l=90 degrees and +z toward the North Galactic Pole.

Therefore the MWM/Astropy-like Cartesian convention is:

- Sun: X < 0;
- +Y: approximately Galactic longitude l=90 degrees;
- +Z: North Galactic Pole.

## Moran convention

Moran et al. explicitly state that +x points away from the Galactic center and +z points to the North Galactic Pole. Thus Moran x has the opposite sign to Astropy/MWM X.

The sign of Moran y can be fixed empirically from the published pulsar position table without using the Stage 6B acceleration result. Four pulsars with independently tabulated Galactic longitudes are decisive:

| Pulsar | Galactic longitude | Moran y | Expected sign if +y points to l=90 deg |
|---|---:|---:|---:|
| J0437-4715 | 253.394 deg | -111.16 pc | negative |
| J0613-0200 | 210.413 deg | -554.5 pc | negative |
| J1713+0747 | 28.751 deg | +570.0 pc | positive |
| J1909-3744 | 359.731 deg | -5.0 pc | approximately zero |

All four agree with +y pointing toward Galactic longitude 90 degrees. This is the same y direction used by the Astropy/MWM frame.

## Fixed mapping

The physically supported map is therefore

\[
X_{\rm MWM}=-x_{\rm Moran},\qquad
Y_{\rm MWM}=+y_{\rm Moran},\qquad
Z_{\rm MWM}=+z_{\rm Moran}.
\]

The Stage 6B `Ysame` branch is the physical branch. `Yreflected` is retained in the archive as an intentionally over-conservative sensitivity experiment, but it should not be treated as an equally plausible coordinate convention in subsequent tests.

## Statistical consequence

Resolving the coordinate convention does **not** retroactively convert Stage 6B into a detection. The strongest history result still depends on pulsar nuisance/outlier handling. The next test must therefore use the fixed coordinate mapping and a larger or independently reduced acceleration catalog without re-tuning the history sign, kernel, or predictor.

## Frozen Stage 6C hypothesis

Before inspecting the expanded Donlon et al. (2025) acceleration catalog, freeze:

- primary history predictor: local MWM source mean `deltaR_present_birth_kpc = R_now - Rbirth_proxy`;
- predicted sign: larger/more positive source displacement corresponds to a more negative baryons-only LOS acceleration residual;
- primary Gaussian source-field scale: 1.0 kpc;
- robustness scale: 1.5 kpc;
- physical coordinate orientation: Astropy/MWM convention above;
- no new migration threshold, azimuth grid, sign flip, or kernel scale will be selected after viewing Stage 6C.
