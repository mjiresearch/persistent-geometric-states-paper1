# Legacy Cepheid / stellar RV OSC sweep — frozen protocol

Status: OUTCOME-BLIND DATA RECOVERY

Purpose: exhaust remaining public pre-modern radial-velocity catalogs for the purity-qualified OSC Cepheid candidates without changing any frozen streaming-field rule.

## Candidate set
Use the existing purity-qualified OSC candidate list. QY Cyg remains excluded by the DCEP purity audit.

## Catalogs searched
1. Gorynya et al. Cepheid RV time series: VizieR III/229/catalog.
2. Borgniet et al. 2019 classical-Cepheid RV time series: VizieR J/A+A/631/A37 (all available RV tables discovered by the catalog service).
3. CRaV / Evans et al. 2015: VizieR J/AJ/150/13/table4 and associated catalog tables.
4. Cruz Reyes et al. 2023 cluster-Cepheid systemic velocities: J/A+A/672/A85/table1.
5. RAVE DR6 master/repeat products: III/283/ravedr6 and III/283/repeats.

## Match rule
Cone match radius <=2 arcsec around the frozen Gaia DR3 coordinates. A catalog hit is discovery only; it is not accepted by value agreement.

## Velocity acceptance
No change to the frozen scientific standard. A new tracer must provide either:
- a published pulsation-corrected systemic/gamma velocity with quoted uncertainty <=5 km/s; or
- at least 8 genuinely distinct RV epochs with sufficient information to estimate a systemic velocity and assigned uncertainty <=5 km/s.

No clipping or selection on agreement with the GRB/H I outcome is allowed.

## Outcome firewall
This sweep must not read H I spectra, H I velocities, H I residuals, the unblinded Outer-arm results, or any Persistence prediction. It reads only the purity-qualified candidate list and public RV catalogs.
