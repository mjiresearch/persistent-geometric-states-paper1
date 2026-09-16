import pytest

from analysis.milky_way.referee_theory_gate import (
    RefereeTheoryProvenance,
    assert_referee_admissible,
    referee_gate_failures,
)


def valid_provenance(**overrides):
    base = dict(
        effective_modification_acknowledged=True,
        einstein_source_retained_in_gr_limit=True,
        auxiliary_initial_data_declared=True,
        auxiliary_constraints_declared=True,
        source_or_relaxation_law_frozen=True,
        observable_metric_coupling_frozen=True,
        normalization_frozen_externally=True,
        state_frame_evolution_frozen=True,
    )
    base.update(overrides)
    return RefereeTheoryProvenance(**base)


def test_effective_model_can_pass_gate():
    assert_referee_admissible(valid_provenance())


def test_exact_gr_reformulation_claim_is_rejected_for_modified_phenomenology():
    failures = referee_gate_failures(
        valid_provenance(effective_modification_acknowledged=False)
    )
    assert any("effective modification" in f for f in failures)


def test_bad_gr_limit_is_rejected():
    failures = referee_gate_failures(
        valid_provenance(einstein_source_retained_in_gr_limit=False)
    )
    assert any("Einstein source" in f for f in failures)


def test_unproved_exact_tail_claim_is_rejected():
    failures = referee_gate_failures(
        valid_provenance(
            exact_tail_derivation_claimed=True,
            exact_tail_derivation_provided=False,
        )
    )
    assert any("exact GR tails" in f for f in failures)


def test_precision_cosmology_requires_full_linear_treatment():
    failures = referee_gate_failures(
        valid_provenance(
            precision_cosmology_claimed=True,
            full_linear_cosmology_done=False,
        )
    )
    assert any("full linear perturbation" in f for f in failures)


def test_gw_dispersion_requires_derivation():
    failures = referee_gate_failures(
        valid_provenance(gw_dispersion_claimed=True, gw_dispersion_derived=False)
    )
    assert any("GW dispersion" in f for f in failures)


def test_target_exposed_parameter_selection_is_rejected():
    with pytest.raises(ValueError):
        assert_referee_admissible(
            valid_provenance(target_exposed_parameter_selection=True)
        )
