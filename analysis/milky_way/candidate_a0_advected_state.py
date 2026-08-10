"""Compatibility shim for the canonical Candidate A0 interface.

New Stage 9 work should import :mod:`analysis.milky_way.candidate_a0`.  This file
is retained temporarily so earlier branch references do not break while the
advected-state route is consolidated.
"""
from analysis.milky_way.candidate_a0 import (  # noqa: F401
    A0TheoryProvenance,
    advect_points,
    advected_relaxation_step,
    require_a0_force_ready,
)
