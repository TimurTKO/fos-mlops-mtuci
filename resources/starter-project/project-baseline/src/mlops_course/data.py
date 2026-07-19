from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_contract(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_dataset(path: str | Path, contract: dict, require_target: bool = True) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = list(contract["feature_columns"])
    if require_target:
        required.append(contract["target_column"])
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    feature_columns = contract["feature_columns"]
    non_numeric = [column for column in feature_columns if not pd.api.types.is_numeric_dtype(frame[column])]
    if non_numeric:
        raise TypeError(f"Non-numeric feature columns: {non_numeric}")
    if frame[feature_columns].isna().any().any():
        raise ValueError("Feature columns contain missing values")
    if require_target:
        target = contract["target_column"]
        allowed = set(contract["target_values"])
        observed = set(frame[target].dropna().astype(int).unique())
        if not observed.issubset(allowed):
            raise ValueError(f"Unexpected target values: {sorted(observed - allowed)}")
    return frame
