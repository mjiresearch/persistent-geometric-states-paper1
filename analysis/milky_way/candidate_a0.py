"""Candidate A0: covariant advected persistent-state scaffold.

A0 represents a persistent state transported along a timelike state-frame
congruence u_H rather than a freely propagating slow gravitational-wave mode.

This module intentionally does not provide an observable force law.  It only
encodes the theory provenance requirements and the weak-field advective-
relaxation characteristic solution.  Halo targets are not inputs.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class A0TheoryProvenance:
    parent_action_documented: bool = False
    unit_timelike_constraint_derived: bool = False
    state_frame_equation_derived: bool = False
    local_deposition_invariant_derived: bool = False
    observable_metric_coupling_derived: bool = False
    normalization_fixed_without_halo_targets: bool = False
    stability_checked: bool = False
    preferred_frame_ppn_checked: bool = False
    cherenkov_checked: bool = False
    gw_constraints_checked: bool = False
    cosmology_checked: bool = False
    frozen_before_halo_comparison: bool = False

    def missing_requirements(self) -> list[str]:
        labels = {
            "parent_action_documented": self.parent_action_documented,
            "unit_timelike_constraint_derived": self.unit_timelike_constraint_derived,
            "state_frame_equation_derived": self.state_frame_equation_derived,
            "local_deposition_invariant_derived": self.local_deposition_invariant_derived,
            "observable_metric_coupling_derived": self.observable_metric_coupling_derived,
            "normalization_fixed_without_halo_targets": self.normalization_fixed_without_halo_targets,
            "stability_checked": self.stability_checked,
            "preferred_frame_ppn_checked": self.preferred_frame_ppn_checked,
            "cherenkov_checked": self.cherenkov_checked,
            "gw_constraints_checked": self.gw_constraints_checked,
            "cosmology_checked": self.cosmology_checked,
            "frozen_before_halo_comparison": self.frozen_before_halo_comparison,
        }
        return [k for k, ok in labels.items() if not ok]

    @property
    def force_ready(self) -> bool:
        return not self.missing_requirements()


def require_a0_force_ready(provenance: A0TheoryProvenance) -> None:
    missing = provenance.missing_requirements()
    if missing:
        raise RuntimeError(
            "Candidate A0 force generation blocked until parent theory is independently "
            "closed. Missing: " + ", ".join(missing)
        )


def advected_relaxation_step(
    q0: np.ndarray,
    source: np.ndarray,
    dt_gyr: float,
    tau_gyr: float,
) -> np.ndarray:
    """Exact constant-source update along one state-frame characteristic.

    Solves dq/dt + q/tau = source for a characteristic segment.  This evolves
    the persistent state only; it is not a gravitational acceleration mapping.
    """
    dt = float(dt_gyr)
    tau = float(tau_gyr)
    if dt < 0.0:
        raise ValueError("dt_gyr must be non-negative")
    if tau <= 0.0:
        raise ValueError("tau_gyr must be positive")
    q = np.asarray(q0, dtype=float)
    s = np.asarray(source, dtype=float)
    decay = np.exp(-dt / tau)
    return q * decay + s * tau * (1.0 - decay)


def advect_points(xyz_kpc: np.ndarray, velocity_kpc_per_gyr: np.ndarray, dt_gyr: float) -> np.ndarray:
    """Kinematic weak-field characteristic transport x -> x + v_H dt.

    The velocity supplied here is a theory/input diagnostic only.  Stage 9 must
    not infer it from halo or residual-force targets.
    """
    xyz = np.asarray(xyz_kpc, dtype=float)
    vel = np.asarray(velocity_kpc_per_gyr, dtype=float)
    if xyz.shape[-1] != 3 or vel.shape[-1] != 3:
        raise ValueError("xyz and velocity must end in dimension 3")
    return xyz + vel * float(dt_gyr)
