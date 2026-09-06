import numpy as np
import pytest

from analysis.milky_way.orientation_history import (
    OrientationHistory,
    exponential_memory_weight,
    rotation_matrix_axis_angle,
)


def test_rotation_matrix_is_orthonormal():
    r = rotation_matrix_axis_angle((1, 2, 3), 73.0)
    assert np.allclose(r @ r.T, np.eye(3), atol=1e-12)
    assert np.isclose(np.linalg.det(r), 1.0, atol=1e-12)


def test_zero_angle_is_identity_at_all_times():
    h = OrientationHistory(total_angle_deg=0.0)
    xyz = np.array([[1.0, 2.0, 3.0], [-2.0, 0.5, 4.0]])
    for t in (0.0, 4.0, 8.0, 12.0):
        assert np.allclose(h.rotate_points(xyz, t), xyz)


def test_ancient_snapshot_reaches_full_angle():
    h = OrientationHistory(
        total_angle_deg=90.0,
        axis=(1.0, 0.0, 0.0),
        transition_lookback_gyr=8.0,
        transition_duration_gyr=2.0,
    )
    v = np.array([0.0, 1.0, 0.0])
    assert np.allclose(h.rotate_vectors(v, 10.0), [0.0, 0.0, 1.0], atol=1e-12)
    assert np.allclose(h.rotate_vectors(v, 0.0), v, atol=1e-12)


def test_mid_transition_is_half_angle_for_symmetric_smoothstep():
    h = OrientationHistory(total_angle_deg=120.0, transition_lookback_gyr=8.0, transition_duration_gyr=2.0)
    assert np.isclose(h.historical_angle_deg(8.0), 60.0)


def test_180_degree_vector_reversal_diagnostic():
    h = OrientationHistory(total_angle_deg=180.0, axis=(1.0, 0.0, 0.0), transition_lookback_gyr=8.0, transition_duration_gyr=0.0)
    v = np.array([0.0, 1.0, 0.0])
    assert np.allclose(h.rotate_vectors(v, 9.0), [0.0, -1.0, 0.0], atol=1e-12)


def test_memory_weight():
    assert np.isclose(exponential_memory_weight(0.0, 4.0), 1.0)
    assert np.isclose(exponential_memory_weight(4.0, 4.0), np.exp(-1.0))
    with pytest.raises(ValueError):
        exponential_memory_weight(1.0, 0.0)
