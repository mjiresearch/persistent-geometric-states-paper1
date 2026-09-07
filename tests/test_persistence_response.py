import pytest

from analysis.milky_way.persistence_response import (
    ResponseLawSpecification,
    manuscript_current_status,
    require_admissible_response,
)


def test_current_manuscript_status_blocks_force_generation():
    spec = manuscript_current_status()
    assert not spec.admissible
    errors = spec.admissibility_errors()
    assert "transport equation is not documented" in errors
    assert "hereditary deposition law is not documented" in errors
    assert "inherited/contemporary interaction law is not documented" in errors
    assert "normalization is not fixed independently of halo targets" in errors
    with pytest.raises(RuntimeError, match="Stage 9 acceleration generation blocked"):
        require_admissible_response(spec)


def test_second_poisson_field_is_rejected():
    spec = ResponseLawSpecification(
        name="invalid_second_poisson",
        causal=True,
        finite_relaxation=True,
        independent_initial_data=True,
        static_source_duplicates_poisson=True,
        gr_recovery=True,
        interaction_vanishes_without_either_sector=True,
        universal_not_galaxy_fitted=True,
        transport_equation_documented=True,
        deposition_law_documented=True,
        interaction_law_documented=True,
        normalization_fixed_without_halo_targets=True,
    )
    assert not spec.admissible
    assert any("duplicate Poisson" in e for e in spec.admissibility_errors())


def test_fully_declared_universal_law_can_pass_gate():
    spec = ResponseLawSpecification(
        name="fully_declared_example",
        causal=True,
        finite_relaxation=True,
        independent_initial_data=True,
        static_source_duplicates_poisson=False,
        gr_recovery=True,
        interaction_vanishes_without_either_sector=True,
        universal_not_galaxy_fitted=True,
        transport_equation_documented=True,
        deposition_law_documented=True,
        interaction_law_documented=True,
        normalization_fixed_without_halo_targets=True,
    )
    assert spec.admissible
    require_admissible_response(spec)
