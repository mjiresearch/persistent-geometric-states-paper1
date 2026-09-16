import pytest

from analysis.milky_way.candidate_a3_parent_action import (
    A3PhysicalParameters,
    A3TheoryProvenance,
    require_a3_force_ready,
)


def test_field_rescaling_preserves_physical_response_combinations():
    p = A3PhysicalParameters(trace_scale=7.0, beta=2.0, conformal_a=3.0, disformal_b=0.5)
    q = p.rescaled_field_convention(11.0)
    assert q.dynamic_response == pytest.approx(p.dynamic_response)
    assert q.lensing_response == pytest.approx(p.lensing_response)
    assert q.lensing_to_dynamics_ratio == pytest.approx(p.lensing_to_dynamics_ratio)


def test_beta_can_be_normalized_by_field_convention_without_changing_physics():
    p = A3PhysicalParameters(trace_scale=5.0, beta=4.0, conformal_a=2.0, disformal_b=0.25)
    q = p.rescaled_field_convention(1.0 / p.beta)
    assert q.beta == pytest.approx(1.0)
    assert q.dynamic_response == pytest.approx(p.dynamic_response)
    assert q.lensing_response == pytest.approx(p.lensing_response)


def test_force_gate_blocks_incomplete_parent_theory():
    with pytest.raises(RuntimeError):
        require_a3_force_ready(A3TheoryProvenance())


def test_force_gate_can_pass_only_when_all_requirements_are_independently_closed():
    p = A3TheoryProvenance(
        auxiliary_or_open_system_derived=True,
        trace_scale_fixed_independently=True,
        dynamic_response_fixed_independently=True,
        lensing_ratio_fixed_independently=True,
        state_frame_sector_closed=True,
        stability_checked=True,
        ppn_equivalence_checked=True,
        lensing_checked=True,
        gw_checked=True,
        cosmology_checked=True,
        frozen_before_halo_comparison=True,
    )
    require_a3_force_ready(p)
