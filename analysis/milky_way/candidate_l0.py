"""Candidate L0: minimal causal linear persistence response.

This module encodes the predeclared L0 theory specification and the local
operator/source definitions needed by a future numerical solver. It does not
read or optimize against halo targets.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analysis.milky_way.persistence_response import ResponseLawSpecification


# Speed of light in kpc/Gyr.  (c ~= 299792.458 km/s.)
C_KPC_PER_GYR = 306601.39378555055


@dataclass(frozen=True)
class CandidateL0Parameters:
    """Frozen parameters for the first L0 test.

    kappa is fixed to unity for the preregistered unit-deposition candidate.
    c_h_kpc_per_gyr defaults to c, avoiding a fitted subluminal length scale.
    """

    tau_gyr: float
    kappa: float = 1.0
    c_h_kpc_per_gyr: float = C_KPC_PER_GYR

    def __post_init__(self) -> None:
        if float(self.tau_gyr) <= 0.0:
            raise ValueError("tau_gyr must be positive")
        if float(self.kappa) != 1.0:
            raise ValueError("Candidate L0 preregistration fixes kappa=1")
        c_h = float(self.c_h_kpc_per_gyr)
        if not (0.0 < c_h <= C_KPC_PER_GYR * (1.0 + 1e-12)):
            raise ValueError("Candidate L0 requires 0 < c_H <= c")

    @property
    def correlation_length_kpc(self) -> float:
        return float(self.c_h_kpc_per_gyr * self.tau_gyr)

    @property
    def damping_coefficient_per_gyr(self) -> float:
        return 2.0 / float(self.tau_gyr)

    @property
    def restoring_coefficient_per_gyr2(self) -> float:
        return 1.0 / float(self.tau_gyr) ** 2

    @property
    def deposition_coefficient_per_gyr(self) -> float:
        return float(self.kappa) / float(self.tau_gyr)


def candidate_l0_specification() -> ResponseLawSpecification:
    """Return the independently declared admissibility record for L0."""
    return ResponseLawSpecification(
        name="candidate_L0_minimal_causal_linear_unit_deposition",
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
    params: CandidateL0Parameters,
) -> np.ndarray:
    """Return L0 RHS source term (kappa/tau) D_H Phi_b.

    Input units are potential per Gyr; output units are potential per Gyr^2.
    A static/comoving baryonic field has zero derivative and therefore zero
    hereditary deposition.
    """
    return params.deposition_coefficient_per_gyr * np.asarray(
        dphi_b_dt_state_frame, dtype=float
    )


def homogeneous_k0_roots_per_gyr(params: CandidateL0Parameters) -> np.ndarray:
    """Roots of r^2 + 2 r/tau + 1/tau^2 = 0 for the spatially uniform mode."""
    tau = float(params.tau_gyr)
    return np.roots([1.0, 2.0 / tau, 1.0 / tau**2])


def acceleration_from_psi_gradient(grad_psi: np.ndarray) -> np.ndarray:
    """Strictly linear L0 inherited acceleration a_H = -grad(Psi_H)."""
    arr = np.asarray(grad_psi, dtype=float)
    if arr.shape[-1] != 3:
        raise ValueError("grad_psi must have final dimension 3")
    return -arr


def interaction_acceleration_linear_limit(shape: tuple[int, ...]) -> np.ndarray:
    """Candidate L0 freezes a_int=0 in the manuscript's strict linear limit."""
    if not shape or shape[-1] != 3:
        raise ValueError("interaction acceleration shape must end in 3")
    return np.zeros(shape, dtype=float)
