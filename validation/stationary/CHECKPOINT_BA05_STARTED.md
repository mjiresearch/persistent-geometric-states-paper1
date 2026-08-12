# Ba05 / NGC4559 stationary H I checkpoint

Status: **PUBLIC-SOURCE AUDIT STARTED**

- Lelli/SPARC family: `Ba05` = Barbieri et al. (2005), A&A 439, 947.
- Frozen target: `NGC4559` — calibration.
- The source paper directly publishes the radial H I column-density profile in Figure 3 (right), derived from the observed total H I map by averaging column densities in ellipses using the kinematic geometry.
- The plotted/source quantity is H I. Appendix A states the gas column density used for mass modelling is obtained by multiplying the H I density by 1.4 for helium; therefore do not apply helium before preserving the source H I profile.
- Public arXiv source audit workflow/script added to determine whether Figure 3 is recoverable as native vector/numeric data without raster digitization.
- `L_A` and `C_A` remain locked. No persistence fitting or blind-outcome inspection.

Resume only from the committed Ba05 audit products after the workflow completes; do not restart earlier Lelli families.
