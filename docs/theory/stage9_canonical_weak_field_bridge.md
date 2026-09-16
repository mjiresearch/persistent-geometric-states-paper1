# Stage 9 Canonical Weak-Field Bridge

## Scope

This note derives the Stage 9 observable mapping directly from the canonical manuscript, **Persistent Geometric States in General Relativity: A Hereditary Framework for Galactic Rotation Curves**. It supersedes any temptation to invent a parallel A/L candidate solely for Stage 9.

## 1. Observable metric

The canonical paper defines the weak-field baryonic metric as

\[
 g^{(b)}_{\mu\nu}=\eta_{\mu\nu}+h^{(b)}_{\mu\nu},
\]

and the leading observable metric as

\[
 g^{\rm obs}_{\mu\nu}=g_{\mu\nu}+\epsilon_H H_{\mu\nu}.
\]

Thus the persistence sector is not a second ordinary Einstein/Poisson solution. It enters through the composite inherited perturbation \(H_{\mu\nu}\).

## 2. Canonical field content and composite state

The parent theory uses the dynamical timelike state frame \(n^\mu\), scalar persistence mode \(\phi\), and spatial vector persistence mode \(A_\mu\), with \(n^\mu A_\mu=0\). The observable inherited perturbation is

\[
H_{\mu\nu}=
\alpha_\phi\phi\,\gamma_{\mu\nu}
+\beta_\phi\phi\,n_\mu n_\nu
+\alpha_A n_{(\mu}A_{\nu)}
+\beta_A L_A D_{(\mu}A_{\nu)}.
\]

The coefficients \(\alpha_\phi,\beta_\phi,\alpha_A,\beta_A\) are universal theory-level constants.

## 3. Source channels

For nonrelativistic baryons in the state frame,

\[
\epsilon\simeq \rho_b c^2,
\qquad
q_i\simeq \rho_b c\,v_i^{\rm rel}.
\]

The canonical scalar history invariant is

\[
I_\phi=\tau_\star\left(\dot\epsilon_M+\chi_q cD_\mu q^\mu\right),
\qquad
\dot\epsilon_M=cD_M\epsilon,
\]

with scalar source

\[
J_\phi=-\frac{g_\phi}{M_\star}I_\phi.
\]

The vector source is

\[
J^A_\mu=-\frac{g_A}{M_\star}q_\mu.
\]

A permanently static source comoving with the state frame has \(\dot\epsilon_M=0\) and \(q_\mu=0\), so it does not regenerate persistence.

## 4. Propagation

The scalar and transverse-vector fields are propagated with the canonical retarded Green functions and reconstructed into \(H_{\mu\nu}\). Schematically,

\[
H_{\mu\nu}(x)=\int d^4x'\,\mathcal G_{\mu\nu}{}^{\alpha\beta,{\rm ret}}(x,x')T^{(b)}_{\alpha\beta}(x').
\]

No halo-derived spatial kernel is to be inserted into this mapping.

## 5. Slow-motion dynamics

The canonical paper defines

\[
g^{\rm obs}_{00}=-1-\frac{2}{c^2}(\Phi_b+\Phi_P),
\qquad
\Phi_P=-\frac{\epsilon_Hc^2}{2}H_{00}.
\]

The slow-motion acceleration is

\[
a^i=-\partial^i(\Phi_b+\Phi_P)+a^i_{\rm mix}+a^i_{\rm spatial}.
\]

Therefore Stage 9 must compute separately:

1. scalar-potential acceleration from \(H_{00}\);
2. velocity-dependent mixed terms from \(H_{0i}\);
3. spatial-metric corrections from \(H_{ij}\), at the order retained by the canonical weak-field expansion.

## 6. Stationary rotating-disk specialization

For the canonical minimal stationary disk, \(\chi_q=1\) and conserved pressureless matter gives \(J_\phi^{\rm dust}=0\). The surviving baseline response is therefore the transverse-vector mode sourced by the observed baryonic streaming current.

