from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "analyze_drift.py"
spec = importlib.util.spec_from_file_location("analyze_drift", MODULE_PATH)
analyze_drift = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(analyze_drift)


def test_psi_is_zero_for_identical_data():
    values = np.linspace(-2, 2, 1000)
    assert analyze_drift.population_stability_index(values, values) < 1e-9


def test_psi_detects_large_shift():
    reference = np.linspace(-2, 2, 1000)
    current = reference + 3.0
    assert analyze_drift.population_stability_index(reference, current) > 0.20


def test_course_drift_scenario_is_detected():
    report = analyze_drift.analyze_pair(
        ROOT / "data/production_normal.csv",
        ROOT / "data/production_drift.csv",
        ROOT / "configs/data_contract.json",
        ROOT / "artifacts/model.joblib",
    )
    assert report["summary"]["drift_detected"] is True
    assert {"feature_00", "feature_01", "feature_02"}.intersection(
        report["summary"]["drifted_features"]
    )
