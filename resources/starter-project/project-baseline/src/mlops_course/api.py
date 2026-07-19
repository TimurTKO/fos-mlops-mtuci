from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from mlops_course.monitoring import (
    configure_build_info,
    observe_prediction,
    prometheus_middleware,
    set_model_ready,
)
from mlops_course.predict import load_model, predict_one

MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/model.joblib"))
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "dev")
MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-dev")
RELEASE_CHANNEL = os.getenv("RELEASE_CHANNEL", "local")
_model = None


class PredictionRequest(BaseModel):
    features: list[float] = Field(min_length=12, max_length=12)


class PredictionResponse(BaseModel):
    prediction: int
    probability: float


def reset_model_cache() -> None:
    """Reset the lazy-loaded model; primarily useful for isolated tests."""
    global _model
    _model = None
    set_model_ready(False)


def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            set_model_ready(False)
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        try:
            _model = load_model(MODEL_PATH)
        except (OSError, ValueError):
            set_model_ready(False)
            raise
        set_model_ready(True)
    return _model


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_build_info(
        service_version=SERVICE_VERSION,
        model_version=MODEL_VERSION,
        release_channel=RELEASE_CHANNEL,
    )
    if os.getenv("SIMULATE_STARTUP_FAILURE", "0") == "1":
        raise RuntimeError("Simulated startup failure for rollback laboratory")
    if os.getenv("PRELOAD_MODEL", "0") == "1":
        get_model()
    yield


app = FastAPI(
    title="MLOps Course Baseline API",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)
app.middleware("http")(prometheus_middleware)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service_version": SERVICE_VERSION,
        "model_version": MODEL_VERSION,
        "release_channel": RELEASE_CHANNEL,
        "model_exists": MODEL_PATH.exists(),
    }


@app.get("/ready")
def ready() -> dict:
    try:
        get_model()
    except (FileNotFoundError, OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return {
        "status": "ready",
        "service_version": SERVICE_VERSION,
        "model_version": MODEL_VERSION,
    }


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    try:
        result = predict_one(get_model(), request.features)
        observe_prediction(
            prediction=result["prediction"], probability=result["probability"]
        )
        return PredictionResponse(**result)
    except (ValueError, FileNotFoundError, OSError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
