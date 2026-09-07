import numpy as np

from analysis.milky_way.candidate_l1 import (
    CandidateL1Parameters,
    candidate_l1_specification,
    deposition_from_baryonic_potential_derivative,
    homogeneous_k0_roots_per_gyr,
    interaction_acceleration_linear_limit,
    transformed_interior_tail_scale_per_gyr,
)
from analysis.milky_way.persistence_response import require_admissible_response


def test_l1_passes_response_gate():
    spec = candidate_l1_specification()
    require_admissible_response(spec)
    assert spec.admissible


def test_l1_static_source_has_zero_deposition():
    params = CandidateL1Parameters(tau_gyr=4.0)
    source = deposition_from_baryonic_potential_derivative(np.zeros((5, 7)), params)
    assert np.all(source == 0.0)


def test_l1_unit_deposition_is_frozen():
    params = CandidateL1Parameters(tau_gyr=2.0)
    assert params.kappa == 1.0
    assert params.deposition_coefficient_per_gyr == 0.5


def test_l1_uniform_modes_both_relax():
    params = CandidateL1Parameters(tau_gyr=8.0)
    roots = homogeneous_k0_roots_per_gyr(params)
    assert np.allclose(np.sort(roots), np.sort(np.array([-1 / 8, -2 / 8])))
    assert np.all(roots < 0.0)


def test_l1_has_nonzero_interior_tail_scale():
    params = CandidateL1Parameters(tau_gyr=4.0)
    assert transformed_interior_tail_scale_per_gyr(params) == 1.0 / 8.0


def test_l1_linear_interaction_is_zero():
    arr = interaction_acceleration_linear_limit((3, 4, 3))
    assert arr.shape == (3, 4, 3)
    assert np.all(arr == 0.0)
