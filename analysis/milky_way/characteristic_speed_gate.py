"""Characteristic-speed admissibility gate for Stage 9 persistence candidates.

The first exposed Candidate L2 run fixed c_H=c.  Because the checked-in parent
theory does not yet derive a slower persistence-mode speed, post-hoc subluminal
speed sweeps are blocked until an independent parent-action derivation and
external-consistency audit are supplied.
"""
from __future__ import annotations

from dataclasses import dataclass

from analysis.milky_way.candidate_l0 import C_KPC_PER_GYR


@dataclass(frozen=True)
class CharacteristicSpeedProvenance:
    parent_action_derived: bool = False
    principal_symbol_documented: bool = False
    stability_checked: bool = False
    cherenkov_checked: bool = False
    observational_coupling_checked: bool = False
    frozen_before_halo_comparison: bool = False

    @property
    def admissible_for_subluminal_stage9(self) -> bool:
        return all(
            (
                self.parent_action_derived,
                self.principal_symbol_documented,
                self.stability_checked,
                self.cherenkov_checked,
                self.observational_coupling_checked,
                self.frozen_before_halo_comparison,
            )
        )


def require_stage9_characteristic_speed(
    c_h_kpc_per_gyr: float,
    provenance: CharacteristicSpeedProvenance | None = None,
) -> None:
    """Allow c_H=c; block c_H<c unless independently derived and audited."""
    c_h = float(c_h_kpc_per_gyr)
    if not (0.0 < c_h <= C_KPC_PER_GYR * (1.0 + 1e-12)):
        raise ValueError("Stage 9 requires 0 < c_H <= c")
    if abs(c_h - C_KPC_PER_GYR) <= 1e-10 * C_KPC_PER_GYR:
        return
    if provenance is None or not provenance.admissible_for_subluminal_stage9:
        raise RuntimeError(
            "Subluminal Stage 9 c_H sweep blocked: the checked-in parent theory does "
            "not yet derive this speed independently of the exposed Milky Way target. "
            "Provide parent-action/principal-symbol derivation, stability, Cherenkov, "
            "observational-coupling checks, and freeze the speed prior before comparison."
        )


def speed_fraction_for_correlation_length(length_kpc: float, tau_gyr: float) -> float:
    """Diagnostic only: c_H/c required for ell_H=c_H tau."""
    length = float(length_kpc)
    tau = float(tau_gyr)
    if length <= 0.0 or tau <= 0.0:
        raise ValueError("length_kpc and tau_gyr must be positive")
    return length / (tau * C_KPC_PER_GYR)
