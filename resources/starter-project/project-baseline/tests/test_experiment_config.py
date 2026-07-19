from pathlib import Path

import yaml


def test_dvc_pipeline_and_params_are_consistent():
    params = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))
    pipeline = yaml.safe_load(Path("dvc.yaml").read_text(encoding="utf-8"))
    assert params["data"]["random_state"] == 42
    assert params["train"]["C"] > 0
    assert {"generate_data", "train"}.issubset(pipeline["stages"])
    assert "artifacts/metrics.json" in pipeline["stages"]["train"]["metrics"]
