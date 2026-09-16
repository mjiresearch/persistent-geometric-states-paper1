import numpy as np
import pytest

from analysis.milky_way.candidate_l0 import (
    C_KPC_PER_GYR,
    CandidateL0Parameters,
    acceleration_from_psi_gradient,
    candidate_l0_specification,
    deposition_from_baryonic_potential_derivative,
    homogeneous_k0_roots_per_gyr,
    interaction_acceleration_linear_limit,
)
from analysis.milky_way.persistence_response import require_admissible_response


def test_candidate_l0_passes_response_gate():
    spec = candidate_l0_specification()
    assert spec.admissible
    require_admissible_response(spec)


def test_static_comoving_baryonic_field_deposits_nothing():
    p = CandidateL0Parameters(tau_gyr=4.0)
    src = deposition_from_baryonic_potential_derivative(np.zeros(5), p)
    assert np.all(src == 0.0)


def test_unit_deposition_normalization_is_frozen():
    with pytest.raises(ValueError):
        CandidateL0Parameters(tau_gyr=4.0, kappa=0.5)


def test_characteristic_speed_cannot_exceed_c():
    CandidateL0Parameters(tau_gyr=2.0, c_h_kpc_per_gyr=C_KPC_PER_GYR)
    with pytest.raises(ValueError):
        CandidateL0Parameters(tau_gyr=2.0, c_h_kpc_per_gyr=1.01 * C_KPC_PER_GYR)


def test_uniform_free_mode_relaxes_with_minus_one_over_tau_root():
    p = CandidateL0Parameters(tau_gyr=8.0)
    roots = homogeneous_k0_roots_per_gyr(p)
    assert np.allclose(roots, [-1.0 / 8.0, -1.0 / 8.0], atol=1e-8)


def test_linear_acceleration_and_interaction_limit():
    grad = np.array([[1.0, -2.0, 3.0]])
    assert np.allclose(acceleration_from_psi_gradient(grad), -grad)
    assert np.all(interaction_acceleration_linear_limit((4, 3)) == 0.0)
