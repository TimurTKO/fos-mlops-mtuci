from pathlib import Path

from mlops_course.train import train_model


def test_training_uses_independent_test_set(tmp_path: Path):
    model = tmp_path / "model.joblib"
    metrics = tmp_path / "metrics.json"
    result = train_model(
        Path("data/train.csv"),
        Path("configs/data_contract.json"),
        model,
        metrics,
        Path("data/test.csv"),
        c=0.5,
    )
    assert model.exists()
    assert metrics.exists()
    assert result["test_f1"] >= 0.70
    assert result["C"] == 0.5
