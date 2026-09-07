"""Candidate A2: local covariant deposition gate for the advected persistent state.

A2 does not choose a Milky-Way-fitted source amplitude.  It records the lowest-
order scalar deposition family compatible with the Stage-9 guardrail that a
static/comoving baryonic configuration must not continuously regenerate the
persistent state.

For pressureless matter, T ~= -rho c^2.  A local scalar source may therefore be
built from the derivative of the trace along the state-frame congruence,

    D_U T = u_H^mu nabla_mu T,

or equivalently from D_U rho_b in the weak-field nonrelativistic limit.

To evolve a dimensionless q_H through

    D_U q_H + q_H/tau = S_q,

one convenient dimensionally closed form is

    S_q = kappa_q * tau * D_U(T/T_star),

where T_star is a universal parent-theory stress/curvature scale and kappa_q is
a universal dimensionless coefficient.  Neither may be chosen from Delta a(R),
halo fits, orbit weights, or galaxy-specific scales.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class A2DepositionProvenance:
    parent_action_derived: bool = False
    source_invariant_derived: bool = False
    universal_scale_derived: bool = False
    dimensionless_coupling_derived: bool = False
    static_source_zero_proven: bool = False
    equivalence_principle_checked: bool = False
    cosmology_checked: bool = False
    frozen_before_halo_comparison: bool = False

    @property
    def ready(self) -> bool:
        return all(self.__dict__.values())


def require_a2_deposition_ready(p: A2DepositionProvenance) -> None:
    if not p.ready:
        missing = [k for k, v in p.__dict__.items() if not v]
        raise RuntimeError("Candidate A2 deposition blocked. Missing: " + ", ".join(missing))


def dimensionless_trace_derivative_source(
    d_trace_dt_state_frame: np.ndarray,
    tau_gyr: float,
    trace_scale: float,
    kappa_q: float,
) -> np.ndarray:
    """Return S_q = kappa_q * tau * D_U(T/T_star).

    Units of d_trace_dt_state_frame and trace_scale must be consistent apart from
    the time derivative, so the result has units 1/time as required by the A0
    first-order relaxation equation for dimensionless q_H.
    """
    tau = float(tau_gyr)
    scale = float(trace_scale)
    if tau <= 0.0:
        raise ValueError("tau_gyr must be positive")
    if not np.isfinite(scale) or scale == 0.0:
        raise ValueError("trace_scale must be finite and nonzero")
    return float(kappa_q) * tau * np.asarray(d_trace_dt_state_frame, dtype=float) / scale


def static_source_gives_zero_deposition(trace_value: np.ndarray, tau_gyr: float, trace_scale: float, kappa_q: float) -> np.ndarray:
    """Diagnostic: a static/comoving trace has D_U T=0 and therefore S_q=0."""
    arr = np.asarray(trace_value, dtype=float)
    return dimensionless_trace_derivative_source(np.zeros_like(arr), tau_gyr, trace_scale, kappa_q)
