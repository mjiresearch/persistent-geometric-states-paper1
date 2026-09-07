import numpy as np
import pandas as pd

from analysis.milky_way.historical_baryonic_potential import (
    G_KPC_KMS2_PER_MSUN,
    ExponentialDiskSnapshot,
    exponential_disk_potential,
    snapshots_from_table_a1,
    state_frame_time_derivative,
)
from analysis.milky_way.orientation_history import OrientationHistory


def test_far_field_recovers_point_mass_limit():
    snap = ExponentialDiskSnapshot(lookback_gyr=5.0, mass_msun=5e10, reff_kpc=3.0)
    xyz = np.array([[0.0, 0.0, 200.0]])
    phi = exponential_disk_potential(xyz, snap, n_ring=128)[0]
    expected = -G_KPC_KMS2_PER_MSUN * snap.mass_msun / 200.0
    assert np.isclose(phi, expected, rtol=0.02)


def test_zero_degree_orientation_is_identity():
    snap = ExponentialDiskSnapshot(lookback_gyr=9.0, mass_msun=2e10, reff_kpc=2.5)
    pts = np.array([[8.0, 1.5, 2.0], [3.0, -4.0, 1.0]])
    plain = exponential_disk_potential(pts, snap, orientation=None, n_ring=96)
    oriented = exponential_disk_potential(
        pts, snap, orientation=OrientationHistory(total_angle_deg=0.0), n_ring=96
    )
    assert np.allclose(plain, oriented, rtol=1e-12, atol=1e-12)


def test_ninety_degree_disk_rotates_potential_geometry():
    snap = ExponentialDiskSnapshot(lookback_gyr=10.0, mass_msun=2e10, reff_kpc=2.5)
    hist = OrientationHistory(
        total_angle_deg=90.0,
        axis=(1.0, 0.0, 0.0),
        transition_lookback_gyr=8.0,
        transition_duration_gyr=2.0,
    )
    # Ancient disk is xy rotated about x, so present-frame y behaves like disk z.
    p_y = np.array([[0.0, 5.0, 0.0]])
    p_z_unrot = np.array([[0.0, 0.0, 5.0]])
    a = exponential_disk_potential(p_y, snap, orientation=hist, n_ring=96)[0]
    b = exponential_disk_potential(p_z_unrot, snap, orientation=None, n_ring=96)[0]
    assert np.isclose(a, b, rtol=2e-10, atol=1e-10)


def test_present_hold_appends_zero_lookback_snapshot():
    table = pd.DataFrame(
        {
            "lookback_time_gyr": [3.0, 0.7],
            "stellar_mass_1e10_msun": [3.0, 4.0],
            "Reff_birth_radius_kpc": [3.0, 4.0],
        }
    )
    snaps = snapshots_from_table_a1(table, append_present_hold=True)
    assert snaps[-1].lookback_gyr == 0.0
    assert snaps[-1].mass_msun == snaps[-2].mass_msun
    assert snaps[-1].reff_kpc == snaps[-2].reff_kpc


def test_held_final_potential_has_zero_present_derivative():
    lookback = np.array([3.0, 0.7, 0.0])
    phi = np.array([[[1.0]], [[2.0]], [[2.0]]])
    deriv = state_frame_time_derivative(lookback, phi)
    assert deriv[-1, 0, 0] == 0.0


def test_forward_time_sign_is_correct():
    lookback = np.array([2.0, 1.0, 0.0])
    # Phi increases linearly with forward cosmic time t=-lookback.
    phi = (-lookback)[:, None]
    deriv = state_frame_time_derivative(lookback, phi)
    assert np.allclose(deriv[:, 0], 1.0)
