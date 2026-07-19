from pathlib import Path

from fastapi.testclient import TestClient

from mlops_course.api import app, reset_model_cache
from mlops_course.data import load_contract, load_dataset
from mlops_course.train import train_model


def _ensure_model():
    path = Path("artifacts/model.joblib")
    if not path.exists():
        train_model(
            Path("data/train.csv"),
            Path("configs/data_contract.json"),
            path,
            Path("artifacts/train_metrics.json"),
        )
    reset_model_cache()


def test_health_endpoint():
    _ensure_model()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "service_version" in payload
    assert "model_version" in payload


def test_ready_endpoint_loads_model():
    _ensure_model()
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_predict_endpoint():
    _ensure_model()
    contract = load_contract("configs/data_contract.json")
    frame = load_dataset("data/test.csv", contract)
    features = frame[contract["feature_columns"]].iloc[0].tolist()
    with TestClient(app) as client:
        response = client.post("/predict", json={"features": features})
    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction"] in [0, 1]
    assert 0.0 <= payload["probability"] <= 1.0


def test_predict_rejects_wrong_feature_count():
    _ensure_model()
    with TestClient(app) as client:
        response = client.post("/predict", json={"features": [1.0, 2.0]})
    assert response.status_code == 422