For an axisymmetric disk,

\[
\mathcal J_b(R)=\sum_\alpha \Sigma_\alpha(R)\,\bar v_{\varphi,\alpha}(R),
\]

and

\[
(-\nabla^2+L_A^{-2})\mathbf a^{\rm T}
=-\frac{g_A}{M_\star}\mathbf q_b.
\]

The midplane effective vector potential yields

\[
B_{P,z}(R)=\frac{1}{R}\frac{d}{dR}\left[R A^{\rm eff}_{\hat\varphi}(R,0)\right],
\]

and the canonical vector-mediated radial acceleration is

\[
\boxed{a_R^{(A)}(R)=\zeta_A v_c(R)B_{P,z}(R)}.
\]

Equivalently,

\[
a_R^{(A)}(R)=\mathcal C_A v_c(R)
\int_0^\infty dR'\,R'\mathcal J_b(R')\,\mathcal K_A(R,R';L_A),
\]

with universal

\[
\mathcal C_A=\zeta_A\mathcal G_A.
\]

This is the **canonical stationary Stage 9 force law**. It is not Candidate L2 and must not inherit the L2 falsification result.

## 7. Historical/nonstationary Stage 9 extension

The Milky Way historical reconstruction must add the scalar/history channel and time-dependent vector source consistently with the same canonical parent equations:

- evolve \(\rho_b(\mathbf x,t)\) and baryonic relative current \(q_i(\mathbf x,t)\);
- apply the historical orientation operator to the baryonic history before evaluating the state-frame sources;
- compute \(I_\phi\) and \(q_i\) in the physical state frame;
- propagate \(\phi\) and \(A_i^{\rm T}\) with the canonical retarded operators;
- reconstruct \(H_{00},H_{0i},H_{ij}\);
- compute the stellar acceleration from the canonical observable metric.

The 0-degree history is Stage 9A. The 30--180 degree runs remain sensitivity tests and may not alter the theory parameters.

## 8. Free universal combinations that remain to be frozen

The canonical paper still contains theory-level quantities that Stage 9 may not choose from the halo target. The principal combinations are:

- \(L_A\): vector correlation/screening length;
- \(\mathcal C_A\): stationary vector force amplitude, combining source, embedding and probe-response coefficients;
- scalar-sector propagation parameters \(c_\phi,\tau_\phi,L_\phi\);
- scalar source combination involving \(g_\phi\tau_\star/M_\star\) and \(\chi_q\);
- vector propagation parameters \(c_A,\tau_A,L_A\) where the nonstationary equation requires them;
- the state-frame history \(n^\mu(x,t)\) or an independently specified approximation to it;
- any retained higher-order interaction coefficients beyond the probe-level observable metric.

These must be fixed by the canonical action, prior sections of the paper, external constraints, or an explicitly declared calibration sample that is separate from the Stage 9 confirmatory targets.

## 9. Stage 9 implementation order

1. **Stationary sanity reproduction:** reproduce the canonical Sec. 10 disk equation numerically with prescribed baryonic current and no Milky Way halo exposure.
2. **Milky Way source construction:** construct \(\rho_b(\mathbf x,t)\), \(q_i(\mathbf x,t)\), and \(I_\phi(\mathbf x,t)\) from the available historical inputs.
3. **Freeze universal parameters/provenance:** record where every value came from.
4. **Generate Stage 9A 0-degree field:** compute \(H_{\mu\nu}\) and the stellar acceleration.
5. **Freeze prediction.**
6. **Only then** compare with \(\Delta a\), Portail17/Hunter24 orbit weights, and other conventional benchmarks.
7. Run the preregistered orientation sensitivity suite without retuning.

## 10. Guardrail conclusion

The next implementation is not a new response-law search. The canonical paper already supplies the weak-field source-to-observable chain. The remaining task is parameter provenance and faithful numerical implementation of that chain.