#!/usr/bin/env python3
"""Synthetic validation of stationary H I interpolation rule v1.

Synthetic profiles only; no galaxy velocity, persistence quantity, or blind
outcome is read or evaluated.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from stationary_hi_profile_rule_v1 import evaluate_tabulated_profile


OUT = Path("validation/stationary/hi_interpolation_rule_v1_mock_validation.json")


def eval_profile(radii: list[float], sigma: list[float], radius: float) -> float:
    return evaluate_tabulated_profile(radii, sigma, radius).sigma


def trapz_mass(radii: list[float], sigma: list[float], n: int = 20_000) -> float:
    # 2*pi integral Sigma R dR over measured support, arbitrary consistent units.
    maximum = radii[-1]
    step = maximum / n
    total = 0.0
    for index in range(n):
        left = index * step
        right = (index + 1) * step
        f_left = eval_profile(radii, sigma, left) * left
        f_right = eval_profile(radii, sigma, right) * right
        total += (f_left + f_right) * 0.5 * step
    return 2 * math.pi * total


def main() -> None:
    tests: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        tests.append({"name": name, "pass": bool(passed), "detail": detail})

    radii = [1.0, 2.0, 4.0]
    sigma = [5.0, 9.0, 1.0]
    check("inner_constant", eval_profile(radii, sigma, 0.2) == 5.0)
    check(
        "node_exactness",
        all(eval_profile(radii, sigma, radius) == value for radius, value in zip(radii, sigma)),
    )
    check("linear_segment", abs(eval_profile(radii, sigma, 1.5) - 7.0) < 1e-12)
    check("outer_zero", eval_profile(radii, sigma, 4.01) == 0.0)
    check(
        "nonnegative_dense",
        min(eval_profile(radii, sigma, index * 0.001) for index in range(5001)) >= 0,
    )

    try:
        eval_profile([1, 1, 2], [1, 2, 3], 1.5)
        duplicate_rejected = False
    except ValueError:
        duplicate_rejected = True
    check("reject_duplicate_radius", duplicate_rejected)

    try:
        eval_profile([1, 2, 3], [1, -1, 2], 1.5)
        negative_rejected = False
    except ValueError:
        negative_rejected = True
    check("reject_negative_sigma", negative_rejected)

    constant_radii = [0.0, 2.0, 4.0]
    constant_sigma = [3.0, 3.0, 3.0]
    mass = trapz_mass(constant_radii, constant_sigma)
    exact_mass = math.pi * 3.0 * 4.0**2
    relative_error = abs(mass - exact_mass) / exact_mass
    check("constant_profile_mass", relative_error < 1e-8, f"relerr={relative_error:.3e}")

    result = {
        "status": "HI_INTERPOLATION_RULE_V1_MOCK_VALIDATED",
        "rule": {
            "interior": "piecewise_linear_in_surface_density_vs_radius",
            "inner": "constant_equal_first_measured_value_to_R0",
            "outer": "zero_beyond_last_measured_radius",
            "negative_sigma": "reject",
        },
        "n_tests": len(tests),
        "n_pass": sum(bool(test["pass"]) for test in tests),
        "all_pass": all(bool(test["pass"]) for test in tests),
        "tests": tests,
        "boundary": (
            "Synthetic numerical validation only; no L_A, C_A, tau_A, persistence "
            "prediction, or blind outcome evaluated."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
