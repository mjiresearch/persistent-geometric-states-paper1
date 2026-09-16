import numpy as np
import pandas as pd

from analysis.milky_way.orientation_history import OrientationHistory
from analysis.milky_way.provisional_source_history import (
    build_memory_source_cloud,
    build_radial_increments,
    ring_quadrature_points,
    source_cloud_moments,
)


def _table():
    return pd.DataFrame(
        {
            "lookback_time_gyr": [8.0, 4.0, 1.0],
            "stellar_mass_1e10_msun": [1.0, 2.0, 2.5],
            "Reff_birth_radius_kpc": [2.0, 2.5, 3.0],
        }
    )


def test_builds_adjacent_intervals():
    inc = build_radial_increments(_table(), radius_kpc=np.linspace(0.01, 15.0, 200))
    assert len(inc) == 2
    assert inc[0].older_lookback_gyr == 8.0
    assert inc[0].younger_lookback_gyr == 4.0
    assert inc[0].representative_lookback_gyr == 6.0


def test_nonnegative_envelope_clips_negative_surface_density():
    signed = build_radial_increments(_table(), radius_kpc=np.linspace(0.01, 15.0, 200))
    clipped = build_radial_increments(
        _table(),
        radius_kpc=np.linspace(0.01, 15.0, 200),
        envelope="nonnegative_clipped",
    )
    assert any(np.any(x.delta_sigma_msun_kpc2 < 0.0) for x in signed)
    assert all(np.all(x.delta_sigma_msun_kpc2 >= 0.0) for x in clipped)


def test_ring_quadrature_is_axisymmetric_and_mass_finite():
    inc = build_radial_increments(
        _table(), radius_kpc=np.linspace(0.01, 15.0, 100), envelope="nonnegative_clipped"
    )[0]
    points, weights = ring_quadrature_points(inc, n_phi=12)
    assert points.shape == (1200, 3)
    assert weights.shape == (1200,)
    assert np.isfinite(weights).all()
    assert abs(points[:, 0].mean()) < 1e-12
    assert abs(points[:, 1].mean()) < 1e-12
    assert np.allclose(points[:, 2], 0.0)


def test_zero_degree_memory_cloud_remains_in_present_plane():
    inc = build_radial_increments(
        _table(), radius_kpc=np.linspace(0.01, 12.0, 80), envelope="nonnegative_clipped"
    )
    points, weights, times = build_memory_source_cloud(
        inc, OrientationHistory(total_angle_deg=0.0), tau_gyr=8.0, n_phi=8
    )
    assert points.shape[0] == weights.size == times.size
    assert np.allclose(points[:, 2], 0.0)
    assert np.all(weights >= 0.0)


def test_old_90_degree_source_is_rotated_out_of_present_plane():
    inc = build_radial_increments(
        _table(), radius_kpc=np.linspace(0.01, 12.0, 80), envelope="nonnegative_clipped"
    )
    orientation = OrientationHistory(
        total_angle_deg=90.0,
        axis=(1.0, 0.0, 0.0),
        transition_lookback_gyr=4.0,
        transition_duration_gyr=0.0,
    )
    points, weights, _ = build_memory_source_cloud(inc, orientation, tau_gyr=16.0, n_phi=8)
    moments = source_cloud_moments(points, weights)
    assert moments["second_moment_eigenvalue_mid_kpc2"] > 0.0
    assert np.max(np.abs(points[:, 2])) > 1.0


def test_clipped_cloud_has_zero_negative_weight_fraction():
    inc = build_radial_increments(
        _table(), radius_kpc=np.linspace(0.01, 12.0, 80), envelope="nonnegative_clipped"
    )
    points, weights, _ = build_memory_source_cloud(
        inc, OrientationHistory(total_angle_deg=60.0), tau_gyr=4.0, n_phi=8
    )
    moments = source_cloud_moments(points, weights)
    assert moments["negative_weight_fraction"] == 0.0
