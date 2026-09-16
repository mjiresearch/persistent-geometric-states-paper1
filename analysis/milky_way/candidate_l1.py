"""Candidate L1: minimal causal hereditary-tail persistence response.

L0 used the critically damped operator (D+1/tau)^2 - c_H^2 Laplacian.
That operator factorizes after an exponential field redefinition into the
ordinary massless wave equation, so its free-space retarded Green function has
support only on the light cone.  L0 is therefore retained as a null/control
candidate but is not sufficient to represent an interior-cone hereditary tail.

L1 changes no fitted scale and introduces no new dimensionless parameter.  It
uses the two distinct relaxation factors already available from the single
predeclared time scale tau:

    [(D_H + 1/tau)(D_H + 2/tau) - c_H^2 Laplacian] Psi_H
        = (1/tau) D_H Phi_b.

Equivalently,

    D_H^2 Psi_H + (3/tau) D_H Psi_H - c_H^2 Laplacian Psi_H
        + (2/tau^2) Psi_H = (1/tau) D_H Phi_b.

The spatially uniform free modes decay as exp(-t/tau) and exp(-2t/tau), while
the full retarded Green function has causal interior-cone support.  Static or
comoving baryons still have D_H Phi_b=0 and do not continuously regenerate a
second Poisson field.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analysis.milky_way.candidate_l0 import C_KPC_PER_GYR
from analysis.milky_way.persistence_response import ResponseLawSpecification


@dataclass(frozen=True)
class CandidateL1Parameters:
    tau_gyr: float
    kappa: float = 1.0
    c_h_kpc_per_gyr: float = C_KPC_PER_GYR

    def __post_init__(self) -> None:
        if float(self.tau_gyr) <= 0.0:
            raise ValueError("tau_gyr must be positive")
        if float(self.kappa) != 1.0:
            raise ValueError("Candidate L1 preregistration fixes kappa=1")
        c_h = float(self.c_h_kpc_per_gyr)
        if not (0.0 < c_h <= C_KPC_PER_GYR * (1.0 + 1e-12)):
            raise ValueError("Candidate L1 requires 0 < c_H <= c")

    @property
    def damping_coefficient_per_gyr(self) -> float:
        return 3.0 / float(self.tau_gyr)

    @property
    def restoring_coefficient_per_gyr2(self) -> float:
        return 2.0 / float(self.tau_gyr) ** 2

    @property
    def deposition_coefficient_per_gyr(self) -> float:
        return float(self.kappa) / float(self.tau_gyr)

    @property
    def correlation_length_kpc(self) -> float:
        return float(self.c_h_kpc_per_gyr * self.tau_gyr)


def candidate_l1_specification() -> ResponseLawSpecification:
    return ResponseLawSpecification(
        name="candidate_L1_two_rate_causal_hereditary_tail_unit_deposition",
        causal=True,
        finite_relaxation=True,
        independent_initial_data=True,
        static_source_duplicates_poisson=False,
        gr_recovery=True,
        interaction_vanishes_without_either_sector=True,
        universal_not_galaxy_fitted=True,
        transport_equation_documented=True,
        deposition_law_documented=True,
        interaction_law_documented=True,
        normalization_fixed_without_halo_targets=True,
    )


def deposition_from_baryonic_potential_derivative(
    dphi_b_dt_state_frame: np.ndarray,
    params: CandidateL1Parameters,
) -> np.ndarray:
    return params.deposition_coefficient_per_gyr * np.asarray(
        dphi_b_dt_state_frame, dtype=float
    )


def homogeneous_k0_roots_per_gyr(params: CandidateL1Parameters) -> np.ndarray:
    tau = float(params.tau_gyr)
    return np.array([-1.0 / tau, -2.0 / tau], dtype=float)


def transformed_interior_tail_scale_per_gyr(params: CandidateL1Parameters) -> float:
    """Positive scale of the interior-cone term after removing first damping.

    With Psi=exp[-3t/(2tau)] u, L1 becomes

        u_tt - c_H^2 Laplacian u - u/(4 tau^2) = transformed source,

    whose retarded Green function has nonzero support inside the characteristic
    cone (modified-Bessel tail) in addition to the direct light-cone term.
    """
    return 1.0 / (2.0 * float(params.tau_gyr))


def acceleration_from_psi_gradient(grad_psi: np.ndarray) -> np.ndarray:
    arr = np.asarray(grad_psi, dtype=float)
    if arr.shape[-1] != 3:
        raise ValueError("grad_psi must have final dimension 3")
    return -arr


def interaction_acceleration_linear_limit(shape: tuple[int, ...]) -> np.ndarray:
    if not shape or shape[-1] != 3:
        raise ValueError("interaction acceleration shape must end in 3")
    return np.zeros(shape, dtype=float)
