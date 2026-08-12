# El10 stationary H I resume checkpoint

Status: **EL10 SOURCE ASSET AUDIT STARTED — AFTER CA88 REDIRECT**

This checkpoint is opened while the Ca88 disposition/rerank runner is queued. It assumes only the current canonical priority ordering in which El10 is immediately behind Ca88; it must not supersede the final Ca88 rerank if that ordering changes unexpectedly.

## Locked state
- `L_A` and `C_A` remain locked.
- Public H I source-profile acquisition only.
- No raster digitization, map/cube-to-profile reconstruction, persistence fitting, or blind-outcome inspection.

## Current likely next Lelli/SPARC family
- Ref: `El10`
- Target: `NGC2915`
- Current queue role: calibration
- Paper: Elson, de Blok & Kraan-Korteweg 2010, MNRAS 404, 2061, *The dark matter content of the blue compact dwarf NGC 2915*, arXiv:1002.0403.

## Provenance gate
El10 is itself a new ATCA H I synthesis-observation paper. It states that the observations are deeper and higher-resolution than previous NGC2915 H I data. From the total-intensity map the authors constructed an azimuthally averaged, inclination-corrected H I surface-density profile using 17-arcsec rings (PA 285 deg, inclination 55 deg), shown in Figure 5.

## Exact next action
Audit the arXiv source package for the Figure-5 radial H I profile asset and any native numeric sidecar. If Figure 5 is source-native vector, decode its published H I samples and axes. If numeric table exists, prefer it. If raster-only and no table exists, disposition under the no-raster rule.
