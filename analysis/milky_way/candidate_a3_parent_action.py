"""Candidate A3: parent-action reduction for the advected persistence route.

A3 records two theory facts:

1. The first-order dissipative A0 equation requires an auxiliary/response field
   (or an equivalent doubled/open-system description) at action level.
2. At linear order, q-field rescaling makes beta, a, and b individually
   convention-dependent.  The physical combinations are beta(a-b) and beta b,
   together with the universal trace/stress scale Lambda_T^4.

This module does not generate Milky Way forces.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class A3PhysicalParameters:
    trace_scale: float
    beta: float
    conformal_a: float
    disformal_b: float

    def __post_init__(self) -> None:
        if self.trace_scale == 0.0:
            raise ValueError("trace_scale must be nonzero")

    @property
    def dynamic_response(self) -> float:
        return float(self.beta) * (float(self.conformal_a) - float(self.disformal_b))

    @property
    def lensing_response(self) -> float:
        return float(self.beta) * float(self.disformal_b)

    @property
    def lensing_to_dynamics_ratio(self) -> float:
        dyn = self.dynamic_response
        if dyn == 0.0:
            raise ZeroDivisionError("dynamic_response is zero")
        return self.lensing_response / dyn

    def rescaled_field_convention(self, zeta: float) -> "A3PhysicalParameters":
        """Return parameters after q -> zeta q, p -> p/zeta.

        The physical response combinations remain invariant when
        beta -> zeta beta and a,b -> a/zeta,b/zeta.
        """
        z = float(zeta)
        if z == 0.0:
            raise ValueError("zeta must be nonzero")
        return A3PhysicalParameters(
            trace_scale=self.trace_scale,
            beta=z * self.beta,
            conformal_a=self.conformal_a / z,
            disformal_b=self.disformal_b / z,
        )


@dataclass(frozen=True)
class A3TheoryProvenance:
    auxiliary_or_open_system_derived: bool = False
    trace_scale_fixed_independently: bool = False
    dynamic_response_fixed_independently: bool = False
    lensing_ratio_fixed_independently: bool = False
    state_frame_sector_closed: bool = False
    stability_checked: bool = False
    ppn_equivalence_checked: bool = False
    lensing_checked: bool = False
    gw_checked: bool = False
    cosmology_checked: bool = False
    frozen_before_halo_comparison: bool = False

    @property
    def force_ready(self) -> bool:
        return all(self.__dict__.values())


def require_a3_force_ready(provenance: A3TheoryProvenance) -> None:
    if not provenance.force_ready:
        missing = [k for k, ok in provenance.__dict__.items() if not ok]
        raise RuntimeError("Candidate A3 force generation blocked. Missing: " + ", ".join(missing))
