from pathlib import Path

from sklearn.metrics import f1_score

from mlops_course.data import load_contract, load_dataset
from mlops_course.predict import load_model, predict_one
from mlops_course.train import train_model


def _ensure_model():
    path = Path("artifacts/model.joblib")
    if not path.exists():
        train_model(Path("data/train.csv"), Path("configs/data_contract.json"), path, Path("artifacts/train_metrics.json"))
    return path


def test_model_roundtrip_and_prediction_shape():
    payload = load_model(_ensure_model())
    contract = load_contract("configs/data_contract.json")
    frame = load_dataset("data/test.csv", contract)
    result = predict_one(payload, frame[contract["feature_columns"]].iloc[0].tolist())
    assert result["prediction"] in {0, 1}
    assert 0.0 <= result["probability"] <= 1.0


def test_model_meets_baseline_f1():
    payload = load_model(_ensure_model())
    contract = load_contract("configs/data_contract.json")
    frame = load_dataset("data/test.csv", contract)
    predictions = payload["pipeline"].predict(frame[contract["feature_columns"]])
    assert f1_score(frame[contract["target_column"]], predictions) >= 0.70
