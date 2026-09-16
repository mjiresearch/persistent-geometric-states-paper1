"""Admissibility interface for the Stage 9 persistence response law.

This module intentionally does not define a force kernel.  The checked-in
manuscript specifies that the persistent state H_{mu nu} is an independently
evolving hereditary sector and explicitly forbids treating it as a second
instantaneous Poisson field sourced by static baryons.  It also states that the
observable residual may contain both inherited and interaction terms.

Until the transport/deposition/interaction equations and their universal
couplings are supplied independently of halo targets, acceleration generation
must remain blocked.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class ResponseLawSpecification:
    name: str
    causal: bool
    finite_relaxation: bool
    independent_initial_data: bool
    static_source_duplicates_poisson: bool
    gr_recovery: bool
    interaction_vanishes_without_either_sector: bool
    universal_not_galaxy_fitted: bool
    transport_equation_documented: bool
    deposition_law_documented: bool
    interaction_law_documented: bool
    normalization_fixed_without_halo_targets: bool

    def admissibility_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.causal:
            errors.append("persistence propagation is not causal")
        if not self.finite_relaxation:
            errors.append("finite relaxation is not enforced")
        if not self.independent_initial_data:
            errors.append("persistent sector lacks independent initial data")
        if self.static_source_duplicates_poisson:
            errors.append("static matter is treated as a duplicate Poisson source")
        if not self.gr_recovery:
            errors.append("continuous GR recovery is not demonstrated")
        if not self.interaction_vanishes_without_either_sector:
            errors.append("interaction does not vanish when either sector is absent")
        if not self.universal_not_galaxy_fitted:
            errors.append("response law is galaxy-specific or target-fitted")
        if not self.transport_equation_documented:
            errors.append("transport equation is not documented")
        if not self.deposition_law_documented:
            errors.append("hereditary deposition law is not documented")
        if not self.interaction_law_documented:
            errors.append("inherited/contemporary interaction law is not documented")
        if not self.normalization_fixed_without_halo_targets:
            errors.append("normalization is not fixed independently of halo targets")
        return errors

    @property
    def admissible(self) -> bool:
        return not self.admissibility_errors()


class PersistenceResponseLaw(Protocol):
    """Protocol that a future universal persistence response implementation must satisfy."""

    specification: ResponseLawSpecification

    def acceleration(
        self,
        evaluation_xyz_kpc: np.ndarray,
        source_xyz_kpc: np.ndarray,
        source_weights: np.ndarray,
        present_baryonic_context: object | None = None,
    ) -> np.ndarray:
        ...


def require_admissible_response(specification: ResponseLawSpecification) -> None:
    errors = specification.admissibility_errors()
    if errors:
        raise RuntimeError(
            "Stage 9 acceleration generation blocked: response law is not independently "
            "specified and admissible. " + "; ".join(errors)
        )


def manuscript_current_status() -> ResponseLawSpecification:
    """Encode what the current checked-in manuscript actually supplies.

    The conceptual requirements are present, but the explicit transport,
    deposition, interaction and independently frozen normalization are not yet
    present in the checked-in revision.  Therefore this specification is
    deliberately inadmissible for force generation.
    """
    return ResponseLawSpecification(
        name="current_manuscript_requirements_only",
        causal=True,
        finite_relaxation=True,
        independent_initial_data=True,
        static_source_duplicates_poisson=False,
        gr_recovery=True,
        interaction_vanishes_without_either_sector=True,
        universal_not_galaxy_fitted=True,
        transport_equation_documented=False,
        deposition_law_documented=False,
        interaction_law_documented=False,
        normalization_fixed_without_halo_targets=False,
    )
