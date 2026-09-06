"""Candidate A1: minimal observable-metric coupling for the advected state.

This module does not fit or generate a Milky Way persistence force.  It records
the most general local algebraic isotropic effective metric that can be built
from the background metric g_{mu nu}, the unit timelike state-frame u_H^mu, and
a dimensionless persistent-state scalar q_H:

    g_eff_{mu nu} = C(q_H) g_{mu nu} + D(q_H) u^H_mu u^H_nu.

Around q_H=0,

    C(q_H) = 1 + 2 a q_H + O(q_H^2)
    D(q_H) = 2 b q_H + O(q_H^2).

For signature (-,+,+,+), weak fields, and a locally resting state-frame, the
linearized effective Newtonian-gauge potentials are

    Phi_eff = Phi_b + c^2 (a-b) q_H,
    Psi_eff = Psi_b - c^2 a q_H.

Thus non-relativistic dynamics and lensing depend on different combinations of
a and b.  Neither coefficient may be chosen from Delta-a, halo forces, orbit
weights, or lensing targets after exposure.  A one-parameter conformal or
pure-disformal truncation is a physical hypothesis with a fixed gravitational
slip prediction, not a neutral minimal choice.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class A1MetricCouplingProvenance:
    parent_action_derived: bool = False
    matter_metric_identified: bool = False
    q_normalization_fixed_without_halo_targets: bool = False
    linear_coefficients_derived: bool = False
    equivalence_principle_checked: bool = False
    solar_system_ppn_checked: bool = False
    lensing_slip_checked: bool = False
    gw_propagation_checked: bool = False
    cosmology_checked: bool = False
    frozen_before_halo_comparison: bool = False

    def missing_requirements(self) -> list[str]:
        values = {
            "parent_action_derived": self.parent_action_derived,
            "matter_metric_identified": self.matter_metric_identified,
            "q_normalization_fixed_without_halo_targets": self.q_normalization_fixed_without_halo_targets,
            "linear_coefficients_derived": self.linear_coefficients_derived,
            "equivalence_principle_checked": self.equivalence_principle_checked,
            "solar_system_ppn_checked": self.solar_system_ppn_checked,
            "lensing_slip_checked": self.lensing_slip_checked,
            "gw_propagation_checked": self.gw_propagation_checked,
            "cosmology_checked": self.cosmology_checked,
            "frozen_before_halo_comparison": self.frozen_before_halo_comparison,
        }
        return [name for name, ok in values.items() if not ok]

    @property
    def force_ready(self) -> bool:
        return not self.missing_requirements()


def require_a1_metric_coupling_ready(provenance: A1MetricCouplingProvenance) -> None:
    missing = provenance.missing_requirements()
    if missing:
        raise RuntimeError(
            "Candidate A1 observable metric coupling is not theory-closed. Missing: "
            + ", ".join(missing)
        )


def weak_field_potential_shifts(q_h: np.ndarray, a: float, b: float, c_kms: float = 299792.458):
    """Return (delta_Phi, delta_Psi) in (km/s)^2 for diagnostic algebra only.

    This helper is intentionally coefficient-explicit.  Stage 9 must not infer
    a or b from Milky Way force/lensing targets.  q_h is dimensionless and its
    normalization must be independently fixed by the parent theory.
    """
    q = np.asarray(q_h, dtype=float)
    c2 = float(c_kms) ** 2
    return c2 * (float(a) - float(b)) * q, -c2 * float(a) * q


def nonrelativistic_acceleration_shift(grad_q_per_kpc: np.ndarray, a: float, b: float, c_kms: float = 299792.458):
    """Return -grad(delta Phi) for diagnostic algebra only.

    Output units are (km/s)^2/kpc when grad_q_per_kpc is in 1/kpc.
    """
    grad = np.asarray(grad_q_per_kpc, dtype=float)
    return -(float(c_kms) ** 2) * (float(a) - float(b)) * grad


def lensing_potential_shift(q_h: np.ndarray, a: float, b: float, c_kms: float = 299792.458):
    """Return delta(Phi+Psi), the weak-field lensing-potential shift."""
    dphi, dpsi = weak_field_potential_shifts(q_h, a=a, b=b, c_kms=c_kms)
    return dphi + dpsi
