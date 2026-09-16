"""Canonical stationary vector-current disk solver from Section 10.

This module implements the manuscript equations without fitting any target data.
It supports a prescribed current profile or the cold-disk self-consistent closure
J_b(R)=Sigma_b(R)V(R). Numerical regularization is explicit and configurable.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.integrate import simpson
from scipy.special import j0, j1


@dataclass(frozen=True)
class SpectralGrid:
    k_min: float
    k_max: float
    n_k: int = 2048

    def values(self) -> np.ndarray:
        if self.k_min <= 0 or self.k_max <= self.k_min or self.n_k < 64:
            raise ValueError("invalid spectral grid")
        return np.geomspace(self.k_min, self.k_max, self.n_k)


def exponential_vertical_form_factor(kappa: np.ndarray, h_z: float) -> np.ndarray:
    """F_z for f_z=exp(-|z|/h_z)/(2 h_z): F_z = 1/(1+kappa h_z)."""
    if h_z < 0:
        raise ValueError("h_z must be non-negative")
    if h_z == 0:
        return np.ones_like(kappa)
    return 1.0 / (1.0 + kappa * h_z)


def transformed_current(R: np.ndarray, J: np.ndarray, k: np.ndarray) -> np.ndarray:
    R = np.asarray(R, float)
    J = np.asarray(J, float)
    k = np.asarray(k, float)
    if R.ndim != 1 or J.shape != R.shape or np.any(R <= 0):
        raise ValueError("R and J must be matching 1D arrays with R>0")
    x = np.outer(k, R)
    return simpson(j1(x) * (R * J)[None, :], x=R, axis=1)


def field_functional_spectral(
    R: np.ndarray,
    Sigma: np.ndarray,
    V_source: np.ndarray,
    L_A: float,
    grid: SpectralGrid,
    h_z: float = 0.0,
) -> np.ndarray:
    """Return B_A[V](R) excluding the universal amplitude G_A/C_A.

    Implements the Section 10 spectral sequence
      J_b -> Jtilde -> F_z -> integral k^2 J0(kR)/kappa * F_z * Jtilde.
    With the cold-disk closure J_b=Sigma*V_source.
    """
    if L_A <= 0:
        raise ValueError("L_A must be positive")
    R = np.asarray(R, float)
    Sigma = np.asarray(Sigma, float)
    V_source = np.asarray(V_source, float)
    if Sigma.shape != R.shape or V_source.shape != R.shape:
        raise ValueError("R, Sigma and V_source must match")

    k = grid.values()
    kappa = np.sqrt(k * k + L_A ** -2)
    Jtilde = transformed_current(R, Sigma * V_source, k)
    Fz = exponential_vertical_form_factor(kappa, h_z)
    integrand_prefactor = (k * k / kappa) * Fz * Jtilde
    kernel_R = j0(np.outer(R, k)) * integrand_prefactor[None, :]
    return simpson(kernel_R, x=k, axis=1)


@dataclass
class SolverResult:
    velocity: np.ndarray
    field: np.ndarray
    iterations: int
    converged: bool
    iterate_error: float
    equation_residual: float


def solve_cold_disk(
    R: np.ndarray,
    Sigma: np.ndarray,
    V_b: np.ndarray,
    L_A: float,
    C_A: float,
    grid: SpectralGrid,
    *,
    h_z: float = 0.0,
    relaxation: float = 0.35,
    tol_iter: float = 1e-6,
    tol_res: float = 1e-6,
    max_iter: int = 300,
    epsilon_v: float = 1e-12,
) -> SolverResult:
    """Solve manuscript Eq. (nonlinear Fredholm cold-disk closure).

    Units are caller-consistent. C_A must carry the corresponding length/mass
    dimensions required by the manuscript. No parameter calibration occurs here.
    """
    R = np.asarray(R, float)
    Sigma = np.asarray(Sigma, float)
    V_b = np.asarray(V_b, float)
    if not (R.ndim == Sigma.ndim == V_b.ndim == 1 and R.shape == Sigma.shape == V_b.shape):
        raise ValueError("R, Sigma, V_b must be matching 1D arrays")
    if np.any(R <= 0) or np.any(V_b < 0) or not (0 < relaxation <= 1):
        raise ValueError("invalid physical/numerical inputs")

    V = V_b.copy()
    last_field = np.zeros_like(V)
    iterate_error = np.inf

    for n in range(1, max_iter + 1):
        B = field_functional_spectral(R, Sigma, V, L_A, grid, h_z=h_z)
        X = R * C_A * B
        radicand = X * X + 4.0 * V_b * V_b
        V_hat = 0.5 * (X + np.sqrt(np.maximum(radicand, 0.0)))
        V_new = (1.0 - relaxation) * V + relaxation * V_hat
        iterate_error = float(np.max(np.abs(V_new - V) / (np.abs(V) + epsilon_v)))
        V = V_new
        last_field = B
        if iterate_error < tol_iter:
            break

    # Recompute at final state and check original nonlinear equation.
    last_field = field_functional_spectral(R, Sigma, V, L_A, grid, h_z=h_z)
    residual = V * V - V_b * V_b - R * C_A * V * last_field
    denom = V * V + V_b * V_b + epsilon_v
    equation_residual = float(np.max(np.abs(residual) / denom))
    converged = bool(iterate_error < tol_iter and equation_residual < tol_res)
    return SolverResult(V, last_field, n, converged, iterate_error, equation_residual)


def solve_prescribed_current(
    R: np.ndarray,
    V_b: np.ndarray,
    J_b: np.ndarray,
    L_A: float,
    C_A: float,
    grid: SpectralGrid,
    *,
    h_z: float = 0.0,
) -> np.ndarray:
    """Positive physical branch when baryonic streaming current is prescribed."""
    R = np.asarray(R, float)
    V_b = np.asarray(V_b, float)
    J_b = np.asarray(J_b, float)
    k = grid.values()
    kappa = np.sqrt(k * k + L_A ** -2)
    Jtilde = transformed_current(R, J_b, k)
    Fz = exponential_vertical_form_factor(kappa, h_z)
    B = simpson(j0(np.outer(R, k)) * ((k*k/kappa)*Fz*Jtilde)[None, :], x=k, axis=1)
    X = R * C_A * B
    return 0.5 * (X + np.sqrt(X*X + 4.0 * V_b*V_b))
