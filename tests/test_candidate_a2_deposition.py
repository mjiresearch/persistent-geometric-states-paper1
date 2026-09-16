import numpy as np
import pytest

from analysis.milky_way.candidate_a2_deposition import (
    A2DepositionProvenance,
    dimensionless_trace_derivative_source,
    require_a2_deposition_ready,
    static_source_gives_zero_deposition,
)


def test_a2_blocks_without_parent_theory_normalization():
    with pytest.raises(RuntimeError):
        require_a2_deposition_ready(A2DepositionProvenance())


def test_static_source_has_zero_deposition():
    x = np.array([1.0, 2.0, 3.0])
    out = static_source_gives_zero_deposition(x, tau_gyr=4.0, trace_scale=2.0, kappa_q=1.0)
    np.testing.assert_allclose(out, 0.0)


def test_trace_derivative_source_is_linear_and_dimensionally_closed():
    dTdt = np.array([2.0, -4.0])
    out = dimensionless_trace_derivative_source(dTdt, tau_gyr=3.0, trace_scale=6.0, kappa_q=2.0)
    np.testing.assert_allclose(out, np.array([2.0, -4.0]))


def test_trace_scale_must_be_nonzero():
    with pytest.raises(ValueError):
        dimensionless_trace_derivative_source(np.array([1.0]), 1.0, 0.0, 1.0)
