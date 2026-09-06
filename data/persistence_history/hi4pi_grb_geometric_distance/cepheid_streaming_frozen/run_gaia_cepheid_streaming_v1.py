#!/usr/bin/env python3
"""Serialization-only runner for frozen Gaia-Cepheid streaming V1.

This wrapper does not alter any scientific calculation. It only teaches the
standard JSON encoder to convert NumPy scalar types to native Python scalars.
"""
import importlib.util
import json
from pathlib import Path
import numpy as np

_original_dumps = json.dumps

def _numpy_default(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def _dumps(obj, *args, **kwargs):
    kwargs.setdefault("default", _numpy_default)
    return _original_dumps(obj, *args, **kwargs)

json.dumps = _dumps
path = Path(__file__).with_name("build_gaia_cepheid_streaming_v1.py")
spec = importlib.util.spec_from_file_location("gaia_cepheid_streaming_v1_frozen", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.main()
