# Stage 9 Candidate A1 observable-metric coupling

Date: 2026-08-10

## Purpose

Candidate A0 supplies an advected-relaxing persistent state carried by a unit
timelike state-frame congruence.  It does not by itself specify how matter and
light respond to that state.  Candidate A1 records the smallest local covariant
observable-metric layer without using Milky Way halo targets to choose its
coefficients.

## Minimal local algebraic coupling

With only the metric g_{mu nu}, a normalized timelike vector u_H^mu, and a
scalar dimensionless state q_H, the most general local algebraic isotropic
rank-two metric deformation has the form

    g_eff_{mu nu} = C(q_H) g_{mu nu} + D(q_H) u^H_mu u^H_nu.

GR recovery requires C(0)=1 and D(0)=0.  At linear order,

    C = 1 + 2 a q_H + O(q_H^2),
    D = 2 b q_H + O(q_H^2).

The coefficients a and b and the normalization that makes q_H dimensionless
must come from the parent theory or an independent non-halo calibration.

## Weak-field consequence

For signature (-,+,+,+), a locally resting state-frame, and

    g_00 = -(1 + 2 Phi_b/c^2),
    g_ij =  (1 - 2 Psi_b/c^2) delta_ij,

linearization gives

    Phi_eff = Phi_b + c^2 (a-b) q_H,
    Psi_eff = Psi_b - c^2 a q_H.

Therefore the non-relativistic acceleration contribution is

    a_A1 = -c^2 (a-b) grad q_H,

while the lensing-potential shift is

    delta(Phi+Psi) = -c^2 b q_H.

This immediately shows why a single arbitrary coupling is not neutral.  Pure
conformal coupling (b=0) changes non-relativistic dynamics but gives no linear
shift in Phi+Psi.  Pure disformal coupling (a=0) ties the dynamical and lensing
responses to a fixed relation.  Either is an additional physical hypothesis
that must survive lensing and PPN tests rather than being selected because it
helps a rotation curve.

## Stage 9 decision

A1 remains a theory gate, not a Milky Way force model.  No values of a, b, or
the q_H normalization will be selected from Delta-a(R), Portail17+halo,
Hunter24+halo, orbit weights, or Galactic lensing data after exposure.

Force generation remains blocked until the parent theory independently fixes:

1. which metric matter follows;
2. the normalization and dimensions of q_H;
3. the leading coefficients a and b (or a more complete C,D relation);
4. equivalence-principle behavior;
5. Solar-System/PPN consistency;
6. lensing/gravitational-slip consistency;
7. gravitational-wave propagation consistency;
8. cosmological background behavior;
9. the complete set of choices before halo comparison.

## Consequence for the persistence program

The moving-background/advected-state idea survives this step as a mathematically
coherent transport mechanism, but it does not yet predict the amplitude of an
observable gravitational acceleration.  The next legitimate theory task is to
derive C(q_H), D(q_H), and the normalization of q_H from a parent action or a
truly independent calibration.  Only after that should A0/A1 be returned to the
Milky Way 0--180 degree orientation experiment.
