# Milky Way Stage 9A Candidate L2 — corrected-c verdict

Date: 2026-08-10

## Correction

The first L2 implementation used `c=306.60139378555056` while labeling the units kpc/Gyr. That value is c in kpc/Myr. The corrected value used here is

`c = 306601.39378555055 kpc/Gyr`.

All earlier numerical L2 amplitude claims from the incorrect constant are superseded by this file.

## Frozen inputs

- orientation: 0 degrees (Stage 9A)
- tau: 1, 2, 4, 8, 16 Gyr
- kappa: 1
- c_H: c
- interaction acceleration: zero at strict linear order
- source history: Ratcliffe et al. 2026 Table A.1 cumulative exponential-disk minimum-information history
- youngest 0.70-Gyr snapshot held fixed to the present
- free-space interior-cone Green function
- no force softening
- no halo-derived normalization
- no post-hoc parameter selection

The numerical reproduction follows the checked-in `build_milky_way_stage9a_candidate_l2_field.py` equations and quadrature: 64 Gauss-Legendre radial nodes, 32 azimuthal nodes, R=0.5--25 kpc with 99 evaluation points.

## Corrected field amplitudes

| tau (Gyr) | a_R(8 kpc) [(km/s)^2/kpc] | a_R(15 kpc) | a_R(20 kpc) | c tau (kpc) |
|---:|---:|---:|---:|---:|
| 1 | 1.4401e-15 | 2.7018e-15 | 3.5998e-15 | 3.0660e5 |
| 2 | 1.1848e-15 | 2.2322e-15 | 2.9610e-15 | 6.1320e5 |
| 4 | 6.5399e-16 | 1.2143e-15 | 1.6220e-15 | 1.2264e6 |
| 8 | 2.2725e-16 | 4.2501e-16 | 5.7506e-16 | 2.4528e6 |
| 16 | 5.2909e-17 | 9.9747e-17 | 1.3010e-16 | 4.9056e6 |

The already-frozen Stage-3 required residual at R=8 kpc is approximately

`Delta a_required = 2617.2179 (km/s)^2/kpc`.

Thus the frozen L2/required ratios at 8 kpc are approximately:

- tau=1 Gyr: 5.50e-19
- tau=2 Gyr: 4.53e-19
- tau=4 Gyr: 2.50e-19
- tau=8 Gyr: 8.68e-20
- tau=16 Gyr: 2.02e-20

So the unit-normalized luminal L2 candidate is about 18--20 orders of magnitude below the required Milky Way acceleration at the solar radius.

## Radial-shape comparison

Using the frozen Stage-3 residual over R=5--12.5 kpc, the corrected L2 radial acceleration increases outward while the required residual decreases outward.

Pearson correlations for the five frozen tau cases are approximately:

- tau=1 Gyr: -0.935
- tau=2 Gyr: -0.933
- tau=4 Gyr: -0.935
- tau=8 Gyr: -0.931
- tau=16 Gyr: -0.899

Spearman correlations are -1.0 for tau=1--8 Gyr and approximately -0.985 for tau=16 Gyr.

## Verdict

**Candidate L2 with the preregistered luminal characteristic speed, unit coupling, strict-linear zero interaction, and the current provisional Ratcliffe history is falsified as the source of the Milky Way acceleration deficit.**

This verdict is stronger than the invalid pre-correction estimate. The corrected c_H=c produces a correlation length hundreds of thousands to millions of kpc, making Psi_H effectively uniform across the Galactic disk and leaving an extremely small spatial gradient.

No multiplicative rescue, c_H sweep, tau selection, added kernel scale, or halo-derived normalization is permitted after this target exposure.

This result falsifies this particular effective response law/normalization under the stated provisional source history; it does not by itself falsify the broader persistence hypothesis. The next legitimate theory step must alter the response structure for independent physical reasons, not tune L2 to the Milky Way residual.
