import numpy as np

from analysis.milky_way.candidate_l2 import (
    CandidateL2Parameters,
    _interior_tail_green_per_kpc3_gyr,
    candidate_l2_specification,
    interval_integrated_density_change_clouds,
    present_psi_from_interval_clouds,
)
from analysis.milky_way.historical_baryonic_potential import ExponentialDiskSnapshot
from analysis.milky_way.orientation_history import OrientationHistory
from analysis.milky_way.persistence_response import require_admissible_response


def test_l2_passes_response_gate():
    spec = candidate_l2_specification()
    require_admissible_response(spec)
    assert spec.admissible


def test_l2_green_is_zero_outside_characteristic_cone():
    params = CandidateL2Parameters(tau_gyr=2.0, c_h_kpc_per_gyr=10.0)
    g = _interior_tail_green_per_kpc3_gyr(1.0, np.array([5.0, 15.0]), params)
    assert g[0] > 0.0
    assert g[1] == 0.0


def test_l2_green_has_positive_interior_tail():
    params = CandidateL2Parameters(tau_gyr=4.0)
    g = _interior_tail_green_per_kpc3_gyr(5.0, np.array([0.0, 8.0]), params)
    assert np.all(g > 0.0)


def test_identical_held_snapshots_give_zero_signed_density_change():
    old = ExponentialDiskSnapshot(lookback_gyr=0.7, mass_msun=4e10, reff_kpc=3.5)
    new = ExponentialDiskSnapshot(lookback_gyr=0.0, mass_msun=4e10, reff_kpc=3.5)
    clouds = interval_integrated_density_change_clouds(
        [old, new], OrientationHistory(total_angle_deg=0.0), n_ring=24, n_phi=12
    )
    _, pts, dm = clouds[0]
    n = dm.size // 2
    assert np.allclose(pts[:n], pts[n:])
    assert np.allclose(dm[:n], -dm[n:])
    assert np.isclose(dm.sum(), 0.0, atol=1e-6)


def test_identical_held_interval_generates_zero_psi():
    old = ExponentialDiskSnapshot(lookback_gyr=0.7, mass_msun=4e10, reff_kpc=3.5)
    new = ExponentialDiskSnapshot(lookback_gyr=0.0, mass_msun=4e10, reff_kpc=3.5)
    clouds = interval_integrated_density_change_clouds(
        [old, new], OrientationHistory(total_angle_deg=0.0), n_ring=24, n_phi=12
    )
    psi = present_psi_from_interval_clouds(
        np.array([[8.0, 0.0, 1.0]]), clouds, CandidateL2Parameters(tau_gyr=4.0)
    )
    assert np.allclose(psi, 0.0, atol=1e-12)


def test_l2_unit_normalization_is_frozen():
    params = CandidateL2Parameters(tau_gyr=8.0)
    assert params.kappa == 1.0
