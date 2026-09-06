import numpy as np
import pytest

from analysis.milky_way.candidate_a1_metric_coupling import (
    A1MetricCouplingProvenance,
    lensing_potential_shift,
    nonrelativistic_acceleration_shift,
    require_a1_metric_coupling_ready,
    weak_field_potential_shifts,
)


def test_a1_force_generation_blocked_without_theory_closure():
    with pytest.raises(RuntimeError):
        require_a1_metric_coupling_ready(A1MetricCouplingProvenance())


def test_a1_fully_closed_provenance_can_pass_gate():
    p = A1MetricCouplingProvenance(
        parent_action_derived=True,
        matter_metric_identified=True,
        q_normalization_fixed_without_halo_targets=True,
        linear_coefficients_derived=True,
        equivalence_principle_checked=True,
        solar_system_ppn_checked=True,
        lensing_slip_checked=True,
        gw_propagation_checked=True,
        cosmology_checked=True,
        frozen_before_halo_comparison=True,
    )
    require_a1_metric_coupling_ready(p)
    assert p.force_ready


def test_pure_conformal_linear_lensing_shift_cancels():
    q = np.array([1e-8, -2e-8])
    shift = lensing_potential_shift(q, a=1.0, b=0.0)
    assert np.allclose(shift, 0.0, atol=1e-12)


def test_pure_disformal_has_fixed_dynamics_and_lensing_relation():
    q = np.array([1e-8])
    dphi, dpsi = weak_field_potential_shifts(q, a=0.0, b=1.0)
    lens = lensing_potential_shift(q, a=0.0, b=1.0)
    assert np.allclose(dpsi, 0.0)
    assert np.allclose(lens, dphi)


def test_acceleration_depends_only_on_a_minus_b_at_linear_order():
    grad = np.array([[1e-10, 0.0, 0.0]])
    x = nonrelativistic_acceleration_shift(grad, a=2.0, b=1.0)
    y = nonrelativistic_acceleration_shift(grad, a=4.0, b=3.0)
    assert np.allclose(x, y)
