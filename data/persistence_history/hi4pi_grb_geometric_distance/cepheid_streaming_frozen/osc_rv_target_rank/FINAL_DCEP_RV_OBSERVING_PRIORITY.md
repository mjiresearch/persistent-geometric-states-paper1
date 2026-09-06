# Final DCEP systemic-RV priority for the frozen OSC streaming test

Status: **outcome-blind observing/data-recovery priority**. No GRB H I spectrum, H I velocity, H I residual, or Persistence prediction is used in this ranking.

## Purity correction

The initial top-ranked missing-RV candidate, Gaia DR3 2072235820984829312 (QY Cyg), is excluded because the independent classification audit identifies it as a Type II Cepheid rather than a strict classical (DCEP) tracer. Other non-DCEP/uncertain contaminants identified by the audit are likewise excluded from this final priority list.

## Highest-priority clean classical Cepheids

1. **Gaia DR3 2025179884408158464 — ZTF J193847.38+272448.5**
   - l = 62.4937457 deg, b = +2.7434948 deg
   - Cepheid distance = 17.54 kpc
   - frozen OSC along-arm phase offset s = +3.6755 kpc
   - frozen perpendicular arm offset d_perp = -1.3959 kpc
   - a systemic-RV measurement with assumed sigma_RV = 2 km/s raises the best frozen support statistic to min(N_eff,U,N_eff,V) ≈ 3.615
   - formally support-qualified at h = 7 kpc
   - no usable Gaia mean/epoch RV or SIMBAD radial velocity was found in the outcome-blind public-data audit.

2. **Gaia DR3 2031745858613175040 — ZTF J194732.88+292037.3**
   - l = 65.1277628 deg, b = +2.0292076 deg
   - Cepheid distance = 17.64 kpc
   - frozen along-arm phase offset s = +4.4143 kpc
   - frozen d_perp = -1.1001 kpc
   - one sigma_RV = 2 km/s systemic velocity also individually clears the formal support threshold at h = 7 kpc
   - no usable Gaia mean/epoch RV or SIMBAD radial velocity was found in the outcome-blind public-data audit.

Additional clean DCEP priorities include Gaia DR3 1873298884367855872 (OGLE GD-CEP-1487), 2165006259882192128 (ZTF J212053.83+484722.8), and 4513281175196176512 (ZTF J185708.05+174343.1).

## Preferred two-star program

The scientifically preferred program is to obtain systemic velocities for **both 2025179884408158464 and 2031745858613175040**. Under the already-frozen uncertainty/support calculation, this pair reaches support at **h = 3 kpc**, with approximately

- N_eff,U = 4.512
- N_eff,V = 4.561

This is preferable to relying on one new velocity at h = 7 kpc because it creates a substantially more local OSC streaming prediction.

A second useful pair is 2031745858613175040 + 4513281175196176512, also reaching the frozen support criterion at h = 3 kpc.

## Interpretation

One high-quality systemic velocity is sufficient to cross the formal V3 support threshold, but **two measurements are preferred** because they reduce the required along-arm smoothing scale from 7 kpc to 3 kpc. This file ranks measurement leverage only and must not be treated as an H I comparison or a Persistence result.
