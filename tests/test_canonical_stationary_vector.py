import numpy as np

from analysis.milky_way.canonical_stationary_vector import (
    SpectralGrid,
    exponential_vertical_form_factor,
    solve_cold_disk,
    solve_prescribed_current,
)


def toy_disk():
    R = np.linspace(0.2, 12.0, 120)
    Sigma = np.exp(-R / 2.6)
    Vb = 120.0 * (1.0 - np.exp(-R / 1.8)) + 10.0
    grid = SpectralGrid(k_min=2e-3, k_max=40.0, n_k=700)
    return R, Sigma, Vb, grid


def test_vertical_form_factor_thin_limit():
    kappa = np.array([0.1, 1.0, 10.0])
    assert np.allclose(exponential_vertical_form_factor(kappa, 0.0), 1.0)


def test_vertical_form_factor_suppresses_high_k():
    kappa = np.array([0.1, 1.0, 10.0])
    f = exponential_vertical_form_factor(kappa, 0.3)
    assert np.all(f > 0)
    assert np.all(f <= 1)
    assert f[2] < f[1] < f[0]


def test_zero_coupling_returns_baryonic_curve():
    R, Sigma, Vb, grid = toy_disk()
    out = solve_cold_disk(R, Sigma, Vb, L_A=6.0, C_A=0.0, grid=grid, h_z=0.3)
    assert out.converged
    assert np.allclose(out.velocity, Vb, rtol=1e-10, atol=1e-10)
    assert out.equation_residual < 1e-10


def test_prescribed_zero_current_returns_baryonic_curve():
    R, Sigma, Vb, grid = toy_disk()
    got = solve_prescribed_current(
        R, Vb, np.zeros_like(R), L_A=6.0, C_A=1.0, grid=grid, h_z=0.3
    )
    assert np.allclose(got, Vb)


def test_small_coupling_converges_and_satisfies_equation():
    R, Sigma, Vb, grid = toy_disk()
    out = solve_cold_disk(
        R,
        Sigma,
        Vb,
        L_A=6.0,
        C_A=1e-4,
        grid=grid,
        h_z=0.3,
        relaxation=0.3,
        tol_iter=2e-6,
        tol_res=2e-6,
    )
    assert out.converged
    assert np.all(np.isfinite(out.velocity))
    assert np.all(out.velocity >= 0)
    assert out.equation_residual < 2e-6
