# Stationary H I numerical-tolerance policy v1

**Status:** FROZEN BEFORE ANY EVALUATION OF `L_A`, `C_A`, `tau_A`, PERSISTENCE PREDICTIONS, OR BLIND OUTCOMES.

This policy handles only sub-resolution numerical coordinate residuals introduced by deterministic source-vector calibration. It does not alter measured H I surface densities.

## NGC5907 / HEROES source-vector calibration

The certified NGC5907 m=0 H I profile is the already-recovered deterministic mean product:

`data/stationary/source_reconstruction/sa87_ngc5907_heroes2015_hi_m0_mean_v1.csv`

The corresponding source-vector recovery QC is:

`validation/stationary/sa87_ngc5907_heroes2015_native_hi_recovery_v1.json`

The independent x-axis tick-reconstruction QC gives a maximum absolute calibration residual of approximately `1.11156e-05 kpc`. The first m=0 radial coordinate is `-2.68537e-06 kpc`, which is smaller in magnitude than that independently measured calibration residual and represents the origin within the source-vector calibration precision.

## Frozen rule

1. Use the already-certified deterministic NGC5907 m=0 mean profile; do not re-average the signed side-profile radii.
2. For a source-native radial coordinate produced by deterministic vector calibration, if `R < 0` and `abs(R) <= source_axis_calibration_tolerance`, map that radial coordinate to exactly `R = 0`.
3. The applicable tolerance must come from a durable, independent source-calibration QC artifact generated before profile normalization. It may not be chosen from rotation-curve or persistence behavior.
4. Any negative radial coordinate whose magnitude exceeds the documented source-calibration tolerance fails closed.
5. Surface-density values, uncertainties, profile ordering, and all positive radial coordinates are left unchanged by this rule.
6. This tolerance rule may not be used to repair negative H I surface densities, missing source values, or discrepancies in physical scale.

## Scientific boundary

This is a numerical-coordinate precision rule only. It was frozen from source-vector calibration residuals without evaluating persistence parameters, persistence predictions, blind residuals, or model preference. `L_A` and `C_A` remain locked.
