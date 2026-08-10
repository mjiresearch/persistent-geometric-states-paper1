"""Referee-driven admissibility gate for Stage 9 persistence models.

The gate encodes the conceptual corrections required by the referee report on
"Finite-Memory Gravitational Response from Retarded Green-Function Tails".
It deliberately distinguishes an effective hereditary modification from an
exact reformulation of GR.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RefereeTheoryProvenance:
    effective_modification_acknowledged: bool
    einstein_source_retained_in_gr_limit: bool
    auxiliary_initial_data_declared: bool
    auxiliary_constraints_declared: bool
    source_or_relaxation_law_frozen: bool
    observable_metric_coupling_frozen: bool
    normalization_frozen_externally: bool
    state_frame_evolution_frozen: bool
    exact_tail_derivation_claimed: bool = False
    exact_tail_derivation_provided: bool = False
    precision_cosmology_claimed: bool = False
    full_linear_cosmology_done: bool = False
    gw_dispersion_claimed: bool = False
    gw_dispersion_derived: bool = False
    target_exposed_parameter_selection: bool = False


def referee_gate_failures(p: RefereeTheoryProvenance) -> list[str]:
    failures: list[str] = []

    if not p.effective_modification_acknowledged:
        failures.append("model must be identified as an effective modification, not an exact GR reformulation")
    if not p.einstein_source_retained_in_gr_limit:
        failures.append("ordinary Einstein source term must remain present in the GR limit")
    if not p.auxiliary_initial_data_declared:
        failures.append("auxiliary/history-state initial data or retarded prescription must be declared")
    if not p.auxiliary_constraints_declared:
        failures.append("auxiliary/history-state constraints and state-space role must be declared")
    if not p.source_or_relaxation_law_frozen:
        failures.append("source/curvature-relaxation law must be frozen")
    if not p.observable_metric_coupling_frozen:
        failures.append("observable metric coupling must be frozen")
    if not p.normalization_frozen_externally:
        failures.append("normalization must be fixed independently of exposed Galactic targets")
    if not p.state_frame_evolution_frozen:
        failures.append("state-frame evolution law must be frozen")
    if p.exact_tail_derivation_claimed and not p.exact_tail_derivation_provided:
        failures.append("cannot claim the effective exponential kernel is derived from exact GR tails without a derivation")
    if p.precision_cosmology_claimed and not p.full_linear_cosmology_done:
        failures.append("precision cosmology claims require a full linear perturbation treatment")
    if p.gw_dispersion_claimed and not p.gw_dispersion_derived:
        failures.append("GW dispersion claims require an explicit derivation from the linearized effective equations")
    if p.target_exposed_parameter_selection:
        failures.append("parameters may not be selected from Portail17/Hunter24, Delta-a, orbit weights, SPARC, or other exposed halo targets")

    return failures


def assert_referee_admissible(p: RefereeTheoryProvenance) -> None:
    failures = referee_gate_failures(p)
    if failures:
        raise ValueError("Stage 9 referee gate failed: " + "; ".join(failures))
