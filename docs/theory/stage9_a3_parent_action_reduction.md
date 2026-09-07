# Stage 9 Candidate A3 — minimal parent-action reduction

Date: 2026-08-10

## Purpose

A0–A2 isolated the advected persistent state, its observable metric coupling, and a derivative deposition family. The remaining question is whether the apparent constants `T_star`, `kappa_q`, `a`, and `b` can be derived or reduced by one covariant parent action rather than selected from Milky Way force targets.

## First result: one-field conservative action is insufficient

The target A0 equation

    D_U q + q/tau = S_q,

with `D_U = u_H^mu nabla_mu`, is first-order and dissipative. A conventional real local action containing only `q`, `u_H`, and `g_mu_nu` does not generically yield this irreversible relaxation equation as the Euler–Lagrange equation of `q` alone. A parent description therefore needs additional structure: an auxiliary/response field, a doubled Schwinger–Keldysh/open-system description, or an equivalent microscopic sector whose coarse-grained limit produces relaxation.

Stage 9 must not hide this fact by writing down an ordinary scalar action and inserting friction by hand.

## Minimal local auxiliary-field action

The smallest covariant bookkeeping action that imposes the desired classical transport equation introduces one dimensionless response field `p_H`:

    S_A3 = integral d^4x sqrt(-g) [
             M_Pl^2 R/2
             + L_u(g,u_H,lambda;c_i)
             + Lambda_H^4 p_H (
                   u_H^mu nabla_mu q_H
                   + q_H/tau
                   - beta tau u_H^mu nabla_mu chi_m
               )
           ]
           + S_m[g_eff(q_H,u_H), psi_m],

where

    chi_m = T / Lambda_T^4,

and

    g_eff_mu_nu = C(q_H) g_mu_nu + D(q_H) u^H_mu u^H_nu.

`L_u` is the normalized-timelike state-frame sector already identified in A0. `lambda` enforces `u_H^mu u^H_mu=-1`. `Lambda_H` normalizes the response-field sector and does not by itself set the observable force amplitude. `Lambda_T^4` is the universal stress scale previously called `T_star`. `beta` is a dimensionless deposition coefficient.

Variation with respect to `p_H` gives exactly

    D_U q_H + q_H/tau = beta tau D_U(T/Lambda_T^4).

Variation with respect to `q_H` gives the adjoint response equation for `p_H`, including the matter-metric coupling. The auxiliary field is therefore not an optional decoration: it is the minimal local field that makes the irreversible-looking first-order equation compatible with an action-level variational bookkeeping description.

This action is still a classical effective scaffold, not a demonstrated microscopic unitary theory. A full open-system or doubled-field derivation remains required before claiming fundamental dissipation.

## Parameter reduction by field normalization

At linear order write

    C(q)=1+2 a q,
    D(q)=2 b q.

The transformation

    q -> z q,
    p -> p/z

leaves the response-field kinetic/relaxation structure invariant provided

    beta -> z beta,
    a -> a/z,
    b -> b/z.

Therefore `beta`, `a`, and `b` are not separately observable at linear order. Only the combinations

    A_dyn  = beta (a-b),
    A_lens = beta b

matter for the leading response to `D_U(T/Lambda_T^4)`.

Equivalently, one may choose a field convention `beta=1` without loss of linear-order physics, but that is a normalization convention, not a physical prediction. The remaining physically relevant quantities are then the universal stress scale `Lambda_T^4` and two dimensionless metric-response combinations (or one overall coupling plus one dynamics/lensing ratio).

Thus the previous four apparent constants reduce to three physical quantities at linear order:

1. a universal stress/curvature scale `Lambda_T^4`;
2. an overall dimensionless dynamical response `A_dyn`;
3. a dimensionless lensing-to-dynamics ratio, equivalently `A_lens/A_dyn`.

If an independently derived symmetry or matter-coupling principle later fixes the ratio between conformal and disformal terms, the parameter count falls to two.

## What the parent action does NOT yet determine

The minimal auxiliary action does not predict numerical values for `Lambda_T`, `A_dyn`, or `A_lens/A_dyn`. Choosing `Lambda_T` to be the Planck density, cosmological critical density, a galactic density, MOND acceleration converted to a density, or any other familiar scale without a derivation would simply relocate the fitting freedom.

Likewise, setting `a`, `b`, or `beta` to one independently is a field-normalization convention unless the completed action/microscopic theory fixes the normalization of `q_H`.

## Stage 9 decision

1. Accept A3 as the minimal action-level scaffold for A0 relaxation, with an explicit auxiliary response field.
2. Replace the bookkeeping set `(T_star,kappa_q,a,b)` by the physical linear-order set `(Lambda_T^4, A_dyn, A_lens/A_dyn)`.
3. Do not compute a Milky Way A0/A1/A2 force until `Lambda_T^4` and the physical coupling combination are fixed independently of the Milky Way halo/residual targets.
4. Use lensing, equivalence-principle/PPN constraints, cosmology, and a microscopic/state-frame derivation to constrain the lensing/dynamics ratio and overall response.
5. Keep the 0–180 degree Galactic orientation suite frozen but unopened for A3 force comparison until these gates are satisfied.

## Falsifiability guardrail

No Milky Way rotation curve, Portail17/Hunter24 halo, orbit weight, SPARC relation, or galaxy-specific acceleration scale may be used to set `Lambda_T`, `A_dyn`, or `A_lens/A_dyn`.