# Stage 9 characteristic-speed audit

Date: 2026-08-10

## Critical unit correction

The first Candidate L0/L1/L2 implementation defined `C_KPC_PER_GYR` as 306.60139378555056. That numerical value is the speed of light in kpc/Myr, not kpc/Gyr. The correct value is approximately 306601.39378555055 kpc/Gyr.

The repository constant has been corrected. Any previously generated Candidate L2 acceleration field or amplitude/shape comparison that used the old constant is invalid and must be regenerated. In particular, the provisional claim that the c_H=c L2 field was about nine orders of magnitude below the Stage-3 residual is withdrawn pending the corrected rerun.

This correction increases the luminal correlation length by a factor of 1000 and therefore strengthens the qualitative observation that a Gyr-relaxation luminal mode is extremely smooth across Galactic scales. It does not by itself determine the corrected acceleration amplitude because the L2 source prefactor and Green function both depend on c_H.

## Question

Can Candidate L2 be rescued, if necessary after the corrected rerun, by lowering the persistence-mode characteristic speed c_H below c so that the correlation length c_H tau becomes Galactic rather than hundreds of thousands to millions of kpc?

## Repository-theory result

The checked-in manuscript requires causal propagation and a covariant parent theory but does not currently provide a completed quadratic action/principal symbol from which the scalar/vector persistence-mode characteristic speed is derived. Therefore c_H < c is mathematically compatible with the effective hyperbolic equation, but it is not yet independently derived by the current theory.

A post-hoc speed sweep chosen after exposure to the L2 Milky Way amplitude/shape target would violate the halo-blind/falsification protocol unless a slower speed is first justified independently from the parent theory and external constraints.

## Scale required for a Galactic correlation length

The frozen relaxation grid is tau = 1, 2, 4, 8, 16 Gyr. With the corrected c, a characteristic length ell_H=c_H tau of order 5--20 kpc requires c_H/c from roughly 10^-6 to 10^-4 across the extreme combinations of the frozen tau grid and Galactic length scale. For a representative 10-kpc scale, c_H/c is about 3.3e-5 at tau=1 Gyr and about 2.0e-6 at tau=16 Gyr. These correspond to propagation speeds of order sub-km/s to tens of km/s, not a modest fractional shift below c.

This is not treated as a viable tuning direction by default.

## External-theory constraint

In Lorentz-violating/vector-tensor gravity analogues, extra scalar/vector modes can have characteristic speeds different from the tensor speed. However, strongly subluminal gravitationally coupled propagating modes are generically constrained by the absence of gravitational Cherenkov losses from ultra-high-energy particles. GW170817/GRB170817A also fixes the observed tensor-mode speed extremely close to c, although extra-mode speeds remain model-dependent.

These results do not by themselves prove that the present persistence mode is excluded at c_H << c, because that depends on its exact coupling and radiative accessibility. They do mean that a km/s-scale gravitational mode cannot be introduced casually: the completed parent theory would have to demonstrate why the mode avoids the relevant Cherenkov/strong-coupling/instability constraints.

## Stage 9 decision

1. Correct the speed-of-light unit error and regenerate the c_H=c Candidate L2 field before interpreting L2.
2. Keep c_H=c as the only currently admissible preregistered L2 speed.
3. Do not execute a c_H sweep against the Milky Way residual or orbit-weight targets.
4. Permit c_H<c only after a parent-action derivation fixes the kinetic coefficients/principal symbol independently of the Milky Way halo comparison and an external-consistency audit addresses stability, causality, gravitational Cherenkov radiation, and observational coupling.
5. If such a derivation exists later, freeze the resulting c_H prior before rerunning Stage 9.

## Minimal covariant bookkeeping for future derivation

For a scalar persistence mode psi in the state-frame congruence u^mu, a generic quadratic principal sector can be written schematically as

    L_principal = -(A/2) (u^mu nabla_mu psi)^2
                  + (B/2) h^{mu nu} nabla_mu psi nabla_nu psi,

with h^{mu nu}=g^{mu nu}+u^mu u^nu. Around a locally inertial state-frame background the characteristic speed is c_H^2=(B/A)c^2, subject to sign conventions and the completed constrained field content. Stability requires the appropriate kinetic/gradient signs; the current manuscript does not yet fix A and B. This expression is therefore a derivation target, not a fitted Stage 9 parameterization.
