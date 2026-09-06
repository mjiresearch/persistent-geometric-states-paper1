# Gaia-Cepheid arm-conditioned streaming field V4: outcome-independent DCEP purity correction

V3 remains immutable. V4 is a data-quality correction motivated by an independently discovered Cepheid-classification inconsistency, not by any GRB H I outcome.

## Exactly one model-side change
The V3 velocity hierarchy, quality cuts, Galactic constants, sign conventions, frozen Outer/OSC arm loci, arm widths, intrinsic dispersion sigma_int=7 km/s, bandwidth grid h={1,2,3,4,5,7,10} kpc, support threshold N_eff>=3 in both U and V, nearest-phase requirement, leave-one-out cross-validation, bootstrap, and target geometries are unchanged.

The only training-sample purity change is:
1. If a source is present in `gaiadr3.vari_cepheid`, require current SOS `type_best_classification='DCEP'`. Current SOS `T2CEP` and `ACEP` sources are excluded from the young-disk streaming field.
2. Sources from the published external DCEP lists (P21/Inno) that are absent from `vari_cepheid` remain eligible under all existing V3 cuts.
3. Gaia DR3 source 2072235820984829312 (QY Cyg) is explicitly excluded because independent spectroscopy/photometry literature identifies it as Type II despite a conflicting Gaia DCEP/catalog label. This exclusion was discovered during the outcome-blind RV-target audit.

No other object-level manual edits are allowed in V4.

## Provenance and guardrail
The Gaia Collaboration (2023) source paper describes its intended Gaia subsample as DCEPs. V4 enforces the current SOS DCEP classification consistently rather than assuming every row in the frozen 3306-star working table retains a pure DCEP status.

No H I spectrum, H I velocity, H I residual, conventional-vs-HI comparison value, or Persistence prediction may be read by the V4 builder. V4 must report the number and identities/types of V3-eligible sources removed by the purity rule before producing new field predictions.
