# Stage 9 crosswalk to the original finite-memory papers

## Source documents

This crosswalk distinguishes two early manuscripts that are easy to conflate:

1. **A Covariant Finite-Memory Formulation of the Einstein Field Equations** (March 3, 2026): foundational structural paper. It introduces the hereditary curvature-source relation and an auxiliary tensor field with first-order relaxation.
2. **Phenomenology of Finite-Memory Gravity: Astrophysical and Cosmological Consequences** (March 6, 2026): first explicit multi-observable paper. It applies the same finite-memory response to galactic dynamics, lensing, cosmological structure growth, and gravitational-wave consistency.

## Main correspondence

### Original hereditary source sector -> A0/A2

The foundational paper writes

    G_mn = 8 pi G (T_mn + lambda H_mn)

with auxiliary evolution

    tau nabla_t H_mn + H_mn = T_mn.

This is structurally the same *class* of first-order hereditary localization now represented by A0. However, current Stage 9 deliberately modifies the deposition rule: A2 uses a derivative source proportional to D_U T rather than T itself so that static/comoving matter does not continuously regenerate the persistent state.

Therefore A0 is a reconstruction of the original auxiliary relaxation architecture, while A2 is a stricter replacement of the original source term.

### Original kernel parameters -> tau and invariant response combinations

The early phenomenology paper uses an exponential kernel characterized by a persistence time tau_K and dimensionless amplitude kappa_K. Current Stage 9 retains tau as the memory time but no longer treats the source amplitude, q normalization, conformal coupling, and disformal coupling as separately physical.

A3 shows that at linear order the observable combinations are

    A_dyn  = beta (a - b)
    A_lens = beta b

plus a universal stress/curvature scale Lambda_T^4.

Thus the old phenomenological kappa_K is not simply one modern parameter. Its physical role is split between deposition normalization and observable metric response, with field-normalization redundancy removed.

### Galactic rotation -> A1 dynamical channel

The early phenomenology paper represents galactic dynamics through an effective persistent contribution to the Newtonian potential and writes a schematic Poisson-type equation with an effective rho_pers.

Current Stage 9 replaces that bookkeeping device with the observable metric relation

    g_eff_mn = C(q_H) g_mn + D(q_H) u^H_m u^H_n.

At linear order,

    Phi_eff = Phi_b + c^2 (a - b) q_H.

The persistence acceleration is therefore controlled by the invariant dynamical response A_dyn after deposition normalization is included.

This is the rigorous successor of the original rotation-curve channel, but it avoids treating rho_pers as literal extra matter or as a second freely chosen Poisson halo.

### Lensing -> A1 lensing channel

The early phenomenology paper already emphasized that lensing probes the Weyl potential Phi + Psi rather than the same single quantity as nonrelativistic dynamics.

Current A1 makes that split explicit:

    Delta(Phi + Psi) = -c^2 b q_H.

After source normalization is included, lensing is governed by A_lens while stellar dynamics is governed by A_dyn. The ratio A_lens/A_dyn is therefore the modern form of the early paper's joint rotation+lensing consistency requirement.

### Cosmological evolution -> A4/FLRW closure

The early phenomenology paper treats cosmological structure growth through a scale- and time-dependent effective response mu(k,a). Current Stage 9 has not yet derived mu(k,a), but A2 gives a direct homogeneous source because cosmological matter evolves even in FLRW:

    D_U rho_m = -3 H rho_m

for pressureless matter. Consequently the cosmological branch can source q_H without using a galaxy residual and is the natural place to determine or constrain Lambda_T^4 and A_dyn independently.

This is the modern derivational route back to the early paper's cosmological response function.

### Gravitational waves -> preserved original principle

Both early papers insist that the Einstein kinetic operator and vacuum tensor propagation remain unchanged. The failed L0/L1/L2 detour clarified why Stage 9 should not model persistence as a slow gravitational radiation mode. The A0 advected-state route is more faithful to the original architectural principle: modify the state/source response without changing ordinary tensor-wave propagation.

## What is genuinely new in Stage 9

The current A0-A4 construction is not merely a renaming of the original formulation. It adds several constraints that were missing or only schematic in the early papers:

- a time-dependent Galactic orientation history R(t);
- halo-blind preregistration and no-post-hoc-rescue rules;
- rejection of the luminal additive L2 implementation after corrected unit testing;
- explicit distinction between state advection and gravitational-wave propagation;
- derivative deposition D_U T so static matter gives zero new persistence;
- explicit conformal/disformal observable metric coupling;
- field-normalization invariance and reduction to physical response combinations;
- separation of consistency constraints from amplitude calibration;
- requirement that cosmology or another non-galactic dynamical sector fix the normalization before the Milky Way target is exposed.

## Scientific conclusion

Stage 9 has largely derived its way back to the same **rotation + lensing + cosmology** triangle identified in the March 6 phenomenology paper. The convergence is substantive rather than merely thematic: the same three sectors now arise because they constrain distinct parts of one response architecture.

However, the modern formulation is not identical to the original finite-memory equations. In particular, the original auxiliary equation sourced H_mn directly from T_mn, while A2 sources the modern persistent state from the state-frame derivative D_U T. That is the most important theoretical deviation and must be justified from the parent theory rather than hidden under notation.

The next step should therefore be to derive the homogeneous FLRW equations for the A0-A4 branch and compare their linear response with the original phenomenological mu(k,a). If the resulting response reduces to the same functional structure without fitting galaxy data, then the new Stage 9 branch can be interpreted as a more rigorous reconstruction of the original Paper-1 mechanism. If it does not, the difference must be treated as a genuine theory change.