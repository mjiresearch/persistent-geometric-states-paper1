# Stage 9 Candidate A0: covariant advected persistent state

Date: 2026-08-10

## Purpose

Candidate A0 is a theory scaffold for a persistent geometric state transported along a dynamical timelike state-frame congruence rather than represented as a freely propagating slow gravitational-wave mode.

It is introduced after the corrected luminal L2 additive channel was falsified and after a perturbative bilinear inherited/current interaction was shown to be far too weak at order-unity coupling.

A0 is not yet an observable force law and must not be compared to halo targets until its metric coupling is independently specified.

## Minimal covariant field content

Introduce:

- the spacetime metric g_{mu nu};
- a future-directed unit timelike state-frame vector u_H^mu satisfying

  u_H^mu u^H_mu = -1;

- a scalar persistent-state amplitude Q_H;
- a Lagrange multiplier lambda enforcing the unit-timelike constraint.

Define the spatial projector

  h_{mu nu} = g_{mu nu} + u^H_mu u^H_nu.

## Minimal action scaffold

A conservative first-order covariant scaffold is

S = integral d^4x sqrt(-g) [
      (M_Pl^2/2) R
    + L_m[g, matter]
    + L_u
    + L_Q
    + L_dep
    + lambda (u_H^mu u^H_mu + 1)
    ].

The state-frame sector may be represented in generic Einstein-aether form

L_u = -M_H^2/2 * K^{alpha beta}_{mu nu}
      (nabla_alpha u_H^mu)(nabla_beta u_H^nu),

where

K^{alpha beta}_{mu nu}
 = c1 g^{alpha beta} g_{mu nu}
 + c2 delta^alpha_mu delta^beta_nu
 + c3 delta^alpha_nu delta^beta_mu
 - c4 u_H^alpha u_H^beta g_{mu nu}.

No values of c1...c4 are selected in Stage 9. They are parent-theory coefficients requiring stability and observational constraints before any numerical Milky Way use.

For the memory variable, A0 uses a first-order worldline relaxation law rather than a second-order propagating wave equation. The covariant equation to be obtained from the completed action/effective theory is

  u_H^mu nabla_mu Q_H + Q_H/tau = S_H.

A local weak-field deposition candidate consistent with the previous source guardrail is

  S_H proportional to u_H^mu nabla_mu I_b,

where I_b is a local scalar built from the baryonic/current curvature source rather than the long-ranged Newtonian potential itself. Static matter comoving with u_H therefore gives zero continuous deposition.

## Weak-field reduction

For

u_H^mu approximately (1, v_H/c)

in a locally inertial chart,

  u_H^mu nabla_mu -> partial_t + v_H dot grad,

so the state equation becomes

  partial_t Q_H + v_H dot grad Q_H + Q_H/tau = S_H.

Along a state-frame characteristic x_H(t),

  dQ_H/dt + Q_H/tau = S_H,

with solution

  Q_H(t,x_H(t)) = Q_H(t0) exp[-(t-t0)/tau]
                  + integral_{t0}^t dt' exp[-(t-t')/tau] S_H(t',x_H(t')).

The displacement of an inherited feature is therefore controlled by

  Delta x_H = integral v_H(t) dt,

not by a radiative correlation length c_H tau.

This is the precise mathematical version of an advected/moving-background persistent state.

## What A0 does and does not solve

A0 solves the conceptual problem that a long-lived state need not be represented by a km/s-scale gravitational radiation mode. The state may be transported by a timelike geometric congruence while ordinary tensor gravity remains luminal.

A0 does not yet specify:

1. the parent-action origin and allowed parameter domain of the state-frame kinetic coefficients;
2. the exact local baryonic deposition invariant I_b;
3. whether Q_H is a scalar fundamental field or shorthand for a tensorial state sector;
4. the observable metric coupling by which Q_H modifies geodesic motion;
5. the normalization of that coupling;
6. the independent initial/boundary conditions for u_H^mu;
7. stability, preferred-frame, Cherenkov, PPN, cosmological, and gravitational-wave constraints.

Therefore A0 is not yet permitted to generate a_H.

## Stage 9 guardrail

No state-frame velocity, aether coefficient, deposition coefficient, metric-coupling coefficient, or initial state may be selected from Portail17+halo, Hunter24+halo, Delta a(R), pulsar residuals, or orbit-weight targets.

The next admissible task is to derive the weak-field observable coupling and the state-frame equations from a completed parent action, then freeze their parameters from external/theoretical constraints before a new Milky Way field is generated.
