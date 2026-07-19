from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "smoke_test.py"
spec = importlib.util.spec_from_file_location("smoke_test", MODULE_PATH)
smoke_test = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(smoke_test)


def test_default_feature_vector_matches_api_contract():
    assert len(smoke_test.DEFAULT_FEATURES) == 12
    assert all(isinstance(value, float) for value in smoke_test.DEFAULT_FEATURES)


def test_smoke_error_is_runtime_error():
    assert issubclass(smoke_test.SmokeTestError, RuntimeError)
