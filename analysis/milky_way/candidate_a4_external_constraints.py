"""Candidate A4: external-constraint audit for the A0-A3 advected-state route.

A4 does not calibrate the Milky Way. It records which combinations of the
parent-theory parameter set can in principle be constrained by independent
observations and which remain non-identifiable until a complete cosmological
and matter-coupling solution is supplied.

The physical linear-response set inherited from A3 is

    Lambda_T^4      universal stress/curvature scale
    A_dyn           overall dynamical response
    r_lens          A_lens / A_dyn

plus the state-frame/aether kinetic coefficients.

Current external constraints strongly restrict tensor-wave speed and preferred-
frame effects in any Einstein-aether-like realization, and lensing/PPN constrain
observable metric slip.  However, because A2 deposits only when D_U T != 0,
static/comoving weak-field systems do not by themselves determine Lambda_T^4 or
A_dyn.  Those quantities remain blocked until a cosmological/background or
other independent dynamical calibration is derived from the parent theory.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class A4ConstraintStatus:
    tensor_speed_checked: bool = False
    preferred_frame_ppn_checked: bool = False
    strong_field_checked: bool = False
    equivalence_principle_checked: bool = False
    lensing_slip_checked: bool = False
    cosmological_background_solved: bool = False
    universal_stress_scale_fixed: bool = False
    dynamical_response_fixed: bool = False
    lensing_ratio_fixed: bool = False
    frozen_before_halo_comparison: bool = False

    @property
    def external_consistency_ready(self) -> bool:
        return all(
            [
                self.tensor_speed_checked,
                self.preferred_frame_ppn_checked,
                self.strong_field_checked,
                self.equivalence_principle_checked,
                self.lensing_slip_checked,
            ]
        )

    @property
    def normalization_ready(self) -> bool:
        return all(
            [
                self.cosmological_background_solved,
                self.universal_stress_scale_fixed,
                self.dynamical_response_fixed,
                self.lensing_ratio_fixed,
                self.frozen_before_halo_comparison,
            ]
        )

    @property
    def stage9_force_ready(self) -> bool:
        return self.external_consistency_ready and self.normalization_ready


def static_comoving_system_calibrates_a2_normalization(d_u_trace: float) -> bool:
    """Return whether a system can calibrate the A2 source normalization.

    A2 uses D_U T. A truly static/comoving system has D_U T = 0 and therefore
    supplies no source-amplitude calibration, even though it can still constrain
    metric coupling, preferred-frame behavior, or other aspects of the theory.
    """
    return float(d_u_trace) != 0.0


def require_a4_stage9_force_ready(status: A4ConstraintStatus) -> None:
    if status.stage9_force_ready:
        return
    missing = [k for k, v in status.__dict__.items() if not v]
    raise RuntimeError(
        "Candidate A4 blocks Stage 9 force generation until external consistency "
        "and normalization are independently closed. Missing: " + ", ".join(missing)
    )
