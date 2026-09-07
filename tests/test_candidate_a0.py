import numpy as np
import pytest

from analysis.milky_way.candidate_a0 import (
    A0TheoryProvenance,
    advect_points,
    advected_relaxation_step,
    require_a0_force_ready,
)


def test_a0_force_generation_is_blocked_by_default():
    with pytest.raises(RuntimeError):
        require_a0_force_ready(A0TheoryProvenance())


def test_a0_force_gate_can_only_pass_complete_independent_provenance():
    p = A0TheoryProvenance(
        parent_action_documented=True,
        unit_timelike_constraint_derived=True,
        state_frame_equation_derived=True,
        local_deposition_invariant_derived=True,
        observable_metric_coupling_derived=True,
        normalization_fixed_without_halo_targets=True,
        stability_checked=True,
        preferred_frame_ppn_checked=True,
        cherenkov_checked=True,
        gw_constraints_checked=True,
        cosmology_checked=True,
        frozen_before_halo_comparison=True,
    )
    require_a0_force_ready(p)
    assert p.force_ready


def test_advected_relaxation_zero_source_decays_exponentially():
    q0 = np.array([1.0, 2.0])
    q1 = advected_relaxation_step(q0, np.zeros(2), dt_gyr=2.0, tau_gyr=4.0)
    np.testing.assert_allclose(q1, q0 * np.exp(-0.5))


def test_advected_relaxation_constant_source_has_correct_equilibrium():
    source = np.array([2.0])
    tau = 3.0
    q1 = advected_relaxation_step(np.zeros(1), source, dt_gyr=100.0, tau_gyr=tau)
    np.testing.assert_allclose(q1, source * tau, rtol=1e-12, atol=1e-12)


def test_advect_points_follows_state_frame_characteristic():
    xyz = np.array([[1.0, 2.0, 3.0]])
    vel = np.array([[-2.0, 0.5, 1.0]])
    out = advect_points(xyz, vel, dt_gyr=4.0)
    np.testing.assert_allclose(out, np.array([[-7.0, 4.0, 7.0]]))
