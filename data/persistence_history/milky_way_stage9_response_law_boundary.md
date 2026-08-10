# Milky Way Stage 9 response-law boundary

Date: 2026-08-10

## Purpose

Stage 9 must not manufacture a persistence force kernel after the Milky Way halo targets are visible. The response law is therefore developed and frozen source-side first, with failed candidates retained as controls rather than rescaled post hoc.

## Candidate L0 — light-cone control

The first minimal causal law was

\[
(D_H+1/\tau)^2\Psi_H-c_H^2\nabla^2\Psi_H
=\frac{1}{\tau}D_H\Phi_b.
\]

It is causal, finite-relaxation, unit-normalized, and has zero deposition for a static/comoving baryonic field. However, with \(\Psi_H=e^{-t/\tau}u\), the free operator reduces exactly to the ordinary massless wave equation for \(u\). Its free-space retarded Green function therefore has only light-cone support and no genuine interior-cone hereditary tail. L0 is retained as a null/control candidate, not promoted as the persistence model.

## Candidate L1 — two-rate hereditary transport

To obtain an interior-cone tail without adding a fitted dimensionless parameter, the transport operator was changed to

\[
[(D_H+1/\tau)(D_H+2/\tau)-c_H^2\nabla^2]\Psi_H=S_H.
\]

The spatially uniform free modes decay on \(\tau\) and \(\tau/2\). After removing the mean damping factor the propagator contains a nonzero interior-cone modified-Bessel tail. Causality and finite relaxation are retained.

An intermediate L1 source choice \(S_H=(1/\tau)D_H\Phi_b\) was then rejected as the primary implementation because \(\Phi_b\) is long-ranged. Treating its time derivative as a volume deposition source would create persistence throughout the field volume rather than only where the baryonic source/curvature changes.

## Candidate L2 — primary local curvature-change candidate

L2 retains the L1 two-rate transport but adopts the local weak-field curvature-change source

\[
S_H
=4\pi G\,c_H^2\tau\,D_H\rho_b
=c_H^2\tau\,D_H(\nabla^2\Phi_b),
\]

with preregistered \(\kappa=1\), \(c_H=c\), \(\tau\in\{1,2,4,8,16\}\) Gyr, relaxed-zero initial persistent state, and \(\mathbf a_{\rm int}=0\) at strict linear order.

This choice:

- is local to baryonic density/curvature change;
- is zero for static/comoving baryons;
- introduces no new length scale or fitted amplitude;
- naturally includes disk reorientation through displacement of the full cumulative baryonic source;
- preserves causal free-space propagation and an interior-cone hereditary tail;
- permits a boundary-free retarded Green-function evaluation for the first Stage 9A field.

## Source-history implementation

The public Ratcliffe Table A.1 history remains provisional. Each epoch is represented by the minimum-information cumulative razor-thin exponential disk defined by its tabulated stellar mass and birth-radius effective radius. Adjacent epochs are differenced at quadrature level as

\[
\Delta\rho_b = \rho_{b,\mathrm{young}}-\rho_{b,\mathrm{old}},
\]

including the independently predeclared historical orientation of each endpoint. This represents the interval-integrated \(D_H\rho_b\) source and captures both mass-profile evolution and disk reorientation.

The youngest public epoch is 0.70 Gyr lookback. Its mass profile is held fixed to 0 Gyr in the provisional Stage 9A run, giving exactly zero invented deposition during the unobserved final interval.

## Falsification rule

Candidate L2 is not to be rescued by fitting \(\kappa\), \(c_H\), \(\tau\), an added spatial kernel, or a halo-derived normalization after comparison. All five preregistered \(\tau\) cases are compared unchanged. If the predicted acceleration is orders of magnitude too small or has the wrong radial structure, L2 is recorded as a failed candidate and any replacement law must be independently motivated and frozen before a new comparison.
