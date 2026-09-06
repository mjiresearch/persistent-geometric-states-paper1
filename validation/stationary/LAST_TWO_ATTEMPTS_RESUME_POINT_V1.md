# Last Two Attempts — Exact Resume Point

This record prevents accidental restart or reclassification of the two acquisition attempts immediately preceding the current continuation.

## Attempt 1 — Spekkens radial H I extraction

Workflow: `Extract Spekkens radial HI vectors`
Run: 31498789803
Artifact: `spekkens-radial-hi-vector-geometry`
Targets: IC4202, NGC2955, NGC6195, UGC11455.

The workflow completed successfully as an execution, but the scientific result is that the source EPS figures are raster images embedded in PostScript (GIMP-exported), not recoverable vector plots. PyMuPDF returned 0 words and 0 drawings for all four targets. Therefore the earlier phrase "vector extraction" must not be interpreted as a numerical vector-profile recovery.

The existing high-resolution publication panels remain valid public inputs. Panel (d) in each target is explicitly the face-on radial H I surface-density profile, with approaching side, receding side, their average, and a dotted 1 Msun pc^-2 reference line. The continuation is publication-figure digitization of the averaged profile, followed by frozen-distance conversion and independent R_HI / radial-coverage QC. No new H I reduction threshold is introduced.

## Attempt 2 — Richards/Spekkens atlas extraction

Workflow: `Extract Richards and Spekkens HI atlas`
Run: 31498789833
Artifact: `richards-spekkens-atlas-extraction`.

The Richards appendix figures are galaxy-identified public H I atlas products. They contain integrated-intensity H I maps and velocity products, but the bottom-right radial plots are optical/photometric quantities rather than direct radial Sigma_HI profiles. Therefore Richards is retained as a public map-reduction route under the frozen annular-extraction rules; it is not a direct radial-profile promotion route.

## Standing checkpoint

Do not restart either audit. Continue from these outputs.

Active promoted stationary public H I build before any new Spekkens promotion: 18 frozen galaxies / 912 direct H I bins / 505 no-extrapolation source rows.

`L_A` and `C_A` remain locked until the source-profile freeze is complete.
