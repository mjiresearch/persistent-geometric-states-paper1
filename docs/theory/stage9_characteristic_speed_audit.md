# Stage 9 characteristic-speed audit

Date: 2026-08-10

## Question

Can Candidate L2 be rescued by lowering the persistence-mode characteristic speed c_H below c so that the correlation length c_H tau becomes Galactic rather than hundreds to thousands of kpc?

## Repository-theory result

The checked-in manuscript requires causal propagation and a covariant parent theory but does not currently provide a completed quadratic action/principal symbol from which the scalar/vector persistence-mode characteristic speed is derived. Therefore c_H < c is mathematically compatible with the effective hyperbolic equation, but it is not yet independently derived by the current theory.

The first Stage 9 L2 run deliberately fixed c_H=c. A post-hoc speed sweep chosen after seeing the L2 amplitude/shape failure would therefore violate the halo-blind/falsification protocol unless a slower speed is first justified independently from the parent theory and external constraints.

## Scale required for a Galactic correlation length

The frozen relaxation grid is tau = 1, 2, 4, 8, 16 Gyr. To obtain a characteristic length ell_H=c_H tau of order 5--20 kpc requires c_H/c roughly 10^-6--10^-5 (depending on tau and the chosen Galactic scale), i.e. propagation speeds of order km/s to tens of km/s rather than a modest fractional shift below c.

This is not treated as a viable tuning direction by default.

## External-theory constraint

In Lorentz-violating/vector-tensor gravity analogues, extra scalar/vector modes can have characteristic speeds different from the tensor speed. However, strongly subluminal gravitationally coupled propagating modes are generically constrained by the absence of gravitational Cherenkov losses from ultra-high-energy particles. GW170817/GRB170817A also fixes the observed tensor-mode speed extremely close to c, although extra-mode speeds remain model-dependent.

These results do not by themselves prove that the present persistence mode is excluded at c_H << c, because that depends on its exact coupling and radiative accessibility. They do mean that a km/s-scale gravitational mode cannot be introduced casually: the completed parent theory would have to demonstrate why the mode avoids the relevant Cherenkov/strong-coupling/instability constraints.

## Stage 9 decision

1. Keep c_H=c as the only currently admissible preregistered L2 speed.
2. Record the c_H=c L2 result as a failed/strongly disfavored primary candidate rather than renormalizing or slowing it after target exposure.
3. Do not execute a c_H sweep against the Milky Way residual or orbit-weight targets.
4. Permit c_H<c only after a parent-action derivation fixes the kinetic coefficients/principal symbol independently of the Milky Way halo comparison and an external-consistency audit addresses stability, causality, gravitational Cherenkov radiation, and observational coupling.
5. If such a derivation exists later, freeze the resulting c_H prior before rerunning Stage 9.

## Minimal covariant bookkeeping for future derivation

For a scalar persistence mode psi in the state-frame congruence u^mu, a generic quadratic principal sector can be written schematically as

    L_principal = -(A/2) (u^mu nabla_mu psi)^2
                  + (B/2) h^{mu nu} nabla_mu psi nabla_nu psi,

with h^{mu nu}=g^{mu nu}+u^mu u^nu. Around a locally inertial state-frame background the characteristic speed is c_H^2=(B/A)c^2, subject to sign conventions and the completed constrained field content. Stability requires the appropriate kinetic/gradient signs; the current manuscript does not yet fix A and B. This expression is therefore a derivation target, not a fitted Stage 9 parameterization.
