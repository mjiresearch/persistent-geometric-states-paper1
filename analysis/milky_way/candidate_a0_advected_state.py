"""Candidate A0 scaffold: advected persistent-state transport.

This is a theory scaffold, not yet an admissible force-generating Stage 9 model.
It represents the distinct possibility that the hereditary geometric state is
carried by a dynamical timelike state-frame congruence rather than behaving as a
freely propagating slow gravitational radiation mode.

The minimal transport form is

    D_U Q_H + Q_H / tau = S_H,

where

    D_U = u_H^mu nabla_mu

is the derivative along the persistent-state congruence.  In a weak-field local
frame this becomes approximately

    (partial_t + v_H . grad) Q_H + Q_H/tau = S_H.

This should not be interpreted as assigning a gravitational-wave
characteristic speed |v_H|.  The state is advected along a timelike congruence;
causal creation/coupling of the state still has to follow from a completed
covariant parent theory.

No Milky Way halo target is used here.  No force normalization is supplied.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AdvectedStateSpecification:
    tau_gyr: float
    parent_action_derived: bool = False
    state_frame_dynamics_derived: bool = False
    deposition_law_derived: bool = False
    observable_metric_coupling_derived: bool = False
    stability_checked: bool = False
    causality_checked: bool = False
    frozen_before_halo_comparison: bool = True

    def __post_init__(self) -> None:
        if float(self.tau_gyr) <= 0.0:
            raise ValueError("tau_gyr must be positive")

    @property
    def admissible_for_force_generation(self) -> bool:
        return all(
            [
                self.parent_action_derived,
                self.state_frame_dynamics_derived,
                self.deposition_law_derived,
                self.observable_metric_coupling_derived,
                self.stability_checked,
                self.causality_checked,
                self.frozen_before_halo_comparison,
            ]
        )


def advective_material_derivative(
    partial_t_field: np.ndarray,
    gradient_field: np.ndarray,
    state_frame_velocity: np.ndarray,
) -> np.ndarray:
    """Return weak-field D_U q = partial_t q + v_H dot grad q.

    This helper only encodes kinematics.  It does not specify what persistent
    variable q is, what deposits it, or how it affects the observable metric.
    """
    dt = np.asarray(partial_t_field, dtype=float)
    grad = np.asarray(gradient_field, dtype=float)
    vel = np.asarray(state_frame_velocity, dtype=float)
    if grad.shape[-1] != 3 or vel.shape[-1] != 3:
        raise ValueError("gradient_field and state_frame_velocity must end in dimension 3")
    return dt + np.sum(vel * grad, axis=-1)


def require_advected_state_theory_closure(spec: AdvectedStateSpecification) -> None:
    if not spec.admissible_for_force_generation:
        raise RuntimeError(
            "Candidate A0 is a theory scaffold only. Force generation is blocked until "
            "the parent action, state-frame dynamics, deposition law, observable metric "
            "coupling, stability and causality are independently derived."
        )
