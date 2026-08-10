import pytest

from analysis.milky_way.candidate_l0 import C_KPC_PER_GYR
from analysis.milky_way.candidate_l2 import CandidateL2Parameters
from analysis.milky_way.characteristic_speed_gate import (
    CharacteristicSpeedProvenance,
    require_stage9_characteristic_speed,
    speed_fraction_for_correlation_length,
)


def test_luminal_stage9_speed_remains_allowed():
    require_stage9_characteristic_speed(C_KPC_PER_GYR)
    CandidateL2Parameters(tau_gyr=4.0)


def test_posthoc_subluminal_speed_is_blocked_without_provenance():
    with pytest.raises(RuntimeError):
        CandidateL2Parameters(tau_gyr=4.0, c_h_kpc_per_gyr=0.1 * C_KPC_PER_GYR)


def test_fully_independent_speed_provenance_can_pass_gate():
    provenance = CharacteristicSpeedProvenance(
        parent_action_derived=True,
        principal_symbol_documented=True,
        stability_checked=True,
        cherenkov_checked=True,
        observational_coupling_checked=True,
        frozen_before_halo_comparison=True,
    )
    params = CandidateL2Parameters(
        tau_gyr=4.0,
        c_h_kpc_per_gyr=0.9 * C_KPC_PER_GYR,
        speed_provenance=provenance,
    )
    assert params.c_h_kpc_per_gyr < C_KPC_PER_GYR


def test_galactic_correlation_length_requires_extreme_subluminality():
    frac_1gyr = speed_fraction_for_correlation_length(10.0, 1.0)
    frac_16gyr = speed_fraction_for_correlation_length(10.0, 16.0)
    assert 1e-5 < frac_1gyr < 1e-4
    assert 1e-6 < frac_16gyr < 1e-5
