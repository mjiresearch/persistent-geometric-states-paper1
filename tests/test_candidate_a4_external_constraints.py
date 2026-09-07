import pytest

from analysis.milky_way.candidate_a4_external_constraints import (
    A4ConstraintStatus,
    require_a4_stage9_force_ready,
    static_comoving_system_calibrates_a2_normalization,
)


def test_static_comoving_system_does_not_calibrate_a2_source():
    assert not static_comoving_system_calibrates_a2_normalization(0.0)


def test_dynamical_trace_can_in_principle_calibrate_source():
    assert static_comoving_system_calibrates_a2_normalization(1.0)


def test_external_consistency_is_not_normalization():
    status = A4ConstraintStatus(
        tensor_speed_checked=True,
        preferred_frame_ppn_checked=True,
        strong_field_checked=True,
        equivalence_principle_checked=True,
        lensing_slip_checked=True,
    )
    assert status.external_consistency_ready
    assert not status.normalization_ready
    assert not status.stage9_force_ready


def test_fully_closed_status_is_force_ready():
    status = A4ConstraintStatus(**{k: True for k in A4ConstraintStatus.__dataclass_fields__})
    assert status.stage9_force_ready
    require_a4_stage9_force_ready(status)


def test_gate_blocks_incomplete_status():
    with pytest.raises(RuntimeError):
        require_a4_stage9_force_ready(A4ConstraintStatus())
