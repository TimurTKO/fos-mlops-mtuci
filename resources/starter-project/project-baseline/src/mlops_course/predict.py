from __future__ import annotations

from pathlib import Path
from typing import Sequence

import joblib
import pandas as pd


def load_model(path: str | Path):
    payload = joblib.load(path)
    if "pipeline" not in payload or "feature_columns" not in payload:
        raise ValueError("Model artifact has invalid structure")
    return payload


def predict_one(model_payload, values: Sequence[float]) -> dict:
    columns = model_payload["feature_columns"]
    if len(values) != len(columns):
        raise ValueError(f"Expected {len(columns)} features, got {len(values)}")
    frame = pd.DataFrame([list(values)], columns=columns)
    pipeline = model_payload["pipeline"]
    prediction = int(pipeline.predict(frame)[0])
    probability = float(pipeline.predict_proba(frame)[0, 1])
    return {"prediction": prediction, "probability": probability}
