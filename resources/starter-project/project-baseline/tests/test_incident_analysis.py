from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "investigate_incident.py"
spec = importlib.util.spec_from_file_location("investigate_incident", MODULE_PATH)
investigate_incident = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(investigate_incident)


def _classify(filename: str):
    return investigate_incident.classify_incident(
        ROOT / "data/production_normal.csv",
        ROOT / f"data/{filename}",
        ROOT / "configs/data_contract.json",
        ROOT / "artifacts/model.joblib",
    )


def test_bad_schema_is_classified_before_model_inference():
    report = _classify("incident_bad_schema.csv")
    assert report["scenario"] == "data_contract_violation"
    assert report["severity"] == "high"


def test_shifted_data_is_not_automatically_called_quality_failure():
    report = _classify("production_drift.csv")
    assert report["scenario"] == "data_drift_without_confirmed_quality_degradation"


def test_degraded_relationship_can_escape_univariate_psi():
    report = _classify("incident_degraded.csv")
    assert report["scenario"] == "quality_degradation_without_univariate_data_drift"
